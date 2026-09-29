# Delete-all flow specification (DRAFT)

**Status: DRAFT v0.1 · 2026-09-29 · pending attorney review (M0-LEGAL-02).** Not legal advice. This specifies the per-user **"Delete my data"** flow promised in `SPEC.md §7` and `governance/SECURITY_CHECKLIST.md §5.4, §6.4`. Retention periods and storage locations live in [`RETENTION_SCHEDULE.md`](RETENTION_SCHEDULE.md). Engineering builds this in M4/M5 (SECURITY_CHECKLIST §6.4 is an M5 gate); this document is the contract that build is tested against.

## 1. Promise (user-facing)

"Delete my data" removes your account and everything you made or sent us: scans, environments (including published ones), ratings, reports, times, corrections, telemetry and purchase-linked unlocks on our side. It finishes **within 30 days**. We keep only a record that you accepted our terms and a deletion receipt, neither of which contains your content, for as long as the law requires.

## 2. Entry point and user experience

1. **Settings → Account → Delete my data.** One tap from Settings, no support ticket, no email round-trip. Apple requires in-app account deletion for apps with account creation (App Store Review Guideline 5.1.1(v)).
2. **Confirmation sheet** in plain language with no dark patterns:
   - Title: "Delete everything?"
   - Body: what is deleted (the §1 list); that published environments disappear for everyone; that it cannot be undone; that it completes within 30 days.
   - Primary button: **Delete my data** (destructive style). Secondary: **Cancel**, equally prominent.
   - If the user has an active subscription, a line saying the subscription is managed by Apple, with a link to Apple's subscription settings. Deleting data does not cancel an App Store subscription.
3. **Re-authentication**: a fresh Sign in with Apple / Google prompt, so a borrowed unlocked phone cannot wipe an account, and so the Apple authorization code is available for token revocation (§4 step 6).
4. **Immediately after confirming**: the app signs out, clears the local cache in the app container (scans not yet uploaded, downloaded environments, settings) and shows "Your data is being deleted. This finishes within 30 days." The same message goes to the user's email only if we hold one (Apple private relay or Google). No marketing content.
5. **On completion**: nothing further is required from the user. If we hold an email, a short "Deletion complete" notice is sent.

## 3. Request handling

- The client calls `POST /account/delete` (a Supabase edge function, `verify_jwt = true`) with the fresh session.
- The function writes a `deletion_requests` row `{request_id, pseudonymous user_id, requested_at, status: pending}` and fires an Inngest event `account/delete.requested`. It returns 202 at once.
- A durable Inngest workflow runs the §4 steps. Each step is idempotent and retried with backoff; a step that fails permanently alerts the Owner (SECURITY_CHECKLIST §11) and never marks the request complete.
- **Deadline:** the workflow targets completion within 24 h. A daily sweep escalates any request older than 7 days to the Owner. Day 30 is the hard legal limit.

## 4. Steps per data class

Order matters: stop new processing first, then delete content, then identity.

| # | Step | Data class (SPEC §7) | Action | Receipt |
|---|---|---|---|---|
| 1 | **Freeze** | all | Revoke all refresh tokens (sign out everywhere); cancel pending pipeline runs for the user (Inngest cancel on `user_id`); reject new uploads from this user id | `sessions_revoked`, `jobs_cancelled: n` |
| 2 | **Raw scan media** | Raw scan video, poses, depth | Delete every object under `{user_id}/` in the private scan storage bucket; confirm that no running Modal job holds the user's data (ephemeral containers are destroyed when a job ends or is cancelled) | `objects_deleted: n` |
| 3 | **Derived environments** | Derived environment assets | Unpublish all (removed from feeds, search and leaderboards at once); delete the objects under `{user_id}/` in the `environments` bucket; delete the `environments` rows; purge CDN paths if a CDN is in front (M4) | `environments_deleted: n`, `cdn_purge: ok / n.a.` |
| 4 | **Community rows** | Ratings, reports, leaderboard times | Delete the user's ratings, reports and times. Rows on the user's environments cascade with step 3. Recompute the affected aggregates. | `rows_deleted: n` |
| 5 | **Telemetry and corrections** | Telemetry events, correction events | Delete every raw telemetry and correction row with the user's pseudonymous id; mark the corrections excluded from future training snapshots; rotate the pseudonymous-id mapping so no later event can be linked back. Existing aggregates hold no user id and stay. | `telemetry_deleted: n`, `corrections_deleted: n` |
| 6 | **Identity** | Account, character selection, cosmetics | Delete profile, character selection and entitlement rows; **revoke the Sign in with Apple token** (Apple REST `auth/revoke`, as Apple requires); Google needs no revocation for the OIDC sign-in scope, but revoke the refresh token if one is held; delete the Supabase auth user | `apple_revoke: 200 / n.a.`, `auth_user_deleted` |
| 7 | **Keep** | Consent/ToS records, deletion receipts | Not deleted: kept without content until the counsel-set period ends, then destroyed by the scheduled sweep (RETENTION_SCHEDULE §1) | — |
| 8 | **Close** | — | Mark `deletion_requests.status = complete` with `completed_at`; send the completion notice if an email is held | `completed_at` |

**Processors and their deletion mechanisms:**

| Processor | Holds | Deletion mechanism | Receipt source |
|---|---|---|---|
| Supabase (storage, database, auth) | Scan media, environments, rows, auth user | Storage API delete by prefix; SQL deletes in one transaction; Admin API `deleteUser` | API response codes, row counts |
| Modal (reconstruction compute) | Nothing at rest for user jobs; ephemeral container scratch space during a run | Cancel the running call; no persistent volume is used for user data (the `gj-corpus` volume is corpus-only) | Cancel response; confirmation that no user-data volume exists |
| Inngest (workflow orchestration) | Event payloads with ids and storage paths, no media | Payloads contain no content. Run history expires on Inngest's retention window **[confirm]**. | n.a. (documented) |
| Apple (Sign in with Apple, App Store) | Sign-in link; purchase records | `auth/revoke`; purchase records stay under Apple's own terms | HTTP status |
| Google (Sign in with Google) | Sign-in link | Token revocation when a refresh token is held | HTTP status |
| CDN (if added in M4) | Cached published assets | Purge by path | API response |

No third-party processor receives user media in v1: reconstruction is self-hosted (ADR-0005, AUTH #030) and there is no avatar vendor (AUTH #020). If a managed reconstruction bridge is ever enabled for user data, it needs its own DPA and deletion API before use, and it must be added to this table.

## 5. Receipts and audit

Each step appends `{request_id, pseudonymous user_id, step, data_class, processor, action, count, response_code, timestamp}` to an append-only `deletion_receipts` table. Receipts hold **no media, no content, no email and no sign-in subject id**. The Owner can export a request's receipts to answer a regulator or a user ("prove it was deleted"). Receipts are kept for the counsel-set period (RETENTION_SCHEDULE §4).

## 6. Edge cases

- **Upload in flight:** step 1 rejects further uploads. Objects that land after step 2 are caught by a final re-sweep of the `{user_id}/` prefixes just before step 8.
- **Published environment someone is playing:** the signed URLs already issued expire within 15 minutes. After that the environment cannot be loaded.
- **Moderation hold or legal hold:** if a report under review involves the user's environment, or a legal hold exists, the request pauses for that item only. The Owner is alerted, the user is told "some items are held for a legal reason", and the 30-day clock is documented. **[Counsel to confirm hold wording and limits.]**
- **Re-signup:** a new account with the same Apple/Google identity gets a new pseudonymous id. Nothing from the deleted account is restored.
- **No network at request time:** the button needs connectivity. Offline, the app says so and does not queue a silent request.

## 7. How it is tested on staging (SECURITY_CHECKLIST §6.4)

An end-to-end staging test (`supabase/scripts/`, built with the feature in M4/M5), run with synthetic data only, never real user scans:

1. Create a synthetic staging user through the Admin API, one of each data class: a scan object, a published environment with a thumbnail, ratings/reports/times (including rows on another user's environment), telemetry and correction rows, a character selection, a consent record.
2. Call `POST /account/delete` and wait for the workflow.
3. Assert: no storage object under the user's prefixes; no rows keyed to the user in any application table (a query over every table with a `user_id` column, so a new table cannot be forgotten); the auth user is gone; aggregates have been recomputed; the consent record and receipts remain and contain no content; every step has a receipt.
4. Assert the idempotency: running the workflow twice gives the same end state and no errors.
5. Report PASS/FAIL into `qa/reports/` like the existing staging smoke (`supabase/scripts/staging_smoke.py`).

A CI-level unit test also checks that every table with a `user_id` column is covered by a delete step, so adding a table without a deletion path fails the build.

## 8. Open items for counsel

- Hold wording and limits (§6), and whether a legal hold pauses the 30-day clock.
- Whether to keep the consent/ToS record after deletion, and for how long (RETENTION_SCHEDULE §4).
- Whether the completion email is required, allowed or should be omitted when only a relay address is held.
- The CCPA/GDPR response wording if deletion requests also arrive by email (route them to the same workflow after identity verification).
