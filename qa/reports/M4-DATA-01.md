# M4-DATA-01 — AUTH #038 social migration applied to Supabase STAGING

Operator: gj-operator (Grok Bot) · 2026-10-02 11:45 AM CT (16:45 UTC) · target: **STAGING only**
(the staging ref is checked against `SUPABASE_PROD_PROJECT_REF` before any write; production is
CI-only, SECURITY_CHECKLIST §8.3). No keys, URLs, or project refs are recorded here.

## What was applied

- `supabase/migrations/20261002164500_m4_social.sql`: the reviewed draft
  (`design/proposals/m4-data-01-social/20261101000000_m4_social.sql`), unchanged below a new
  `APPROVED #038` header, with a current timestamp.
- Route: the session pooler (`supabase/README.md` § Staging),
  `psql -v ON_ERROR_STOP=1 --single-transaction -f <migration> -c "insert into supabase_migrations.schema_migrations (version, name) values ('20261002164500','m4_social')"`,
  so the DDL and the migration record commit together or not at all. Exit 0.
- Why not the Management API: the account's `SUPABASE_ACCESS_TOKEN` is fine-grained and lacks
  `database_read`/`database_write` (HTTP 403 on `/database/query`). It confirmed project health
  only (`ACTIVE_HEALTHY`, `ca-central-1`). The documented pooler route uses the staging DB password.

## Pre-apply checks

- Staging before: one migration (`20260926120000` AUTH #034), one public table (`environments`).
- `python supabase/scripts/check_rls.py`: `2 migration(s) OK — every created table has RLS + a policy`.
- `GJ_PG_BIN=<pg17>/bin pytest -q design/proposals/m4-data-01-social supabase`: **44 passed**
  (31 M4 RLS/rate-limit cases + 13 check_rls/smoke cases) on a user-space PostgreSQL 17.

## Live verification on staging (catalog queries)

```
== migrations
 20260926120000 | m1_environments_staging
 20261002164500 | m4_social

== public tables: RLS + policy count
       table        | rls_enabled | policies
 environments       | t           |        2
 leaderboard_times  | t           |        5
 moderation_actions | t           |        1
 publishes          | t           |        2
 rate_limit_rules   | t           |        1
 ratings            | t           |        5
 reports            | t           |        3
 user_blocks        | t           |        2
== tables lacking RLS or a policy (must be 0): 0

== rate limit rules (per rolling window: per user / per device)
 leaderboard_times |  600 s | 20 | 30
 ratings           | 3600 s | 30 | 45
 reports           | 3600 s | 10 | 15

== rate-limit triggers (BEFORE INSERT)
 leaderboard_times_rate_limit · ratings_rate_limit · reports_rate_limit

== client table grants (column-level INSERT/UPDATE grants not shown)
 leaderboard_times | anon, authenticated | SELECT
 publishes         | authenticated       | SELECT
 ratings           | authenticated       | SELECT
 reports           | authenticated       | SELECT
 user_blocks       | authenticated       | DELETE, SELECT
 moderation_actions, rate_limit_rules: no client grant

== enforce_rate_limit() executable by anon / authenticated: f / f
```

All 21 policies: `environments` owner_all + published_read; `leaderboard_times` creator_read,
owner_insert, owner_read, published_read, service_role_all; `moderation_actions` service_role_all;
`publishes` owner_read, service_role_all; `rate_limit_rules` service_role_all; `ratings`
creator_read, owner_insert, owner_read, owner_update, service_role_all; `reports` owner_insert,
owner_read, service_role_all; `user_blocks` owner_all, service_role_all.

## Live role smoke (rolled back; no rows persist)

`supabase/scripts/m4_social_live_smoke.sql` seeds two synthetic users and two environments inside
one transaction, then acts as `anon` and `authenticated` (JWT claims set per statement). It ends in
`ROLLBACK`, and a residue check confirms nothing was left behind.

```
PASS 1 anon -> moderation_actions: permission denied
PASS 2 user -> moderation_actions: permission denied
PASS 3 anon sees 1 of {published, draft} environments
PASS 4 user rates a published+cleared env
PASS 5 rating a draft: RLS violation
PASS 6 client cannot set leaderboard status
PASS 7 21st time submission in 10 min -> P0429 (rate limit exceeded for leaderboard_times)
PASS 8 anon sees 0 pending times
LIVE SMOKE: 8 PASS / 0 FAIL
== post-rollback residue (must be 0 0): users 0, envs 0
```

## Repo staging smoke

`python supabase/scripts/staging_smoke.py --report qa/reports/STAGING-smoke.md`:
**12 PASS / 0 FAIL / 0 PENDING**, including `db.rls_every_table` (8 app tables, all RLS + a policy)
and `db.migrations` (2 applied).

## Acceptance tests

| AT | Level | Evidence | Result |
|---|---|---|---|
| AT-1 RLS + a policy on every new table; the three policy patterns | required | `check_rls.py` green; live catalog: 0 tables lacking RLS/policy; policy list above | met |
| AT-2 two users + anon visibility; moderation queue service-role-only | required | `test_m4_social_rls.py` (31 pass); live smoke 1–3, 5, 8 | met |
| AT-3 per-user + per-device rate limits on ratings/reports/times | required | rate-limit tests in `test_m4_social_rls.py`; live smoke 7 (P0429); rules + triggers live | met |
| AT-4 no secret in the repo | required | this report and the smoke script hold no key, URL or ref; secret-scan CI | met (CI) |

Remaining (not this ticket): a leaderboard handle column once a profiles table exists (#038
condition — `user_id` is acceptable for internal M4 testing only); production apply rides CI at M4.
