# `supabase/`

Owner: gj-platform

Migrations, RLS policies, edge functions. Rule: every table has RLS enabled and at least one policy in the same migration, enforced by `supabase/scripts/check_rls.py` (M0-PLAT-01). Table creation needs an AUTH (data schema).

First migration: `migrations/20260926120000_m1_environments_staging.sql` (M1 `environments` table + private storage bucket + RLS) — **APPROVED #034**, **applied to STAGING 2026-09-26** by gj-operator (M1-PLAT-01; evidence `qa/reports/M1-PLAT-01.md`). Align `environment_spec` with M1-DATA-01 when it freezes. `scripts/check_rls.py` enforces the rule in CI (the `governance` workflow's `rls` job): every table created in a migration must enable RLS + have at least one policy in the same migration.

## Policy patterns (SECURITY_CHECKLIST §2.2)

| Pattern | Use for | Shape |
|---|---|---|
| **owner-only** | drafts, a user's own rows, creator stats | `for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid())` |
| **published-read** | public browse/play | `for select to anon, authenticated using (status = 'published' and moderation_state = 'cleared')` |
| **service-role-only** | moderation queue, ranking jobs, pipeline writes | RLS enabled with **no client policy** for that path; the service role bypasses RLS server-side. A table that is service-role-only still needs RLS on; add an explicit deny-all or owner-read policy so `check_rls.py` passes. |

Storage follows the same rule: private buckets, owner-prefixed object paths (`{user_id}/…`), and delivery only through ≤15-min signed URLs issued server-side (`functions/environment-urls/`).

## Local

`config.toml` is the local-dev config (`supabase start`). Auth mirrors staging: email sign-in with confirmation required, anonymous sign-in off, minimum password length 8; Apple and Google (§9.3) are present but disabled until the Owner creates the OAuth clients, with secrets only via `env()`. `functions.environment-urls.verify_jwt = true`. No keys or project refs live in this directory.

## Staging (gj-operator; staging credentials only, never production)

- **Apply a migration** (after its AUTH): the staging DB is IPv6-only on the direct host, so use the session pooler — `psql -h aws-0-ca-central-1.pooler.supabase.com -p 5432 -U postgres.$SUPABASE_PROJECT_REF -d postgres -v ON_ERROR_STOP=1 --single-transaction -f migrations/<file>.sql`, then record the version in `supabase_migrations.schema_migrations` (the table `supabase db push` uses) in the same transaction. Password: `SUPABASE_STAGING_DB_PASSWORD` from `.env.local`.
- **Smoke test**: `set -a; . ./.env.local; set +a; python supabase/scripts/staging_smoke.py --report qa/reports/STAGING-smoke.md` — auth health + settings, anon read/insert under RLS, private bucket, RLS on every app table, pending migrations, edge-function deploy. It refuses to run against the production ref and redacts the project ref. Exit 1 on any FAIL; PENDING items need the Owner.
- **Edge functions** deploy with `supabase functions deploy <name>`, which needs a Supabase access token (account-wide, so it is an Owner/CI credential, not a Bot one).
