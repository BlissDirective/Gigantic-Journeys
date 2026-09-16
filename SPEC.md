# Gigantic Journeys — SPEC.md

Version 1.2 · 2026-09-16 · Owner: BlissDirective (SparkForge Labs) · Maintainer: Coordinator (Claude Code)

**Authority.** This file is the only authority on *what* v1 is. Below it rank `design/MOVEMENT_BIBLE.md` v1.0 (how the avatar moves), `design/Gigantic-Journey-Design-Skills.md` v1.1 with `design/DESIGN_SYSTEM.md` (how it looks and feels), then `ADRs/` (how it is built). Where documents disagree, this file wins until an authorized change says otherwise.

**Change control.** Any edit to this file requires an `AUTH REQUEST` of type design-change and a PR citing `APPROVED #n` (`governance/AUTHORIZATION_LOG.md`). CI blocks PRs that touch it without one. Creation of this v1.0 was authorized by Prompt 1 (AUTH #000).

**Sources.** `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` v0.5 (the v1 product lock of 2026-09-13 and the phase prompts), `context/DEVELOPMENT_PLAN.md` v0.1 (history), the Movement Bible, the Design Skills. Values marked *(initial)* are starting targets that M1–M3 measurements may revise, still through AUTH.

---

## 1. Product definition

Gigantic Journeys is a mobile game (v1 on the iOS App Store; one Unity 6 codebase that keeps Android buildable for a later release) in which the player scans a real place, a room or a tabletop build, becomes a near-photorealistic 1:12 avatar of themselves, and journeys through that place: reaching its summit, running its routes, finding its vistas. The environment is the content; the avatar is the piece; traversal is the product. Finished environments can be published to an opt-in global database where they are ranked and played by others.

In one line (Bible §0): *a real person, 15 cm tall, parkouring through a real place, with the weight and hesitation of a real body and the responsiveness of a great platformer.*

Identity: name "Gigantic Journeys"; bundle id `com.sparkforgelabs.giganticjourneys`; repo slug `gigantic-journeys`; Bot prefix `gj-`; hashtags #GiganticJourneys, #GJrun.

## 2. The player's journey

1. **Install → play in 60 s.** A pre-scanned demo environment lets the player run, jump, and mantle before scanning anything (Design Skills rule 9: play first, scan second). First playable moment under 3 minutes, first summit under 5.
2. **Scan.** One illustrated toggle chooses room walkthrough or tabletop orbital; guided capture with live coverage, speed, blur, and light coaching; a quality gate before upload; under 90 seconds of active capture.
3. **Become the avatar.** A separate, explicit biometric consent step; a full-body shot with a 360° rotation, then a face close-up with rotation; head from image-to-3D realistic mode, body from a parametric fit; "Is this you?" with Retake or four coarse tweaks; under 2 minutes; source photos deleted afterwards.
4. **Journey.** The environment resolves progressively while the player waits (never a blank spinner). Then: the summit beacon visible from the start; two or three generated routes of rising difficulty plus player-recorded challenge routes; three vistas rewarded with photo mode; the flag plant at the summit.
5. **Publish and browse.** Opt-in publish (GPS stripped, moderation pass); browse by place; rate on four axes; race per-route time trials; see creator stats. A friend plays it from a link within five minutes.
6. **Return.** New scans, other people's environments, the diorama view for sharing clips, the cosmetic wardrobe after a win.

## 3. v1 scope (in)

### 3.1 Capture: indoor rooms and tabletop builds
- Two guided modes: **room walkthrough** (chest-height arc around the space) and **tabletop orbital** (slow circle at two heights). Mode chosen by one toggle with an illustration, never a settings page.
- ARKit camera poses and depth recorded alongside video (LiDAR depth when the device has it; ARKit poses give metric scale without it). Live coverage heat-map; speed meter that turns amber when moving too fast; blur rejection with a gentle haptic; a "you missed this corner" hint before upload; a quality gate that rejects early and kindly ("Too dark here — turn on a lamp?").
- Passes of 1–3 minutes; active capture under 90 seconds.
- GPS and EXIF stripped on device before upload and verified again server-side.
- Reconstruction through the Luma API into a Gaussian splat plus a collision mesh (ADR-0003). The package format is vendor-neutral.
- Well-lit indoor rooms and tabletop builds only.

### 3.2 Avatar: realistic, 1:12
- Consent gate first: a separate, explicit, versioned biometric consent record must exist before any face bytes leave the device (§7, SECURITY_CHECKLIST §5).
- Capture (DESIGN_SYSTEM decision 4): a full-body shot with a 360° body rotation, then a face close-up with rotation, with lighting guidance and retakes.
- Realistic proportions (about 7 heads), stylized "grounded" materials, a unified shader with an environment probe from the splat, a subtle rim light and contact shadow so the avatar pops off the photoreal floor (Design Skills rule 20).
- Head via image-to-3D realistic mode (Meshy or Tripo; vendor fixed by ADR at M2 after the M0 vendor-terms review) with a fixed material prompt. Body via parametric fit with a small default wardrobe roughly matching the photo.
- Merge, retopo to a fixed budget, bake, auto-rig to the **shared GJ humanoid skeleton**, retarget the shared animation set. Validation checklist (bone count, T-pose, eye height, texture seams) with automatic retry.
- Likeness confirmation: the generated head turning beside the source photo, "Is this you?", Retake or Tweak (skin tone, hair, glasses, build). No slider editor.
- Default scale 1:12 (1.75 m → 14.6 cm) with a per-environment scale multiplier; every movement threshold is expressed in avatar heights **A** (Bible §1).
- Targets: generated in under 2 minutes; recognizable by friends in a blind test at 60 % or better; source photos deleted after generation.

### 3.3 Environment understanding (scene graph)
- Mesh cleanup: hole fill, ceiling cap, floater removal.
- Surface classification into the Bible §4 classes: walkable-hard, walkable-soft, walkable-narrow, ledge, rung, stud, textured-vertical, pole, overhang, slope, wall-smooth, soft-hanging, void.
- Gap, height, and edge measurement; scale inference (1:12 default, tuned for small builds so Lego studs are climbable); semantic and material labels via a vision pass.
- Affordance library mapping surface classes to traversal verbs; traversal-graph export (which surfaces reach which, by which verb, at what difficulty).
- Frozen schemas in `data/schemas/` (scene_graph, traversal_graph, environment_spec); changes need AUTH.

### 3.4 Journey generation: summit, routes, vistas
- **Summit**: the auto-designated highest reachable point; reaching it plants the player's flag.
- **Routes**: two or three generated routes of rising difficulty, each with a `beat` per segment structured introduce → develop → twist → resolve (Design Skills rule 22). Beat 1 uses only walk, jog, run, jump, step-up, hop-over, and mantle (Bible §10). Player-recorded challenge routes. Per-route time trials.
- **Vistas**: three auto-picked vantage points chosen for the view, not for difficulty; reaching one opens photo mode.
- **Validator**: a deterministic reachability search against `config/movement.json` with a 15 % margin (85 % of maximum reach and distance). Three generation retries, then a template fallback. A route is valid only if every transition is achievable under the constants.
- The summit beacon and the vista sparkle are always drawn on top with depth-fade so orientation is never lost (Bible §8).

### 3.5 Traversal: the product
The verb set, trigger thresholds, feel rules, camera rules, and landing tiers are defined in the Movement Bible and are not restated here. In v1 the avatar can: idle, walk, jog, run, sprint, plant-turn, balance-walk, crouch; step-up, hop-over, vault, mantle; standing, running, precision, ledge-to-ledge, and wall-push jumps with coyote time and jump buffering; controlled drop, hang-and-drop, slide, fall, and four landing tiers; ledge hang and shimmy, rung climb, stud climb, textured free climb, pole climb, overhang hang-traverse; slips and catches; one contextual action (plant flag > grab > drop > slide).
- Two-thumb landscape layout: a floating stick under the left thumb, jump as the largest right-thumb target, one contextual action button that appears only when relevant; controls repositionable and resizable; controller support from day one.
- Assist mode (longer coyote time, jump bonus, slips off, auto-grab) per Bible §10.
- Camera per Bible §8: collision-aware follow, look-ahead, dither-fade on occluding real geometry, manual orbit that auto-recenters, never fights the player mid-move.
- Reactions and idle personality per Bible §7.
- No stamina, no damage, no wall-run in v1. Falls cost time only; off-table falls on tabletops respawn at the last stable surface.

### 3.6 Environment reactivity
- **Tier 0 (ships):** material-keyed footstep, landing, grab, and slide audio; particles; haptics; camera shake, per the Bible §9 matrix, all scaled with the environment scale multiplier.
- **Tier 1 (ships):** object segmentation of the splat plus procedural, shader-driven displacement: cushions dent, curtains sway, papers flutter, plants rustle. Adds roughly $0.02–0.10 of segmentation compute per scan. Must hold 30 fps on the reference device (M3 exit test).
- **Tier 2 (does not ship in v1):** §5.

### 3.7 Publish, browse, rank, leaderboards
- **Environment package**: splat, collision mesh, scene graph, environment spec, thumbnail; Supabase storage behind a CDN; delivered only through signed, short-lived URLs.
- **Publish flow** (opt-in): GPS and EXIF stripped again server-side, a vision moderation pass, an "Under review" badge until cleared, a one-tap report with a reason sheet, a moderation queue operated by gj-data with escalation to the Owner.
- **Browse by place**: thumbnails are the environment itself; titles optional; feeds "Top this week", "New", and "Near your scale" (room versus tabletop); deep links.
- **Rating**: one tap on four axes: fun / interesting / interactive / exciting.
- **Ranking**: community ratings blended with derived signals: verticality, move variety, reachable volume, completion rate, replay rate. Anti-gaming rules (owned by gj-data) must survive a deliberate rate-spam test (M4 exit test).
- **Leaderboards**: per-route time trials with plausibility validation; creator stats (plays, completions, best times) on the creator's own environments.
- Free tier: unlimited scans and play; 3 published environments live at once.

### 3.8 Monetization: two launch SKUs
- SKU 1: a cosmetic outfit pack. SKU 2: "realism+" avatar materials.
- Cosmetic only: no timers, no gacha, no pay-to-win, no fake scarcity; clear prices; one-tap restore. The store is shown after a win, never on a loss, and never before the first level (Design Skills rules 16 and 26).
- Owning either SKU lifts the published-environment cap (the lifted cap value is set at M5 via AUTH).
- Implemented with RevenueCat or Unity IAP (ADR at M5).

### 3.9 Compliance and privacy
- Written, BIPA-compliant biometric consent before any face processing; a published retention schedule; source photos and video deleted once derived assets exist.
- A training opt-in toggle separate from consent; derived data only; per-user deletion of everything, including vendor-side deletion.
- 13+ age gate; no COPPA scope in v1.
- GPS and EXIF stripped from every upload; vendor DPAs and retention terms on file before a vendor touches user data.
- App Store privacy labels accurate to the frozen telemetry schema (the Play data safety form joins when Android ships).

### 3.10 Platform and backend
- Supabase (auth, Postgres with RLS on every table, storage, edge functions), Vercel API, Inngest durable workflows for scan → reconstruct → scene graph → journey → package (ADR-0002).
- Telemetry and correction events are ingested only against the frozen schemas (§7); no PII in events.
- Production service keys, signing certificates, and payment credentials exist only in CI secrets.

### 3.11 The diorama view and the signature transition
- Diorama view: the environment as a floating tiny world with the tiny avatar in it; used for sharing clips and as the store hero shot.
- The shrink/diorama transition is the one signature hero animation. It has its own budget and a Reduce Motion cross-fade (Design Skills rules 7–8; DESIGN_SYSTEM.md decision 3).

## 4. Non-goals for v1 (explicit)

Not in v1, and not added without an AUTH (design-change) that also edits this section:
- **No synthetic game objects.** No enemies, coins, platforms, creatures, tokens, hazards, or branded items. The only non-photo things on screen are the avatar, one summit beacon, optional route and vista markers, and the HUD.
- **No Tier 2 physics** in the shipped app (research track only, §5).
- **No Android release in v1.** Android stays a compiling build target; its launch is v1.1 (`BACKLOG.md`).
- No stamina, damage, health, lives, or wall-run; no V2 verb tools (grapple, glider, picks, spring shoes, rope).
- No outdoor, garden, or street capture; no face or plate blur pipeline.
- No multiplayer, live races, seasonal content, or level packs.
- No slider-based avatar editor; no self-hosted reconstruction (documented only as a fallback path in ADR-0003).
- No under-13 audience; no COPPA scope.
- No paid content beyond the two SKUs; no creator revenue share.
Every item above lives in `BACKLOG.md` with a one-line rationale.

## 5. Tier 2 research track (funded from M0; not a v1 feature)

**Question.** Can true physics on segmented real objects (object–scene decoupling, tet-embedded Gaussians, XPBD) run at mobile frame rates and per-scan costs that make it a v1.1 or V2 feature?

**Owner.** gj-scenegraph, under `research/tier2/`. A standing research ticket per milestone from M1 (`M<n>-RES-01`), reported at every checkpoint.

**Budget.** A separate authorized line: hourly H100/A100 rental, $400–1,000 per month at realistic utilization, approved month by month by the Owner and paused whenever the core build needs the budget. No compute spend without an approved AUTH for that month.

**Scope.** Prototype on the Owner-supplied test corpus only, never on user data: segment objects from the splat, embed them for simulation, simulate at least three classes (cushion, cloth or curtain, small loose object), render the result in the Unity test scene on the reference device.

**Success metrics** *(initial)*. Every report states the measured value against each:

| # | Metric | Target |
|---|---|---|
| R1 | Corpus feasibility: segmentation plus embedding succeeds with no manual fixes | ≥ 70 % of the 30-room corpus and ≥ 80 % of the 20-tabletop corpus, for ≥ 3 object classes |
| R2 | Per-scan preprocessing on rented GPU | ≤ $0.50 and ≤ 10 min wall-clock per scan (target $0.25) |
| R3 | Mobile runtime on the reference Android device | ≤ 6 ms/frame added at 30 fps with ≥ 5 simulated objects; ≤ 150 MB added memory; no NaN or explosion in a 5-minute stress run |
| R4 | Plausibility | Blind A/B against Tier 1 on 10 scans: ≥ 70 % of testers prefer Tier 2 or judge it "more real"; zero "broken world" incidents (sinking, tearing) per 5-minute session |
| R5 | Decoupling quality | Moving or removing a segmented object leaves a plausible fill with no visible hole at play-camera distance in ≥ 80 % of cases |
| R6 | Budget discipline | Monthly spend within the approved line; paused within 24 h of the Owner's word |

**Decision point.** At the M4 checkpoint the Owner decides, on R1–R5 evidence, whether Tier 2 enters v1.1, V2, or is shelved. Nothing from the track ships in v1.

## 6. Quality scaling and performance targets

Targets, not gates (§11). The app renders the best it can on the device it is on and scales down automatically rather than excluding models.

| Target | Value | Source |
|---|---|---|
| Newest iPhones (current Pro and standard models, ProMotion) | Best-possible quality by default: full splat density, all Tier 1 effects, 60 fps target at up to 120 Hz | Owner decision, AUTH #003; Design Skills rule 27 |
| Older iPhones (every model that runs the iOS version the shipped Unity 6 build requires) | Automatic quality tiering (splat LOD and culling, resolution scale, effect density, Tier 1 object count) toward a 30 fps target; no model is excluded by policy | AUTH #003; plan §8 fallback |
| Active scan time | < 90 s | Plan §10 |
| Avatar generation | < 2 min | Plan §10 |
| Scan → playable environment, end to end | ≤ 10 min p50 *(initial)*, progress shown throughout | measured in M1 |
| Animation + IK + warping CPU | ≤ 4 ms/frame; motion-matching search every 3rd frame | Bible §2 |
| Motion database on device | ≤ 60 MB compressed (target 40) | Bible §2 |
| IK chains beyond feet | ≤ 2 simultaneous | Bible §2 |
| HUD | top 8 % of the screen in landscape; one overlay pass; no full-screen blur in play | Design Skills rules 21, 27 |
| Environment package download | ≤ 150 MB *(initial)*, so a friend plays from a link within 5 min on 20 Mbps | Plan §10 |
| Crash-free sessions | ≥ 99 % | Plan §10 |
| Motion-warping accuracy | hands within 0.05 A of the edge (target) | Bible §13 |

Measurements are suggested evidence: the Owner gathers them on their own iPhones and Bots gather them where tooling allows (the debug overlay's saved performance report). They inform tuning and never gate a merge.

## 7. Data, privacy, and retention model

| Data class | Collected when | Retained | Deleted |
|---|---|---|---|
| Raw scan video, poses, depth | capture | until derived assets exist; failed jobs ≤ 7 days | automatically; per-user delete-all |
| Face and body photos | avatar creation, after consent | until the avatar is generated (vendor job only) | immediately after generation, on device, in storage, and at the vendor; deletion receipt logged |
| Derived environment assets (splat, mesh, graph, spec, thumbnail) | reconstruction | while the user keeps the environment; published copies while published | per-user delete-all; unpublish removes from feeds immediately |
| Avatar assets (head mesh, textures, body parameters) | avatar creation | while the account exists | per-user delete-all |
| Consent records (policy version, timestamp, locale, text hash) | consent | as long as legally required | per the retention schedule |
| Telemetry events (frozen schema, pseudonymous ids, no GPS, no media references) | play | aggregated; raw events per the retention schedule | per-user delete-all |
| Correction events | one-tap "fix this label" | opt-in training only, derived data only | opt-out stops future use; delete-all removes |
| Ratings, reports, leaderboard times | community actions | while the environment exists | with the environment or the account |

The authoritative retention schedule and deletion flow are drafted in `legal/` (M0-LEGAL-02) and reviewed by counsel before M5 (AUTH spend).

## 8. Milestone plan (summary; the kit §4 phase prompts are the detail)

| Milestone | Weeks | Exit test |
|---|---|---|
| **M0 Harness** | 1–2 | One ticket goes from creation to merged PR with a QA screenshot attached and no human typing. Also: repo and CI green; Unity 6 URP project with splat renderer and controller scaffold; Inngest skeleton; every Bot's SKILLS.md merged; Unity on the QA VM with one scripted task proven; telemetry and correction schemas frozen; consent copy and retention schedule drafted; vendor retention terms collected; design system proposal ready for lock; the M0 AUTH batch filed. |
| **M1 Scan to playable** | 3–6 | 8 of 10 fresh room scans produce a reachable summit with at least two valid routes and no manual fixes. Under 6/10: stop and re-plan via AUTH. Motion matching versus blend trees decided (Bible §13). |
| **M2 Avatar** | 5–8 | 20 tester avatars recognizable by friends in a blind test at 60 %+, generated under 2 minutes, all on the shared rig. |
| **M3 Game loop and tabletop** | 7–10 | The Owner and three testers each explore five environments and want a sixth; Tier 1 holds its 30 fps target on the Owner's older test iPhone. |
| **M4 Sharing, moderation, leaderboards** | 9–12 | 50 tester-published environments with zero moderation misses in the Owner's review; the ranking survives a deliberate rate-spam test. |
| **M5 Store readiness and IAP** | 12–16 | App Store submitted after the Owner's explicit approval; the TestFlight cohort at a 99 %+ crash-free target. |
| **M6 Learning loops** | post-launch | First surface-classifier retrain on opt-in derived data with before/after metrics on the held-out corpus; affordance library v1. |

Changing this table is a milestone-plan change (AUTH).

## 9. Definition of done (v1)

v1 is done when all of the following hold, with evidence linked from `governance/CHECKPOINTS/M5.md`:
1. A new user on iPhone scans a room or a Lego build in under 90 seconds of active capture.
2. The same user creates a recognizable 1:12 avatar of themselves in under 2 minutes, behind an explicit consent step, and their source photos are provably deleted afterwards.
3. In their own scan they reach an auto-designated summit, plant the flag, complete at least two generated routes, and find a vista, with no manual fixes to the environment.
4. They publish the environment and a friend plays it from a link within five minutes.
5. The app meets its quality targets on the Owner's iPhones (60 fps on current models, 30 fps on older ones, Tier 0 and Tier 1 on) and holds a 99 %+ crash-free target across the TestFlight cohort; the Owner judges the targets, no test gates them.
6. Every row of the compliance gates (`governance/SECURITY_CHECKLIST.md` §12, M5 row) is green: consent, retention, deletion, 13+ gate, GPS/EXIF stripping, moderation queue, vendor DPAs, accurate privacy labels.
7. The App Store has approved the app.
8. No synthetic game object exists in the shipped build (§4).

## 10. Glossary

**A** one avatar height, the unit for every movement threshold · **Environment** a captured place with its derived package · **Summit / route / vista** the three goal types (§3.4) · **Tier 0 / 1 / 2** reactivity levels (§3.6, §5) · **Splat** the Gaussian-splat representation of a scan · **Scale multiplier** the per-environment factor applied to the default 1:12 · **Beat** a route segment's narrative role (introduce, develop, twist, resolve) · **Environment package** the published bundle (§3.7) · **Quality tier** the rendering tier the app selects automatically for a device; the Owner's newest and oldest iPhones are the informal reference points.

## 11. Platform, device, and testing policy (AUTH #003, 2026-09-15)

1. **Platform.** v1 launches on the iOS App Store only. The Unity project keeps the Android build target compiling (on-demand CI job) so a v1.1 Android release needs no re-architecture, but no Android feature work, QA, or store work happens in v1.
2. **Devices.** No minimum model is set. Every iPhone that runs the iOS version the shipped Unity build requires is supported; quality tiers (§6) scale automatically. The newest iPhones get the best graphics and capabilities the team can build; older models get a playable, tiered experience.
3. **Testing.** Every test, QA pass, performance measurement, coverage figure, and device check in this repository is a suggestion, never a merge gate. The Owner tests thoroughly on real iPhones throughout and judges milestone exit tests at each checkpoint. The only merge gates are the automated CI checks (secret scan, repository hygiene, lint, governance) and the security rules in `governance/SECURITY_CHECKLIST.md`. Acceptance criteria in tickets carry a `level`: `required` (deliverables, security, governance, automated CI) or `suggested` (tests, QA, performance, device evidence).
4. **Where older documents disagree.** The Movement Bible §2 reference device and §13 pass/fail thresholds, Design Skills rule 27, and any "reference Android device" wording are read as targets measured on the Owner's iPhones. Field notes in both locked documents record this.

## 12. iPhone Duo optional feature track

Apple's first foldable iPhone ships October 23, 2026 (7.6-inch inner display, 5.4-inch outer, stand and tent postures, Split View, Apple Pencil later in 2026). v1 may add optional, additive features that use it, chosen by the Owner from `design/proposals/iphone-duo-track.md`, each as its own ticket with a go/no-go at the M3 checkpoint. Constraints: identical value on every iPhone; no synthetic game objects; no delay to v1; verification when a Duo, or a Mac with Xcode's simulator, is available.

## 13. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 1.0 | 2026-09-15 | Initial spec from the kit v0.5 product lock, plan v0.1, Movement Bible v1.0, Design Skills v1.1 | AUTH #000 (Prompt 1 kickoff) |
| 1.1 | 2026-09-15 | v1 on the iOS App Store only; no minimum device model with automatic quality tiers (§6); tests, QA, and device measurements are suggestions, never merge gates (§11); iPhone Duo optional track (§12); Android deferred to v1.1 | AUTH #003 (Owner instruction) |
| 1.2 | 2026-09-16 | §2 and §3.2 capture wording aligned to the locked design decision 4 (rotation capture instead of three stills) | Transcription of the 2026-09-14 lock (M0-OWNER-02); no AUTH consumed |
