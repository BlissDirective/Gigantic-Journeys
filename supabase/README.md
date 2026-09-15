# `supabase/`

Owner: gj-platform

Migrations, RLS policies, edge functions. Rule: every table has RLS enabled and at least one policy in the same migration, enforced by `supabase/scripts/check_rls.py` (M0-PLAT-01). Table creation needs an AUTH (data schema).
