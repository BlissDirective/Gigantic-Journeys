# Development Plan — "Play Your Room" (working title)

Version 0.1 · September 12, 2026 · Owner: BlissDirective (SparkForge Labs)

A mobile game where you scan a room or tabletop build, become a 1:12 realistic avatar of yourself, and run, jump, and climb through an auto-generated platformer level built from your own space. Publish levels; play everyone else's.

---

## 1. Assumptions

| Item | Decision |
|---|---|
| Platforms | iOS and Android at launch, single Unity 6 codebase |
| Capture modes (v1) | Indoor rooms, tabletop builds (two guided-capture flows) |
| Avatar | Realistic proportions (~7 heads), stylized materials, shared humanoid rig, 1:12 default scale with per-level scale multiplier |
| Reconstruction | Third-party APIs: Luma (splat + mesh), Meshy or Tripo realistic mode (avatar head), parametric body fit |
| Backend | Supabase (auth, storage, Postgres, edge functions), Vercel (API), Inngest (durable workflows) |
| Team | You (decisions, gates, capture testing) · Claude (orchestrator, builder, reviewer) · Grok Bot agents (computer-use and long-running ops, one per role) |
| Budget | $500–1,500 / month |
| Timeline | "ASAP" translated to a 16-week plan to TestFlight/closed Play testing, store submission at week 16–18. Faster is possible if M1 lands clean; slower if scan quality fights us. |

Hard prerequisite: iOS builds need macOS. Either a used Mac mini (~$500 one-time) or a cloud Mac runner (~$100/mo). Buy the Mac mini; it pays for itself in five months and can run the Grok Bot editor tasks too.

---

## 2. Team and roles

### You
- Own all gates (Section 5). Approve architecture changes, spend over cap, anything touching billing, and every store submission.
- Do the physical capture testing: scan your own rooms, your kids' Lego builds, your garage. Agents cannot hold a phone.
- Post the Day N updates. The build-in-public loop is a marketing asset from week 1.

### Claude (Claude Agent SDK + Claude Code)
Three subagents with separate contexts so no agent reviews its own work:
- **Architect / orchestrator** — owns `SPEC.md`, decomposes milestones into tickets with acceptance tests, maintains `BACKLOG.md`, runs the weekly data-review job.
- **Builder** — takes one ticket, works one branch, writes C#, Python, and TypeScript plus tests, drives Unity via `-batchmode` and editor scripts.
- **Reviewer** — reviews every PR against the ticket's acceptance tests and `SPEC.md`. Only the reviewer merges.
- **Runtime role** — Claude is also the level generator in production (structured JSON from scene graph, then deterministic validator).

### Grok Bot agents
Each Bot gets a role document (`agents/grok/<role>.md`) that it reads at every session, a persistent memory scoped to its role, and access only to the tools its job needs. "Training" here means role docs, curated examples, and accumulated memory — not fine-tuning; xAI does not expose that for Bot. Start with three; add the rest when their milestone arrives.

| Bot | Role | Tools / access | Starts |
|---|---|---|---|
| **Editor QA** | Opens the Unity project on its VM, imports test scans, runs Play Mode, takes screenshots and short clips, files visual defects as tickets | Unity editor (Linux), repo read, ticket write | M0 |
| **Pipeline Ops** | Submits Luma / Meshy jobs for the test corpus, polls, archives results, tracks per-job cost, flags vendor regressions | Vendor dashboards, Supabase storage (staging), cost sheet | M1 |
| **Release** | TestFlight and Play Console uploads, metadata, screenshots, review responses, crash dashboards | App Store Connect, Play Console, Crashlytics — separate ops account, no prod secrets | M5 |
| **Data Analyst** | Weekly telemetry pull, cohort tables, failure-pattern summaries written to `data/reports/` for Claude's review job | Supabase read-only replica | M4 |
| **Moderation** | Reviews flagged levels, applies policy, escalates edge cases to you | Admin panel (staging first) | M4 |

Security rule: all Bots share one cloud computer per account, and xAI says not to treat them as a security boundary. Therefore no Bot ever holds production Supabase service keys, signing certificates, or payment credentials. Those live only in CI secrets.

---

## 3. Repository layout (source of truth)

```
/SPEC.md                  product spec, the only authority on "what"
/ADRs/                    architecture decisions, one file each
/BACKLOG.md               logged DLC / add-on ideas with one-line rationale
/tickets/*.json           id, milestone, acceptance tests, status, owner
/agents/claude/           subagent prompts, CLAUDE.md, skills
/agents/grok/             one role doc per Bot
/unity/                   Unity 6 project
/services/scenegraph/     Python: mesh cleanup, surface classification, graph export
/services/levelgen/       TypeScript: Claude call, JSON schema, validator
/services/avatar/         Python: head + body merge, retopo, rig, validation
/api/                     Vercel functions, Inngest workflows
/supabase/                migrations, RLS policies, edge functions
/data/schemas/            telemetry and correction event schemas (frozen early)
/data/reports/            weekly agent-written analyses
/legal/                   privacy policy, BIPA consent copy, retention schedule
```

Nothing an agent "remembers" counts. If it isn't in the repo, it didn't happen.

---

## 4. The autonomous loop

1. Architect picks the highest-priority unblocked ticket and posts it to the Builder with acceptance tests.
2. Builder works a branch; CI runs `Unity -batchmode -runTests`, service unit tests, and a headless Android build on every push.
3. Editor QA Bot pulls the branch, runs the visual checklist for that ticket, attaches screenshots or a defect ticket.
4. Reviewer checks PR against acceptance tests and `SPEC.md`; requests changes or merges.
5. Nightly: CI builds iOS on the Mac runner; Release Bot pushes to TestFlight / internal Play track (from M5).
6. Weekly: Data Analyst Bot writes the report; Architect reads it, proposes spec or validator changes as tickets, and opens a "learning loop" PR with before/after metrics on the held-out scan corpus.
7. You review the weekly summary and clear the gates.

Inngest runs the loop as durable steps so a vendor timeout or Bot flake retries instead of stalling the pipeline.

---

## 5. Human gates (hard stops)

- Any ADR (architecture or vendor change)
- Spend over $50/day in agent + API cost, or any new paid service
- Anything touching IAP, pricing, or payment config
- Credential creation or rotation
- Store submission and any public-facing policy text
- Any change to what data is collected or retained

Everything else runs unattended.

---

## 6. Milestones

Weeks are targets, not promises. M1 is the real validation; if it fails, everything after it re-plans.

### M0 — Harness (weeks 1–2)
- Repo, CI (GitHub Actions + Mac runner), Unity 6 project with URP, splat renderer package, humanoid controller scaffold.
- Claude subagents wired via Agent SDK; ticket schema; Inngest loop with one trivial end-to-end ticket ("add a debug menu") to prove the loop.
- Editor QA Bot provisioned: Unity installed on its VM, role doc, first scripted task (open project, import sample splat, screenshot, report).
- Telemetry and correction event schemas frozen in `data/schemas/`.
- Legal: consent copy and retention schedule drafted; vendor data-retention terms confirmed.
- **Exit:** a ticket goes from creation to merged PR with a Bot-attached screenshot, no human typing.

### M1 — Scan to playable (weeks 3–6) — the validation milestone
- Guided room capture in-app (ARKit/ARCore poses and depth recorded alongside video, coverage hints, blur rejection).
- Upload → Luma job → splat + mesh stored; Pipeline Ops Bot manages the test corpus of 30 rooms you scan.
- Scene-graph service: hole fill, ceiling cap, floater removal, surface classification (walkable / wall / ledge / soft), gap measurement, scale inference.
- Level generator: Claude structured output against JSON schema; validator does reachability search against movement constants; three retries then template fallback.
- Unity loads splat + collision mesh + level spec; placeholder capsule runs, jumps, climbs ledges to a flag.
- **Exit:** 8 of 10 fresh room scans produce a completable level with no manual fixes. If below 6/10, stop and re-plan the scene-graph approach before anything else.

### M2 — Avatar (weeks 5–8, parallel with M1 from week 5)
- Capture flow: front/left/right face + full-body, lighting guidance.
- Head: image-to-3D realistic mode with fixed material prompt. Body: parametric fit, small wardrobe. Merge, retopo to fixed budget, bake, auto-rig, retarget shared animation set (idle, run, jump, land, climb, hurt, celebrate).
- Validation checklist (bone count, T-pose, eye height, texture seams) with retry.
- Unified "grounded" shader with environment probe from the splat.
- Source photos deleted after generation; consent recorded.
- **Exit:** 20 test users' avatars recognizable by friends in a blind test, generated in under 2 minutes, all on the shared rig.

### M3 — Game loop and tabletop mode (weeks 7–10)
- Tabletop capture mode (close orbital pattern, scale inference tuned for small builds).
- Enemies (2 types), hazards, coins, checkpoint, flag; time-trial scoring; 3-star rating on completion.
- Camera that respects the collision mesh; controller feel pass against M1 telemetry.
- Diorama view (the room as a floating tiny world) for sharing clips.
- **Exit:** you and three testers each play five levels and want to play a sixth.

### M4 — Sharing, moderation, leaderboards (weeks 9–12)
- Level package format (splat, mesh, graph, spec, thumbnail), Supabase storage behind CDN, RLS policies.
- Publish flow: GPS stripped, vision moderation pass, report button, moderation queue.
- Browse, rate, per-level time-trial leaderboard, "top rated" and "new" feeds; deep links.
- Data Analyst and Moderation Bots go live on staging.
- **Exit:** 50 community-published levels from testers, zero moderation misses in review.

### M5 — Store readiness and IAP (weeks 12–16)
- IAP: cosmetic outfit pack and "realism+" avatar materials as the two launch SKUs (RevenueCat or Unity IAP). Free tier: unlimited scans, 3 published levels; paid tier lifts caps.
- Privacy policy, BIPA consent, age gate (13+), data deletion flow, App Store privacy labels, Play data safety form.
- Release Bot live; TestFlight and closed Play testing with 100 users; crash-free rate above 99%.
- Store listings, screenshots, preview video (the diorama view is the hero shot).
- **Exit:** both stores submitted.

### M6 — Learning loops (instrumented from M1, first retrain 4 weeks post-launch)
- Correction UI: one-tap "fix this label" with in-game reward.
- Weekly Architect job already running; first classifier retrain and validator-rule update on accumulated opt-in data.
- Affordance library v1 exported from corrections (chair, table, couch, shelf, plant, lamp).

---

## 7. Budget (monthly, steady state during build)

| Line | Estimate |
|---|---|
| Claude API (orchestration, review, level gen dev) | $250–500 |
| Grok Bot access (SuperGrok Heavy or equivalent seat) | $300 |
| Luma / Meshy jobs on test corpus | $100–200 |
| Supabase Pro + storage/egress | $25–75 |
| Vercel Pro, Inngest | $40 |
| Unity Pro seat | $185 (required once revenue exists; Personal until then) |
| Apple + Google developer accounts | $8/mo amortized + $25 one-time |
| Mac mini | ~$500 one-time (or $100/mo cloud Mac) |

Total: roughly $750–1,300/month, inside range. Biggest variable is reconstruction spend; Pipeline Ops Bot tracks per-job cost and halts at a daily cap.

---

## 8. Risks and mitigations

| Risk | Signal | Mitigation |
|---|---|---|
| Scan-to-level quality below bar | M1 exit under 6/10 | Constrain v1 to well-lit rooms with guidance; add human-in-the-loop surface edits before generation; revisit self-hosting |
| Splat performance on mid-range Android | Under 30 fps on a 2023 mid-tier phone | Splat LOD and culling; fall back to textured mesh visuals on low-end devices |
| Avatar likeness disappoints | Blind test under 60% | Add fourth photo, tighten material prompt, allow a manual likeness tweak screen |
| Grok Bot flakiness (product is one month old) | Editor QA task fails more than 20% | Fall back to Claude editor scripts plus a cheaper computer-use runner; Bots keep ops roles |
| BIPA / privacy exposure | Any face data outside the one vendor job | Opt-in, derived-data-only training, deletion flow, vendor terms verified before M2 |
| Vendor lock-in | Price or API change | Package format is vendor-neutral; keep a self-hosted gsplat path documented in an ADR |
| Scope creep | Ticket count growing faster than merges | Everything not in M1–M5 goes to `BACKLOG.md`; Architect cannot promote backlog items without a gate |

---

## 9. Compliance checklist (must be green before M5 exit)

- Written BIPA-compliant consent before any face processing; retention schedule published
- Source photos and video deleted after derived assets are generated
- Training opt-in toggle; derived data only; per-user deletion
- 13+ age gate; no COPPA scope in v1
- GPS and EXIF stripped from all uploads
- Moderation queue and report flow live
- Vendor DPAs and retention terms on file
- App Store privacy labels and Play data safety accurate to the telemetry schema

---

## 10. Definition of v1 done

A new user can, on either platform: scan a room or a Lego build in under 90 seconds, create a recognizable 1:12 avatar of themselves in under 2 minutes, play a completable auto-generated level in their own space, publish it, and have a friend play it from a link within five minutes. Crash-free rate above 99%. Both stores approved.

---

## 11. Backlog seed (`BACKLOG.md`)

Outfits and cosmetics · realism tiers · outdoor/garden capture · street capture with face/plate blur · multiplayer race · level packs by theme · seasonal enemies · community challenges · Apple Vision Pro / Quest port of the diorama view · affordance library licensing · creator revenue share.

---

## 12. First week, concretely

1. Buy the Mac mini, create Apple and Google developer accounts, Unity account.
2. I scaffold the repo, `SPEC.md`, ticket schema, Claude subagent prompts, and the Inngest loop skeleton.
3. You provision the Editor QA Bot and hand it `agents/grok/editor-qa.md`; run the first scripted Unity task.
4. You scan 10 rooms with your phone camera app (raw video is fine) so M1 has a corpus on day one.
5. Draft consent copy and send vendor data-retention questions to Luma and Meshy.
