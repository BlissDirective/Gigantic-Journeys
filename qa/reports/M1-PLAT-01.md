# M1-PLAT-01 — Backend staging stand-up evidence

Operator: gj-operator (Grok Bot) · 2026-09-26, ~2:25–3:00 PM CT · Target: **STAGING only**.
No keys, URLs, passwords, or project refs are recorded here (refs shown as `<staging-ref>`).

Covers AUTH #011 (Supabase), #012 (Vercel), #013 (Inngest), #034 (M1 staging schema).

## 1. Credentials sanity (values never printed)

| Check | Result |
|---|---|
| `SUPABASE_URL` contains `SUPABASE_PROJECT_REF` (staging) and not `SUPABASE_PROD_PROJECT_REF` | yes / not prod |
| `SUPABASE_ANON_KEY` JWT claims | role `anon`, ref = staging |
| `SUPABASE_STAGING_SERVICE_ROLE_KEY` JWT claims | role `service_role`, ref = staging |
| Any production-ref JWT or secret key in `.env.local` | **none** |
| `SUPABASE_DB_PASSWORD` vs `SUPABASE_STAGING_DB_PASSWORD` | identical (both staging) |
| GoTrue `/auth/v1/health` with the anon key | HTTP 200 |

Note for the Owner: production Supabase credentials were found **outside** `.env.local`, in the git-ignored `.secrets-local/` directory of the main clone (see "Owner actions" in the ticket report). They were not used.

## 2. Migration applied to STAGING (AUTH #034)

Before: staging had no app tables, no buckets, and no `supabase_migrations` schema (`rest/v1/environments` → PGRST205; bucket → NoSuchBucket).

The direct DB host is IPv6-only (unreachable from the VM), so the session pooler (`aws-0-ca-central-1`) was used:

```
psql -h aws-0-ca-central-1.pooler.supabase.com -p 5432 -U postgres.<staging-ref> -d postgres \
     -v ON_ERROR_STOP=1 --single-transaction \
     -f supabase/migrations/20260926120000_m1_environments_staging.sql \
     -c "<create supabase_migrations.schema_migrations if absent; insert version 20260926120000>"
```

Output: `CREATE TYPE ×2, CREATE TABLE, CREATE INDEX ×2, CREATE FUNCTION, CREATE TRIGGER, ALTER TABLE, CREATE POLICY ×2, INSERT 0 1 (bucket), CREATE POLICY (storage.objects), CREATE SCHEMA, CREATE TABLE, INSERT 0 1 (migration record)`. One transaction, no errors.

## 3. RLS on every table + policy probe

`staging_smoke.py` `db.rls_every_table`: every table outside Supabase system schemas has `relrowsecurity = true` and ≥ 1 policy → **PASS** (1 app table: `public.environments`, 2 policies).

Two-user + anon probe, run inside a transaction that was **rolled back** (nothing persisted). Two throwaway `auth.users` rows (A, B) with `@example.invalid` emails; A owns three environments: `draft` (ready/pending), `held` (ready/cleared), `pub` (published/cleared).

| Probe | Result |
|---|---|
| Set `draft` to published while moderation pending | rejected by `environments_published_requires_cleared` |
| Owner A selects | `draft, held, pub` |
| User B selects | `pub` only |
| User B updates / deletes all rows | 0 / 0 rows affected |
| User B inserts a row with `user_id = A` | rejected by RLS |
| anon selects | `pub` only |
| REST anon `POST /rest/v1/environments` | HTTP 401, 42501 |

## 4. Vercel (#012) and Inngest (#013) — read-only

| Check | Result |
|---|---|
| Vercel `GET /v2/user` with `VERCEL_TOKEN` | authenticated |
| Vercel projects in `VERCEL_TEAM_ID` | 4 projects, **none for Gigantic Journeys** (the team is shared with the Owner's other products) |
| Inngest `GET /v1/events` with `INNGEST_SIGNING_KEY` (a production-environment key; `INNGEST_ENV=production`) | HTTP 200, 0 events |
| Inngest app synced | none (api/ has not been deployed) |

In scope as **accounts** (AUTH #012/#013 approved; ADR-0002 keeps Vercel + Inngest). A Vercel project, API deploy, and Inngest app sync are **not** in scope yet: `api/` is a local-only skeleton (M0-PIPE-01 AT-6) and the real deploy lands with M1-PIPE-01. Recommendation: create an Inngest **branch/staging environment** before that deploy so staging does not send events into Inngest `production`.

## 5. GitHub Actions secrets and variables (names only)

Secrets (27): `ASC_ISSUER_ID ASC_KEY_ID ASC_KEY_P8_BASE64 CRASH_REPORTING_KEY INNGEST_EVENT_KEY INNGEST_SIGNING_KEY SENTRY_DSN SENTRY_ORG SENTRY_PROJECT SUPABASE_ANON_KEY SUPABASE_DB_PASSWORD SUPABASE_PRODUCTION_SERVICE_ROLE_KEY SUPABASE_PROD_ANON_KEY SUPABASE_PROD_DB_PASSWORD SUPABASE_PROD_PROJECT_REF SUPABASE_PROD_SERVICE_ROLE_KEY SUPABASE_PROD_URL SUPABASE_PROJECT_REF SUPABASE_SERVICE_ROLE_KEY SUPABASE_STAGING_SERVICE_ROLE_KEY SUPABASE_URL UNITY_EMAIL UNITY_LICENSE UNITY_PASSWORD VERCEL_ORG_ID VERCEL_TEAM_ID VERCEL_TOKEN`

Variables (2): `APPLE_TEAM_ID UNITY_CI_ENABLED`. Environments: none.

Backend coverage: staging (URL, anon, service role, ref, DB password), production (URL, anon, service role, ref, DB password), Inngest (event + signing key), Vercel (token, org, team), crash reporting — **all present**.

Gaps / ambiguities for the Owner (values not inspected):
- `SUPABASE_PRODUCTION_SERVICE_ROLE_KEY` **and** `SUPABASE_PROD_SERVICE_ROLE_KEY` both exist — keep one.
- `SUPABASE_SERVICE_ROLE_KEY` is unlabeled (staging or prod?) alongside `SUPABASE_STAGING_SERVICE_ROLE_KEY` — rename or delete.
- No `SUPABASE_ACCESS_TOKEN` (needed for `supabase functions deploy` / `db push` from CI) and no `VERCEL_PROJECT_ID` (no project yet).
- Outside the backend: workflows reference `secrets.UNITY_SERIAL` and `vars.IOS_MAC_RUNNER` / `vars.TESTFLIGHT_ENABLED`, which are not set (defaults may be intentional).
- No workflow consumes the Supabase/Vercel/Inngest secrets yet.

## 6. Local scaffold (`supabase start`)

`supabase/config.toml` added (Supabase CLI 2.118.0 `init`, then GJ settings: email confirmations on, anonymous off, min password 8, Apple + Google stanzas disabled with `env()` secrets, `functions.environment-urls.verify_jwt = true`). The CLI parsed it and pulled all images, but `supabase start` on the VM fails at "Initialising schema": the realtime migrator cannot connect to the local DB container (`DBConnection.ConnectionError … connection not available`), also with `-x realtime`, and a plain two-container network test hung — a VM Docker networking problem, not a config problem. M0-PLAT-01 AT-1 stays open.

## 7. Smoke test

`supabase/scripts/staging_smoke.py` (unit tests: `supabase/scripts/tests/test_staging_smoke.py`). Latest run: `qa/reports/STAGING-smoke.md` — **9 PASS · 0 FAIL · 3 PENDING** (Apple sign-in, Google sign-in, edge-function deploy).

## 8. Acceptance summary

| AT | Status |
|---|---|
| AT-1 reachable, keys are staging | met |
| AT-2 migrations applied | met |
| AT-3 RLS every table + probe | met |
| AT-4 auth settings | email/anon met; **Apple + Google pending Owner OAuth clients** |
| AT-5 edge function deployed | **pending — needs a Supabase access token (Owner/CI)** |
| AT-6 Vercel + Inngest | met (accounts verified; deploy is M1-PIPE-01) |
| AT-7 CI secrets by name | met (ambiguities listed) |
| AT-8 no secrets in repo | met (secret-scan) |
