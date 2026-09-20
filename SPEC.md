# Gigantic Journeys — SPEC.md

Version 1.9 · 2026-09-20 · Owner: BlissDirective (SparkForge Labs) · Maintainer: Coordinator (Claude Code)

**Authority.** This file is the only authority on *what* v1 is. Below it rank `design/MOVEMENT_BIBLE.md` v1.0 (how the avatar moves), `design/Gigantic-Journey-Design-Skills.md` v1.1 with `design/DESIGN_SYSTEM.md` (how it looks and feels), then `ADRs/` (how it is built). Where documents disagree, this file wins until an authorized change says otherwise.

**Change control.** Any edit to this file requires an `AUTH REQUEST` of type design-change and a PR citing `APPROVED #n` (`governance/AUTHORIZATION_LOG.md`). CI blocks PRs that touch it without one. Creation of this v1.0 was authorized by Prompt 1 (AUTH #000).

**Sources.** `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` v0.5 (the v1 product lock of 2026-09-13 and the phase prompts), `context/DEVELOPMENT_PLAN.md` v0.1 (history), the Movement Bible, the Design Skills. Values marked *(initial)* are starting targets that M1–M3 measurements may revise, still through AUTH.

---

## 1. Product definition

Gigantic Journeys is a mobile game (v1 on the iOS App Store; one Unity 6 codebase that keeps Android buildable for a later release) in which the player scans a real place, a room or a tabletop build, chooses a near-photorealistic 1:12 character (a curated roster; custom likeness avatars are a V2 feature — AUTH #020), and journeys through that place: reaching its summit, running its routes, finding its vistas. The environment is the content; the avatar is the piece; traversal is the product. Finished environments can be published to an opt-in global database where they are ranked and played by others.

In one line (Bible §0): *a real person, 15 cm tall, parkouring through a real place, with the weight and hesitation of a real body and the responsiveness of a great platformer.*

Identity: name "Gigantic Journeys"; bundle id `com.sparkforgelabs.giganticjourneys`; repo slug `gigantic-journeys`; Bot prefix `gj-`; hashtags #GiganticJourneys, #GJrun.

## 2. The player's journey

1. **Install → play in 60 s.** A pre-scanned demo environment lets the player run, jump, and mantle before scanning anything (Design Skills rule 9: play first, scan second). First playable moment under 3 minutes, first summit under 5.
2. **Scan.** One illustrated toggle chooses room walkthrough or tabletop orbital; guided capture with live coverage, speed, blur, and light coaching; a quality gate before upload; under 90 seconds of active capture.
3. **Choose your character.** Pick from a curated roster of rigged, semi-photorealistic 1:12 characters; the cosmetic wardrobe (outfit pack, realism+ materials) reskins them. No photos and no scan of the player — selection is instant. (Custom avatars from the player's own likeness are a V2 feature — AUTH #020, ADR-0006.)
4. **Journey.** The environment resolves progressively while the player waits (never a blank spinner). Then: the summit beacon visible from the start; two or three generated routes of rising difficulty plus player-recorded challenge routes; three vistas rewarded with photo mode; the flag plant at the summit.
5. **Publish and browse.** Opt-in publish (GPS stripped, moderation pass); browse by place; rate on four axes; race per-route time trials; see creator stats. A friend plays it from a link within five minutes.
6. **Return.** New scans, other people's environments, the diorama view for sharing clips, the cosmetic wardrobe after a win.

## 3. v1 scope (in)

### 3.1 Capture: indoor rooms and tabletop builds
- **Flow:** Scan → in-context camera permission (value-first, never on launch) → the illustrated mode toggle → framing/relocalize → coached capture → missed-corner check → quality gate → a 5 s preview with Retake → on-device strip + bundle → upload, handing off to the create waiting state (decision 7). The coaching UI is locked (DESIGN_SYSTEM decision 6); this section is the system around it.
- Two guided modes, each with its own coaching script (Design Skills rule 13): **room walkthrough** (chest-height arc around the space; sweep back for overlap; a low and a high pass where there is verticality) and **tabletop orbital** (slow circle at two heights, keep the build centered). Mode chosen by one toggle with an illustration, never a settings page.
- ARKit camera poses and depth recorded alongside video (LiDAR depth when the device has it; ARKit poses give metric scale without it). Live coverage wash, a speed meter that turns amber when moving too fast, and blur rejection with a gentle haptic — all per decision 6.
- **Reconstruction-readiness quality gate:** before upload the app computes a cheap **on-device readiness score** from coverage, overlap/parallax, blur ratio, light, and ARKit tracking continuity, and rejects early and kindly ("Too dark here — turn on a lamp?"). When the score is thin it recommends **"add a quick pass"** at the weak region and lets the player **append passes to the same scan** (a multi-pass loop) before uploading; it never hard-stops ("Upload anyway" is always available) — AUTH #025.
- **Upload bundle (the capture→reconstruction contract):** compressed video, per-frame ARKit poses, camera intrinsics, optional LiDAR depth, the gravity/up vector and metric scale, and the mode + readiness score + coverage map so failures can be diagnosed. It shares one shape with the corpus manifest (M0-CAPT-01).
- Passes of 1–3 minutes; active capture under 90 seconds. **Failure/recovery:** tracking loss relocalizes and keeps progress; an interruption offers Resume or Start over; a downstream reconstruction failure returns a kind, free retry that preserves the mode and the user's place in the loop.
- **First-run:** after the play-first demo (rule 9), the first capture gets a one-time, richer coach-through that does not repeat on later scans.
- GPS and EXIF stripped on device before upload and verified again server-side. **People who wander into frame** are handled by coaching ("scan spaces, not people") and the opt-in publish-time moderation pass — no on-device person detection in v1 (§3.9); processing stays on our own infrastructure.
- Reconstruction into a Gaussian splat plus a collision mesh via a **self-hosted pipeline** (gsplat/Brush + COLMAP + Open3D), with a managed bridge (KIRI, corpus-only) for early validation (ADR-0005). The package format is vendor-neutral. User home imagery is processed on our own infrastructure.
- Well-lit indoor rooms and tabletop builds only.

### 3.2 Avatar: a curated 1:12 character (v1)
- The player picks from a **curated roster of rigged, semi-photorealistic 1:12 characters** — **eight at launch**, cast against an inclusive matrix (body type, apparent gender presentation, skin tone, apparent age, and a distinct silhouette + hero color each) so players see themselves without any capture (≥6 is the M2 floor). **No face or body capture and no biometric processing in v1** — selection is instant (AUTH #020, ADR-0006).
- All characters share the **GJ humanoid skeleton** and the shared animation/traversal set, so every character moves identically well; the roster is an authored art asset, not a per-user generation step. One enforced **rig standard** — Unity Humanoid mapping, normalized eye-height/scale to 1A, standardized foot/hand IK + contact markers, and the AUTH #021 carried-tool sockets (grapple coil, pole) — is checked by an automated rig-conformance gate on every character and cosmetic (AUTH #024).
- **Grounded semi-photoreal** fidelity: realistic proportions (about 7 heads), stylized "grounded" materials, a unified shader with an environment probe from the splat, a subtle rim light and contact shadow so the character pops off the photoreal floor (Design Skills rule 20); warm but low-to-moderate-detail faces (a small reactive-idle blendshape set, no full FACS) — deliberately short of hyperreal to avoid uncanny valley and any real-person resemblance. **V2 pushes the same rig toward hero-photoreal** (the "realism+" tier is the on-ramp), unified with the custom-avatar track (`research/rnd/`) — AUTH #024.
- Cosmetic customization only, through the two IAP SKUs (outfit pack, realism+ materials) plus free defaults, previewed on the chosen character in the diorama; each cosmetic passes the rig-conformance gate plus a clip test across the full verb + tool set. No slider editor.
- Default scale 1:12 (1.75 m → 14.6 cm) with a per-environment scale multiplier; every movement threshold is expressed in avatar heights **A** (Bible §1).
- **Sourcing** (clean-IP, zero biometric; AUTH #024): a **dual-track** build against the one rig contract — **open-base authoring as the primary path** (MakeHuman CC0 / Human Generator, uplifted in Blender; owned outright, $0 spend now) with a **leaner license path** (Character Creator 4 + Mixamo bring-up) held as a short-term contingency (its own spend AUTH if used). No scanned-real-people libraries; no MetaHuman (Unreal-only). Details: `research/vendors/character-roster-sourcing.md`.
- **Custom avatars from the player's own likeness are deferred to V2** (own-model R&D track, `research/rnd/`). v1 ships zero biometric processing.

### 3.3 Environment understanding (scene graph)
- Mesh cleanup: hole fill, ceiling cap, floater removal.
- Surface classification into the Bible §4 classes: walkable-hard, walkable-soft, walkable-narrow, ledge, rung, stud, textured-vertical, pole, overhang, slope, wall-smooth, soft-hanging, void.
- Gap, height, and edge measurement; scale inference (1:12 default, tuned for small builds so Lego studs are climbable); semantic and material labels via a vision pass.
- Affordance library mapping surface classes to traversal verbs; traversal-graph export (which surfaces reach which, by which verb, at what difficulty).
- Frozen schemas in `data/schemas/` (scene_graph, traversal_graph, environment_spec); changes need AUTH.

### 3.4 Journey generation: summit, routes, vistas
Generation is deterministic and inspectable: affordance library → traversal graph → summit → routes → validator → `environment_spec` (§3.3). Every published route is proven completable, and no scannable environment is ever a dead end.
- **Difficulty model**: every traversal-graph edge carries a verb-difficulty tier — **T0** ground locomotion (walk, jog, run, step-up, hop-over, mantle, standing/running jump), **T1** basic parkour (vault + variants, precision jump, controlled/hang drop, slide, dive-roll), **T2** climbing + advanced (ledge shimmy; rung/stud/free/pole/overhang climb; ledge-to-ledge; wall-push; tic-tac), **T3** high-skill + tools (wall-run; grapple swing/ascend/rappel; pole-vault; near-margin commits). A route's difficulty blends its highest tier, its count of distinct T2+ verbs, its tightest margin, its total climb/traverse, and its commit points. Difficulty is graded **relative to each environment** (every environment yields its own rising spread); a **global difficulty score** is also recorded on each route as metadata so absolute cross-environment filtering can be added later without a redesign.
- **Summit**: the highest validated-reachable point with a plantable stance; reaching it plants the player's flag. **Traversal tools (grapple, pole-vault, wall-run) may be required** to reach the summit when they are the only way up — provided the required tool is taught in an earlier beat of that route, never in beat 1. When even a tool cannot reach the true peak, the summit is the highest reachable plantable point.
- **Routes**: two or three generated routes of **per-environment rising difficulty**, each segment a `beat` structured introduce → develop → twist → resolve (Design Skills rule 22). **Beat 1 uses only the T0 set** — walk, jog, run, jump, step-up, hop-over, mantle (Bible §10); beat 2 teaches one new move; the **twist is the signature moment** — the "aha" use of the real environment, and on the hardest route the tool beat (a grapple swing across a void, a pole-vault over a gap, a wall-run along a face); beat 4 resolves to the summit. Plus player-recorded challenge routes and per-route time trials.
- **Vistas**: three auto-picked vantage points **chosen for the view, not for difficulty** — scored by viewshed (how much of the place and the summit is visible), framing, **low-to-moderate-difficulty access** (a short T0–T1 detour, never a gauntlet), and spatial spread; reaching one opens photo mode.
- **Validator**: a deterministic reachability search against `config/movement.json` at a 15 % margin (85 % of maximum reach and distance), also checking entry prerequisites (min speed, plant window) and surface prerequisites (wall-run wall length, grapple anchor reach). Three generation retries with relaxed *shaping* (never a relaxed margin), then a **template fallback** — a single guaranteed-simple validated route — so the loop never breaks. A route is valid only if every transition is achievable under the constants; the same validator gates player-recorded challenge routes.
- The summit beacon and the vista sparkle are always drawn on top with depth-fade so orientation is never lost (Bible §8).

### 3.5 Traversal: the product
The verb set, trigger thresholds, feel rules, camera rules, and landing tiers are defined in the Movement Bible and are not restated here. In v1 the avatar can: idle, walk, jog, run, sprint, plant-turn, balance-walk, crouch; step-up, hop-over, vault, mantle; standing, running, precision, ledge-to-ledge, and wall-push jumps with coyote time and jump buffering; controlled drop, hang-and-drop, slide, fall, and four landing tiers; ledge hang and shimmy, rung climb, stud climb, textured free climb, pole climb, overhang hang-traverse; slips and catches; one contextual action (plant flag > grab > drop > slide).
- Two-thumb landscape layout: a floating stick under the left thumb, jump as the largest right-thumb target, one contextual action button that appears only when relevant; controls repositionable and resizable; controller support from day one.
- Assist mode (longer coyote time, jump bonus, slips off, auto-grab) per Bible §10.
- Camera per Bible §8: collision-aware follow, look-ahead, dither-fade on occluding real geometry, manual orbit that auto-recenters, never fights the player mid-move.
- Reactions and idle personality per Bible §7.
- No stamina, no damage in v1. Falls cost time only; off-table falls on tabletops respawn at the last stable surface.
- **Expanded verbs + traversal tools (AUTH #021):** the full parkour set plus dive-roll, tic-tac, vault variants, and **wall-run**; and two **found-object tools** — the safety-pin **grapple** (swing/ascend/rappel) and a matchstick **pole-vault** — real 1:1-scale objects the character carries and uses, registered via `IVerbProvider` (Bible §3.6, §14). These tools are the sole §4 exception to "no synthetic game objects."

### 3.6 Environment reactivity and sound (AUTH #022)
The captured place must feel real and alive at 15 cm; sound and reactivity are the primary production value. Diegetic-first; everything **scales with the environment multiplier** (Lego clicks stay tiny, floor booms stay big).
- **Sound (ships):** a material × event bank (Bible §9) covering every verb and tool — layered, round-robin, impact-scaled, and contact-frame-locked to the animation; 3D spatialized with an ambience bed and category mix buses. **Scale-aware acoustics:** reverb is derived from the reconstructed room's volume and materials, so each captured place sounds unique and real. **Restrained adaptive music:** a quiet ambient bed plus sparse stings at key beats (summit approach, vista reveal, flag plant) and the signature shrink-transition theme — never a wallpaper soundtrack. Sourced CC0/royalty-free or self-recorded (no encumbered audio).
- **Tier 0 (ships):** material-keyed audio, particles, haptics, and camera shake per the Bible §9 matrix, all scaled with the environment multiplier.
- **Tier 1 (ships):** object segmentation of the splat plus procedural, shader-driven displacement (no physics): cushions dent, curtains sway, papers flutter, plants rustle, cords swing — extended to the new verbs and tools (a wall-run scuffs dust, a rappel bells a curtain, the grapple twine sways). Adds roughly $0.02–0.10 of segmentation compute per scan. Must hold 30 fps on the reference device (M3 exit test).
- **Accessibility:** playable fully muted — visual/caption cues for key audio events, plus haptics and camera-shake toggles (DESIGN_SYSTEM decision 10).
- **Tier 2 (does not ship in v1):** real rigid/soft-body physics — research track, §5.

### 3.7 Publish, browse, rank, leaderboards
- **Environment package**: splat, collision mesh, scene graph, environment spec, thumbnail; vendor-neutral and versioned; Supabase storage behind a CDN; delivered **only through signed URLs (≤15 min TTL) issued server-side after an auth check, with the CDN forwarding the signature** — direct storage URLs are never exposed, and packages carry no location data (SECURITY_CHECKLIST §3, §4.4).
- **Publish flow** (opt-in): draft (creator-playable) → GPS/EXIF stripped again server-side → an **automated vision moderation pass** → "Under review" (creator-only) → cleared to public, or rejected with a one-line reason and an appeal. **Moderation model: auto-clear + human-on-report** — the vision pass clears most publishes; a human queue (gj-data, escalation to the Owner) handles low-confidence flags, all user reports, and appeals, with no raw media to Bots beyond the thumbnail + package.
- **UGC compliance (Apple guideline 1.2, a launch gate):** an automated content filter (the vision pass), a one-tap report with a timely human response, the ability to **block abusive users**, and published developer contact info.
- **Browse by place**: thumbnails are the environment itself; titles optional; feeds "Top this week", "New", and "Near your scale" (room versus tabletop); deep links that open the environment with a single Journey action (App Store fallback; no location data).
- **Rating**: one tap on four axes: fun / interesting / interactive / exciting; rate-limited per user and device.
- **Ranking**: a **balanced blend** of the four-axis community ratings and derived objective signals — verticality, move variety, reachable volume, completion rate, replay rate — with a time-decay for "Top this week"; weights are telemetry-tunable. Anti-gaming rules (owned by gj-data) must survive a deliberate rate-spam test (M4 exit test).
- **Leaderboards**: per-route time trials with **plausibility validation** — a time is accepted only if it clears the deterministic reachability validator's theoretical minimum for that route (the same `config/movement.json` constants as journey generation, §3.4) plus telemetry sanity; impossible times are rejected. A ghost replay for the UX; creator stats (plays, completions, best times) on the creator's own environments (creator-only in v1).
- **Backend**: Supabase tables with **RLS on every table** — owner-only for drafts and creator stats, published-read (**published and moderation-cleared**) for public browse/play, service-role-only for the moderation queue and ranking jobs (SECURITY_CHECKLIST §2).
- Free tier: unlimited scans and play; 3 published environments live at once (the cap enforced at publish; an owned IAP SKU lifts it, §3.8).
- **v1 social non-goals** (post-launch): public creator profiles, follows/friends feeds, comments/DMs, and remix/fork of others' environments.

### 3.8 Monetization: two launch SKUs
- SKU 1: a cosmetic **outfit pack** — outfits on rig-clean silhouettes (casual, athletic, layered, dressed) as mesh/material swaps. SKU 2: **"realism+" materials** — a higher-fidelity skin/cloth/hair material tier on the chosen character (the V2 hero-photoreal on-ramp). Both preview live on the chosen character in the diorama; each passes the rig-conformance gate + a clip test across the full verb + tool set so a purchased cosmetic never breaks a move (AUTH #024).
- Cosmetic only: no timers, no gacha, no pay-to-win, no fake scarcity; clear prices; one-tap restore. The store is shown after a win, never on a loss, and never before the first level (Design Skills rules 16 and 26).
- Owning either SKU lifts the published-environment cap (the lifted cap value is set at M5 via AUTH).
- Implemented with RevenueCat or Unity IAP (ADR at M5).

### 3.9 Compliance and privacy
- **v1 has no biometric processing** (characters are pre-made; no face or body capture — AUTH #020). BIPA/CUBI/MHMDA consent applies only to the V2 custom-avatar feature. A published retention schedule; scan source video deleted once derived assets exist.
- A training opt-in toggle for derived scan/telemetry data, default off, derived data only; per-user deletion of everything.
- 13+ age gate; no COPPA scope in v1.
- GPS and EXIF stripped from every upload. Reconstruction runs on our own infrastructure (self-host); any managed bridge (KIRI) processes only the consented corpus, never real user scans, so no third party touches real user data in v1.
- **People in a scan:** capture coaches "scan spaces, not people" rather than detecting faces on device; because processing stays on our own infrastructure and GPS/EXIF are stripped, the capture-time control is the coaching, and any **published** environment additionally passes the §3.7 vision moderation pass. On-device person detection/blur is a deferred option, not v1 (AUTH #025).
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
- **No synthetic game objects,** with one narrow exception: **character-carried traversal tools** — real 1:1-scale found objects the avatar uses as gear (the safety-pin grapple, the matchstick pole-vault; AUTH #021). Still no *placed* game objects: no enemies, coins, platforms, creatures, tokens, hazards, or branded items. The only non-photo things on screen are the avatar, its carried tools, one summit beacon, optional route and vista markers, and the HUD.
- **No Tier 2 physics** in the shipped app (research track only, §5).
- **No Android release in v1.** Android stays a compiling build target; its launch is v1.1 (`BACKLOG.md`).
- No stamina, damage, health, or lives. (Wall-run and the grapple + pole-vault tools are now in v1 — AUTH #021.) The remaining V2 verb tools stay out of v1: glider, picks, spring shoes, rope/zipline.
- No outdoor, garden, or street capture; no face or plate blur pipeline.
- No multiplayer, live races, seasonal content, or level packs.
- No slider-based avatar editor. **No user face/body capture or biometric processing in v1**; custom avatars from the player's likeness are a V2 feature (AUTH #020, ADR-0006). (Self-hosted reconstruction is now the v1 backend — ADR-0005 — no longer a non-goal.)
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
| ~~Face and body photos~~ | **not collected in v1** (pre-made characters, no biometric) — a V2 custom-avatar data class | — | — |
| Derived environment assets (splat, mesh, graph, spec, thumbnail) | reconstruction | while the user keeps the environment; published copies while published | per-user delete-all; unpublish removes from feeds immediately |
| Character selection + owned cosmetics (no biometric) | character pick / purchase | while the account exists | per-user delete-all |
| Consent/ToS acceptance records (policy version, timestamp, locale, text hash) | account setup | as long as legally required | per the retention schedule |
| Telemetry events (frozen schema, pseudonymous ids, no GPS, no media references) | play | aggregated; raw events per the retention schedule | per-user delete-all |
| Correction events | one-tap "fix this label" | opt-in training only, derived data only | opt-out stops future use; delete-all removes |
| Ratings, reports, leaderboard times | community actions | while the environment exists | with the environment or the account |

The authoritative retention schedule and deletion flow are drafted in `legal/` (M0-LEGAL-02) and reviewed by counsel before M5 (AUTH spend).

## 8. Milestone plan (summary; the kit §4 phase prompts are the detail)

| Milestone | Weeks | Exit test |
|---|---|---|
| **M0 Harness** | 1–2 | One ticket goes from creation to merged PR with a QA screenshot attached and no human typing. Also: repo and CI green; Unity 6 URP project with splat renderer and controller scaffold; Inngest skeleton; every Bot's SKILLS.md merged; Unity on the QA VM with one scripted task proven; telemetry and correction schemas frozen; consent copy and retention schedule drafted; vendor retention terms collected; design system proposal ready for lock; the M0 AUTH batch filed. |
| **M1 Scan to playable** | 3–6 | 8 of 10 fresh room scans produce a reachable summit with at least two valid routes and no manual fixes. Under 6/10: stop and re-plan via AUTH. Motion matching versus blend trees decided (Bible §13). |
| **M2 Character & rig** | 5–8 | The curated character roster (eight at launch; ≥6 floor) passes rig-conformance and retargets the shared animation/traversal set cleanly with no per-character fixes; the two cosmetic SKUs pass the verb+tool clip test; a tester picks a character and it moves identically well across environments. No biometric (AUTH #020, #024). |
| **M3 Game loop and tabletop** | 7–10 | The Owner and three testers each explore five environments and want a sixth; Tier 1 holds its 30 fps target on the Owner's older test iPhone. |
| **M4 Sharing, moderation, leaderboards** | 9–12 | 50 tester-published environments with zero moderation misses in the Owner's review; the ranking survives a deliberate rate-spam test. |
| **M5 Store readiness and IAP** | 12–16 | App Store submitted after the Owner's explicit approval; the TestFlight cohort at a 99 %+ crash-free target. |
| **M6 Learning loops** | post-launch | First surface-classifier retrain on opt-in derived data with before/after metrics on the held-out corpus; affordance library v1. |

Changing this table is a milestone-plan change (AUTH).

## 9. Definition of done (v1)

v1 is done when all of the following hold, with evidence linked from `governance/CHECKPOINTS/M5.md`:
1. A new user on iPhone scans a room or a Lego build in under 90 seconds of active capture.
2. The same user picks a 1:12 character from the curated roster (instant, no capture) that embodies the shared movement set.
3. In their own scan they reach an auto-designated summit, plant the flag, complete at least two generated routes, and find a vista, with no manual fixes to the environment.
4. They publish the environment and a friend plays it from a link within five minutes.
5. The app meets its quality targets on the Owner's iPhones (60 fps on current models, 30 fps on older ones, Tier 0 and Tier 1 on) and holds a 99 %+ crash-free target across the TestFlight cohort; the Owner judges the targets, no test gates them.
6. Every row of the compliance gates (`governance/SECURITY_CHECKLIST.md` §12, M5 row) is green: retention, deletion, 13+ gate, GPS/EXIF stripping, moderation queue, accurate privacy labels. (No biometric consent and no avatar-vendor DPA in v1 — AUTH #020.)
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
| 1.3 | 2026-09-18 | v1 avatar = curated pre-made character roster, cosmetic-only customization; **no face/body capture or biometric processing in v1** (custom avatars → V2); reconstruction backend = self-host (ADR-0005) with a KIRI corpus-only bridge, Luma dropped; M2 reframed to Character & rig; §5 biometric consent becomes a V2 gate. Applied to §1, §2, §3.1, §3.2, §3.9, §4, §7, §8, §9 | AUTH #018, #020 (Owner instruction) |
| 1.4 | 2026-09-18 | Movement v1 expansion (AUTH #021): added verbs (dive-roll, tic-tac, vault variants, wall-run) and a v1 traversal-tools layer (safety-pin grapple, matchstick pole-vault); opened a narrow §4 exception for diegetic character-carried tools; §3.5 and §4 updated | AUTH #021 (Owner instruction) |
| 1.5 | 2026-09-19 | Sound design + environment reactivity (AUTH #022): deepened §3.6 — scale-aware acoustics (reverb from the reconstructed room), material×event sound bank for all verbs/tools, spatialization + ambience + mix, restrained adaptive music, Tier 1 reactivity extended to tools, muted-playable accessibility; Tier 2 physics stays research | AUTH #022 (Owner instruction) |
| 1.6 | 2026-09-19 | Journey generation v1 (AUTH #023): deepened §3.4 — T0–T3 verb-difficulty model; per-environment rising-difficulty routes with a global difficulty score as metadata; beat-per-tier (beat 1 = T0 only) with the twist as the signature/tool beat; traversal tools may be required to reach the summit when taught in an earlier beat (never beat 1); vista scoring; retry→template-fallback guarantee; validator checks entry/surface prerequisites | AUTH #023 (Owner instruction) |
| 1.7 | 2026-09-19 | Character roster art spec (AUTH #024): roster = 8 at launch on an inclusive casting matrix (≥6 floor); one enforced rig standard (Unity Humanoid, IK/contact markers, AUTH #021 tool sockets, rig-conformance gate); grounded semi-photoreal fidelity for v1 with a V2 hero-photoreal roadmap on the same rig; cosmetic SKUs gated by a verb+tool clip test; dual-track sourcing (open-base primary at $0, leaner license contingency); §3.2/§3.8/§8 + DESIGN_SYSTEM decision 4 updated | AUTH #024 (Owner instruction) |
| 1.8 | 2026-09-20 | Capture UX + coaching (AUTH #025): deepened §3.1 into a capture system around the locked coaching UI — flow/state machine, room + tabletop coaching scripts, a reconstruction-readiness quality gate (coverage/overlap/blur/light/tracking), the capture→reconstruction upload contract, failure/recovery, first-run guided capture; an on-device readiness predictor + multi-pass "add a pass" loop (extends DESIGN_SYSTEM decision 6); §3.9 — people in frame handled by coaching + publish-time moderation, no on-device person detection in v1 | AUTH #025 (Owner instruction) |
| 1.9 | 2026-09-20 | Publish/browse/rank/moderation (AUTH #026): deepened §3.7 — auto-clear + human-on-report moderation with Apple 1.2 UGC compliance (filter/report/block/contact); balanced-blend ranking (ratings + objective signals, Top-this-week decay, anti-gaming); plausibility-floor leaderboards reusing the deterministic validator; signed-URL/CDN delivery (≤15 min) + RLS (published-read = published AND cleared); free-tier cap; v1 social non-goals. Decomposed M4 into tickets; SECURITY_CHECKLIST §10.5 | AUTH #026 (Owner instruction) |
