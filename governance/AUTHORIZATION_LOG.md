# Authorization Log

`governance/AUTHORIZATION_LOG.md` · Maintained by the Coordinator. The only record of what the Owner has authorized. A PR that touches a protected path cites `APPROVED #n` from this log; CI (`auth-gate`) checks the reference and the Coordinator checks the substance.

Numbering is sequential across all types. **Next free number: #003** (the Foreman's M0 batch starts here, ticket M0-FORE-02).

## Decisions

| # | Date | Type | What | Why | Cost | Reversible | Decision | Evidence |
|---|---|---|---|---|---|---|---|---|
| #000 | 2026-09-14 | design-change | Coordinator kickoff (Prompt 1): create `SPEC.md` v1.0, ADRs 0001–0004 (records of decisions already made in the kit and plan), `tickets/SCHEMA.json`, `design/DESIGN_SYSTEM.md` v0.1, `config/movement.json` (verbatim Bible §10), the governance and CI scaffold | The Owner's Prompt 1 instructed the creation of these files | $0 | yes | **APPROVED** by instruction (Prompt 1, 2026-09-14) | `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` §1 |
| #001 | 2026-09-14 | spend | Movement asset plan: free pipeline (Mixamo clips, open MIT motion matching by jlpm22 with inertialized blending, Blender retargeting, Cascadeur Basic, Rokoko Vision single-camera capture, Move.ai iPhone trial) plus **Motion Warping: Climb & Interact** (Kinemation, Unity Asset Store) | The Movement Bible v1.0 pipeline (§2, §11–13) needs warped contact clips; everything else is free tier | **$19.99 one-time**; $0 monthly | yes | **APPROVED as amended, 2026-09-14.** Deferred to V2 pending v1 results: Ultimate Traversal Anims, traceur capture via Move.ai, MxM commercial license, any mocap suit | `design/MOVEMENT_BIBLE.md` header ("Spend lock") and §13; purchase executed under ticket M1-MOVE-01 |

## Pending

| # | Filed | Type | What | Cost | Requested by | Blocks | Status |
|---|---|---|---|---|---|---|---|
| #002 | 2026-09-15 | account | GitHub machine user (suggested `gj-bots`) with a fine-grained PAT scoped to this repository: Contents RW, Pull requests RW, Issues RW, Metadata R; expiry ≤ 90 days; stored only in the Bot credential store and `.env.local`; added as a collaborator with Write | $0 | Coordinator | M0-REPO-04 and every Bot PR. Without it Bots act as the Owner's account and CODEOWNERS review and branch protection cannot tell Bot from Owner | Waiting on Owner |

Expected next, filed by the Foreman as the M0 batch (M0-FORE-02) from #003: Apple Developer Program ($99/yr), Google Play Console ($25 one-time), Unity account and plan, Luma API, Meshy and/or Tripo (per M0-LEGAL-04), Supabase (staging and production), Vercel, Inngest, `giganticjourneys.com` and `.app` (about $21/yr), USPTO TESS search on "Gigantic Journeys" in classes 9 and 41 with a filing recommendation (kit §9), Mac mini (about $500 one-time) versus a cloud Mac, reference Android device (2023 mid-tier) or device-farm minutes, an App Store Connect record to reserve the name, attorney review of the M0 legal drafts before M5.

## Standing limits (kit §7; reminders, not authorizations)

- Steady state $750–1,300/month, Owner-authorized only. Daily cap $50 in agent plus API spend; the pipeline halts at the cap.
- Tier 1 segmentation about $0.02–0.10 per scan. Tier 2 research compute is a separate line ($400–1,000/month), approved per month, paused whenever the core build needs the budget.
- Unity Pro seat becomes mandatory once revenue exists.

## How to use this log

- Bots never edit the Decisions table. The Foreman may add Pending rows in an `auth/<nnn>-<slug>` PR when filing a batch; the Coordinator moves rows to Decisions when the Owner replies on the issue.
- A denied request is recorded with the Owner's reason; re-requesting needs new information.
- A design-change approval names the exact file and section it covers; a PR may not rely on an approval for a different change.
