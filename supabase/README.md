# `supabase/`

Owner: gj-platform

Migrations, RLS policies, edge functions. Rule: every table has RLS enabled and at least one policy in the same migration, enforced by `supabase/scripts/check_rls.py` (M0-PLAT-01). Table creation needs an AUTH (data schema).

First migration drafted: `migrations/20260926120000_m1_environments_staging.sql` (M1 `environments` table + private storage bucket + RLS) — **DRAFT, pending AUTH #034** and M1-DATA-01's environment_spec freeze; not applied. `scripts/check_rls.py` (the enforcement) is M0-PLAT-01, not built yet.
