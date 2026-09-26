# `supabase/`

Owner: gj-platform

Migrations, RLS policies, edge functions. Rule: every table has RLS enabled and at least one policy in the same migration, enforced by `supabase/scripts/check_rls.py` (M0-PLAT-01). Table creation needs an AUTH (data schema).

First migration: `migrations/20260926120000_m1_environments_staging.sql` (M1 `environments` table + private storage bucket + RLS) — **APPROVED #034**, ready for gj-platform to apply to staging (align `environment_spec` with M1-DATA-01 when it freezes). `scripts/check_rls.py` enforces the rule in CI (the `governance` workflow's `rls` job): every table created in a migration must enable RLS + have at least one policy in the same migration.
