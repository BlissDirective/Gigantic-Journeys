-- Minimal stand-in for the parts of a Supabase database the migrations touch, so the
-- RLS policies can be exercised on a plain PostgreSQL (the box has no Docker, and CI's
-- lint job has no Supabase stack). NOT a migration; test-only.
--   roles:   anon, authenticated, service_role (BYPASSRLS, like Supabase)
--   auth:    auth.users, auth.uid() reading request.jwt.claim.sub (as PostgREST sets it)
--   storage: storage.buckets, storage.objects, storage.foldername()
--   grants:  Supabase's default "ALL on new public objects" for the three API roles
do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'anon') then
        create role anon nologin noinherit;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'authenticated') then
        create role authenticated nologin noinherit;
    end if;
    if not exists (select 1 from pg_roles where rolname = 'service_role') then
        create role service_role nologin noinherit bypassrls;
    end if;
end
$$;

create schema auth;
create table auth.users (id uuid primary key, email text);
create function auth.uid() returns uuid
language sql stable
as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;

create schema storage;
create table storage.buckets (id text primary key, name text not null, public boolean default false);
create table storage.objects (
    id uuid primary key default gen_random_uuid(),
    bucket_id text references storage.buckets (id),
    name text not null
);
alter table storage.objects enable row level security;
create function storage.foldername(name text) returns text[]
language sql immutable
as $$
    select (string_to_array(name, '/'))[1:array_length(string_to_array(name, '/'), 1) - 1]
$$;

grant usage on schema public, auth, storage to anon, authenticated, service_role;
grant execute on function auth.uid() to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on functions to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
