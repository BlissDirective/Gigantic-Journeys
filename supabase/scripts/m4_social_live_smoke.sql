-- Live RLS + rate-limit smoke on STAGING. Everything runs in one transaction that is
-- ROLLED BACK at the end: no rows persist. Synthetic UUIDs only, no real user data.
\set ON_ERROR_STOP on
begin;
insert into auth.users (id) values
  ('aaaaaaaa-0000-4000-8000-0000000000a1'), ('bbbbbbbb-0000-4000-8000-0000000000b2');
insert into public.environments (id, user_id, scan_id, status, moderation_state) values
  ('e0000000-0000-4000-8000-0000000000e1', 'aaaaaaaa-0000-4000-8000-0000000000a1', 'smoke-pub', 'published', 'cleared'),
  ('e0000000-0000-4000-8000-0000000000e2', 'aaaaaaaa-0000-4000-8000-0000000000a1', 'smoke-draft', 'ready', 'pending');
insert into public.moderation_actions (environment_id, actor, action, reason)
  values ('e0000000-0000-4000-8000-0000000000e2', 'vision', 'auto_flag', 'smoke');
do $$
declare
  ok int := 0; bad int := 0; n int;
  procedure_note text;
  b constant text := '{"sub":"bbbbbbbb-0000-4000-8000-0000000000b2","role":"authenticated"}';
  pub constant uuid := 'e0000000-0000-4000-8000-0000000000e1';
  draft constant uuid := 'e0000000-0000-4000-8000-0000000000e2';
  i int;
begin
  -- 1. anon cannot read the moderation queue
  begin
    execute 'set local role anon';
    perform count(*) from public.moderation_actions;
    raise notice 'FAIL 1 anon read moderation_actions'; bad := bad + 1;
  exception when insufficient_privilege then
    raise notice 'PASS 1 anon -> moderation_actions: permission denied'; ok := ok + 1;
  end;
  execute 'reset role';
  -- 2. authenticated user B cannot read the moderation queue
  begin
    perform set_config('request.jwt.claims', b, true);
    execute 'set local role authenticated';
    perform count(*) from public.moderation_actions;
    raise notice 'FAIL 2 user read moderation_actions'; bad := bad + 1;
  exception when insufficient_privilege then
    raise notice 'PASS 2 user -> moderation_actions: permission denied'; ok := ok + 1;
  end;
  execute 'reset role';
  -- 3. anon sees the published+cleared env, not the draft
  execute 'set local role anon';
  select count(*) into n from public.environments where id in (pub, draft);
  execute 'reset role';
  if n = 1 then raise notice 'PASS 3 anon sees 1 of {published, draft} environments'; ok := ok + 1;
  else raise notice 'FAIL 3 anon sees % environments', n; bad := bad + 1; end if;
  -- 4. B can rate the public env
  perform set_config('request.jwt.claims', b, true);
  execute 'set local role authenticated';
  begin
    insert into public.ratings (environment_id, user_id, device_hash, fun, interesting, interactive, exciting)
      values (pub, 'bbbbbbbb-0000-4000-8000-0000000000b2', repeat('b', 32), 5, 4, 3, 5);
    raise notice 'PASS 4 user rates a published+cleared env'; ok := ok + 1;
  exception when others then raise notice 'FAIL 4 rating insert: %', sqlerrm; bad := bad + 1; end;
  -- 5. B cannot rate the draft (RLS with-check)
  begin
    insert into public.ratings (environment_id, user_id, device_hash, fun, interesting, interactive, exciting)
      values (draft, 'bbbbbbbb-0000-4000-8000-0000000000b2', repeat('b', 32), 5, 4, 3, 5);
    raise notice 'FAIL 5 user rated a draft'; bad := bad + 1;
  exception when insufficient_privilege then raise notice 'PASS 5 rating a draft: RLS violation'; ok := ok + 1; end;
  -- 6. B cannot write status on a time (column grant narrowing)
  begin
    insert into public.leaderboard_times (environment_id, route_id, user_id, device_hash, session_id, time_ms, status)
      values (pub, 'summit', 'bbbbbbbb-0000-4000-8000-0000000000b2', repeat('b', 32), gen_random_uuid(), 1000, 'accepted');
    raise notice 'FAIL 6 user set status=accepted'; bad := bad + 1;
  exception when insufficient_privilege then raise notice 'PASS 6 client cannot set leaderboard status'; ok := ok + 1; end;
  -- 7. rate limit: 20 time submissions / 10 min per user, the 21st fails with P0429
  for i in 1..20 loop
    insert into public.leaderboard_times (environment_id, route_id, user_id, device_hash, session_id, time_ms)
      values (pub, 'summit', 'bbbbbbbb-0000-4000-8000-0000000000b2', repeat('b', 32), gen_random_uuid(), 30000 + i);
  end loop;
  begin
    insert into public.leaderboard_times (environment_id, route_id, user_id, device_hash, session_id, time_ms)
      values (pub, 'summit', 'bbbbbbbb-0000-4000-8000-0000000000b2', repeat('b', 32), gen_random_uuid(), 29999);
    raise notice 'FAIL 7 21st submission accepted'; bad := bad + 1;
  exception when sqlstate 'P0429' then raise notice 'PASS 7 21st time submission in 10 min -> P0429 (%)', sqlerrm; ok := ok + 1; end;
  -- 8. B's submissions are pending; anon sees none of them (accepted-only)
  execute 'reset role';
  execute 'set local role anon';
  select count(*) into n from public.leaderboard_times where environment_id = pub;
  execute 'reset role';
  if n = 0 then raise notice 'PASS 8 anon sees 0 pending times'; ok := ok + 1;
  else raise notice 'FAIL 8 anon sees % times', n; bad := bad + 1; end if;
  raise notice 'LIVE SMOKE: % PASS / % FAIL', ok, bad;
end $$;
rollback;
\echo '== post-rollback residue (must be 0 0)'
select (select count(*) from auth.users where id in ('aaaaaaaa-0000-4000-8000-0000000000a1','bbbbbbbb-0000-4000-8000-0000000000b2')) as users,
       (select count(*) from public.environments where scan_id like 'smoke-%') as envs;
