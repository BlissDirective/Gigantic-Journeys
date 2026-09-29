-- Fixture (M0-PLAT-01 AT-3): a non-compliant migration. Never applied; check_rls.py must fail it:
-- fixture_open has neither RLS nor a policy, fixture_half has RLS but no policy.
create table public.fixture_open (id uuid primary key default gen_random_uuid());
create table if not exists public.fixture_half (id uuid primary key default gen_random_uuid());
alter table public.fixture_half enable row level security;
