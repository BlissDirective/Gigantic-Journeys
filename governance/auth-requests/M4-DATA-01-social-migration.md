# AUTH request: create the M4 social tables (M4-DATA-01)

> **STATUS: APPROVED as AUTH #038 (Owner, 2026-09-29; re-confirmed 2026-09-29).** Logged in
> `governance/AUTHORIZATION_LOG.md` as Decision #038 (schema/table creation; security-sensitive →
> secondary review under AUTH #007). **Coordinator secondary security review complete (AUTH #027,
> 2026-09-29):** `check_rls.py` passes on the draft (every created table has RLS + a policy); the #038
> conditions are all present — device IDs hashed (`device_hash`, cross-account, in the privacy label),
> `user_blocks` (Apple 1.2), leaderboards show a handle not a raw user id, narrowed client grants, and the
> §10.2 rate-limit trigger; the 31 RLS/rate-limit tests pass in CI (they only ERROR in this sandbox because
> `initdb` cannot start a local PostgreSQL). **The migration is staging-ready.** Remaining step is the
> Operator's: add the `APPROVED #038` header + a current timestamp, move it to `supabase/migrations/`, and
> apply it to Supabase **staging** (requires Supabase access this Coordinator does not hold).
>
> **APPLIED TO STAGING 2026-10-02 (gj-operator):** `supabase/migrations/20261002164500_m4_social.sql`,
> one transaction via the session pooler; live RLS/policy/rate-limit verification + a rolled-back role
> smoke (8/0) + `staging_smoke.py` 12/0/0 in `qa/reports/M4-DATA-01.md`. Production untouched.

```
AUTH REQUEST (next free #)
Type: schema change: create tables (SECURITY_CHECKLIST §2.5; security-sensitive → secondary review, AUTH #007)
What: One migration creating publishes, ratings, reports, leaderboard_times, moderation_actions,
      user_blocks and rate_limit_rules, with RLS on every table, narrowed grants and per-user/per-device
      rate-limit triggers. Drafted in design/proposals/m4-data-01-social/ with 31 passing policy tests.
      On approval it moves into supabase/migrations/ and is applied to STAGING first.
Why:  M4-DATA-01 (P0) is the backend contract for publish, browse, rate, report and race (SPEC §3.7,
      design AUTH #026). M4-DATA-02/03, M4-GAME-01/02 and M4-PLAT-01 build on it. Nothing uses it before
      M4, so there is no rush. Approving now lets the policies soak in the local and staging stacks.
Cost: $0 (fits the Supabase free tier)
Reversible: yes before production data exists (drop the tables); afterwards, by a follow-up migration.
Waiting on: the Owner; secondary security review (gj-data + the Coordinator, AUTH #007)
```

## What the Owner is approving (plain language)

- Seven new database tables for the community features: publish history, ratings, reports, leaderboard
  times, the moderation log, user blocks, and rate-limit settings.
- Who can see what:
  - A player's rating, report or block is private to that player.
  - A creator sees the ratings and times on their own places, but never who reported them.
  - Anyone can see accepted leaderboard times on a published place.
  - Only the server sees the moderation queue.
- A player can rate or report a place only when it is published and cleared, and can't rate their own.
- Leaderboard times always start as "pending"; only the server's validator can accept them.
- Spam limits count per account and per device. Example: 30 ratings an hour per account, 45 per device.
  Over the limit, the app gets a "try again later" error.

## Questions for the Owner or reviewers (defaults are in the draft)

1. **Device identifier.** The rate limits store a salted hash of the per-app install id. That is a
   "Device ID" under Apple's privacy label, used for fraud prevention and not linked to tracking. Add it to
   the label (M0-DATA-01 proposed label), or drop the per-device limits and keep only the per-account ones?
2. **Blocks table now.** `user_blocks` is not in the ticket's table list, but Apple guideline 1.2 requires
   blocking. It is included here. OK?
3. **Starting limits:**
   - ratings: 30 per hour per account, 45 per device;
   - reports: 10 / 15 per hour;
   - time submissions: 20 / 30 per 10 minutes.

   gj-data will tune them.
4. **Leaderboards show user ids, not names,** until a profiles table exists. OK for M4 testing?
