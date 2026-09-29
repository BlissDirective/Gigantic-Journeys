# M0-PLAT-01: Supabase local scaffold and RLS-by-default lint

2026-09-29, gj-operator (overnight worker, acting for gj-platform). Built on main in `95cdecc`, pushed in
the `76b943b` batch. The log filter was then hardened (see AT-5).

## Acceptance tests

| AT | Result | Evidence |
|---|---|---|
| AT-1 `supabase start` works on the VM, log attached, no keys | **PASS, on CI instead of the VM** | The shared box has no Docker access, so the local stack runs in the new `.github/workflows/supabase-local.yml` on a GitHub runner. Run [36517116390](https://github.com/BlissDirective/Gigantic-Journeys/actions/runs/36517116390) (2026-09-28 22:27 CT) on `76b943b` was green. It ran `supabase@2.118.0 start` with studio, imgproxy, edge-runtime, logflare, vector and supavisor excluded; logged "Applying migration 20260926120000_m1_environments_staging.sql… Started supabase local development setup."; confirmed `migrations applied: 1 / files: 1`; ran a live RLS query (`environments | rls t | policies 2`, "public tables without RLS or a policy: 0"); then `supabase stop`. The filtered log is uploaded as the `supabase-start-log` artifact. `supabase/config.toml` and `supabase/migrations/` already existed. |
| AT-2 `check_rls.py` fails a table without RLS + a policy | **PASS** | Unchanged logic. It now takes an optional directory argument and prints repo-relative paths for annotations. The governance `rls` job runs it on every push. |
| AT-3 compliant + non-compliant fixtures, pytest in the lint workflow | **PASS** | `supabase/scripts/tests/fixtures/{compliant,noncompliant}/`, driven by `test_check_rls.py` through the CLI (exit 0 / exit 1 with the table named). The lint job's pytest ran 309 tests, all passing, on `76b943b`. |
| AT-4 README states the rule, the patterns and the AUTH gate | **PASS** | `supabase/README.md` covers RLS by default, owner-only / published-read / service-role-only, and says table creation needs `APPROVED #n`. A "Local stack" section was added (CI workflow, excluded services, why not the VM). |
| AT-5 no URL, key or project ref | **PASS after a fix** | The repo has no project URL, key or ref. The workflow uses only the CLI's local default DB URL. **Finding:** the first run's filter (`key\|secret\|jwt\|token`) missed the new CLI table row "Publishable │ sb_publishable_…", so the **local stack's default publishable key** appeared once in the public run log and artifact. It is the static demo value every Supabase CLI install uses for `127.0.0.1`, not a staging or production credential, so it is **not a secret leak** and needs no rotation. It still broke the intent, so the follow-up commit adds `publishable\|password\|sb_[a-z]+_\|eyJ` to the filter, plus a guard step that fails the job if any key-like string survives. |

## Notes

- **Why a CI workflow rather than the VM:** the box's user can't reach the Docker daemon, and installing or
  granting Docker is an Owner/box decision (not needed now). The CI run is the reproducible evidence and
  guards every future migration: it runs when `supabase/config.toml`, `supabase/migrations/**`, `supabase/seed.sql` or the workflow changes, and on manual dispatch.
- **Next:** when the M4-DATA-01 draft (`design/proposals/m4-data-01-social/`) is approved and moved into
  `supabase/migrations/`, this workflow applies it on a real Supabase stack. The live RLS query then covers
  the seven new tables.
