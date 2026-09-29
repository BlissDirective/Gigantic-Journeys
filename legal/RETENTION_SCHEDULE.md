# Retention Schedule (DRAFT)

**Status: DRAFT v0.2 · 2026-09-29 · pending attorney review (M0-LEGAL-02).** Not legal advice. The in-house legal team reviews this before M5 (SPEC §7, §9.6; AUTH #016). It puts `SPEC.md §7` and `governance/SECURITY_CHECKLIST.md §4–§6` into practice, and the per-user delete-all flow is specified in [`DELETION_FLOW.md`](DELETION_FLOW.md). This schedule is written to be **published**: drop §4 before publishing.

**v0.2 changes (from v0.1, 2026-09-17):** aligned with SPEC v1.9 and AUTH #020, so v1 collects **no face or body photos** (pre-made characters, no biometric) and that class is marked V2-only. Added the storage location, access and vendor columns for every SPEC §7 class. Named the current infrastructure: self-host reconstruction on Modal per ADR-0005 and AUTH #030, Supabase per AUTH #034, Inngest per M0-PIPE-01, and the telemetry schema frozen at v1.0.0 (M0-DATA-01, AUTH #029). The deletion flow moved to its own file.

---

## 1. Retention schedule (the published table)

One row per SPEC §7 data class. "Pipeline" means the Supabase service role acting on behalf of the Inngest workflow. No engineer or Bot reads user content during normal operation (SECURITY_CHECKLIST §6.5, §8.3).

| Data class (SPEC §7) | Retention period | Deletion trigger | Storage location | Who can access | Vendor (processor) |
|---|---|---|---|---|---|
| **Raw scan media**: video, per-frame poses, intrinsics, depth, gravity (the capture bundle) | Until derived assets exist, **no later than 24 h** after upload. Failed jobs: **no later than 7 days**. | Derivation succeeds (pipeline deletes in the same workflow run), or a lifecycle sweep (hourly: success older than 24 h; failure older than 7 days), or delete-all | On device until upload succeeds (removed from the app container after upload, §9.9). In transit: TLS, signed upload URL. At rest: a private Supabase Storage bucket, owner-prefixed `{user_id}/…`. During processing: ephemeral Modal GPU container scratch space, destroyed when the job ends. | The user (their own upload); the pipeline (service role); the Modal job for the duration of the run | Supabase (storage); Modal (compute only, ephemeral, no retention) |
| ~~Face and body photos~~ | **Not collected in v1** (AUTH #020 / ADR-0006). V2 custom-avatar class only: if re-introduced, deleted immediately after generation on device, in storage and at the vendor, with a receipt (SECURITY_CHECKLIST §6.2) | — | — | — | — |
| **Derived environment assets**: splat, collision mesh, scene/traversal graph, environment spec, thumbnail | While the user keeps the environment. Published copies stay while published. | User deletes the environment (immediate purge); unpublish (removed from feeds immediately, private copy kept); delete-all | Private Supabase `environments` bucket at `{user_id}/{environment_id}/…` plus the `environments` table row (asset pointers, status) | The owner (RLS owner-only). Viewers of a published and cleared environment only through ≤ 15-min signed URLs issued server-side. The pipeline (service role). Moderators: the published thumbnail and package only (§10.4). | Supabase (storage, database); a CDN if one is added in M4 (cache purge on delete) |
| **Character selection + owned cosmetics** (no biometric) | While the account exists | Delete-all | Supabase database (profile/entitlement rows); purchase records at Apple | The user; the pipeline; Apple for App Store purchases | Supabase; Apple (App Store purchase records under Apple's own retention) |
| **Consent/ToS acceptance records** (policy version, timestamp, locale, text hash) | As long as legally required: **[period set by counsel, §4]**, then destroyed | The statutory period elapses. **Not** removed by delete-all (kept as proof, without content) until then | Supabase database, append-only table, no media | The pipeline; the Owner for legal requests | Supabase |
| **Telemetry events** (frozen schema v1.0.0: pseudonymous ids, no GPS, no media references, no free text) | Raw events: **[N days, set by counsel/Owner, §4; proposal 90]**. Aggregates (no user id) are kept. | Raw-event TTL (daily purge); delete-all removes every raw event with the user's pseudonymous id and rotates the id | Analytics tables in the Supabase database (M1 telemetry) | The pipeline; gj-data weekly aggregate reports (aggregates only) | Supabase |
| **Correction events** ("fix this label") | Derived data only. Used for training only while `training_opt_in` is true. | Opt-out stops future use. Delete-all removes the user's corrections and excludes them from future training sets. | Supabase database | The pipeline; the training job (opt-in rows only) | Supabase; Modal (training compute, ephemeral) |
| **Ratings, reports, leaderboard times** | While the environment exists | The environment is deleted (cascade) or delete-all (the user's own rows) | Supabase database | The user (own rows); aggregates shown publicly; moderators see reports (reason enum only, no free text) | Supabase |
| **Account + sign-in identity** (Supabase auth user; Apple/Google subject id; relay email if the user shares one) | While the account exists | Delete-all (auth user deleted; the Apple token revoked through Apple's REST API) | Supabase Auth | The user; the pipeline | Supabase; Apple and Google (identity providers under their own terms) |
| **Deletion receipts / audit entries** (no content) | [Counsel sets the period, §4; proposal 3 years] | The period elapses | Supabase database, append-only | The pipeline; the Owner | Supabase |

**Location data:** never retained. GPS/EXIF/location atoms are stripped on device and verified again server-side before storage (SECURITY_CHECKLIST §4). Any upload still carrying location is rejected.

**Corpus (not user data):** the Owner-supplied, consented test corpus and open-licence clips live on the private `gj-corpus` Modal volume. They are governed by the corpus manifest (M0-CAPT-01), not this schedule, and are never mixed with user scans.

## 2. Backups

Supabase point-in-time recovery backups roll over on the provider's backup window **[days, confirm with the plan, §4]**. Deleted rows disappear from backups when that window ends. The published deletion promise ("within 30 days") must be at least as long as the window. Storage objects are not backed up separately.

## 3. Deletion evidence

We keep only receipts that contain no media and no content: `{ request_id, pseudonymous user_id, data_class, action, processor, timestamp, processor_response_code }`. That proves the deletion happened without keeping any of the deleted data. See `DELETION_FLOW.md` §5.

## 4. Open items for counsel (before M5; drop this section before publishing)

- **Consent-record retention period** after account deletion.
- **Raw telemetry TTL**, `N` days (proposal 90).
- **Deletion-receipt retention period** (proposal 3 years).
- **Backup window**: confirm the Supabase plan's PITR window and that "within 30 days" covers it.
- **Raw-media ceiling**: SPEC says "until derived assets exist"; this schedule adds a hard 24 h ceiling for successful jobs (M0-LEGAL-02 AT-2). Confirm the 24 h and 7-day numbers as the published promise.
- **V2 biometric**: the BIPA/CUBI/MHMDA ceilings apply only if V2 custom avatars ship. v1 collects no biometric identifiers (AUTH #020).
- **Publication**: confirm the URL where this schedule (minus §4) is published and that the Privacy Policy links it.
