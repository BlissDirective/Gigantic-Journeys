#!/usr/bin/env python3
"""Smoke-test the STAGING Supabase project (backend staging stand-up, AUTH #011).

Read-only except for one insert attempt that RLS must refuse. Checks:

  auth.health         GoTrue answers 200
  auth.settings       email sign-in on, email confirmation required, anonymous
                      sign-in off; Apple + Google (SECURITY_CHECKLIST §9.3) are
                      PENDING until the Owner supplies their OAuth credentials
  rest.anon_select    anon can query public.environments (table exists) and
                      sees no unpublished rows
  rest.anon_insert    anon insert into public.environments is refused (RLS)
  storage.bucket      'environments' bucket exists and is private (service role)
  storage.public_url  the public-object URL for that bucket is refused
  db.rls_every_table  every table in an app schema has RLS on + >=1 policy
  db.migrations       every file in supabase/migrations/ is recorded as applied
  fn.environment_urls edge function deployed and rejects a call with no user JWT

Environment (from .env.local; values are never printed):
  SUPABASE_URL, SUPABASE_ANON_KEY                      required
  SUPABASE_STAGING_SERVICE_ROLE_KEY                    optional (storage.bucket)
  SUPABASE_STAGING_DB_PASSWORD, SUPABASE_PROJECT_REF   optional (db.* via psql)
  SUPABASE_POOLER_HOST   session-pooler host (default: the staging region's)

Refuses to run if SUPABASE_URL points at SUPABASE_PROD_PROJECT_REF. The report
redacts the project ref and never contains a key.

Usage:
    python supabase/scripts/staging_smoke.py [--report qa/reports/STAGING-smoke.md]
Exit code: 1 if any check FAILs (PENDING does not fail).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
DEFAULT_POOLER = "aws-0-ca-central-1.pooler.supabase.com"
TIMEOUT_S = 15
# Schemas owned by Supabase itself; everything else is ours and must be RLS'd.
SYSTEM_SCHEMAS = {
    "auth",
    "storage",
    "realtime",
    "extensions",
    "graphql",
    "graphql_public",
    "pgbouncer",
    "vault",
    "supabase_functions",
    "supabase_migrations",
    "net",
    "cron",
    "pgsodium",
    "pgsodium_masks",
    "information_schema",
    "pg_catalog",
    "pg_toast",
}

PASS, FAIL, PENDING = "PASS", "FAIL", "PENDING"


def http(method: str, url: str, headers: dict[str, str], body: object | None = None):
    """Return (status, parsed-json-or-text). Never raises on HTTP errors."""
    if not url.startswith("https://"):
        raise ValueError("https only")
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method, headers=headers)  # noqa: S310
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:  # noqa: S310
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    try:
        return status, json.loads(raw or b"null")
    except ValueError:
        return status, raw.decode(errors="replace")[:200]


def auth_settings_checks(settings: dict) -> list[tuple[str, str, str]]:
    """Evaluate /auth/v1/settings against the spec (pure; unit-tested)."""
    ext = settings.get("external", {})
    out = []
    ok = ext.get("email") is True and settings.get("mailer_autoconfirm") is False
    out.append(
        (
            "auth.email",
            PASS if ok else FAIL,
            f"email={ext.get('email')} mailer_autoconfirm={settings.get('mailer_autoconfirm')}",
        )
    )
    anon = ext.get("anonymous_users")
    out.append(("auth.anonymous_off", PASS if anon is False else FAIL, f"anonymous_users={anon}"))
    for p in ("apple", "google"):
        on = ext.get(p) is True
        out.append(
            (
                f"auth.{p}",
                PASS if on else PENDING,
                "enabled" if on else "disabled — needs Owner OAuth credentials (§9.3)",
            )
        )
    return out


def rls_gaps(rows: list[tuple[str, str, bool, int]]) -> list[str]:
    """rows = (schema, table, rls_enabled, policy_count); return offenders (pure)."""
    bad = []
    for schema, table, rls, n in rows:
        if schema in SYSTEM_SCHEMAS:
            continue
        if not rls:
            bad.append(f"{schema}.{table}: RLS disabled")
        elif n < 1:
            bad.append(f"{schema}.{table}: no policy")
    return bad


def pending_migrations(files: list[str], applied: set[str]) -> list[str]:
    """Migration files whose version prefix is not recorded as applied (pure)."""
    return [f for f in sorted(files) if f.split("_", 1)[0] not in applied]


def psql(sql: str, env: dict[str, str]) -> list[list[str]]:
    ref = env["SUPABASE_PROJECT_REF"]
    host = env.get("SUPABASE_POOLER_HOST", DEFAULT_POOLER)
    penv = dict(os.environ, PGPASSWORD=env["SUPABASE_STAGING_DB_PASSWORD"])
    penv.update(PGSSLMODE="require", PGCONNECT_TIMEOUT="10")
    cmd = ["psql", "-h", host, "-p", "5432", "-U", f"postgres.{ref}", "-d", "postgres"]
    cmd += ["-X", "-At", "-F", "\t", "-c", sql]
    res = subprocess.run(cmd, env=penv, capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip().splitlines()[0] if res.stderr else "psql failed")
    return [line.split("\t") for line in res.stdout.splitlines() if line]


def run(env: dict[str, str]) -> list[tuple[str, str, str]]:
    url = env["SUPABASE_URL"].rstrip("/")
    anon = env["SUPABASE_ANON_KEY"]
    ah = {"apikey": anon, "Authorization": f"Bearer {anon}"}
    results: list[tuple[str, str, str]] = []

    s, _ = http("GET", f"{url}/auth/v1/health", ah)
    results.append(("auth.health", PASS if s == 200 else FAIL, f"HTTP {s}"))

    s, settings = http("GET", f"{url}/auth/v1/settings", ah)
    if s == 200 and isinstance(settings, dict):
        results += auth_settings_checks(settings)
    else:
        results.append(("auth.settings", FAIL, f"HTTP {s}"))

    s, body = http("GET", f"{url}/rest/v1/environments?select=id,status&limit=5", ah)
    ok = s == 200 and isinstance(body, list) and all(r.get("status") == "published" for r in body)
    results.append(
        (
            "rest.anon_select",
            PASS if ok else FAIL,
            f"HTTP {s}, rows={len(body) if isinstance(body, list) else '-'}",
        )
    )

    probe = {"user_id": "00000000-0000-0000-0000-000000000000", "scan_id": "smoke-rls-probe"}
    s, body = http("POST", f"{url}/rest/v1/environments", ah, probe)
    code = body.get("code") if isinstance(body, dict) else None
    results.append(
        ("rest.anon_insert", PASS if s in (401, 403) else FAIL, f"HTTP {s} {code or ''}".strip())
    )

    svc = env.get("SUPABASE_STAGING_SERVICE_ROLE_KEY")
    if svc:
        sh = {"apikey": svc, "Authorization": f"Bearer {svc}"}
        s, body = http("GET", f"{url}/storage/v1/bucket/environments", sh)
        ok = s == 200 and isinstance(body, dict) and body.get("public") is False
        pub = body.get("public") if isinstance(body, dict) else None
        results.append(("storage.bucket", PASS if ok else FAIL, f"HTTP {s} public={pub}"))
    else:
        results.append(("storage.bucket", PENDING, "no staging service-role key in env"))

    s, _ = http("GET", f"{url}/storage/v1/object/public/environments/smoke/none.bin", {})
    results.append(
        ("storage.public_url", PASS if s != 200 else FAIL, f"HTTP {s} (must not be 200)")
    )

    if (
        env.get("SUPABASE_STAGING_DB_PASSWORD")
        and env.get("SUPABASE_PROJECT_REF")
        and shutil.which("psql")
    ):
        try:
            rows = psql(
                "select n.nspname, c.relname, c.relrowsecurity, "
                "(select count(*) from pg_policies p "
                "where p.schemaname=n.nspname and p.tablename=c.relname) "
                "from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                "where c.relkind in ('r','p') order by 1,2",
                env,
            )
            typed = [(r[0], r[1], r[2] == "t", int(r[3])) for r in rows]
            app = [t for t in typed if t[0] not in SYSTEM_SCHEMAS]
            bad = rls_gaps(typed)
            detail = "; ".join(bad) if bad else f"{len(app)} app table(s), all RLS + policy"
            results.append(("db.rls_every_table", FAIL if bad else PASS, detail))
            applied = {
                r[0]
                for r in psql(
                    "select version from supabase_migrations.schema_migrations "
                    "where to_regclass('supabase_migrations.schema_migrations') is not null",
                    env,
                )
            }
            files = [p.name for p in MIGRATIONS.glob("*.sql")]
            todo = pending_migrations(files, applied)
            results.append(
                (
                    "db.migrations",
                    FAIL if todo else PASS,
                    f"pending: {todo}" if todo else f"{len(files)} applied",
                )
            )
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            results.append(
                ("db.connect", FAIL, str(e).replace(env["SUPABASE_PROJECT_REF"], "<ref>"))
            )
    else:
        results.append(("db.rls_every_table", PENDING, "no DB password / psql; skipped"))

    s, body = http("POST", f"{url}/functions/v1/environment-urls", {"apikey": anon}, {})
    if s == 404:
        results.append(
            ("fn.environment_urls", PENDING, "not deployed (needs `supabase functions deploy`)")
        )
    else:
        results.append(
            ("fn.environment_urls", PASS if s == 401 else FAIL, f"HTTP {s} without user JWT")
        )
    return results


def render(results: list[tuple[str, str, str]]) -> str:
    now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Staging Supabase smoke",
        "",
        f"Run: {now} · `python supabase/scripts/staging_smoke.py` · "
        "target: STAGING project (ref redacted).",
        "No keys, URLs, or project refs are recorded here.",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    lines += [f"| `{n}` | {r} | {d} |" for n, r, d in results]
    counts = {k: sum(1 for _, r, _ in results if r == k) for k in (PASS, FAIL, PENDING)}
    lines += [
        "",
        f"Totals: {counts[PASS]} PASS · {counts[FAIL]} FAIL · {counts[PENDING]} PENDING",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", type=Path, help="write the markdown report here")
    args = ap.parse_args(argv)
    env = dict(os.environ)
    for k in ("SUPABASE_URL", "SUPABASE_ANON_KEY"):
        if not env.get(k):
            print(f"missing {k} (source .env.local)", file=sys.stderr)
            return 2
    prod = env.get("SUPABASE_PROD_PROJECT_REF")
    if prod and prod in env["SUPABASE_URL"]:
        print("refusing: SUPABASE_URL is the PRODUCTION project", file=sys.stderr)
        return 2
    results = run(env)
    report = render(results)
    ref = env.get("SUPABASE_PROJECT_REF")
    if ref:
        report = report.replace(ref, "<ref>")
    print(report)
    if args.report:
        args.report.write_text(report)
    return 1 if any(r == FAIL for _, r, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
