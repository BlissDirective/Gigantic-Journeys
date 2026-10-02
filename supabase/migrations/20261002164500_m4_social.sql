-- 20261002164500_m4_social.sql
--
-- APPROVED #038 (Owner, 2026-09-29; decision packet item 5) — table creation for the
-- M4 social layer (SECURITY_CHECKLIST §2.5). Security-sensitive: Coordinator + gj-data
-- secondary security review complete 2026-09-29 (AUTH #007/#027; check_rls green, 31
-- RLS/rate-limit tests pass). #038 conditions: device ids hashed (device_hash, in the
-- privacy label), user_blocks included (Apple 1.2), leaderboards expose a handle not a
-- raw user id (user_id OK for internal M4 testing only), approved starting rate limits.
-- Drafted 2026-09-29 as design/proposals/m4-data-01-social/20261101000000_m4_social.sql;
-- moved here unchanged below this header. Applied to the STAGING project only by
-- gj-operator (M4-DATA-01); production is CI-only (SECURITY_CHECKLIST §8.3).
--
-- AUTH: APPROVED #038 (Owner, 2026-09-29).
--
-- Scope (M4-DATA-01; SPEC §3.7; design/proposals/publish-browse-rank-moderation-v1.md §5):
-- the social layer that sits on the existing public.environments table (AUTH #034):
--   publishes            publish/moderation history of an environment (owner reads; server writes)
--   ratings              one four-axis rating per user per environment (DESIGN_SYSTEM §8: 1..5 per row)
--   reports              one-tap report with a reason (decision 8d reasons)
--   leaderboard_times    per-route time-trial submissions (validated by the server)
--   moderation_actions   the moderation queue's audit trail (service-role only)
--   user_blocks          block abusive users (Apple guideline 1.2 pillar 3)
--   rate_limit_rules     per-user / per-device limits (SECURITY_CHECKLIST §10.2; service-role only)
--
-- Policy patterns (SECURITY_CHECKLIST §2.2): owner-only (user_id = auth.uid()),
-- published-read (environment published AND moderation cleared), service-role-only
-- (the only policy targets service_role, which grants clients nothing; service_role
-- bypasses RLS anyway, and the explicit policy satisfies check_rls.py and says so).
-- Tests: design/proposals/m4-data-01-social/tests/ (two users + anon, rate limits).

-- ---------- enums ----------
create type public.report_reason as enum
    ('private_information', 'inappropriate_content', 'not_a_real_place',
     'broken_environment', 'other');

create type public.report_state as enum ('open', 'actioned', 'dismissed');

create type public.time_status as enum ('pending', 'accepted', 'rejected');

create type public.publish_outcome as enum
    ('under_review', 'cleared', 'rejected', 'unpublished');

create type public.moderation_action_kind as enum
    ('auto_clear', 'auto_flag', 'clear', 'reject', 'unpublish', 'restore',
     'appeal_upheld', 'appeal_denied', 'block_user', 'escalate_owner');

-- A per-install identifier supplied by the client: a salted hash of the vendor id,
-- never the raw id. It is spoofable, so per-user limits are the primary guard and the
-- device limit catches several accounts on one install.
create domain public.device_hash as text
    check (value ~ '^[0-9a-f]{32,128}$');

-- ---------- helper: is an environment publicly visible? ----------
-- security definer so policies on other tables can ask without the caller needing
-- read access to the row; it only returns a boolean for a given id.
create or replace function public.environment_is_public(env uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1 from public.environments e
        where e.id = env and e.status = 'published' and e.moderation_state = 'cleared'
    );
$$;

-- true when the signed-in caller (auth.uid()) created the environment; takes no
-- user id, so it cannot be used to probe who owns what
create or replace function public.owns_environment(env uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1 from public.environments e where e.id = env and e.user_id = auth.uid()
    );
$$;

-- ---------- publishes ----------
create table public.publishes (
    id                  uuid primary key default gen_random_uuid(),
    environment_id      uuid not null references public.environments (id) on delete cascade,
    user_id             uuid not null references auth.users (id) on delete cascade,
    requested_at        timestamptz not null default now(),
    -- server-side re-strip of GPS/EXIF/location atoms, verified (SECURITY_CHECKLIST §4.4)
    metadata_stripped_at timestamptz,
    vision_score        real check (vision_score is null or (vision_score >= 0 and vision_score <= 1)),
    outcome             public.publish_outcome not null default 'under_review',
    -- the one-line reason shown to the creator on rejection (DESIGN_SYSTEM §8)
    rejection_reason    text check (rejection_reason is null or char_length(rejection_reason) <= 140),
    appeal_requested_at timestamptz,
    decided_at          timestamptz,
    unpublished_at      timestamptz,
    constraint publishes_rejection_has_reason
        check (outcome <> 'rejected' or rejection_reason is not null)
);
create index publishes_environment_idx on public.publishes (environment_id, requested_at desc);
create index publishes_user_idx on public.publishes (user_id);

alter table public.publishes enable row level security;

-- owner-only read: the creator sees their own publish history and rejection reasons.
create policy publishes_owner_read on public.publishes
    for select to authenticated
    using (user_id = auth.uid());

-- service-role-only writes: publish, re-strip, vision pass and appeals run server-side.
create policy publishes_service_role_all on public.publishes
    for all to service_role
    using (true) with check (true);

-- ---------- ratings ----------
create table public.ratings (
    id              uuid primary key default gen_random_uuid(),
    environment_id  uuid not null references public.environments (id) on delete cascade,
    user_id         uuid not null references auth.users (id) on delete cascade,
    device_hash     public.device_hash not null,
    fun             smallint check (fun between 1 and 5),
    interesting     smallint check (interesting between 1 and 5),
    interactive     smallint check (interactive between 1 and 5),
    exciting        smallint check (exciting between 1 and 5),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    -- one rating per account per environment (anti-gaming, SPEC §3.7)
    constraint ratings_one_per_user unique (environment_id, user_id),
    -- the sheet allows skipping rows, not skipping all of them
    constraint ratings_at_least_one_axis
        check (coalesce(fun, interesting, interactive, exciting) is not null)
);
create index ratings_user_idx on public.ratings (user_id, created_at desc);
create index ratings_device_idx on public.ratings (device_hash, created_at desc);

create trigger ratings_set_updated_at
    before update on public.ratings
    for each row execute function public.set_updated_at();

alter table public.ratings enable row level security;

-- owner-only: a rater reads their own ratings
create policy ratings_owner_read on public.ratings
    for select to authenticated
    using (user_id = auth.uid());

-- creator stats: the environment's creator reads the ratings on it (creator-only in v1)
create policy ratings_creator_read on public.ratings
    for select to authenticated
    using (public.owns_environment(environment_id));

-- insert: as yourself, only on a public environment, never on your own
create policy ratings_owner_insert on public.ratings
    for insert to authenticated
    with check (
        user_id = auth.uid()
        and public.environment_is_public(environment_id)
        and not public.owns_environment(environment_id)
    );

-- re-rate: change your own rating while the environment is still public
create policy ratings_owner_update on public.ratings
    for update to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid() and public.environment_is_public(environment_id));

create policy ratings_service_role_all on public.ratings
    for all to service_role
    using (true) with check (true);

-- ---------- reports ----------
create table public.reports (
    id              uuid primary key default gen_random_uuid(),
    environment_id  uuid not null references public.environments (id) on delete cascade,
    reporter_id     uuid not null references auth.users (id) on delete cascade,
    device_hash     public.device_hash not null,
    reason          public.report_reason not null,
    note            text check (note is null or char_length(note) <= 500),
    state           public.report_state not null default 'open',
    created_at      timestamptz not null default now(),
    resolved_at     timestamptz,
    constraint reports_one_open_per_user unique (environment_id, reporter_id)
);
create index reports_open_idx on public.reports (state, created_at) where state = 'open';
create index reports_reporter_idx on public.reports (reporter_id, created_at desc);
create index reports_device_idx on public.reports (device_hash, created_at desc);

alter table public.reports enable row level security;

-- owner-only read: the reporter sees their own report ("Under review" shows to them)
create policy reports_owner_read on public.reports
    for select to authenticated
    using (reporter_id = auth.uid());

-- insert: as yourself, state 'open', on a public environment (what you can see)
create policy reports_owner_insert on public.reports
    for insert to authenticated
    with check (
        reporter_id = auth.uid()
        and state = 'open'
        and resolved_at is null
        and public.environment_is_public(environment_id)
    );

-- the moderation queue (triage, resolution) is service-role-only
create policy reports_service_role_all on public.reports
    for all to service_role
    using (true) with check (true);

-- ---------- leaderboard_times ----------
create table public.leaderboard_times (
    id              uuid primary key default gen_random_uuid(),
    environment_id  uuid not null references public.environments (id) on delete cascade,
    route_id        text not null check (route_id ~ '^[a-z0-9][a-z0-9_-]{0,63}$'),
    user_id         uuid not null references auth.users (id) on delete cascade,
    device_hash     public.device_hash not null,
    -- the telemetry session of the completed run the time comes from (data/schemas)
    session_id      uuid not null,
    time_ms         integer not null check (time_ms > 0 and time_ms < 86400000),
    status          public.time_status not null default 'pending',
    -- set by the server validator (plausibility floor, SPEC §3.7); never by clients
    reject_reason   text check (reject_reason is null or char_length(reject_reason) <= 140),
    created_at      timestamptz not null default now(),
    validated_at    timestamptz,
    constraint leaderboard_one_per_session unique (session_id, route_id)
);
create index leaderboard_board_idx
    on public.leaderboard_times (environment_id, route_id, time_ms)
    where status = 'accepted';
create index leaderboard_user_idx on public.leaderboard_times (user_id, created_at desc);
create index leaderboard_device_idx on public.leaderboard_times (device_hash, created_at desc);

alter table public.leaderboard_times enable row level security;

-- published-read: accepted times on a published+cleared environment are public
create policy leaderboard_published_read on public.leaderboard_times
    for select to anon, authenticated
    using (status = 'accepted' and public.environment_is_public(environment_id));

-- owner-only: a runner sees all their own submissions, including pending/rejected
create policy leaderboard_owner_read on public.leaderboard_times
    for select to authenticated
    using (user_id = auth.uid());

-- creator stats: the creator sees every submission on their own environment
create policy leaderboard_creator_read on public.leaderboard_times
    for select to authenticated
    using (public.owns_environment(environment_id));

-- submit: as yourself, 'pending' only, on a public environment; the validator
-- (service role) accepts or rejects. Clients cannot update or delete times.
create policy leaderboard_owner_insert on public.leaderboard_times
    for insert to authenticated
    with check (
        user_id = auth.uid()
        and status = 'pending'
        and reject_reason is null
        and validated_at is null
        and public.environment_is_public(environment_id)
    );

create policy leaderboard_service_role_all on public.leaderboard_times
    for all to service_role
    using (true) with check (true);

-- ---------- moderation_actions (the queue's audit trail) ----------
create table public.moderation_actions (
    id              uuid primary key default gen_random_uuid(),
    environment_id  uuid references public.environments (id) on delete set null,
    report_id       uuid references public.reports (id) on delete set null,
    subject_user_id uuid references auth.users (id) on delete set null,
    actor           text not null check (actor in ('vision', 'gj-data', 'owner')),
    action          public.moderation_action_kind not null,
    reason          text check (reason is null or char_length(reason) <= 500),
    created_at      timestamptz not null default now()
);
create index moderation_actions_env_idx on public.moderation_actions (environment_id, created_at desc);

alter table public.moderation_actions enable row level security;

-- service-role-only: no client (anon or authenticated) policy exists
create policy moderation_actions_service_role_all on public.moderation_actions
    for all to service_role
    using (true) with check (true);

-- ---------- user_blocks (Apple 1.2: block abusive users) ----------
create table public.user_blocks (
    blocker_id  uuid not null references auth.users (id) on delete cascade,
    blocked_id  uuid not null references auth.users (id) on delete cascade,
    created_at  timestamptz not null default now(),
    primary key (blocker_id, blocked_id),
    constraint user_blocks_not_self check (blocker_id <> blocked_id)
);

alter table public.user_blocks enable row level security;

-- owner-only: you manage (create, list, remove) your own blocks; the blocked user
-- cannot see that they are blocked
create policy user_blocks_owner_all on public.user_blocks
    for all to authenticated
    using (blocker_id = auth.uid())
    with check (blocker_id = auth.uid());

create policy user_blocks_service_role_all on public.user_blocks
    for all to service_role
    using (true) with check (true);

-- ---------- rate limits (SECURITY_CHECKLIST §10.2) ----------
create table public.rate_limit_rules (
    table_name      text primary key check (table_name in ('ratings', 'reports', 'leaderboard_times')),
    window_seconds  integer not null check (window_seconds > 0),
    max_per_user    integer not null check (max_per_user > 0),
    max_per_device  integer not null check (max_per_device > 0)
);

alter table public.rate_limit_rules enable row level security;

-- service-role-only: clients can neither read nor tune the limits
create policy rate_limit_rules_service_role_all on public.rate_limit_rules
    for all to service_role
    using (true) with check (true);

-- PROVISIONAL starting values (gj-data tunes them from telemetry; M4-DATA-02 owns
-- the rate-spam exit test). Per rolling window, counted per user AND per device.
insert into public.rate_limit_rules (table_name, window_seconds, max_per_user, max_per_device) values
    ('ratings',           3600, 30, 45),
    ('reports',           3600, 10, 15),
    ('leaderboard_times',  600, 20, 30);

-- Counts recent inserts by the same user and by the same device across ALL users
-- (security definer: runs as the table owner, so RLS does not hide other rows).
create or replace function public.enforce_rate_limit()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    rule        public.rate_limit_rules%rowtype;
    uid         uuid;
    uid_col     text;
    user_count  integer;
    dev_count   integer;
begin
    -- The service role (server jobs, backfills) is not rate-limited. Inside a security
    -- definer function current_user is the owner, but the 'role' setting still names
    -- the role PostgREST switched to (service_role / authenticated / anon). A JWT claim
    -- is not trusted here.
    if current_setting('role', true) = 'service_role' or session_user = 'service_role' then
        return new;
    end if;

    select * into rule from public.rate_limit_rules where table_name = tg_table_name;
    if not found then
        return new;
    end if;

    -- the server clock, not the client, decides when a row was created (a back-dated
    -- created_at would otherwise fall outside the window)
    new.created_at := now();
    uid_col := case tg_table_name when 'reports' then 'reporter_id' else 'user_id' end;
    -- (read through jsonb: PL/pgSQL cannot reference a column one table lacks)
    uid := (to_jsonb(new) ->> uid_col)::uuid;

    -- serialise concurrent inserts by the same user on this table, so two parallel
    -- requests cannot both slip under the limit (released at transaction end)
    perform pg_advisory_xact_lock(hashtextextended(tg_table_name || ':' || uid::text, 0));

    execute format(
        'select count(*) filter (where %I = $1), count(*) filter (where device_hash = $2)
           from public.%I
          where created_at > now() - make_interval(secs => $3)',
        uid_col,
        tg_table_name)
    into user_count, dev_count
    using uid, new.device_hash, rule.window_seconds;

    if user_count >= rule.max_per_user or dev_count >= rule.max_per_device then
        raise exception 'rate limit exceeded for %', tg_table_name
            using errcode = 'P0429',
                  hint = 'try again later';
    end if;
    return new;
end;
$$;

create trigger ratings_rate_limit
    before insert on public.ratings
    for each row execute function public.enforce_rate_limit();

create trigger reports_rate_limit
    before insert on public.reports
    for each row execute function public.enforce_rate_limit();

create trigger leaderboard_times_rate_limit
    before insert on public.leaderboard_times
    for each row execute function public.enforce_rate_limit();

-- ---------- privileges: least privilege on top of RLS ----------
-- Supabase grants ALL on new public tables to anon and authenticated by default and
-- RLS then filters rows. Here the table grants are narrowed as well, so a client can
-- only write the columns it owns (ids, created_at, status/state, validator fields and
-- server timestamps always come from defaults or the server) and has no TRUNCATE.
revoke all on public.publishes, public.ratings, public.reports, public.leaderboard_times,
              public.moderation_actions, public.user_blocks, public.rate_limit_rules
    from anon, authenticated;

grant select on public.publishes to authenticated;

grant select on public.ratings to authenticated;
grant insert (environment_id, user_id, device_hash, fun, interesting, interactive, exciting)
    on public.ratings to authenticated;
grant update (fun, interesting, interactive, exciting) on public.ratings to authenticated;

grant select on public.reports to authenticated;
grant insert (environment_id, reporter_id, device_hash, reason, note)
    on public.reports to authenticated;

grant select on public.leaderboard_times to anon, authenticated;
grant insert (environment_id, route_id, user_id, device_hash, session_id, time_ms)
    on public.leaderboard_times to authenticated;

grant select, delete on public.user_blocks to authenticated;
grant insert (blocker_id, blocked_id) on public.user_blocks to authenticated;

-- moderation_actions and rate_limit_rules: no client grant at all (service-role-only).

-- the trigger function is never called directly
revoke execute on function public.enforce_rate_limit() from public, anon, authenticated;
