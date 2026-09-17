# PROGRESS.md

Living tracker. Updated by the Coordinator on every merge, AUTH decision, and checkpoint. Last update: **2026-09-17** (Coordinator: AUTH #007 Builder self-review-and-merge with periodic secondary review; Builder engineering handbook; AUTH #006 agent model; design system locked; M1 decomposed). Ticket table regenerated with `python tickets/validate.py --summary`.

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
| open | 55 |
| in-progress | 0 |
| in-review | 0 |
| changes-requested | 0 |
| blocked | 2 |
| merged | 1 |
| done | 3 |
| cancelled | 0 |
| **total** | **61** |

## Blockers

- Bots cannot start until the Owner hands the Bot machine-user PAT to the team (AUTH #002 approved; Owner creating it) and creates the Foreman Bot from `agents/grok/roles/gj-foreman.md`.
- Unity CI jobs skip until the Unity project exists (M0-UNITY-01) and license secrets are added (M0-REPO-03, after the Unity account AUTH).

## Pending AUTH REQUESTs

| # | What | Status |
|---|---|---|
| #003+ | M0 batch (developer accounts, Unity, Luma, Meshy/Tripo, Supabase, Vercel, Inngest, domains, USPTO search, Mac mini, reference device, attorney review) | To be filed by gj-foreman (M0-FORE-02) |

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
- The Foreman's M0 AUTH batch proceeds from #004 once the Foreman exists.

## Owner actions needed now

1. Create the machine user and PAT (M0-REPO-04), then create the Foreman Bot by pasting the block in `agents/grok/roles/gj-foreman.md`; it will ask you for the token first. Then the eight specialists from the other prompt packs.
2. Configure branch protection and native secret scanning on main (M0-REPO-02).
3. Lock decision 5: reply `APPROVED #004: decision 5 = recommended package` (or the letters that differ) against `design/proposals/decision-5-play-layout-options.md`; optionally adopt items from `decision-3-transition-input.md` in the same reply. Then decisions 6–10.
4. Add the App Store Connect key to CI (M0-REPO-05): secrets `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`; variable `APPLE_TEAM_ID`; create the App Store Connect app record (reserves the name) with an internal TestFlight group on automatic distribution. Set `TESTFLIGHT_ENABLED=true` after M0-UNITY-01 merges.
5. Decide whether to acquire an iPhone Duo for verifying the three selected features (AUTH spend), or accept adaptive design until one is available.
6. Scan 10 rooms and 5 tabletop builds (M0-OWNER-01) once the corpus intake path exists (M0-CAPT-01).

## Risk watch

- Repository is public by Owner decision: every planning document, Bot prompt, and design doc is visible.
- Tests are suggestions, so regressions surface at the Owner's device sessions rather than in PRs; mitigation: a weekly TestFlight build from M1 and the debug overlay's one-tap performance report (M0-UNITY-04).
- The Owner is the only on-device tester until TestFlight external testers arrive; a paid iOS device farm is the fallback if that becomes a bottleneck.
- Motion-matching spike (M1-MOVE-01) decides the animation stack; a miss sends locomotion to blend trees.
- iPhone Duo features depend on iOS 27 posture and Split View APIs reaching Unity; the research spike comes first.

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
| M0-REPO-03 | Unity license secrets in GitHub Actions | owner | P0 | blocked | M0-FORE-02 | — |
| M0-REPO-04 | Bot GitHub identity with least-privilege access | owner | P0 | open | — | — |
| M0-REPO-05 | App Store Connect API key and signing secrets in GitHub Actions | owner | P0 | open | — | — |
| M0-SKILL-01 | gj-foreman: research handbook (RESOURCES.md + SKILLS.md) | gj-foreman | P0 | open | — | — |
| M0-UNITY-01 | Unity 6 URP project scaffold with test assemblies | gj-gameplay | P0 | open | — | — |
| M0-UNITY-02 | Gaussian splat renderer package integrated with a sample scene | gj-capture | P0 | open | M0-UNITY-01 | — |
| M0-UNITY-03 | Traversal controller scaffold: five assemblies, movement.json loader, capsule locomotion and jump | gj-gameplay | P0 | open | M0-UNITY-01, M0-MOVE-01 | — |
| M0-UNITY-04 | Debug overlay — the loop-proving ticket (M0 exit test) | gj-gameplay | P0 | open | M0-UNITY-01 | — |
| M1-CAPT-01 | In-app guided room capture (ARKit poses + depth, coverage, blur, quality gate) | gj-capture | P0 | open | M0-UNITY-01, M0-CAPT-01, M0-OWNER-03 | — |
| M1-CAPT-02 | Upload → Luma reconstruction → splat + collision mesh stored | gj-platform | P0 | open | M1-CAPT-01, M1-PIPE-01, M0-LEGAL-03 | — |
| M1-DATA-01 | Freeze scene-graph, traversal-graph, and environment-spec schemas v1.0 | gj-scenegraph | P0 | open | — | — |
| M1-FORE-01 | M1 checkpoint report | gj-foreman | P0 | open | M1-QA-01, M1-GAME-02, M1-GAME-03, M1-CAPT-02, M1-SCEN-04, M1-PIPE-01, M1-MOVE-01, M1-DATA-01 | — |
| M1-GAME-01 | Unity loads splat + collision mesh + environment spec | gj-gameplay | P0 | open | M0-UNITY-02, M1-DATA-01, M1-CAPT-02 | — |
| M1-GAME-02 | Placeholder capsule journeys to the summit | gj-gameplay | P0 | open | M1-GAME-01, M1-SCEN-05, M1-MOVE-01 | — |
| M1-MOVE-01 | Motion-matching vs blend-tree spike (Movement Bible §13) | gj-gameplay | P0 | open | M0-UNITY-03, M0-MOVE-01 | — |
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
| M0-LEGAL-01 | BIPA-compliant biometric consent copy and learn-more sheet (draft) | gj-avatar | P1 | open | — | — |
| M0-LEGAL-02 | Retention schedule and deletion flow specification (draft) | gj-platform | P1 | open | — | — |
| M0-LEGAL-03 | Luma data-retention and training terms on file | gj-capture | P1 | open | — | — |
| M0-LEGAL-04 | Meshy and Tripo data-retention and training terms, with a vendor recommendation for M2 | gj-avatar | P1 | open | — | — |
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
| M1-DUO-01 | iPhone Duo research spike: posture, Split View, Duo Preview, outer display in Unity 6 | gj-gameplay | P2 | open | M0-UNITY-01 | — |
| M1-RES-01 | Tier 2 research prototype — month 1 (segment, embed, simulate on the corpus) | gj-scenegraph | P2 | blocked | — | — |
| M2-DUO-01 | Rear-camera avatar capture with Duo Preview (iPhone Duo, optional) | gj-avatar | P2 | open | M1-DUO-01 | — |
| M3-DUO-01 | Stand-mode console layout (iPhone Duo, optional) | gj-gameplay | P2 | open | M1-DUO-01, M0-OWNER-03 | — |
| M3-DUO-02 | Unfold triggers the signature transition (iPhone Duo, optional) | gj-gameplay | P2 | open | M1-DUO-01, M0-OWNER-02 | — |
| M5-DUO-01 | App Store featuring nomination and iPhone Duo launch video | gj-qa-release | P2 | open | M3-DUO-01, M3-DUO-02 | — |

## Merge log

| Date | PR | Ticket | Notes |
|---|---|---|---|
| 2026-09-15 | fast-forward of `claude/gigantic-journeys-governance-f0wgak` (no PR; process not yet in force on main) | M0-REPO-01 | Scaffold: governance, CI, tickets, design system v0.1, ADRs; CI green on the branch before merge and on main afterwards ([actions](https://github.com/BlissDirective/Gigantic-Journeys/actions?query=branch%3Amain)) |
