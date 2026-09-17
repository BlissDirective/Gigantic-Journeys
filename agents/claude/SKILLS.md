# Claude Code Builder — Engineering Skills Handbook

`agents/claude/SKILLS.md` · v1.0 · 2026-09-17 · Authorization: APPROVED #007. Read at the start of every Builder session with `BUILDER.md` and `SELF_GOVERNANCE.md`. This is the working handbook the Builder uses to write, self-review, secure, merge, and ship code. It cross-references the authorities rather than duplicating them: `governance/REVIEW_RUBRIC.md`, `governance/SECURITY_CHECKLIST.md`, `SPEC.md`, `design/MOVEMENT_BIBLE.md`, `design/DESIGN_SYSTEM.md`.

## 0. How the Builder works now (AUTH #007)

The Builder writes code, **self-reviews it, and merges its own PRs to `main` once CI is green** — no session hand-off to merge. A **secondary reviewer** (the Coordinator by default, or an Owner-designated reviewer) reviews independently at intervals, not per-PR (`governance/AGENT_GOVERNANCE.md` §5). Self-review replaces the second pair of eyes on each merge, so the bar for self-review is higher, not lower. Two things are non-negotiable: **CI must be green before any merge**, and **security-sensitive changes are flagged for priority secondary review** (§2).

## 1. Code review (how to self-review before merging)

Run this on your own diff as if a stranger wrote it, before you merge:

1. **Against the ticket.** Every required-level acceptance criterion is met with evidence in the PR; suggested-level criteria are noted (`REVIEW_RUBRIC.md` §A). If a criterion is not met, the PR is not ready.
2. **Against SPEC.** The change matches `SPEC.md`; nothing added that is a non-goal (§4). Behavior SPEC does not describe needs a design-change AUTH first.
3. **Adversarial diff read.** Ask: what input makes this crash, loop, or corrupt state? What did I forget to handle (empty, null, huge, concurrent, offline, malformed)? What would make CI reject this? Fix everything you find before merging.
4. **Determinism where SPEC demands it.** The validator, route generation, and ranking must give the same output for the same input, with a test proving it (`REVIEW_RUBRIC.md` §A6).
5. **Scope.** Only the ticket's files changed; no drive-by edits; no scope creep. Split anything extra into its own ticket or `BACKLOG.md`.
6. **Walk the rubric.** REVIEW_RUBRIC.md rows A–H apply to you as the reviewer now. Any blocking row that fails means do not merge.
7. **Flag for secondary review.** Anything touching auth, RLS, secrets, signed URLs, consent, payments, or the movement/validator contract: mark the PR `secondary-review: required` in its body so the periodic reviewer covers it first. When unsure whether a change is significant, flag it.

Merge only when every blocking rubric row passes, CI is green, and the acceptance evidence is in the PR. A merge with red CI is a process violation.

## 2. Code security (the checklist is the authority)

`governance/SECURITY_CHECKLIST.md` is binding; this is the working summary. On every change ask which of these apply and satisfy them:

- **Secrets (§1).** No key, token, or `.env*` (other than `.env.example`) in the diff, history, logs, screenshots, or fixtures. If a secret ever touched git, it is compromised: rotate within the hour and record it. You hold no production credentials.
- **OWASP Mobile Top 10 (§9).** For app changes note the applicable items in the PR: credential usage (no keys in the binary; vendor calls via the backend), supply chain (pinned deps), auth/authz (every endpoint checks auth; RLS backs every query), input/output validation (schemas at ingestion; size and type limits), communication (TLS only), privacy controls, binary protections (IL2CPP, symbols stripped, debug compiled out), misconfiguration, data storage (app container only; media removed after upload), cryptography (platform only).
- **Supabase RLS (§2).** Every new or changed table has `enable row level security` and policies in the same migration; the client uses only the anon key; the service-role key is server-side only; buckets private by default. A policy test is suggested, not required, but the RLS itself is required and `check_rls.py` gates it.
- **Signed URLs (§3).** Packages, splats, meshes, avatars, and full-size media are served only through short-lived signed URLs after an authorization check; no public buckets except an ADR-named thumbnail case.
- **Media privacy (§4, §6).** Any image or video path strips GPS/EXIF on device and re-verifies server-side; source media is deleted after derivation; face and body photos are deleted after avatar generation with a logged receipt.
- **Consent gate (§5).** No face or body byte leaves the device and no vendor job starts before a consent record exists; consent is a separate explicit step; training is a separate opt-in, default off.
- **Dependencies (§7).** Exact pins everywhere; `pip-audit` and `npm audit` clean at high and above; each new dependency justified in one line with a commercial-compatible license (no GPL/AGPL in the app).
- **Telemetry (§10).** Events validate against the frozen schema; no GPS, email, raw media references, or user free text; no PII in logs or reports.

When you touch any of the above, flag the PR for secondary review (§1.7).

## 3. Development skills (this stack)

- **Unity 6 (C#, URP, mobile).** Target the newest iPhones best, tier down automatically for older ones (SPEC §6). Movement and camera constants come only from `config/movement.json`; never hard-code them (`REVIEW_RUBRIC.md` §E2). Keep the five movement assemblies referencing only downward (Bible §2). Drive the editor headless with `-batchmode` for anything scriptable; a GUI-only step goes to the Grok Operator. Keep `Assets/StreamingAssets/movement.json` byte-identical to `config/movement.json` (CI `movement-sync` gates it).
- **TypeScript (Inngest, Vercel API).** Strict mode; `package-lock.json` committed. Inngest steps are idempotent and retry-safe; every vendor call has a timeout and classified errors (`REVIEW_RUBRIC.md` §E3). No secret in the repo; names in `.env.example` only.
- **Python (services).** `requirements.txt` with exact `==` pins; `ruff` clean; typed I/O at the boundaries; validators and metadata-stripping tools carry property or fixture tests covering edge cases (empty graph, unreachable summit, GPS in several container formats).
- **Testing.** Tests are suggestions for the merge gate (AUTH #003) but they are how you make code correct and how you trust your own merge. Deterministic and hermetic: no network, no vendor calls, no real media; fixtures synthetic and small. Never delete or skip a test to get green.
- **Git and CI.** One ticket per branch `ticket/<id>-<slug>`; push every 2 hours; conventional commit subject `<ticket-id>: <what>`. Before merge run the repo's fast checks locally (`ruff check . && ruff format --check .`; `python tickets/validate.py`; `python .github/scripts/check_movement_sync.py`; the language checks for the files touched) and confirm the PR's CI is green.
- **The movement/validator contract.** `config/movement.json` is the single source of truth shared by the controller and the traversal validator; changing a value is a design-change AUTH (Bible §10). The validator accepts a route segment only under the constants with a 15% margin.

## 4. Production development skills (shipping, not just building)

- **Release readiness.** Debug code compiled out of release via `GJ_DEBUG`; IL2CPP; symbols stripped; no verbose logging or test modes in release builds (SECURITY_CHECKLIST §9.7, §9.8). The debug overlay's saved performance report is the Owner's device-measurement evidence.
- **Performance.** Every gameplay, UI, capture, and avatar change states its expected effect on the SPEC §6 targets; hold 30 fps on older iPhones and target 60 on current ones with Tier 0 and Tier 1 on; animation plus IK plus warping ≤ 4 ms/frame; motion DB ≤ 60 MB; no full-screen blur in play.
- **Observability.** Telemetry against the frozen schema only; structured logs with no PII; the daily $50 cap and per-key vendor caps are respected and the pipeline halts at the cap.
- **Data and migrations.** Schema changes are AUTH-gated and versioned; migrations are forward-only with a documented rollback; RLS ships in the same migration as the table.
- **Error handling.** Handle at the boundary with user-facing copy in the design-system voice; never swallow errors; failures are kind, specific, and actionable (DESIGN_SYSTEM §7).
- **IAP and privacy (M5).** Cosmetic-only, no pay-to-win or dark patterns; restore and Family Sharing on day one; App Store privacy labels accurate to the telemetry schema; consent, retention, and deletion flows verified end to end before submission.
- **Definition of done.** A change is done when its acceptance criteria pass, CI is green, it is merged, and it moves the milestone toward its exit test (SPEC §8, §9).

## 5. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 1.0 | 2026-09-17 | Initial Builder engineering handbook: self-review, code security, development, and production-development skills, aligned to the Builder's new self-review-and-merge authority | AUTH #007 |
