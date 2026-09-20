# PROGRESS.md

Living tracker. Updated by the Coordinator on every merge, AUTH decision, and checkpoint. Last update: **2026-09-20** (M0 AUTH batch #008–#017 **approved**; #016 legal review is in-house at $0 (no external spend); M0-REPO-03 unblocked; M0 legal drafts in `legal/` for the Owner's in-house team; Meshy selected as head vendor (Tripo dropped); vendor research landed (`research/vendors/`) with two flags — Meshy needs Enterprise+DPA for biometric, Luma reconstruction/train concerns; build-vs-buy research complete; **Owner set the v1 game plan (2026-09-18): self-host reconstruction + KIRI corpus-only bridge (AUTH #018, spike M1-CAPT-03); v1 avatar = pre-made curated character roster with NO biometric (AUTH #020 / ADR-0006, supersedes the avatar vendor); focus on video→playable + world-class movement. Custom avatars → V2 R&D track (`research/rnd/`). Then the **movement v1 expansion (AUTH #021): full parkour + dive-roll/tic-tac/vault-variants/wall-run and a traversal-tools layer (safety-pin grapple + matchstick pole-vault) via IVerbProvider; a narrow §4 exception for diegetic character tools.** SPEC → v1.4; Movement Bible + movement.json updated; tickets M1-MOVE-02, M3-MOVE-01. Then **sound + environment reactivity (AUTH #022, SPEC → v1.5):** scale-aware acoustics (reverb from the reconstructed room), the §9 feedback matrix extended to all verbs/tools, Tier 1 soft reactivity extended to tools, restrained adaptive music, muted-playable accessibility; tickets M1-GAME-04, M3-GAME-01.** Then **journey generation v1 (AUTH #023, SPEC → v1.6):** a T0–T3 verb-difficulty model; per-environment rising-difficulty routes (a global difficulty score kept as metadata for later absolute filtering); beat 1 = T0 only with the twist as the signature/tool beat; **traversal tools may be required to summit when taught in an earlier beat (never beat 1)**; vista scoring; a retry→template-fallback so no scanned environment is ever a dead end; tickets M1-SCEN-03/04/05 sharpened (`design/proposals/journey-route-generation-v1.md`). Then **character roster art spec (AUTH #024, SPEC → v1.7):** a curated roster of **8** rigged semi-photoreal 1:12 characters on one enforced GJ rig standard (Unity Humanoid + IK/contact markers + AUTH #021 tool sockets + rig-conformance gate); grounded semi-photoreal for v1 with a V2 hero-photoreal roadmap on the same rig; cosmetic SKUs gated by a verb+tool clip test; **dual-track sourcing — open-base authoring primary at $0 spend, leaner CC4/Mixamo license path noted as a short-term contingency** (`design/proposals/character-roster-v1.md`, `research/vendors/character-roster-sourcing.md`); DESIGN_SYSTEM decision 4 + M2-AVAT-01 updated. Then **capture UX + coaching (AUTH #025, SPEC → v1.8):** the capture flow/state machine + room & tabletop coaching scripts + a reconstruction-readiness quality gate (coverage/overlap/blur/light/tracking) + the capture→reconstruction upload contract + failure/recovery + first-run coaching, built on the locked coaching UI (decision 6); **an on-device readiness predictor + multi-pass 'add a pass' loop** (extends decision 6; new ticket **M1-CAPT-04**); **people in frame handled by coaching + publish-time moderation, no on-device person detection** (§3.9); tickets M0-CAPT-01/M1-CAPT-01/02 sharpened (`design/proposals/capture-ux-coaching-v1.md`). Then **publish/browse/rank/moderation (AUTH #026, SPEC → v1.9):** deepened §3.7 and **decomposed M4** (no tickets existed) — auto-clear + human-on-report moderation with **Apple 1.2 UGC compliance** (filter/report/block/contact); **balanced-blend ranking** (four-axis ratings + objective signals, Top-this-week decay, anti-gaming/rate-spam); **plausibility-floor leaderboards** reusing the deterministic validator (M1-SCEN-05); signed-URL/CDN delivery (≤15 min) + RLS (published-read = published AND cleared); free-tier cap; v1 social non-goals. SECURITY_CHECKLIST §10.5 added; 8 M4 tickets created (M4-PLAT-01, M4-DATA-01/02/03, M4-GAME-01/02, M4-QA-01, M4-FORE-01) (`design/proposals/publish-browse-rank-moderation-v1.md`). Ticket table regenerated with `python tickets/validate.py --summary`.

## Milestone

| | |
|---|---|
| Current milestone | **M0 Harness** (scaffold in progress; `START M0` not yet issued by the Owner) |
| M0 target checkpoint | 2 weeks after `START M0` (2026-09-29 if issued today) |
| Exit test | One ticket goes from creation to merged PR with a QA screenshot attached and no human typing (M0-UNITY-04) |
| Next checkpoint report | `governance/CHECKPOINTS/M0.md` by gj-foreman (M0-FORE-04) |

Milestone states: M0 in progress · M1–M6 not started (SPEC §8).

## Ticket counts

| Status | Count |
|---|---|
| open | 68 |
| in-progress | 0 |
| in-review | 0 |
| changes-requested | 0 |
| blocked | 1 |
| merged | 1 |
| done | 3 |
| cancelled | 3 |
| **total** | **76** |

## Blockers

- Bots cannot start until the Owner hands the Bot machine-user PAT to the team (AUTH #002 approved; Owner creating it) and creates the Foreman Bot from `agents/grok/roles/gj-foreman.md`.
- Unity CI jobs skip until the Unity project exists (M0-UNITY-01) and license secrets are added (M0-REPO-03). The Unity account AUTH is now approved (#008); M0-REPO-03 is unblocked and awaits the Owner creating the Unity account and adding the secrets.

## Pending AUTH REQUESTs

| # | What | Status |
|---|---|---|
| #008–#017 | M0 batch: Unity, Luma, Meshy+Tripo, Supabase, Vercel, Inngest, domains, USPTO search, legal review, crash reporting | **APPROVED 2026-09-17** (Decisions #008–#017; #016 = $0 in-house legal review). No AUTHs pending. |

## Owner decisions (2026-09-15)

- **AUTH #007 (2026-09-17): Builder self-review and merge.** The Builder self-reviews and merges its own PRs to main on green CI (no session hand-off). Per-PR separation is replaced by periodic independent secondary review (weekly, at checkpoints, 100% of security-sensitive merges). New Builder engineering handbook `agents/claude/SKILLS.md`. Residual risk accepted; automated gates plus secondary review mitigate.

- **AUTH #006 (2026-09-17): agent operating model.** Claude Code Builder writes code, the Coordinator reviews and merges, one Grok Bot Operator does computer use and long-running ops (skill hats). Cursor retired from the loop. Single-threaded writes, bounded bursts by exception. Docs: `governance/AGENT_GOVERNANCE.md`, `agents/claude/SELF_GOVERNANCE.md`, `agents/claude/BUILDER.md`, `agents/grok/roles/gj-operator.md`.

- AUTH #002 approved: the Owner creates the Bot machine user and PAT and hands it to the Bot team; every Bot asks for it before any work.
- Scaffold merged to main on the Owner's instruction.
- Repository stays **public** for now (free Actions minutes, free macOS runners, native secret scanning; plan and design docs are world-readable). Revisit before M4 when user data flows.
- The Owner already holds an Apple Developer Program membership.
- **AUTH #003: v1 launches on the iOS App Store only.** Android stays a compiling build target (on-demand CI) for a v1.1 release; no Play Console, Android device, or Mac mini in v1.
- **No minimum device model.** Best-possible graphics and capabilities on the newest iPhones; automatic quality tiers keep older iPhones playable (SPEC §6).
- **Tests are suggestions, never merge gates.** The Owner tests thoroughly on real iPhones; merge gates are the automated CI checks and the security rules (SPEC §11). Acceptance criteria carry `required` or `suggested` levels.
- **iPhone Duo features selected:** stand-mode console layout, unfold as the signature transition, rear-camera avatar capture (candidates 1–3 of `design/proposals/iphone-duo-track.md`). Tickets M1-DUO-01 (research spike), M2-DUO-01, M3-DUO-01, M3-DUO-02, M5-DUO-01; go/no-go at the M3 checkpoint.
- The Owner holds an App Store Connect API key; CI has a TestFlight lane ready behind `TESTFLIGHT_ENABLED` (M0-REPO-05, M0-REPO-06).
- 2026-09-16: design decisions 1–4 transcribed into DESIGN_SYSTEM.md v0.4 (M0-OWNER-02 done; M0-DSGN-02 unblocked). Palette contrast measured: `text.muted` and the semantic colors need derived tokens (DESIGN_SYSTEM §12). Coordinator input on decision 3 and options for decision 5 filed under `design/proposals/`, awaiting the Owner's AUTH #004.
- The M0 AUTH batch #008–#017 is **approved** (2026-09-17); #016 legal review is in-house ($0, no external spend). **Vendor research complete** (`research/vendors/`) → **ADR-0005 / AUTH #018–#019 (2026-09-18):** reconstruction backend = **self-host + managed bridge** (Luma dropped, API deprecated), head vendor = **Avatar SDK/MetaPerson on-prem** (Meshy dropped, #010 superseded). Spike ticket **M1-CAPT-03** created; ADR-0003 superseded. M0 legal drafts in `legal/` for the Owner's in-house legal team.

## Owner actions needed now

1. Create the machine user and PAT (M0-REPO-04), then create the Foreman Bot by pasting the block in `agents/grok/roles/gj-foreman.md`; it will ask you for the token first. Then the eight specialists from the other prompt packs.
2. Configure branch protection and native secret scanning on main (M0-REPO-02).
3. Lock decision 5: reply `APPROVED #004: decision 5 = recommended package` (or the letters that differ) against `design/proposals/decision-5-play-layout-options.md`; optionally adopt items from `decision-3-transition-input.md` in the same reply. Then decisions 6–10.
4. Add the App Store Connect key to CI (M0-REPO-05): secrets `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`; variable `APPLE_TEAM_ID`; create the App Store Connect app record (reserves the name) with an internal TestFlight group on automatic distribution. Set `TESTFLIGHT_ENABLED=true` after M0-UNITY-01 merges.
5. Decide whether to acquire an iPhone Duo for verifying the three selected features (AUTH spend), or accept adaptive design until one is available.
6. Scan 10 rooms and 5 tabletop builds (M0-OWNER-01) once the corpus intake path exists (M0-CAPT-01).
7. **Create/enable the approved accounts (#008–#017).** Bot-prep once the Grok Bot arrives (it drives signup; you accept ToS/payment and move production keys to CI). Priority order: Unity (unblocks M0-REPO-03), Supabase. **Luma is dropped** (ADR-0005); the reconstruction bridge and Avatar SDK on-prem are the new vendor lines. Near-term real spend is only domains (#014, ~$25–55/yr).
8. **In-house legal review** of the drafts in `legal/` (privacy policy, BIPA consent copy, retention schedule, ToS, vendor template + DPA checklist). No external legal spend (#016 = $0). The consent-text hash is frozen only after their sign-off (SECURITY_CHECKLIST §5.5).
9. **Reconstruction backend — DECIDED (ADR-0005 / AUTH #018): self-host + managed bridge; bridge = KIRI, corpus-only.** Next: the **spike** (M1-CAPT-03) runs once the Unity project + splat renderer exist (M0-UNITY-01/02) — it proves a real room reconstructs and renders on a physical iPhone (the iOS Metal splat sort is the risk). KIRI only ever processes the consented corpus (never real user homes); real user scans wait for self-host. No Luma account.
10. **v1 avatar — DECIDED (ADR-0006 / AUTH #020): pre-made curated character roster, no biometric, no vendor.** Next: author the 8-character roster (open-base authoring primary; art spec + rig standard set by AUTH #024) and wire selection + cosmetic IAP (M2-AVAT-01). **No avatar vendor, no DPA, no biometric consent in v1.** Custom likeness avatars → V2 R&D (`research/rnd/`).

## Risk watch

- Repository is public by Owner decision: every planning document, Bot prompt, and design doc is visible.
- Tests are suggestions, so regressions surface at the Owner's device sessions rather than in PRs; mitigation: a weekly TestFlight build from M1 and the debug overlay's one-tap performance report (M0-UNITY-04).
- The Owner is the only on-device tester until TestFlight external testers arrive; a paid iOS device farm is the fallback if that becomes a bottleneck.
- Motion-matching spike (M1-MOVE-01) decides the animation stack; a miss sends locomotion to blend trees.
- iPhone Duo features depend on iOS 27 posture and Split View APIs reaching Unity; the research spike comes first.
- **Reconstruction backend (decided, ADR-0005):** self-host + managed bridge replaces Luma. Residual risk: **iOS-in-Unity splat rendering** (~200–500K splats @30 fps) and self-host ops/reliability — the M1-CAPT-03 spike targets the render path first; mitigate by shipping compressed splats and/or the mesh for gameplay.
- **Biometric handling — REMOVED from v1 (ADR-0006 / AUTH #020):** v1 uses pre-made characters, so there is **no face/body capture and no biometric processing at all** — no consent flow, no avatar vendor, no DPA, and SECURITY_CHECKLIST §5 is a V2 gate (13+ age gate stays). A large App Store + legal de-risk. Biometric returns only in the **V2 custom-avatar track** (`research/rnd/`), processed on our own infra. Home-scan data stays on our infra (self-host reconstruction); the KIRI bridge sees corpus only.

## Tickets (M0, M1, and the Duo track)

| ID | Title | Owner | Pri | Status | Depends on | Branch / PR |
|---|---|---|---|---|---|---|
| M0-DATA-01 | Freeze telemetry and correction event schemas v1.0 | gj-platform | P0 | open | — | — |
| M0-DSGN-01 | Design system proposal for decisions 5–10 (play, capture, create, browse, store, accessibility) | gj-design | P0 | open | — | — |
| M0-FORE-01 | VM repo bootstrap and secret-hygiene proof | gj-foreman | P0 | open | — | — |
| M0-FORE-02 | File the M0 AUTH batch (accounts, spend, name protection) | gj-foreman | P0 | open | — | — |
| M0-FORE-04 | M0 checkpoint report | gj-foreman | P0 | open | M0-UNITY-04, M0-QA-01, M0-DATA-01, M0-PIPE-01, M0-DSGN-01, M0-FORE-02, M0-FORE-03 | — |
| M0-MOVE-01 | movement.json as the shared tuning contract (loaders, schema, CI sync) | gj-gameplay | P0 | open | — | — |
| M0-OWNER-01 | Capture the day-one corpus: 10 rooms and 5 tabletop builds | owner | P0 | open | M0-CAPT-01 | — |
| M0-OWNER-03 | Lock design system decisions 5–10 at the M0 checkpoint | owner | P0 | done | M0-DSGN-01 | — |
| M0-PIPE-01 | Inngest loop skeleton: scan.submitted → reconstruct → scenegraph → journey → package (stubs) | gj-platform | P0 | open | — | — |
| M0-QA-01 | Unity on the QA VM and the scripted editor smoke task | gj-qa-release | P0 | open | M0-UNITY-01, M0-UNITY-02 | — |
| M0-QA-02 | Visual QA procedure and evidence standard | gj-qa-release | P0 | open | — | — |
| M0-REPO-01 | Repository scaffold and CI harness green on main | coordinator | P0 | merged | — | https://github.com/BlissDirective/Gigantic-Journeys/commit/fd4d44b291bc2ec626bde4d54c2039416334beea |
| M0-REPO-02 | Branch protection, merge policy, and native secret scanning on main | owner | P0 | open | M0-REPO-01, M0-REPO-04 | — |
| M0-REPO-03 | Unity license secrets in GitHub Actions | owner | P0 | open | M0-FORE-02 | — |
| M0-REPO-04 | Bot GitHub identity with least-privilege access | owner | P0 | open | — | — |
| M0-REPO-05 | App Store Connect API key and signing secrets in GitHub Actions | owner | P0 | open | — | — |
| M0-SKILL-01 | gj-foreman: research handbook (RESOURCES.md + SKILLS.md) | gj-foreman | P0 | open | — | — |
| M0-UNITY-01 | Unity 6 URP project scaffold with test assemblies | gj-gameplay | P0 | open | — | — |
| M0-UNITY-02 | Gaussian splat renderer package integrated with a sample scene | gj-capture | P0 | open | M0-UNITY-01 | — |
| M0-UNITY-03 | Traversal controller scaffold: five assemblies, movement.json loader, capsule locomotion and jump | gj-gameplay | P0 | open | M0-UNITY-01, M0-MOVE-01 | — |
| M0-UNITY-04 | Debug overlay — the loop-proving ticket (M0 exit test) | gj-gameplay | P0 | open | M0-UNITY-01 | — |
| M1-CAPT-01 | In-app guided room capture (ARKit poses + depth, coverage, blur, quality gate) | gj-capture | P0 | open | M0-UNITY-01, M0-CAPT-01, M0-OWNER-03 | — |
| M1-CAPT-02 | Upload → reconstruction (self-host/bridge, ADR-0005) → splat + collision mesh stored | gj-platform | P0 | open | M1-CAPT-01, M1-PIPE-01, M1-CAPT-03 | — |
| M1-CAPT-03 | Self-host reconstruction spike + managed-bridge stand-up (ADR-0005) | claude-builder | P0 | open | M0-UNITY-01, M0-UNITY-02, M0-CAPT-01 | — |
| M1-CAPT-04 | On-device reconstruction-readiness predictor + multi-pass 'add a pass' loop (AUTH #025) | gj-capture | P1 | open | M1-CAPT-01 | — |
| M2-AVAT-01 | Character roster: rig, retarget, and in-app selection (ADR-0006) | claude-builder | P0 | open | M0-UNITY-01, M0-UNITY-03, M0-MOVE-01 | — |
| M1-DATA-01 | Freeze scene-graph, traversal-graph, and environment-spec schemas v1.0 | gj-scenegraph | P0 | open | — | — |
| M1-FORE-01 | M1 checkpoint report | gj-foreman | P0 | open | M1-QA-01, M1-GAME-02, M1-GAME-03, M1-CAPT-02, M1-SCEN-04, M1-PIPE-01, M1-MOVE-01, M1-DATA-01 | — |
| M1-GAME-01 | Unity loads splat + collision mesh + environment spec | gj-gameplay | P0 | open | M0-UNITY-02, M1-DATA-01, M1-CAPT-02 | — |
| M1-GAME-02 | Placeholder capsule journeys to the summit | gj-gameplay | P0 | open | M1-GAME-01, M1-SCEN-05, M1-MOVE-01 | — |
| M1-MOVE-01 | Motion-matching vs blend-tree spike (Movement Bible §13) | gj-gameplay | P0 | open | M0-UNITY-03, M0-MOVE-01 | — |
| M1-MOVE-02 | Expanded verb set: dive-roll, tic-tac, vault variants, wall-run (AUTH #021) | claude-builder | P1 | open | M0-UNITY-03, M0-MOVE-01, M1-MOVE-01 | — |
| M3-MOVE-01 | Traversal tools: safety-pin grapple + matchstick pole-vault (AUTH #021) | claude-builder | P1 | open | M1-MOVE-01, M1-MOVE-02, M1-SCEN-04, M1-SCEN-05 | — |
| M1-PIPE-01 | Inngest pipeline: real steps for reconstruct → scenegraph → journey → package | gj-platform | P0 | open | M0-PIPE-01 | — |
| M1-QA-01 | M1 exit-test harness: 10 fresh scans to reachable summit + two routes | gj-qa-release | P0 | open | M1-GAME-02, M1-SCEN-04, M1-CAPT-01 | — |
| M1-SCEN-01 | Mesh cleanup: hole fill, ceiling cap, floater removal | gj-scenegraph | P0 | open | M1-CAPT-02 | — |
| M1-SCEN-02 | Surface classification, measurement, scale inference, material and semantic labels | gj-scenegraph | P0 | open | M1-SCEN-01, M1-DATA-01 | — |
| M1-SCEN-03 | Affordance library and traversal-graph export | gj-scenegraph | P0 | open | M1-SCEN-02 | — |
| M1-SCEN-04 | Summit designation, route generation, vista selection | gj-scenegraph | P0 | open | M1-SCEN-03, M1-SCEN-05 | — |
| M1-SCEN-05 | Deterministic reachability validator against movement.json | gj-scenegraph | P0 | open | M0-MOVE-01, M1-SCEN-03 | — |
| M0-CAPT-01 | Corpus intake: manifest schema, metadata stripping tool, storage rules | gj-capture | P1 | open | — | — |
| M0-DSGN-02 | Design tokens v0 (DTCG JSON) and USS export for the locked decisions | gj-design | P1 | open | M0-DSGN-01 | — |
| M0-FORE-03 | Verify every specialist's SKILLS.md is merged | gj-foreman | P1 | open | M0-SKILL-02, M0-SKILL-03, M0-SKILL-04, M0-SKILL-05, M0-SKILL-06, M0-SKILL-07, M0-SKILL-08, M0-SKILL-09 | — |
| M0-LEGAL-01 | [V2] BIPA biometric consent copy (v1 has no biometric) | gj-avatar | P1 | cancelled | — | — |
| M0-LEGAL-02 | Retention schedule and deletion flow specification (draft) | gj-platform | P1 | open | — | — |
| M0-LEGAL-03 | Luma data-retention and training terms on file | gj-capture | P1 | open | — | — |
| M0-LEGAL-04 | [V2] Avatar vendor data terms (no avatar vendor in v1) | gj-avatar | P1 | cancelled | — | — |
| M0-OWNER-02 | Transcribe the four locked design decisions into DESIGN_SYSTEM.md | owner | P1 | done | — | — |
| M0-PLAT-01 | Supabase local scaffold and RLS-by-default lint | gj-platform | P1 | open | — | — |
| M0-REPO-06 | TestFlight lane in ios-build.yml (cloud-managed signing, fastlane pilot) | coordinator | P1 | done | M0-REPO-05 | — |
| M0-SCEN-01 | Tier 2 research track charter (no compute spend in M0) | gj-scenegraph | P1 | open | — | — |
| M0-SKILL-02 | gj-capture: research handbook (RESOURCES.md + SKILLS.md) | gj-capture | P1 | open | — | — |
| M0-SKILL-03 | gj-scenegraph: research handbook (RESOURCES.md + SKILLS.md) | gj-scenegraph | P1 | open | — | — |
| M0-SKILL-04 | gj-gameplay: research handbook (RESOURCES.md + SKILLS.md) | gj-gameplay | P1 | open | — | — |
| M0-SKILL-05 | gj-avatar: research handbook (RESOURCES.md + SKILLS.md) | gj-avatar | P1 | open | — | — |
| M0-SKILL-06 | gj-platform: research handbook (RESOURCES.md + SKILLS.md) | gj-platform | P1 | open | — | — |
| M0-SKILL-07 | gj-design: research handbook (RESOURCES.md + SKILLS.md) | gj-design | P1 | open | — | — |
| M0-SKILL-08 | gj-qa-release: research handbook (RESOURCES.md + SKILLS.md) | gj-qa-release | P1 | open | — | — |
| M0-SKILL-09 | gj-data: research handbook (RESOURCES.md + SKILLS.md) | gj-data | P1 | open | — | — |
| M1-GAME-03 | Tier 0 material feedback wired | gj-gameplay | P1 | open | M1-GAME-02 | — |
| M1-GAME-04 | Audio system: material×event bank, scale-aware acoustics, spatialized mix (AUTH #022) | claude-builder | P1 | open | M0-UNITY-01, M1-SCEN-02, M1-MOVE-01 | — |
| M3-GAME-01 | Tier 1 soft reactivity: shader displacement + tool/verb reactions (AUTH #022) | claude-builder | P1 | open | M1-SCEN-01, M1-SCEN-02, M1-GAME-04 | — |
| M4-PLAT-01 | Environment package + CDN delivery via signed URLs; unpublish; free-tier cap (AUTH #026) | gj-platform | P0 | open | M1-CAPT-02, M1-DATA-01 | — |
| M4-DATA-01 | Social data model + RLS + rate-limits (AUTH #026) | gj-platform | P0 | open | M0-DATA-01 | — |
| M4-DATA-02 | Ranking + anti-gaming: balanced blend, Top-this-week decay, rate-spam (AUTH #026) | gj-data | P0 | open | M4-DATA-01, M1-DATA-01 | — |
| M4-DATA-03 | Moderation pipeline + queue + appeal + Apple 1.2 UGC (AUTH #026) | gj-data | P0 | open | M4-DATA-01, M4-PLAT-01 | — |
| M4-GAME-01 | In-app publish, browse, rating, report (decisions 8/9) (AUTH #026) | gj-gameplay | P0 | open | M4-PLAT-01, M4-DATA-01, M4-DATA-03 | — |
| M4-GAME-02 | Leaderboards + time-trial integrity (plausibility floor) (AUTH #026) | gj-gameplay | P1 | open | M1-SCEN-05, M4-DATA-01, M4-GAME-01 | — |
| M4-QA-01 | M4 exit harness: 50 published, zero moderation misses, rate-spam + plausibility (AUTH #026) | gj-qa-release | P0 | open | M4-DATA-02, M4-DATA-03, M4-GAME-01, M4-GAME-02 | — |
| M4-FORE-01 | M4 checkpoint report (AUTH #026) | gj-foreman | P0 | open | M4-QA-01, M4-DATA-03, M4-GAME-01, M4-PLAT-01 | — |
| M1-DUO-01 | iPhone Duo research spike: posture, Split View, Duo Preview, outer display in Unity 6 | gj-gameplay | P2 | open | M0-UNITY-01 | — |
| M1-RES-01 | Tier 2 research prototype — month 1 (segment, embed, simulate on the corpus) | gj-scenegraph | P2 | blocked | — | — |
| M2-DUO-01 | [V2] Rear-camera avatar capture (iPhone Duo) — no face capture in v1 | gj-avatar | P2 | cancelled | M1-DUO-01 | — |
| M3-DUO-01 | Stand-mode console layout (iPhone Duo, optional) | gj-gameplay | P2 | open | M1-DUO-01, M0-OWNER-03 | — |
| M3-DUO-02 | Unfold triggers the signature transition (iPhone Duo, optional) | gj-gameplay | P2 | open | M1-DUO-01, M0-OWNER-02 | — |
| M5-DUO-01 | App Store featuring nomination and iPhone Duo launch video | gj-qa-release | P2 | open | M3-DUO-01, M3-DUO-02 | — |

## Merge log

| Date | PR | Ticket | Notes |
|---|---|---|---|
| 2026-09-15 | fast-forward of `claude/gigantic-journeys-governance-f0wgak` (no PR; process not yet in force on main) | M0-REPO-01 | Scaffold: governance, CI, tickets, design system v0.1, ADRs; CI green on the branch before merge and on main afterwards ([actions](https://github.com/BlissDirective/Gigantic-Journeys/actions?query=branch%3Amain)) |
