# M4-DATA-01: social data model, RLS and rate limits

**Status: APPROVED #038 and APPLIED TO STAGING (2026-10-02, gj-operator).** The migration moved
unchanged (new `APPROVED #038` header + timestamp) to
[`supabase/migrations/20261002164500_m4_social.sql`](../../../supabase/migrations/20261002164500_m4_social.sql)
and was applied to Supabase **staging** only; evidence in
[`qa/reports/M4-DATA-01.md`](../../../qa/reports/M4-DATA-01.md). This folder keeps the design notes and
the test harness (the tests now load the migration from `supabase/migrations/`). Originally filed by
gj-operator on 2026-09-29; request:
[`governance/auth-requests/M4-DATA-01-social-migration.md`](../../../governance/auth-requests/M4-DATA-01-social-migration.md).

## Files

| File | What |
|---|---|
| `../../../supabase/migrations/20261002164500_m4_social.sql` | The migration (moved from this folder as `20261101000000_m4_social.sql` under APPROVED #038; applied to staging 2026-10-02). |
| `tests/supabase_stub.sql` | Test-only stand-in for the Supabase parts the migrations touch: the `anon` / `authenticated` / `service_role` roles, `auth.uid()`, `storage.*`, and the default grants. |
| `tests/test_m4_social_rls.py` | 31 pytest cases. They start a throwaway PostgreSQL, load the stub, the applied environments migration (AUTH #034) and this draft, then act as anon, three users and the service role. |

## Tables and who can do what

"Public env" means an environment that is `published` and moderation `cleared`. The existing
environments table (AUTH #034) already guarantees that `published` implies `cleared`.

| Table | anon | Signed-in user | Service role |
|---|---|---|---|
| `publishes` (publish history, one-line rejection reason, appeal) | nothing | reads own | all |
| `ratings` (one per user per env; four axes, 1–5, rows can be skipped) | nothing | inserts own rating on a public env that isn't theirs; re-rates (axes only); reads own ratings; creator reads the ratings on own envs | all |
| `reports` (decision 8d reasons + "other") | nothing | inserts own report on a public env; reads own report (so the reporter sees "Under review") | all (this is the queue) |
| `leaderboard_times` | reads **accepted** times on public envs | submits own time as `pending` on a public env; reads own; creator reads all times on own envs | all (the validator accepts or rejects) |
| `moderation_actions` (audit trail) | nothing | nothing | all |
| `user_blocks` (Apple 1.2 pillar 3) | nothing | creates, lists and removes own blocks; a blocked user can't see that they are blocked | all |
| `rate_limit_rules` | nothing | nothing | all |

On top of RLS, the table grants are narrowed. Supabase's default is `ALL` for anon and authenticated.
Here clients can write only the columns they own, so ids, `created_at`, `status`/`state` and the
validator fields always come from defaults or the server. Clients also get no `TRUNCATE`, and the
service-role-only tables get no client grant at all. A service-role-only table carries one explicit
`to service_role` policy. That policy gives clients nothing, it satisfies `check_rls.py`, and it
documents the intent.

## Rate limits (SECURITY_CHECKLIST §10.2)

A `BEFORE INSERT` trigger on `ratings`, `reports` and `leaderboard_times` counts the rows inserted in a
rolling window by the same user and by the same `device_hash` (across all accounts). Over the limit,
the insert fails with SQLSTATE `P0429` ("rate limit exceeded for <table>"). Other details:

- The trigger is `security definer`, so RLS does not hide other users' rows from the count.
- An advisory lock serialises concurrent inserts by one user.
- `created_at` is forced to the server clock, so a client can't back-date rows out of the window.
- The service role is exempt. The trigger checks the `role` setting, not a JWT claim.

Provisional limits, per rolling window, per user / per device (gj-data tunes them; M4-DATA-02 owns the
rate-spam exit test):

| Table | Window | Per user | Per device |
|---|---|---|---|
| ratings | 1 h | 30 | 45 |
| reports | 1 h | 10 | 15 |
| leaderboard_times | 10 min | 20 | 30 |

`device_hash` is a salted hash of the per-vendor install id, computed on the device (`^[0-9a-f]{32,128}$`).
It can be spoofed, so the per-user limit is the main guard. The device limit catches many accounts on
one install.

## Tests

```
GJ_PG_BIN=/usr/lib/postgresql/<v>/bin python3 -m pytest -q design/proposals/m4-data-01-social
```

The tests skip when no PostgreSQL server binaries are found. GitHub's ubuntu runners ship them, so the
lint job's pytest step runs them in CI. On the box, a user-space PostgreSQL 17 was extracted from the
Debian package (no root, no Docker): **31 passed**.

A mutation check was also run: removing the self-rating clause, the grant narrowing and the forced
`created_at` made 10 tests fail. So the suite really does catch those regressions.

Coverage against the ticket's acceptance tests:

- **AT-1 (RLS on every table + `check_rls`):** `test_every_public_table_has_rls_enabled` and
  `test_check_rls_passes_on_the_draft`.
- **AT-2 (visibility):**
  - `test_unpublished_or_uncleared_environment_is_invisible_to_others` (draft, under review, and
    cleared-but-unpublished, each checked against anon, user B and creator A);
  - `test_published_and_cleared_environment_is_readable`;
  - `test_service_role_only_tables_are_closed_to_clients` (moderation queue and rate-limit rules);
  - `test_clients_cannot_write_the_moderation_queue`;
  - the per-table tests.
- **AT-3 (rate limits):**
  - per user: `test_ratings_rate_limited_per_user`;
  - per device across accounts: `test_ratings_rate_limited_per_device_across_accounts`;
  - reports and times: `test_reports_rate_limited`, `test_leaderboard_submissions_rate_limited`;
  - the window: `test_old_rows_fall_out_of_the_window`;
  - no back-dating: `test_clients_cannot_backdate_rows_to_dodge_the_window`;
  - service exemption: `test_service_role_is_not_rate_limited`.

  AT-3 is marked `automated: false` in the ticket, but it is automated here.
- **AT-4:** secret-scan (no keys anywhere).

**Not covered here:** a live Supabase run. After approval, the migration moves to `supabase/migrations/`,
and the `supabase-local` workflow (M0-PLAT-01) then applies it on a real local Supabase stack.

## Deliberately out of scope (other tickets)

- Public four-axis score on cards and ranking: a server-computed aggregate (M4-DATA-02).
- The vision pass, appeal flow and Owner escalation: M4-DATA-03. This draft only provides their tables.
- Hiding a blocked user's environments and times from the blocker's feeds: M4-GAME-01 (feed query).
- The free-tier 3-live cap and signed-URL delivery: M4-PLAT-01.
- Display names on leaderboards: a later `profiles` table. Leaderboards expose `user_id` uuids only.
- Plausibility validation of times: M4-GAME-02 (the validator writes `status`).
