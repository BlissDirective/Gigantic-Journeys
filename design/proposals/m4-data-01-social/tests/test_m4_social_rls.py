"""M4-DATA-01 draft: RLS, privilege and rate-limit tests on a throwaway PostgreSQL.

Starts a private PostgreSQL cluster (initdb + pg_ctl on a Unix socket in a temp dir),
loads a minimal Supabase stand-in (``supabase_stub.sql``), the applied environments
migration (AUTH #034) and the draft social migration, then drives the policies as
anon, two signed-in users plus a third, and the service role (SECURITY_CHECKLIST §2.2
"two users plus anon"; §10.2 rate limits). Every test gets a fresh database cloned
from a template, so tests never see each other's writes.

Skipped when no PostgreSQL server binaries are found (set ``GJ_PG_BIN`` to the
directory holding ``initdb``/``pg_ctl``; GitHub's ubuntu runners ship them under
/usr/lib/postgresql/<v>/bin). ``psql`` must be on PATH.
"""

from __future__ import annotations

import itertools
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent
REPO = PROPOSAL.parents[2]
ENV_MIGRATION = REPO / "supabase" / "migrations" / "20260926120000_m1_environments_staging.sql"
SOCIAL_MIGRATION = PROPOSAL / "20261101000000_m4_social.sql"

A = "aaaaaaaa-0000-4000-8000-000000000001"  # creator of most environments
B = "bbbbbbbb-0000-4000-8000-000000000002"  # a player
C = "cccccccc-0000-4000-8000-000000000003"  # another player
E_PUB = "e0000000-0000-4000-8000-000000000001"  # A: published + cleared
E_PUB2 = "e0000000-0000-4000-8000-000000000002"  # A: published + cleared
E_PUB3 = "e0000000-0000-4000-8000-000000000003"  # A: published + cleared
E_DRAFT = "e0000000-0000-4000-8000-000000000004"  # A: ready, moderation pending
E_REVIEW = "e0000000-0000-4000-8000-000000000005"  # A: ready, under review
E_CLEARED_UNPUB = "e0000000-0000-4000-8000-000000000006"  # A: cleared, not published
E_B_PUB = "e0000000-0000-4000-8000-000000000007"  # B: published + cleared
DEV_B = "b" * 32
DEV_C = "c" * 32
DEV_SHARED = "d" * 32

SEED = f"""
insert into auth.users (id) values ('{A}'), ('{B}'), ('{C}');
insert into public.environments (id, user_id, scan_id, status, moderation_state) values
    ('{E_PUB}', '{A}', 's1', 'published', 'cleared'),
    ('{E_PUB2}', '{A}', 's2', 'published', 'cleared'),
    ('{E_PUB3}', '{A}', 's3', 'published', 'cleared'),
    ('{E_DRAFT}', '{A}', 's4', 'ready', 'pending'),
    ('{E_REVIEW}', '{A}', 's5', 'ready', 'under_review'),
    ('{E_CLEARED_UNPUB}', '{A}', 's6', 'ready', 'cleared'),
    ('{E_B_PUB}', '{B}', 's7', 'published', 'cleared');
insert into public.publishes (environment_id, user_id, outcome, rejection_reason) values
    ('{E_DRAFT}', '{A}', 'rejected', 'Private information is visible.');
insert into public.leaderboard_times
    (environment_id, route_id, user_id, device_hash, session_id, time_ms, status) values
    ('{E_PUB}', 'summit', '{B}', '{DEV_B}', gen_random_uuid(), 41000, 'accepted'),
    ('{E_PUB}', 'summit', '{B}', '{DEV_B}', gen_random_uuid(), 39000, 'pending'),
    ('{E_PUB}', 'summit', '{C}', '{DEV_C}', gen_random_uuid(), 900, 'rejected'),
    ('{E_DRAFT}', 'summit', '{A}', '{"a" * 32}', gen_random_uuid(), 50000, 'accepted');
insert into public.reports (environment_id, reporter_id, device_hash, reason) values
    ('{E_B_PUB}', '{C}', '{DEV_C}', 'broken_environment');
insert into public.moderation_actions (environment_id, actor, action, reason) values
    ('{E_DRAFT}', 'vision', 'auto_flag', 'low confidence');
"""


class SqlError(Exception):
    """psql exited non-zero; the message carries stderr."""


def _pg_bin() -> Path | None:
    env = os.environ.get("GJ_PG_BIN")
    if env and (Path(env) / "initdb").exists():
        return Path(env)
    found = shutil.which("initdb")
    if found:
        return Path(found).parent
    candidates = sorted(Path("/usr/lib/postgresql").glob("*/bin/initdb"), reverse=True)
    return candidates[0].parent if candidates else None


def _setup(base: list[str], dbname: str, *args: str) -> None:
    proc = subprocess.run([*base, "-d", dbname, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"setup failed ({' '.join(args)[:60]}): {proc.stderr.strip()}")


@pytest.fixture(scope="module")
def cluster():
    """A private cluster with a template database holding stub + migrations + seed."""
    pg_bin = _pg_bin()
    if pg_bin is None or shutil.which("psql") is None:
        pytest.skip("PostgreSQL server binaries or psql not found (set GJ_PG_BIN)")
    root = Path(tempfile.mkdtemp(prefix="gjpg"))
    data, sock = root / "data", root / "s"
    sock.mkdir()
    port = str(55000 + os.getpid() % 5000)
    subprocess.run(
        [str(pg_bin / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust"],
        check=True,
        capture_output=True,
    )
    opts = f"-p {port} -k {sock} -c listen_addresses='' -c fsync=off"
    # -l sends the server log to a file: the postmaster must not inherit a pipe we wait on
    subprocess.run(
        [
            str(pg_bin / "pg_ctl"),
            "-D",
            str(data),
            "-o",
            opts,
            "-l",
            str(root / "pg.log"),
            "-w",
            "start",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = ["psql", "-h", str(sock), "-p", port, "-U", "postgres", "-X", "-q", "-tA"]
    base += ["-v", "ON_ERROR_STOP=1"]
    try:
        _setup(base, "postgres", "-c", "create database tpl")
        for f in (HERE / "supabase_stub.sql", ENV_MIGRATION, SOCIAL_MIGRATION):
            _setup(base, "tpl", "-f", str(f))
        _setup(base, "tpl", "-c", SEED)
        yield base
    finally:
        subprocess.run(
            [str(pg_bin / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"],
            capture_output=True,
        )
        shutil.rmtree(root, ignore_errors=True)


_counter = itertools.count()


class Db:
    """Runs SQL as a given API role (and signed-in user) in a per-test database."""

    def __init__(self, base: list[str], name: str):
        self.base, self.name = base, name

    def run(self, sql: str, role: str | None = None, uid: str | None = None) -> list[str]:
        prefix = ""
        if role:
            prefix += f"set role {role};\n"
        if uid:
            prefix += f"select set_config('request.jwt.claim.sub', '{uid}', false) \\g /dev/null\n"
        proc = subprocess.run(
            [*self.base, "-d", self.name],
            input=prefix + sql,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise SqlError(proc.stderr.strip())
        return [line for line in proc.stdout.splitlines() if line]

    def as_user(self, uid: str, sql: str) -> list[str]:
        return self.run(sql, role="authenticated", uid=uid)

    def as_anon(self, sql: str) -> list[str]:
        return self.run(sql, role="anon")

    def as_service(self, sql: str) -> list[str]:
        return self.run(sql, role="service_role")

    def count(self, table: str, role: str | None, uid: str | None = None, where: str = "") -> int:
        clause = f" where {where}" if where else ""
        return int(self.run(f"select count(*) from public.{table}{clause};", role, uid)[0])


@pytest.fixture
def db(cluster):
    name = f"t{next(_counter)}"
    _setup(cluster, "postgres", "-c", f"create database {name} template tpl")
    yield Db(cluster, name)
    _setup(cluster, "postgres", "-c", f"drop database {name}")


def rate(env: str, device: str, uid: str) -> str:
    return (
        "insert into public.ratings (environment_id, user_id, device_hash, fun) "
        f"values ('{env}', '{uid}', '{device}', 4);"
    )


def report(env: str, uid: str, device: str, reason: str = "other", **extra: str) -> str:
    cols = "environment_id, reporter_id, device_hash, reason" + "".join(f", {k}" for k in extra)
    vals = f"'{env}', '{uid}', '{device}', '{reason}'" + "".join(f", {v}" for v in extra.values())
    return f"insert into public.reports ({cols}) values ({vals});"


def submit_time(env: str, uid: str, device: str, time_ms: int = 30000, **extra: str) -> str:
    cols = "environment_id, route_id, user_id, device_hash, session_id, time_ms"
    cols += "".join(f", {k}" for k in extra)
    vals = f"'{env}', 'summit', '{uid}', '{device}', gen_random_uuid(), {time_ms}"
    vals += "".join(f", {v}" for v in extra.values())
    return f"insert into public.leaderboard_times ({cols}) values ({vals});"


# ---------- AT-1: RLS on every table + the mechanical check ----------


def test_every_public_table_has_rls_enabled(db):
    rows = db.run(
        "select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity;"
    )
    assert rows == []


def test_check_rls_passes_on_the_draft():
    import sys

    sys.path.insert(0, str(REPO / "supabase" / "scripts"))
    import check_rls

    assert check_rls.violations(SOCIAL_MIGRATION.read_text(encoding="utf-8")) == []


# ---------- AT-2: visibility (two users + anon) ----------


@pytest.mark.parametrize("env", [E_DRAFT, E_REVIEW, E_CLEARED_UNPUB])
def test_unpublished_or_uncleared_environment_is_invisible_to_others(db, env):
    assert db.count("environments", "anon", where=f"id = '{env}'") == 0
    assert db.count("environments", "authenticated", B, where=f"id = '{env}'") == 0
    assert db.count("environments", "authenticated", A, where=f"id = '{env}'") == 1


def test_published_and_cleared_environment_is_readable(db):
    assert db.count("environments", "anon", where=f"id = '{E_PUB}'") == 1
    assert db.count("environments", "authenticated", B, where=f"id = '{E_PUB}'") == 1


@pytest.mark.parametrize("table", ["moderation_actions", "rate_limit_rules"])
def test_service_role_only_tables_are_closed_to_clients(db, table):
    for role, uid in (("anon", None), ("authenticated", A), ("authenticated", B)):
        with pytest.raises(SqlError, match="permission denied"):
            db.count(table, role, uid)
    assert db.count(table, "service_role") >= 1


def test_clients_cannot_write_the_moderation_queue(db):
    sql = (
        "insert into public.moderation_actions (environment_id, actor, action) "
        f"values ('{E_PUB}', 'owner', 'clear');"
    )
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(A, sql)
    db.as_service(sql)


def test_publishes_are_owner_read_and_server_written(db):
    assert db.count("publishes", "authenticated", A) == 1
    assert db.count("publishes", "authenticated", B) == 0
    with pytest.raises(SqlError, match="permission denied"):
        db.count("publishes", "anon")
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(
            A,
            f"update public.publishes set outcome = 'cleared' where environment_id = '{E_DRAFT}';",
        )
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(
            A, f"insert into public.publishes (environment_id, user_id) values ('{E_PUB}', '{A}');"
        )


# ---------- ratings ----------


def test_player_can_rate_a_public_environment(db):
    db.as_user(B, rate(E_PUB, DEV_B, B))
    assert db.count("ratings", "authenticated", B) == 1


def test_rating_rules(db):
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(A, rate(E_PUB, "a" * 32, A))  # self-rating
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(B, rate(E_DRAFT, DEV_B, B))  # not public
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(B, rate(E_PUB, DEV_B, C))  # as someone else
    db.as_user(B, rate(E_PUB, DEV_B, B))
    with pytest.raises(SqlError, match="ratings_one_per_user"):
        db.as_user(B, rate(E_PUB, DEV_B, B))


@pytest.mark.parametrize(
    "values",
    [
        "fun) values ('{e}', '{u}', '{d}', 6",
        "fun) values ('{e}', '{u}', '{d}', 0",
        "fun) values ('{e}', '{u}', '{d}', null",
    ],
)
def test_rating_values_are_bounded_and_not_empty(db, values):
    sql = (
        "insert into public.ratings (environment_id, user_id, device_hash, "
        + values.format(e=E_PUB, u=B, d=DEV_B)
        + ");"
    )
    with pytest.raises(SqlError, match="check constraint"):
        db.as_user(B, sql)


def test_ratings_are_visible_to_rater_and_creator_only(db):
    db.as_user(B, rate(E_PUB, DEV_B, B))
    assert db.count("ratings", "authenticated", B) == 1
    assert db.count("ratings", "authenticated", A) == 1  # creator stats
    assert db.count("ratings", "authenticated", C) == 0
    with pytest.raises(SqlError, match="permission denied"):
        db.count("ratings", "anon")


def test_rerating_changes_only_the_axes(db):
    db.as_user(B, rate(E_PUB, DEV_B, B))
    db.as_user(B, "update public.ratings set fun = 2;")
    assert db.as_service("select fun from public.ratings;") == ["2"]
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(B, f"update public.ratings set environment_id = '{E_PUB2}';")
    assert db.as_user(C, "update public.ratings set fun = 1 returning id;") == []


# ---------- reports ----------


def test_report_is_private_to_the_reporter(db):
    db.as_user(
        B,
        report(E_PUB, B, DEV_B, "not_a_real_place"),
    )
    assert db.count("reports", "authenticated", B) == 1
    assert db.count("reports", "authenticated", A) == 0  # the creator never sees who reported
    assert db.count("reports", "authenticated", C) == 1  # only C's own seeded report
    assert db.count("reports", "service_role") == 2


def test_report_state_is_server_owned(db):
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(
            B,
            report(E_PUB, B, DEV_B, state="'dismissed'"),
        )
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(C, "update public.reports set state = 'dismissed';")
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(
            B,
            report(E_DRAFT, B, DEV_B),
        )


# ---------- leaderboard_times ----------


def test_public_leaderboard_shows_only_accepted_times_on_public_environments(db):
    assert db.as_anon("select time_ms from public.leaderboard_times order by 1;") == ["41000"]
    assert db.count("leaderboard_times", "authenticated", C) == 2  # accepted + own rejected


def test_runner_and_creator_see_their_submissions(db):
    assert db.count("leaderboard_times", "authenticated", B) == 2  # accepted + own pending
    assert db.count("leaderboard_times", "authenticated", A) == 4  # everything on A's envs


def test_times_enter_as_pending_and_only_the_server_validates(db):
    db.as_user(B, submit_time(E_PUB, B, DEV_B))
    assert db.as_service(
        f"select status from public.leaderboard_times where user_id = '{B}' and time_ms = 30000;"
    ) == ["pending"]
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(B, submit_time(E_PUB, B, DEV_B, status="'accepted'"))
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(B, "update public.leaderboard_times set status = 'accepted';")
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(B, submit_time(E_DRAFT, B, DEV_B))


# ---------- user_blocks ----------


def test_blocks_are_owner_only(db):
    db.as_user(B, f"insert into public.user_blocks (blocker_id, blocked_id) values ('{B}', '{C}');")
    assert db.count("user_blocks", "authenticated", B) == 1
    assert db.count("user_blocks", "authenticated", C) == 0  # the blocked user cannot tell
    assert db.count("user_blocks", "authenticated", A) == 0
    with pytest.raises(SqlError, match="row-level security"):
        db.as_user(
            A, f"insert into public.user_blocks (blocker_id, blocked_id) values ('{B}', '{A}');"
        )
    with pytest.raises(SqlError, match="user_blocks_not_self"):
        db.as_user(
            B, f"insert into public.user_blocks (blocker_id, blocked_id) values ('{B}', '{B}');"
        )
    db.as_user(B, "delete from public.user_blocks;")
    assert db.count("user_blocks", "service_role") == 0


# ---------- AT-3: rate limits per user and per device ----------


def _limit(db, table: str, per_user: int, per_device: int) -> None:
    db.run(
        f"update public.rate_limit_rules set max_per_user = {per_user}, "
        f"max_per_device = {per_device} where table_name = '{table}';"
    )


def test_ratings_rate_limited_per_user(db):
    _limit(db, "ratings", 2, 99)
    db.as_user(B, rate(E_PUB, DEV_B, B))
    db.as_user(B, rate(E_PUB2, "e" * 32, B))  # a new device does not reset the user count
    with pytest.raises(SqlError, match="rate limit exceeded for ratings"):
        db.as_user(B, rate(E_PUB3, "f" * 32, B))


def test_ratings_rate_limited_per_device_across_accounts(db):
    _limit(db, "ratings", 99, 2)
    db.as_user(B, rate(E_PUB, DEV_SHARED, B))
    db.as_user(C, rate(E_PUB, DEV_SHARED, C))
    with pytest.raises(SqlError, match="rate limit exceeded"):
        db.as_user(C, rate(E_PUB2, DEV_SHARED, C))


def test_reports_rate_limited(db):
    _limit(db, "reports", 1, 99)
    db.as_user(B, report(E_PUB, B, DEV_B))
    with pytest.raises(SqlError, match="rate limit exceeded for reports"):
        db.as_user(B, report(E_PUB2, B, DEV_B))


def test_leaderboard_submissions_rate_limited(db):
    _limit(db, "leaderboard_times", 99, 2)  # DEV_B already has 2 seeded rows in the window
    with pytest.raises(SqlError, match="rate limit exceeded for leaderboard_times"):
        db.as_user(B, submit_time(E_PUB, B, DEV_B))


def test_old_rows_fall_out_of_the_window(db):
    _limit(db, "leaderboard_times", 99, 2)
    db.run("update public.leaderboard_times set created_at = now() - interval '1 hour';")
    db.as_user(B, submit_time(E_PUB, B, DEV_B))


def test_clients_cannot_backdate_rows_to_dodge_the_window(db):
    with pytest.raises(SqlError, match="permission denied"):
        db.as_user(
            B,
            "insert into public.ratings (environment_id, user_id, device_hash, fun, created_at) "
            f"values ('{E_PUB}', '{B}', '{DEV_B}', 3, now() - interval '1 day');",
        )


def test_service_role_is_not_rate_limited(db):
    _limit(db, "ratings", 1, 1)
    db.as_service(rate(E_PUB, DEV_B, B))
    db.as_service(rate(E_PUB2, DEV_B, B))
    assert db.count("ratings", "service_role") == 2


def test_rate_limit_error_code_is_stable(db):
    _limit(db, "ratings", 1, 99)
    db.as_user(B, rate(E_PUB, DEV_B, B))
    with pytest.raises(SqlError, match="P0429"):
        db.as_user(B, "\\set VERBOSITY verbose\n" + rate(E_PUB2, DEV_B, B))
