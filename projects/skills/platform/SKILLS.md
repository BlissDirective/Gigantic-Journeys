# gj-platform — Working Handbook

Remit: the backend. That covers Supabase (auth, Postgres + RLS, storage, edge functions), the Vercel API host, Inngest durable workflows (scan → reconstruct → scene graph → journey → package), the environment package format and signed-URL/CDN delivery, telemetry and correction ingestion against frozen schemas, GPS/EXIF stripping, the deletion flow and the per-user training opt-in (kit role block; ADR-0002; SPEC §3.10, §7). Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** writes migrations, the API and functions. The **Operator** does staging operations with staging credentials only: applying approved migrations, smoke tests, account checks (SECURITY_CHECKLIST §8.3; `supabase/README.md` "Staging"). Owned paths: `supabase/`, `api/`, `data/schemas/` (AUTH-gated), `services/packages/`. Most of this area is **security-sensitive**, so flag PRs `secondary-review: required` (SECURITY_CHECKLIST §8.2, AUTH #007).

Research list: `projects/skills/platform/RESOURCES.md` (104 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, evidence | `agents/grok/README.md` §3–§5 |
| AUTH before any account, credential, spend, table creation or schema change | `agents/grok/README.md` §6; SECURITY_CHECKLIST §2.5, §8.6; ADR-0002 ("every account needs an AUTH") |
| Secrets: only `.env.local`, the Bot credential store and CI secrets; production keys are CI-only | SECURITY_CHECKLIST §1.3, §1.4, §8.3; REVIEW_RUBRIC C1, C9 |
| RLS on every table in the same migration; the three policy patterns; anon key only in the client; private buckets | SECURITY_CHECKLIST §2.1–§2.4; REVIEW_RUBRIC C3 |
| Signed URLs ≤ 15 min, issued after an authz check; deep links hit authz; CDN forwards the signature | SECURITY_CHECKLIST §3.1–§3.3; REVIEW_RUBRIC C4 |
| GPS/EXIF stripped on device and again server-side; packages carry no location | SECURITY_CHECKLIST §4; REVIEW_RUBRIC C5 |
| Source-media deletion; per-user delete-all | SECURITY_CHECKLIST §6.1, §6.4; REVIEW_RUBRIC C7 |
| Pins and audits (`package-lock.json`, `==`, `npm audit`/`pip-audit` clean) | SECURITY_CHECKLIST §7; REVIEW_RUBRIC C8 |
| Cost caps: $50/day pipeline halt; per-key caps | SECURITY_CHECKLIST §8.5; REVIEW_RUBRIC D4 |
| OWASP Mobile Top 10 walk for app-facing changes | SECURITY_CHECKLIST §9; REVIEW_RUBRIC C2 |
| Telemetry validates against the frozen schema, no PII; rate limits; moderation | SECURITY_CHECKLIST §10; REVIEW_RUBRIC C10 |
| Idempotent, retry-safe Inngest steps; timeouts; classified errors | REVIEW_RUBRIC E3, E4 |
| Deterministic ranking where SPEC demands it | REVIEW_RUBRIC A6 |
| Surface-class enum in schemas = Bible §4 classes; distances in A | Movement Bible §1, §4; M1-DATA-01 AT-1 |
| Moderation state visible ("Under review") and browse by place | Design Skills rules 24, 25 (§3.10); DESIGN_SYSTEM decision 8 |

## 2. RLS-by-default patterns

- **The rule:** every `create table` in a migration comes with `enable row level security` and at least one `create policy` **in the same file**. `supabase/scripts/check_rls.py` enforces this in the `governance` workflow (`rls` job). Fixtures are in `supabase/scripts/tests/` (M0-PLAT-01).
- **Patterns** (`supabase/README.md`; SECURITY_CHECKLIST §2.2):
  - **Owner-only:** `for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid())`. Use it for drafts, a user's own rows and creator stats.
  - **Published-read:** `for select to anon, authenticated using (status = 'published' and moderation_state = 'cleared')`. Back it with a CHECK constraint so a row can't be published uncleared (see `environments_published_requires_cleared` in `20260926120000_m1_environments_staging.sql`).
  - **Service-role-only:** RLS on with no client policy for that path (moderation queue, ranking jobs, pipeline writes). Add an explicit deny-all or owner-read policy so the lint passes.
- **Test with two users plus anon:** another user and anon see only published+cleared rows, and cross-user writes are refused. M1-PLAT-01 ran this probe on staging inside a rolled-back transaction. Make it a pgTAP/pytest test for M4-DATA-01 AT-2.
- **Performance:** wrap `auth.uid()` as `(select auth.uid())` and index the policy columns (`environments_user_id_idx`, the partial published index).
- **Roles for moderators:** use JWT custom claims, never a client-side flag.
- **Storage** follows the same rule: private buckets, `{user_id}/…` object paths, and bucket policies reviewed like table policies (§2.4).
- **Every migration that creates a table cites `APPROVED #n`.** The only one so far is AUTH #034 (environments + private bucket), applied to STAGING on 2026-09-26 (`qa/reports/M1-PLAT-01.md`). Ratings, reports, leaderboard and moderation tables arrive with M4-DATA-01 (AUTH #026 scope; the migration still needs its own approval reference).

## 3. Idempotent Inngest steps

- **Current shape:** `api/src/inngest/functions.ts` has one function, `journey/pipeline`, on `scan.submitted`, with four `step.run` calls: reconstruct → scenegraph → journey → package. Steps are **memoized**, so a retry resumes at the failed step. Transitions are deduplicated by `scanId + step` in the recorder (`api/src/pipeline.ts`). M0-PIPE-01 is merged. M1 swaps the in-memory recorder for a Supabase-backed one (M1-PIPE-01).
- **Rules for real steps (M1-PIPE-01):**
  - **Same event id → no duplicate work.** Use Inngest's function idempotency key (event id / `scanId`), plus upserts keyed on `(scan_id, step)`.
  - **Every external call has a timeout constant** (`TIMEOUTS_MS`; M0-PIPE-01 AT-5).
  - **Classify errors.** Transient errors throw and retry. Permanent ones throw `NonRetriableError`. An `onFailure` handler marks the environment `failed` and gives the kind free-retry handoff (M1-CAPT-02 AT-5).
  - **Keep side effects inside steps.** Code outside `step.run` re-executes on every resume.
  - **Cost:** concurrency limits on GPU steps, per-job cost recorded, and new jobs halt at $50/day, resuming the next day (M1-CAPT-02 AT-2; §8.5).
  - **Waiting on a reconstruction backend:** use `step.waitForEvent` or a timed poll, never a blocking loop.
  - **Deletion:** cancel in-flight runs for the user (Inngest cancellation) as step 2 of delete-all.
- **Deploy status:** no Vercel deploy yet (M0-PIPE-01 AT-6). The Vercel and Inngest accounts exist under AUTH #012/#013, and M1-PLAT-01 AT-6 verifies them read-only. M1-PLAT-01 is **blocked** on Owner items: Apple and Google OAuth clients, and the edge-function deploy, which needs an account-wide Supabase access token (an Owner/CI credential, per `supabase/README.md`).

## 4. Signed URL delivery

- **Today:** `supabase/functions/environment-urls/index.ts`.
  1. It checks the caller's JWT (`verify_jwt = true`) and, through RLS, that they may see the row.
  2. It then issues `createSignedUrl(path, TTL_SECONDS)` with `TTL_SECONDS = 900` (the §3.1 cap).
  3. Unauthenticated calls get 401.
- **Scope:** packages, splats, meshes and full-size thumbnails are **never** public (§3.1). Feed thumbnails are the only possible exception, and only if an ADR names it (§3.4).
- **CDN (M4-PLAT-01):**
  - The CDN must forward the signature, and a direct storage URL is refused (AT-1).
  - Version package objects immutably so they cache well.
  - Downloads must support range requests so resume works.
- **Egress cost:** zero-egress storage (R2 / B2 via the Bandwidth Alliance) is the cost lever flagged in the reconstruction cost analysis. Choosing a CDN or storage vendor is an **ADR + AUTH**. **CDN vendor: TBD (M4-PLAT-01).**
- **Package format:** splat, collision mesh, scene graph, environment spec and thumbnail, vendor-neutral and versioned (M4-PLAT-01). Target ≤ 150 MB (SPEC §6), helped by SOG/.spz compression. **Format and manifest: TBD** (`services/packages/` is README-only; depends on M1-DATA-01).
- **Free-tier cap:** 3 published environments live at once, enforced at publish. Unpublishing removes the environment from feeds immediately and frees a slot (M4-PLAT-01 AT-3; SPEC §3.7).
- **Renderer:** M1-UNITY-01 AT-5 requires the renderer to load splats only through these URLs.

## 5. Schema freezing

- **What gets frozen:**
  - `telemetry_events` and `correction_events` (M0-DATA-01, open).
  - `scene_graph`, `traversal_graph` and `environment_spec` (M1-DATA-01, open, owned by gj-scenegraph with gj-platform review).
  - Today `data/schemas/` holds only a README, so **no schema is frozen yet**.
- **"Frozen" means:**
  - JSON Schema 2020-12, `schema_version` 1.0.0 (semver).
  - Valid fixtures plus one invalid fixture per schema.
  - A forbidden-field test that fails if a schema admits GPS/lat-long, email, phone, user free text, raw media references or device ids beyond a platform enum (M0-DATA-01 AT-3; §10.1).
  - An `APPROVED #n` in the PR.
  - `data/schemas/README.md` records the version and the change rule. Any later change is another AUTH, and CI's `protected paths need APPROVED` check blocks unapproved PRs.
- **Envelope** (M0-DATA-01 AT-1): `schema_version`, `event_id`, pseudonymous `user_id`, `env_id`, `client_version`, `platform`, `ts`, `scale_multiplier`.
- **Corrections** carry the Bible §4 class enum and a `training_opt_in` flag (AT-2).
- **gj-data signs off the catalogue** (AT-5).
- **Validation:** validate at ingestion (Ajv in TS, `jsonschema` in Python) with size and type limits (§9.4).
- **Evolution:** after the freeze, only additive, backward-compatible changes, each under its own AUTH.
- **Until M1-DATA-01 freezes:** `environments.environment_spec` is a flexible `jsonb`, validated at the app layer once frozen (migration header).

## 6. Deletion flows

- **Data classes and retention:** SPEC §7 is the source. The draft schedule and flow live in `legal/RETENTION_SCHEDULE.md` (M0-LEGAL-02, open; DRAFT pending counsel before M5). M0-LEGAL-02 AT-3 also asks for `legal/DELETION_FLOW.md`, which **doesn't exist yet**; today the flow is `RETENTION_SCHEDULE.md` §2. **TBD: M0-LEGAL-02.**
- **Automatic purges:**
  - Raw scan media is deleted once derived assets exist (the migration's `source_media_deleted_at` records it).
  - Failed jobs are deleted within 7 days (§6.1).
  - M0-LEGAL-02 AT-2 tightens this to "on successful derivation and no later than 24 h".
  - Schedule purges with `pg_cron` or an Inngest `step.sleep`. Delete storage objects through the Storage API, not by removing rows.
- **Delete-all** (Settings → Delete my data; complete within 30 days):
  1. Confirm.
  2. Revoke sessions and cancel pending jobs.
  3. Delete environments and published copies, character selection and cosmetics, ratings, reports, leaderboard entries, user-linked telemetry and correction contributions.
  4. Vendor-side deletion with receipts.
  5. Confirm to the user.
  - Receipts hold `{user_id, data_class, action, vendor, timestamp, vendor_response}` and no media.
  - `on delete cascade` from `auth.users` handles table rows. Storage objects and vendors need explicit steps.
  - Apple requires in-app account deletion.
  - A staging end-to-end run is suggested (§6.4, M5 gate).
- **Open counsel items:** consent-record retention, the raw telemetry TTL, and how deletion propagates to backups (`RETENTION_SCHEDULE.md` §4). Supabase backup windows matter for the last one.
- **Training opt-in:** default off, derived data only. Opting out stops future use, and delete-all removes past contributions (SPEC §3.9, §7).

## 7. GPS/EXIF stripping

- **On device** (M1-CAPT-01 AT-4, gj-capture): strip before the bundle is written. That means JPEG/HEIC EXIF, GPS and XMP, and MP4/MOV QuickTime location atoms (§4.1). On iOS, re-encode with ImageIO / `AVAssetExportSession` with metadata cleared.
- **Server side** (§4.2): verify on ingest and strip again. **Reject and count** any upload still carrying location. Re-strip again at publish before the vision pass (M4-DATA-03 AT-1; SPEC §3.7).
- **Outputs** (§4.4): packages and thumbnails carry no location or capture metadata beyond the schema (M4-PLAT-01 AT-2). Image transformations must not re-add metadata.
- **Tests (suggested, §4.3):** fixtures with synthetically injected GPS for all four formats, generated with ExifTool/Pillow/FFmpeg, never real media (§6.5; REVIEW_RUBRIC F3). The corpus tool `services/reconstruction/tools/strip_metadata.py` (M0-CAPT-01 AT-3) **isn't on main yet**. Reuse it once it lands rather than writing a second stripper.

## 8. Mistakes to avoid

- A table (or a new schema in an existing migration) without RLS + policy. Or a policy written `for all` when you meant `for select`, or `using` without `with check`.
- `security definer` functions without a pinned `search_path`, which silently bypass RLS.
- Handing out a public URL, a TTL > 900 s, or a URL issued before the authz check. Letting a CDN cache strip the signature.
- Anything with the service-role key reachable from the client, a fixture, a log or a report. Printing a project ref in evidence (M1-PLAT-01 AT-8; `staging_smoke.py` redacts it).
- Side effects outside `step.run`. Missing timeouts. Retrying permanent errors forever.
- Freezing or changing a schema without the AUTH. Adding a free-text or location-ish field "just for debugging".
- Treating a deleted DB row as deleted media. Storage objects and vendor copies need their own steps and receipts.
- Using production credentials. Bots hold staging only (§8.3). `staging_smoke.py` refuses the production ref; keep that guard.
- Loose dependency ranges without a committed lockfile (`api/package.json` uses `"inngest": "^3"`, so `package-lock.json` is what pins it; keep it committed, §7.1).

## 9. Checklists

**Pre-PR (backend):**
- [ ] `check_rls.py` green; each new policy has a two-user + anon test (C3).
- [ ] Migration cites `APPROVED #n`; schema changes carry their AUTH (B2).
- [ ] Signed URLs ≤ 900 s, issued after authz; no public bucket added (C4).
- [ ] Ingestion validates against the schema, with size/type limits; forbidden-field test passes (§9.4, §10.1).
- [ ] Inngest steps idempotent (test with a repeated event id); timeouts on every vendor call; errors classified (E3).
- [ ] Cost recorded per job; the $50/day halt is untouched or improved (D4).
- [ ] No secret, URL, project ref or key in code, fixtures, logs or evidence; secret-scan green (C1).
- [ ] `npm run lint/typecheck/test` (api) and `pytest` (scripts) green; `npm audit`/`pip-audit` clean (C8).
- [ ] New media input has a deletion path and a GPS/EXIF strip (C5, C7).
- [ ] PR flagged `secondary-review: required` if it touches auth, RLS, secrets, signed URLs or payments (§8.2).

**Staging operation (Operator):** AUTH exists · staging creds only · migration applied in one transaction via the session pooler and recorded in `schema_migrations` · `staging_smoke.py --report` run · evidence redacted · ticket history updated.

## 10. Pointers

`ADRs/0002-backend-platform-and-secrets.md` · `supabase/README.md`, `supabase/migrations/`, `supabase/scripts/check_rls.py`, `supabase/scripts/staging_smoke.py`, `supabase/functions/environment-urls/` · `api/README.md`, `api/src/` · `data/schemas/README.md` · `services/packages/README.md` · `legal/RETENTION_SCHEDULE.md`, `legal/PRIVACY_POLICY.md` · `qa/reports/M1-PLAT-01.md`, `STAGING-smoke.md` · SPEC §3.7, §3.9, §3.10, §7 · tickets M0-DATA-01, M0-PLAT-01, M0-PIPE-01, M1-PIPE-01, M1-PLAT-01, M1-CAPT-02, M1-DATA-01, M4-PLAT-01, M4-DATA-01, M4-DATA-03, M0-LEGAL-02.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | The first migration (AUTH #034) is on STAGING. M1-PLAT-01 is blocked on Owner OAuth clients and the edge-function deploy token. `environment-urls` caps TTL at 900 s. No schema is frozen yet (`data/schemas/` is README-only). `legal/DELETION_FLOW.md` is still missing (M0-LEGAL-02). `strip_metadata.py` isn't on main yet. | gj-operator expanded RESOURCES.md to 104 link-checked entries and rewrote SKILLS.md around the AT-2 topics (M0-SKILL-06). |
