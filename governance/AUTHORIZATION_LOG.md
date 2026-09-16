# Authorization Log

`governance/AUTHORIZATION_LOG.md` · Maintained by the Coordinator. The only record of what the Owner has authorized. A PR that touches a protected path cites `APPROVED #n` from this log; CI (`auth-gate`) checks the reference and the Coordinator checks the substance.

Numbering is sequential across all types. **Next free number: #006**. The Coordinator assigns numbers when logging; the Owner may reply `APPROVED: <what>` without a number. The Foreman's M0 batch takes the next free numbers when filed (M0-FORE-02).

## Decisions

| # | Date | Type | What | Why | Cost | Reversible | Decision | Evidence |
|---|---|---|---|---|---|---|---|---|
| #000 | 2026-09-14 | design-change | Coordinator kickoff (Prompt 1): create `SPEC.md` v1.0, ADRs 0001–0004 (records of decisions already made in the kit and plan), `tickets/SCHEMA.json`, `design/DESIGN_SYSTEM.md` v0.1, `config/movement.json` (verbatim Bible §10), the governance and CI scaffold | The Owner's Prompt 1 instructed the creation of these files | $0 | yes | **APPROVED** by instruction (Prompt 1, 2026-09-14) | `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` §1 |
| #001 | 2026-09-14 | spend | Movement asset plan: free pipeline (Mixamo clips, open MIT motion matching by jlpm22 with inertialized blending, Blender retargeting, Cascadeur Basic, Rokoko Vision single-camera capture, Move.ai iPhone trial) plus **Motion Warping: Climb & Interact** (Kinemation, Unity Asset Store) | The Movement Bible v1.0 pipeline (§2, §11–13) needs warped contact clips; everything else is free tier | **$19.99 one-time**; $0 monthly | yes | **APPROVED as amended, 2026-09-14.** Deferred to V2 pending v1 results: Ultimate Traversal Anims, traceur capture via Move.ai, MxM commercial license, any mocap suit | `design/MOVEMENT_BIBLE.md` header ("Spend lock") and §13; purchase executed under ticket M1-MOVE-01 |
| #002 | 2026-09-15 | account | GitHub machine user (suggested `gj-bots`) with a fine-grained PAT scoped to this repository: Contents RW, Pull requests RW, Issues RW, Metadata R; expiry ≤ 90 days; stored only in the Bot credential store and `.env.local`; added as a collaborator with Write | Bots must not act as the Owner's account, otherwise CODEOWNERS review and branch protection cannot tell Bot from Owner | $0 | yes | **APPROVED 2026-09-15.** The Owner creates the machine user and token and hands it to the Bot team directly; Bots must ask the Owner for it before beginning any work (Coordinator preamble in every `agents/grok/roles/*.md`, README §3 step 0) | Owner reply in chat, 2026-09-15; ticket M0-REPO-04 |
| #003 | 2026-09-15 | design-change + milestone plan | v1 launches on the iOS App Store only; no minimum device model (automatic quality tiers, best-possible graphics on the newest iPhones); every test, QA pass, performance measurement, and device check is a suggestion, never a merge gate; iPhone Duo optional feature track opened; Android deferred to v1.1. Applied to `SPEC.md` v1.1 (§1, §3, §4, §6, §8–§13), REVIEW_RUBRIC, SECURITY_CHECKLIST, `tickets/SCHEMA.json` (`level`), every M0 ticket, DESIGN_SYSTEM.md §5, Field notes in both locked design docs, the Bot prompt packs, CI (android-build on demand) | The Owner does not want device purchases or testing requirements to bottleneck the build, and wants an iPhone Duo launch story | $0 | yes | **APPROVED** by Owner instruction, 2026-09-15. Addendum 2026-09-15: the Owner selected Duo candidates 1, 2, 3 (tickets M1-DUO-01, M2-DUO-01, M3-DUO-01, M3-DUO-02, M5-DUO-01; DESIGN_SYSTEM §3–§5 variant clauses; ticket area `DUO`) | Owner reply in chat; SPEC change log 1.1; `design/proposals/iphone-duo-track.md` |
| #004 | 2026-09-16 | design-change | DESIGN_SYSTEM.md §3 (signature transition) amended with the five Coordinator recommendations the Owner adopted: scale anchor (0.3 s), summit ignites last with a camera nudge, sound and haptics, 0.8 s short form on repeats with the full form on milestones, reverse transition as the results backdrop and default share image (items 1, 2, 3, 6, 7 of `design/proposals/decision-3-transition-input.md`) | Owner asked for visual-improvement and retention input on decision 3 and adopted all five recommendations | $0 | yes | **APPROVED** by Owner instruction, 2026-09-16 ("Adopt all 5 of your recommendations for Decision 3") | Owner reply in chat; DESIGN_SYSTEM change log 0.5 |
| #005 | 2026-09-16 | design-change | Lock DESIGN_SYSTEM.md decisions 5–10 (play layout, capture coaching UI, create-flow waiting states, browse and ranking cards, results and store screens, accessibility baseline), each the recommended package from its option set under `design/proposals/`; the design system is now fully locked | The Owner reviewed the six option sets and chose every recommended package | $0 | yes | **APPROVED** by Owner instruction, 2026-09-16 (per-decision `APPROVED: decision N = recommended package`) | Owner reply in chat; DESIGN_SYSTEM change log 0.6; ticket M0-OWNER-03 |

## Pending

| # | Filed | Type | What | Cost | Requested by | Blocks | Status |
|---|---|---|---|---|---|---|---|
| — | | | (none) | | | | |

Expected next, filed by the Foreman as the M0 batch (M0-FORE-02) from the next free number: Unity account and plan, Luma API, Meshy and/or Tripo (per M0-LEGAL-04), Supabase (staging and production), Vercel, Inngest, `giganticjourneys.com` and `.app` (about $21/yr), USPTO TESS search on "Gigantic Journeys" in classes 9 and 41 with a filing recommendation (kit §9), an App Store Connect record to reserve the name, attorney review of the M0 legal drafts before M5, and, only if the Owner selects iPhone Duo features and wants on-device verification, an iPhone Duo development device ($1,999 to $3,199).

Already held or not needed: the Apple Developer Program and an App Store Connect API key (the Owner holds both, confirmed 2026-09-15; the key goes into CI secrets under ticket M0-REPO-05 and never onto the Bot VM). Not needed for v1 (AUTH #003): Google Play Console, a reference Android device, a Mac mini (GitHub-hosted macOS runners are free on this public repository and Unity exports the iOS Xcode project on Linux, `.github/workflows/ios-build.yml`). When Android is scheduled (v1.1), open the Play Console early: a personal account created after 2023-11-13 must run a closed test with at least 12 testers for 14 continuous days before production access.

## Standing limits (kit §7; reminders, not authorizations)

- Steady state $750–1,300/month, Owner-authorized only. Daily cap $50 in agent plus API spend; the pipeline halts at the cap.
- Tier 1 segmentation about $0.02–0.10 per scan. Tier 2 research compute is a separate line ($400–1,000/month), approved per month, paused whenever the core build needs the budget.
- Unity Pro seat becomes mandatory once revenue exists.

## Transcriptions and consistency fixes (no authorization consumed)

- 2026-09-16: `design/DESIGN_SYSTEM.md` §1–4 transcribed from the Owner's 2026-09-14 lock (ticket M0-OWNER-02); `SPEC.md` v1.2 aligns its capture wording to decision 4. Decision 3 input (`design/proposals/decision-3-transition-input.md`) was adopted as AUTH #004 and the decision 5–10 option sets were locked as AUTH #005; the design system is fully locked (DESIGN_SYSTEM v0.6). The option docs under `design/proposals/` remain as the rationale behind each locked choice.

## How to use this log

- Bots never edit the Decisions table. The Foreman may add Pending rows in an `auth/<nnn>-<slug>` PR when filing a batch; the Coordinator moves rows to Decisions when the Owner replies on the issue.
- A denied request is recorded with the Owner's reason; re-requesting needs new information.
- A design-change approval names the exact file and section it covers; a PR may not rely on an approval for a different change.
