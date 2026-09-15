# PROGRESS.md

Living tracker. Updated by the Coordinator on every merge, AUTH decision, and checkpoint. Last update: **2026-09-15** (Coordinator: scaffold merged to main; AUTH #002 approved). Ticket table regenerated with `python tickets/validate.py --summary`.

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
| open | 35 |
| in-progress | 0 |
| in-review | 0 |
| changes-requested | 0 |
| blocked | 2 |
| merged | 1 |
| done | 0 |
| cancelled | 0 |
| **total** | **38** |

## Blockers

- Bots cannot start until the Owner hands the Bot machine-user PAT to the team (AUTH #002 approved; Owner creating it) and creates the Foreman Bot from `agents/grok/roles/gj-foreman.md`.
- Unity CI jobs skip until the Unity project exists (M0-UNITY-01) and license secrets are added (M0-REPO-03, after the Unity account AUTH).
- M0-DSGN-02 blocked on the Owner transcribing design decisions 1–4 (M0-OWNER-02).

## Pending AUTH REQUESTs

| # | What | Status |
|---|---|---|
| #003+ | M0 batch (developer accounts, Unity, Luma, Meshy/Tripo, Supabase, Vercel, Inngest, domains, USPTO search, Mac mini, reference device, attorney review) | To be filed by gj-foreman (M0-FORE-02) |

## Owner decisions (2026-09-15)

- AUTH #002 approved: the Owner creates the Bot machine user and PAT and hands it to the Bot team; every Bot asks for it before any work.
- Scaffold merged to main on the Owner's instruction.
- Repository stays **public** for now (free Actions minutes and native secret scanning; plan and design docs are world-readable). Revisit before M4 when user data flows.
- The Foreman's M0 AUTH batch proceeds from #003 once the Foreman exists.

## Owner actions needed now

1. Create the machine user and PAT (M0-REPO-04), then create the Foreman Bot by pasting the block in `agents/grok/roles/gj-foreman.md`; it will ask you for the token first. Then the eight specialists from the other prompt packs.
2. Configure branch protection and native secret scanning on main (M0-REPO-02).
3. Transcribe the four locked design decisions into `design/DESIGN_SYSTEM.md` §1–4 (M0-OWNER-02).
4. Scan 10 rooms and 5 tabletop builds (M0-OWNER-01) once the corpus intake path exists (M0-CAPT-01).

## Risk watch

- Repository is public by Owner decision: every planning document, Bot prompt, and design doc is visible. Going private later costs Actions minutes for the Unity jobs.
- Motion-matching spike (M1-MOVE-01) decides the animation stack; a fail sends locomotion to blend trees.

## Tickets (M0)

| ID | Title | Owner | Pri | Status | Depends on | Branch / PR |
|---|---|---|---|---|---|---|
| M0-DATA-01 | Freeze telemetry and correction event schemas v1.0 | gj-platform | P0 | open | — | — |
| M0-DSGN-01 | Design system proposal for decisions 5–10 (play, capture, create, browse, store, accessibility) | gj-design | P0 | open | — | — |
| M0-FORE-01 | VM repo bootstrap and secret-hygiene proof | gj-foreman | P0 | open | — | — |
| M0-FORE-02 | File the M0 AUTH batch (accounts, spend, name protection) | gj-foreman | P0 | open | — | — |
| M0-FORE-04 | M0 checkpoint report | gj-foreman | P0 | open | M0-UNITY-04, M0-QA-01, M0-DATA-01, M0-PIPE-01, M0-DSGN-01, M0-FORE-02, M0-FORE-03 | — |
| M0-MOVE-01 | movement.json as the shared tuning contract (loaders, schema, CI sync) | gj-gameplay | P0 | open | — | — |
| M0-OWNER-01 | Capture the day-one corpus: 10 rooms and 5 tabletop builds | owner | P0 | open | M0-CAPT-01 | — |
| M0-OWNER-03 | Lock design system decisions 5–10 at the M0 checkpoint | owner | P0 | open | M0-DSGN-01 | — |
| M0-PIPE-01 | Inngest loop skeleton: scan.submitted → reconstruct → scenegraph → journey → package (stubs) | gj-platform | P0 | open | — | — |
| M0-QA-01 | Unity on the QA VM and the scripted editor smoke task | gj-qa-release | P0 | open | M0-UNITY-01, M0-UNITY-02 | — |
| M0-QA-02 | Visual QA procedure and evidence standard | gj-qa-release | P0 | open | — | — |
| M0-REPO-01 | Repository scaffold and CI harness green on main | coordinator | P0 | merged | — | https://github.com/BlissDirective/Gigantic-Journeys/commit/fd4d44b291bc2ec626bde4d54c2039416334beea |
| M0-REPO-02 | Branch protection, merge policy, and native secret scanning on main | owner | P0 | open | M0-REPO-01, M0-REPO-04 | — |
| M0-REPO-03 | Unity license secrets in GitHub Actions | owner | P0 | blocked | M0-FORE-02 | — |
| M0-REPO-04 | Bot GitHub identity with least-privilege access | owner | P0 | open | — | — |
| M0-SKILL-01 | gj-foreman: research handbook (RESOURCES.md + SKILLS.md) | gj-foreman | P0 | open | — | — |
| M0-UNITY-01 | Unity 6 URP project scaffold with test assemblies | gj-gameplay | P0 | open | — | — |
| M0-UNITY-02 | Gaussian splat renderer package integrated with a sample scene | gj-capture | P0 | open | M0-UNITY-01 | — |
| M0-UNITY-03 | Traversal controller scaffold: five assemblies, movement.json loader, capsule locomotion and jump | gj-gameplay | P0 | open | M0-UNITY-01, M0-MOVE-01 | — |
| M0-UNITY-04 | Debug overlay — the loop-proving ticket (M0 exit test) | gj-gameplay | P0 | open | M0-UNITY-01 | — |
| M0-CAPT-01 | Corpus intake: manifest schema, metadata stripping tool, storage rules | gj-capture | P1 | open | — | — |
| M0-DSGN-02 | Design tokens v0 (DTCG JSON) and USS export for the locked decisions | gj-design | P1 | blocked | M0-DSGN-01 | — |
| M0-FORE-03 | Verify every specialist's SKILLS.md is merged | gj-foreman | P1 | open | M0-SKILL-02, M0-SKILL-03, M0-SKILL-04, M0-SKILL-05, M0-SKILL-06, M0-SKILL-07, M0-SKILL-08, M0-SKILL-09 | — |
| M0-LEGAL-01 | BIPA-compliant biometric consent copy and learn-more sheet (draft) | gj-avatar | P1 | open | — | — |
| M0-LEGAL-02 | Retention schedule and deletion flow specification (draft) | gj-platform | P1 | open | — | — |
| M0-LEGAL-03 | Luma data-retention and training terms on file | gj-capture | P1 | open | — | — |
| M0-LEGAL-04 | Meshy and Tripo data-retention and training terms, with a vendor recommendation for M2 | gj-avatar | P1 | open | — | — |
| M0-OWNER-02 | Transcribe the four locked design decisions into DESIGN_SYSTEM.md | owner | P1 | open | — | — |
| M0-PLAT-01 | Supabase local scaffold and RLS-by-default lint | gj-platform | P1 | open | — | — |
| M0-SCEN-01 | Tier 2 research track charter (no compute spend in M0) | gj-scenegraph | P1 | open | — | — |
| M0-SKILL-02 | gj-capture: research handbook (RESOURCES.md + SKILLS.md) | gj-capture | P1 | open | — | — |
| M0-SKILL-03 | gj-scenegraph: research handbook (RESOURCES.md + SKILLS.md) | gj-scenegraph | P1 | open | — | — |
| M0-SKILL-04 | gj-gameplay: research handbook (RESOURCES.md + SKILLS.md) | gj-gameplay | P1 | open | — | — |
| M0-SKILL-05 | gj-avatar: research handbook (RESOURCES.md + SKILLS.md) | gj-avatar | P1 | open | — | — |
| M0-SKILL-06 | gj-platform: research handbook (RESOURCES.md + SKILLS.md) | gj-platform | P1 | open | — | — |
| M0-SKILL-07 | gj-design: research handbook (RESOURCES.md + SKILLS.md) | gj-design | P1 | open | — | — |
| M0-SKILL-08 | gj-qa-release: research handbook (RESOURCES.md + SKILLS.md) | gj-qa-release | P1 | open | — | — |
| M0-SKILL-09 | gj-data: research handbook (RESOURCES.md + SKILLS.md) | gj-data | P1 | open | — | — |

## Merge log

| Date | PR | Ticket | Notes |
|---|---|---|---|
| 2026-09-15 | fast-forward of `claude/gigantic-journeys-governance-f0wgak` (no PR; process not yet in force on main) | M0-REPO-01 | Scaffold: governance, CI, tickets, design system v0.1, ADRs; CI green on the branch before merge and on main afterwards ([actions](https://github.com/BlissDirective/Gigantic-Journeys/actions?query=branch%3Amain)) |
