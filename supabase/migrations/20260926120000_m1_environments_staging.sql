-- 20260926120000_m1_environments_staging.sql
--
-- APPROVED #034 (Owner, 2026-09-26) — ready to apply to the STAGING project.
-- Table creation is AUTH-gated (supabase/README.md; SECURITY_CHECKLIST §2.5); this
-- migration carries that approval. The Operator (gj-platform; staging creds only,
-- §8.3) applies it. M1-DATA-01 will later freeze the environment_spec schema; the
-- jsonb column is flexible, so applying now is safe and its shape is validated at
-- the app layer once frozen.
--
-- Scope (why it exists): give the reconstruction pipeline somewhere to land its
-- output — the compressed splat, collision mesh, and thumbnail — with Row-Level
-- Security on every table and delivery ONLY through short-lived signed URLs issued
-- server-side after an auth check (SPEC §3, §7; SECURITY_CHECKLIST §2, §3).
-- Ratings, reports, and leaderboard times are M4 (separate, later, AUTH-gated
-- migrations). Apply to the STAGING project first.
--
-- AUTH: APPROVED #034 (Owner, 2026-09-26).

-- ---------- enums ----------
create type public.environment_status as enum
    ('processing', 'ready', 'published', 'failed', 'archived');

create type public.moderation_state as enum
    ('pending', 'under_review', 'cleared', 'rejected');

-- ---------- environments: one reconstructed, publishable environment ----------
create table public.environments (
    id                      uuid primary key default gen_random_uuid(),
    user_id                 uuid not null references auth.users (id) on delete cascade,
    scan_id                 text not null,
    status                  public.environment_status not null default 'processing',
    moderation_state        public.moderation_state   not null default 'pending',
    title                   text check (title is null or char_length(title) <= 80),
    -- storage object paths in the PRIVATE 'environments' bucket (never public URLs)
    splat_object            text,
    mesh_object             text,
    thumbnail_object        text,
    environment_spec        jsonb,           -- frozen shape arrives with M1-DATA-01
    splat_count             integer check (splat_count is null or splat_count >= 0),
    package_bytes           bigint  check (package_bytes is null or package_bytes >= 0),
    -- SECURITY_CHECKLIST §6.1: raw scan media is purged once derived assets exist
    source_media_deleted_at timestamptz,
    created_at              timestamptz not null default now(),
    updated_at              timestamptz not null default now(),
    published_at            timestamptz,
    -- a row may be 'published' only if moderation cleared it (SPEC §3.7; SECURITY_CHECKLIST §10.5)
    constraint environments_published_requires_cleared
        check (status <> 'published' or moderation_state = 'cleared')
);

create index environments_user_id_idx on public.environments (user_id);
create index environments_published_idx
    on public.environments (status, moderation_state)
    where status = 'published';

-- ---------- keep updated_at fresh ----------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

create trigger environments_set_updated_at
    before update on public.environments
    for each row execute function public.set_updated_at();

-- ---------- RLS: enable + at least one policy, in this same migration ----------
alter table public.environments enable row level security;

-- owner-only: a signed-in user fully controls their own rows (user_id = auth.uid())
create policy environments_owner_all on public.environments
    for all to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

-- published-read: anyone may read an environment only when published AND cleared
create policy environments_published_read on public.environments
    for select to anon, authenticated
    using (status = 'published' and moderation_state = 'cleared');

-- The service role (Inngest / edge functions) bypasses RLS for pipeline writes,
-- so there is deliberately no client insert/update policy for the pipeline path.

-- ---------- private storage bucket for environment assets ----------
insert into storage.buckets (id, name, public)
values ('environments', 'environments', false)
on conflict (id) do nothing;

-- owner-prefixed object paths: '{user_id}/{environment_id}/...'. A signed-in user
-- reads/writes only under their own prefix.
create policy environments_objects_owner_rw on storage.objects
    for all to authenticated
    using (
        bucket_id = 'environments'
        and (storage.foldername(name))[1] = auth.uid()::text
    )
    with check (
        bucket_id = 'environments'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

-- There is intentionally NO public/anon read policy on storage.objects for this
-- bucket: viewers never read storage directly. Published assets are delivered via
-- short-lived (<=15 min) signed URLs issued server-side after an auth check, with
-- the CDN forwarding the signature (SPEC §3; SECURITY_CHECKLIST §3.1–§3.3).
