-- Fixture (M0-PLAT-01 AT-3): a compliant migration. Never applied; check_rls.py must pass it.
create table public.fixture_notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.fixture_notes enable row level security;
create policy fixture_notes_owner on public.fixture_notes
  for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());
