# gj-data — Working Handbook

Remit (kit §3 role block; `agents/grok/roles/gj-data.md`):
- the weekly telemetry analysis in `data/reports/` (fall/quit/stuck heatmaps, summit and route completion rates, vista discovery, ratings);
- the environment ranking model and its anti-gaming rules;
- proposals for validator rules and route-generation example sets;
- correction-data curation and, post-launch, surface-classifier retraining on **opt-in derived data only**;
- moderation queue operation (vision pass, flagged environments, policy application, escalation to the Owner);
- the affordance library export.

Owned paths: `data/reports/`, `services/moderation/`, `ml/`. **This hat never touches raw photos or video.** Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** writes ranking/moderation/ML code and report scripts. The **Operator** runs long jobs, compiles reports and works the queue UI (`AGENT_GOVERNANCE.md` §2). Ranking, moderation, rate limits and anything touching RLS are **security-sensitive**: flag those PRs `secondary-review: required` (SECURITY_CHECKLIST §8.2; AUTH #007).

Research list: `projects/skills/data/RESOURCES.md` (108 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, evidence | `agents/grok/README.md` §3–§5 |
| AUTH before schema changes, new vendors (vision API, analytics), paid tiers (read replica) | `agents/grok/README.md` §6; REVIEW_RUBRIC B2, B3, H1 |
| Telemetry validates against the frozen schema; no GPS, email, raw media refs or free text | SECURITY_CHECKLIST §10.1; REVIEW_RUBRIC C10 |
| Ratings/reports rate-limited per user and device; anti-gaming survives a rate-spam test | SECURITY_CHECKLIST §10.2 (M4 gate) |
| Leaderboard times validated against route length + movement constants | SECURITY_CHECKLIST §10.3 (M4 gate); SPEC §3.7 |
| Moderation queue: "Under review", escalates to the Owner, no raw media to Bots beyond thumbnail + package | SECURITY_CHECKLIST §10.4 (M4 gate) |
| Apple 1.2: filter, one-tap report + timely response, block, published contact | SECURITY_CHECKLIST §10.5; SPEC §3.7 |
| Bots never handle raw user media; corpus is Owner-supplied and consented | SECURITY_CHECKLIST §6.5 |
| RLS: published-read = published AND cleared; queue and ranking jobs service-role-only | SECURITY_CHECKLIST §2.2; REVIEW_RUBRIC C3 |
| Per-user delete-all removes ratings, reports, times, telemetry and correction contributions | SECURITY_CHECKLIST §6.4; SPEC §7 |
| Ranking deterministic (same input, same output) | REVIEW_RUBRIC A6 |
| Tests hermetic, synthetic fixtures; validators/ranking/schema checks get property or fixture tests | REVIEW_RUBRIC F1, F3 |
| Movement numbers only from `config/movement.json` | REVIEW_RUBRIC E2; Movement Bible §2 |
| Correction labels use the surface-class enum | Movement Bible §4; M0-DATA-01 AT-2 |
| Browse by place; one-tap ratings and reports; moderation fast and visible | Design Skills rules 24, 25 (§3.10); DESIGN_SYSTEM decision 8 |
| Assist-mode leaderboard entries tagged, never excluded | DESIGN_SYSTEM decision 10 |
| Incidents (illegal content, PII leak): contain, record, notify the Owner | SECURITY_CHECKLIST §11 |

## 2. Weekly report structure

- **Where and for whom:** `data/reports/`, read by the Coordinator on AUDIT. **Aggregates only, never raw events with identifiers** (`data/reports/README.md`). The report loop is in DEVELOPMENT_PLAN §4 step 6: the analyst writes the report; the Coordinator proposes spec/validator tickets and a "learning loop" PR with before/after metrics on the held-out corpus.
- **Preconditions** (none met yet, so no weekly report can run today):
  - Frozen telemetry schemas. **M0-DATA-01 is open**: AUTH #029 approved the freeze, but `data/schemas/` holds only a README.
  - Ingestion (gj-platform, M1).
  - Real play.
  - **Data access is TBD.** DEVELOPMENT_PLAN names a read-only replica, which is a paid Supabase feature (AUTH first). Until then, use service-role aggregate views run by the Builder/Operator, never ad-hoc raw exports.
- **Suggested skeleton** (proposed here; the first real report can refine it and record the format in `data/reports/README.md`):
  1. **Header:** ISO week, schema_version, client_versions covered, event counts by type, validation-reject counts, known data gaps.
  2. **Funnel:** scan_started → scan_completed → play_started → summit_reached → route_completed → publish, with week-over-week deltas. scan_failed quality metrics get their own table for gj-capture.
  3. **Heatmaps:** fall (by tier, height_A), stuck (dwell > 20 s) and quit positions, in env-local A units per environment (M0-DATA-01 AT-1). Never world or GPS positions.
  4. **Completion:** per route, completion rate with Wilson intervals, time distribution, and beat reached on abandon. Summit rate per environment. Vista discovery rate.
  5. **Ratings:** four-axis distributions, rating volume, and anomalies flagged by the anti-gaming job (§3).
  6. **Ranking model report:** current weights (config version), top movers and why, and spam-detector hits.
  7. **Corrections:** volume by surface class, agreement rate, suspected-noise share (§5).
  8. **Findings → proposals:** each finding becomes a proposed ticket (validator rule, route-gen example set, capture coaching). Nothing changes SPEC or movement.json without the normal AUTH.
- **Disclosure control:** suppress small cells so a single player can't be picked out. **The minimum cell size is TBD**; set it in the first report and record it in `data/reports/README.md`. No user_id, env_id-to-user joins, or free text in any committed report.

## 3. Ranking model and anti-gaming (M4-DATA-02; AUTH #026)

- **Locked shape** (Owner fork 9.2 = balanced blend): score = config-weighted blend of the **four-axis ratings** (fun / interesting / interactive / exciting) and **five derived signals** (verticality, move variety, reachable volume, completion rate, replay rate).
  - Signals are computed from `environment_spec` and telemetry, **never creator-supplied** (AT-1).
  - Weights live in config and are telemetry-tunable. **Weight values are TBD (M4-DATA-02).**
- **Feeds** (decision 8; AT-2): **Top this week** = the blend with a time decay; **New** = recency; **Near your scale** = Room/Tabletop filter. Friends comes later with social features.
- **Robust rating aggregation:** use a Bayesian average or a lower confidence bound per axis so a handful of votes can't top the feed. Put Wilson bounds on completion and replay rates, and normalise signals per scale (room vs tabletop) before blending.
- **Anti-gaming** (proposal §2; SECURITY_CHECKLIST §10.2):
  - rate limits per user **and** device (DeviceCheck/App Attest rather than device IDs in telemetry);
  - one rating per account per environment (a DB unique constraint in M4-DATA-01);
  - no self-rating;
  - weight toward trusted signals: completed-run raters, account age, rater history;
  - brigade detection: bursts, lockstep accounts, skewed distributions.
- **The M4 exit test** (M4-DATA-02 AT-3; M4-QA-01 AT-3, a merge gate): a scripted spam attack must not materially move an environment's rank. Define "materially" in the test before running it, and keep the attack script in the repo (synthetic accounts, staging only).
- **Determinism** (A6): same inputs and config → same order. Break ties by stable keys, never randomness.
- **Assist:** leaderboard entries made with Assist are tagged, never excluded (decision 10). That's a UI rule the ranking data must carry.

## 4. Moderation queue operation (M4-DATA-03; AUTH #026)

- **Pipeline** (SPEC §3.7; Owner fork 9.1 = auto-clear + human-on-report):
  1. Draft (creator-playable).
  2. Publish tapped.
  3. **Server-side GPS/EXIF re-strip**, verified (§4.4).
  4. **Automated vision pass.**
  5. Auto-clear to public, **or** low confidence → the human queue.
  6. The item stays "Under review" and creator-only until cleared.
  7. A rejection carries a one-line reason and an Appeal.
  - Unpublish removes the environment from feeds immediately.
- **The vision pass covers the report reasons** (decision 8): private information visible, inappropriate content, not a real place, broken environment (M4-DATA-03 AT-3).
  - **Vendor or model: TBD (M4-DATA-03).** Candidates are in RESOURCES §C: self-hosted CLIP-style classifiers fit the "our own infrastructure" posture (SPEC §3.9); cloud APIs need an ADR + AUTH.
  - Calibrate confidence so the low-confidence threshold is meaningful. **The threshold is TBD**, tuned on the ~50-environment M4 run (M4-QA-01).
- **The human queue works on:** all low-confidence flags, **all user reports**, and all appeals. Escalate to the Owner. **Queue items show only the published thumbnail + package, never raw media** (§10.4). Reports are rate-limited and show "Under review" to the reporter immediately (AT-2).
- **Operating rules:**
  - Decide against a written policy (the report reasons) and record every action in `moderation_actions` (M4-DATA-01).
  - Give reasons in one line, in the decision-2 voice.
  - Appeals get a second look by someone other than the original decider where possible.
  - Blocking abusive users must work (Apple 1.2 #3).
  - Developer contact info is published (#4; the UGC ToS/EULA is a LEGAL follow-up per proposal §6).
- **Illegal content** (for example CSAM): don't open, forward or download it. Preserve it per the escalation procedure, escalate to the Owner at once, and report to the authorities (NCMEC CyberTipline in the US). Treat it as a SECURITY_CHECKLIST §11 incident. **The written escalation procedure is TBD** (proposal §1 names it; no document yet).
- **Response time:** Apple requires a "timely" response. **No SLA number is set (TBD, M4-DATA-03).**
- **The M4 exit** is zero moderation misses in the Owner's review of 50 publishes (M4-QA-01 AT-2, an Owner judgment).

## 5. Correction curation

- **Source:** one-tap "fix this label" → `correction_submitted` (M0-DATA-01 AT-2), carrying surface id, old label, new label (**Bible §4 class enum**: walkable-hard, walkable-soft, walkable-narrow, ledge, rung, stud, textured-vertical, pole, overhang, slope, wall-smooth, soft-hanging, void, …), env-local position, confidence, and the `training_opt_in` flag.
- **Curation steps:**
  1. Drop events where `training_opt_in` is false from any training set. They may still feed aggregate quality stats in the weekly report.
  2. Validate against the schema and drop malformed events.
  3. Aggregate per surface: majority/agreement across users, weighted by rater reliability. A single user's correction is a hint, not ground truth.
  4. Flag likely label noise with confident-learning methods (cleanlab) and hold it for review.
  5. Watch for poisoning: many corrections from few accounts, or corrections that make surfaces "more traversable" in suspicious patterns.
  6. Keep a versioned, derived-only dataset (labels + derived geometry features) with a datasheet.
- **Uses:** validator-rule proposals and route-generation example sets for gj-scenegraph, with the affordance library v1 (chair, table, couch, shelf, plant, lamp) exported from corrections (DEVELOPMENT_PLAN M6).

## 6. Retraining on derived data only (M6)

- **Scope** (SPEC §3.9, §7, §8 M6): the first surface-classifier retrain on **opt-in derived data**, with before/after metrics on the **held-out corpus**. The training toggle defaults off. Opt-out stops future use; delete-all removes past contributions. Raw photos and video never enter `ml/` (`ml/README.md`).
- **"Derived" means** splat/mesh/scene-graph features and labels, never source frames. Scan source video is deleted once derived assets exist anyway (SPEC §7).
- **Evaluation:** split by environment (GroupKFold style) so no environment is in both train and test. Report per-class precision/recall/F1 and calibration. Publish a model card with the before/after table in the learning-loop PR. **The held-out corpus definition is TBD**: agree it with gj-scenegraph before M6, drawn from the Owner-supplied corpus (§6.5).
- **Deletion-aware training:** record which dataset version each model used (DVC/MLflow-style lineage) so delete-all can be honoured. Retrain from a dataset that excludes deleted/opted-out users. SISA-style sharding is an option if retrains get expensive.
- **Privacy hardening, if needed:** membership-inference checks on the trained model. DP-SGD or federated approaches are options, not decisions; any change of approach goes in an ADR.
- **Change control:** a retrained classifier that changes route generation goes through gj-scenegraph review and the determinism/validator tests (M1-SCEN-05). It never changes `movement.json` constants.

## 7. Leaderboards (shared with gj-gameplay, M4-GAME-02)

- **Plausibility floor** (Owner fork 9.3 = A): reject a time below the validator's theoretical minimum for that route, reusing M1-SCEN-05 and `config/movement.json` with no duplicated numbers. Add telemetry sanity checks, rate limits, and tie each time to a completed, validated run (AT-1, AT-2; §10.3).
  - **How the floor is computed** (fastest legal traversal of the route's transitions under movement.json max speeds and reaches) is **TBD** in M4-GAME-02.
  - Note that the route validator's 85 % margin is for *generating* safe routes, not for bounding the fastest legal time.
- **Full replay verification** (fork B) is out of v1 scope. Keep ghost data in a shape that could support it later.

## 8. Mistakes to avoid

- Committing raw events, user_ids, env_id→user joins, free text or small cells in a report.
- Adding a telemetry field "just for analysis". Schema changes are an AUTH (#029's rule), and the forbidden-field test exists for a reason.
- Letting creators supply ranking signals, or letting unrated/new environments top the feed on two votes.
- Rate limits keyed only on user (account farming) or on a device ID that ends up in telemetry.
- Moderators or Bots viewing anything beyond the thumbnail + package. Downloading or forwarding suspected illegal content.
- Training on opted-out users' corrections, on raw media, or evaluating on environments that were in training.
- Duplicating a movement constant in leaderboard or ranking code.
- Choosing a vision vendor or paid analytics without an ADR + AUTH.

## 9. Checklists

**Pre-PR (data/ranking/moderation):**
- [ ] Schemas unchanged, or the PR cites `APPROVED #n` (B2); forbidden-field test green.
- [ ] Reports aggregate-only with small-cell suppression; no identifiers (C10).
- [ ] Ranking deterministic; weights from config; signals derived, not creator-supplied (A6; M4-DATA-02 AT-1).
- [ ] Rate limits per user and device; rate-spam test present and green (§10.2).
- [ ] Moderation paths expose only thumbnail + package; actions logged; "Under review" states correct (§10.4).
- [ ] Training data opt-in only, derived only, deletion lineage recorded (SPEC §3.9, §7).
- [ ] No movement numbers duplicated (E2); tests hermetic with synthetic fixtures (F3).
- [ ] `secondary-review: required` flag if RLS, rate limits or moderation logic changed (§8.2).
- [ ] Repo checks green: `ruff check .`, `ruff format --check .`, `python tickets/validate.py`, `python .github/scripts/check_movement_sync.py`.

**Weekly report:** data window and schema_version stated · validation rejects counted · cells suppressed · findings turned into proposed tickets · nothing committed but aggregates.

**Queue shift:** policy reasons at hand · only thumbnail + package opened · every action logged with a reason · appeals routed to a second reviewer · illegal content escalated, not handled.

## 10. Pointers

`data/reports/README.md` · `data/schemas/README.md` · `services/moderation/README.md` · `ml/README.md` · `design/proposals/publish-browse-rank-moderation-v1.md` · `context/DEVELOPMENT_PLAN.md` §4, M6 · SPEC §3.7, §3.9, §7, §8 · SECURITY_CHECKLIST §2.2, §6.4–§6.5, §10, §11 · Movement Bible §4 · DESIGN_SYSTEM decisions 8, 10 · Design Skills §3.10 · tickets M0-DATA-01, M1-SCEN-05, M4-DATA-01, M4-DATA-02, M4-DATA-03, M4-GAME-01, M4-GAME-02, M4-QA-01.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | The telemetry/correction schemas are **not frozen yet**: AUTH #029 approved the freeze, but M0-DATA-01 is open and `data/schemas/` is README-only. The previous handbook said "frozen v1.0", which was wrong. Still undecided: vision-pass vendor/model, low-confidence threshold, response SLA, ranking weights, the leaderboard floor computation, the held-out corpus, the report's minimum cell size, and data access for analysis. | gj-operator expanded RESOURCES.md to 108 link-checked entries and rewrote SKILLS.md around the AT-2 topics (M0-SKILL-09). |
