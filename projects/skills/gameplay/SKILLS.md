# gj-gameplay — Working Handbook

Remit: the traversal system, which is the product. That covers the character controller and verbs, the camera, motion matching and motion warping, the procedural layer, Tier 0 feedback, the Tier 1 runtime, the summit beacon, route markers and vistas, time trials, the diorama view, and the 30 fps budget (kit §3.3 role block; SPEC §3.5, §3.6, §3.11). Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** writes most of the C# (AGENT_GOVERNANCE §2). The **Operator** handles Editor-only work, device captures and long Unity runs. Owned paths (kit §3.3): `unity/Assets/Gameplay`, `unity/Assets/Player`, `unity/Assets/Environment`, and the shared tuning file `config/movement.json`. Today the only Unity code lives under `unity/Assets/GiganticJourneys/{Runtime,Tests}` (M0-UNITY-01), so the movement assemblies from M0-UNITY-03 are still to be created.

Research list: `projects/skills/gameplay/RESOURCES.md` (104 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branch names, PR template, evidence, 2-hour push cadence | `agents/grok/README.md` §3–§5 |
| AUTH before any spend, new vendor or asset, or edit to the Bible §3/§5/§10 or `config/movement.json` | `agents/grok/README.md` §6; Movement Bible header; REVIEW_RUBRIC B2, B3 |
| Tests and device measurements are suggestions; only CI checks and the security rules gate a merge | `agents/grok/README.md` §0; SPEC §11 |
| Layer boundaries: the five movement assemblies reference only downward | REVIEW_RUBRIC E1; Bible §2; ADR-0004 |
| No magic numbers: movement and camera constants live only in `config/movement.json` | REVIEW_RUBRIC E2; Bible §10; M0-UNITY-03 AT-7 |
| Performance rows: state the effect on SPEC §6; animation + IK + warping ≤ 4 ms; motion DB ≤ 60 MB; ≤ 2 IK chains beyond feet; motion-db report updated when clips change | REVIEW_RUBRIC D1, D2, D5 |
| Field measurements, clip names and contradictions go to Bible §16 Field notes only | REVIEW_RUBRIC H2 |
| Pins; asset-store purchases recorded with version and licence (Motion Warping, AUTH #001); MIT/BSD/Apache only in the app | SECURITY_CHECKLIST §7.1, §7.3, §7.4 |
| Splats and meshes load only through signed, short-lived URLs | SECURITY_CHECKLIST §3.1; M1-UNITY-01 AT-5 |
| Telemetry and time-trial data carry no PII; times are rate-limited and tied to a validated run | SECURITY_CHECKLIST §10; M4-GAME-02 AT-2 |
| Units (A), scale, gravity | Bible §1 |
| Five-layer architecture and mobile budgets | Bible §2; SPEC §6 |
| Verbs, triggers and feel rules; tools via `IVerbProvider` | Bible §3.1–§3.6, §14 |
| Surface class × verb; landing tiers; climb families; reactions | Bible §4, §5, §6, §7 |
| Camera | Bible §8; DESIGN_SYSTEM decision 5; Design Skills rule 19 |
| Tier 0 feedback matrix and the sound system (AUTH #022) | Bible §9; SPEC §3.6; Design Skills rule 17 |
| Tuning constants and the validator contract | Bible §10; `config/movement.json`; `services/traversal/movement.py` |
| Clip whitelist, pipeline, M1 spike | Bible §11, §12, §13 |
| Controls and HUD | DESIGN_SYSTEM decision 5; Design Skills rules 18, 21; SPEC §3.5 |
| Non-photo element language (avatar rim light and contact shadow, beam, footprints, sparkles) | DESIGN_SYSTEM decision 1; Design Skills rules 2, 20, 23 |
| Assist, haptics and shake toggles, visual twin for every sound cue | DESIGN_SYSTEM decision 10; SPEC §3.6 |
| Performance is part of design: 30 fps floor, no full-screen blur in play, Profiler evidence | Design Skills rule 27 and §4 checklist |

## 2. The five-layer architecture (Bible §2, ADR-0004, M0-UNITY-03)

Each layer is its own assembly, and references point only downward (an EditMode test checks this, per M0-UNITY-03 AT-1):

| Assembly | Does | Must not |
|---|---|---|
| `GJ.Intent` | Reads the virtual stick, jump, action and gamepad through the Input System. Predicts the trajectory 0.6 s ahead. Owns coyote time (`jump.coyoteMs`) and the jump buffer (`jump.bufferMs`). | Know about animation or geometry. |
| `GJ.TraversalQuery` | Casts against the **collision mesh** (never the splat) and the traversal graph, and picks the best verb for the intent using the Bible §3 thresholds. Resolves the contextual action priority: plant flag > grab > drop > slide (Bible §3.5). | Hold its own copy of thresholds. |
| `GJ.AnimationSelection` | Chooses locomotion by motion matching (the open MIT jlpm22 matcher) with inertialized blending. Contact verbs play tagged `MoveClip` clips. Falls back to blend trees + inertialization if the M1 spike misses. | Search every frame. The search runs as a job every 3rd frame, and inertialization covers the gap. |
| `GJ.MotionWarping` | Stretches contact clips so hands and feet land on the real edge (Kinemation Motion Warping, AUTH #001). Falls back to root-motion scaling + IK. | Be bought or upgraded without recording it (SECURITY_CHECKLIST §7.4). |
| `GJ.Procedural` | Foot IK on uneven geometry, hand IK on holds, look-at (beam, vistas, ledges), spine lean, secondary motion, Tier 0 triggers. Uses Animation Rigging (1.4.1 pinned) plus custom code. | Run more than 2 IK chains beyond the feet. |
| `GJ.Movement.Shared` | `IVerbProvider`, the `MoveClip` ScriptableObject, `MovementConfig`. | Depend on any layer above. |

- `MovementConfig` loads `unity/Assets/StreamingAssets/movement.json` at startup. A missing or extra key is a hard error (M0-UNITY-03 AT-2). CI's movement-sync check keeps that file byte-identical to `config/movement.json` and to Bible §10 (`.github/scripts/check_movement_sync.py`, M0-MOVE-01 AT-2).
- Python and C# must agree on every constant. A shared-fixture test is suggested (M0-MOVE-01 AT-4). The validator uses `with_margin` = 0.85 × value, so gameplay must always be able to do *more* than the validator asks.
- Gravity: `g = 9.81 × (1/scale) × gravityScale` (0.8) (Bible §1). Thresholds are in A so they survive the per-environment scale multiplier.

## 3. Verb implementation order

The order is set by tickets and Bible notes. Don't start a later step before its dependencies are merged.

1. **M0-UNITY-03:** walk, jog, run and sprint on a capsule, plus standing and running jump with coyote time and buffering. Touch stick + jump and gamepad both drive one intent layer. No contact verbs yet. Depends on M0-MOVE-01 (in progress).
2. **M0-UNITY-04:** the debug overlay behind `GJ_DEBUG` (fps 1 s average and p99 over 5 s, frame ms, SHA, device), so every later step has a measurement tool.
3. **M1-MOVE-01:** build the ~110-clip DB (Bible §11), run the motion matching vs blend-tree spike on device, and buy and record Motion Warping. This locks the locomotion core.
4. **M1-GAME-01 → M1-GAME-02:** load the splat, collision mesh and `environment_spec.json`, then add the contact verbs M1 needs: hop-over, vault, mantle, ledge hang/shimmy/climb-up and rung climb, all warped. The capsule must reach the summit on a validator-approved route and plant the flag.
5. **Procedural climbs:** stud climb first ("the signature tabletop verb; polish it before free climb", Bible §6.3), then textured free climb, pole and overhang (§6.4–6.6). Slips and catches (§6.7) come last and are off in Assist.
6. **M1-MOVE-02:** the AUTH #021 verbs (dive-roll, tic-tac, vault variants, wall-run). The validator must learn the same transitions (M1-SCEN-05).
7. **M1-GAME-03 / M1-GAME-04:** Tier 0 feedback and the audio system.
8. **M3-MOVE-01:** tools through `IVerbProvider` (safety-pin grapple swing/ascend/rappel, matchstick pole-vault) with no core change. The proposal says to polish the core first (`design/proposals/movement-v1-expansion.md` §5).
9. **M3-GAME-01:** the Tier 1 runtime. **M4-GAME-02:** time trials, ghosts and the plausibility floor.

Reactions and idle personality (Bible §7) layer on as clips arrive. They never block input, and any input cancels within one frame.

## 4. Motion matching and warping pipeline (Bible §11–§13)

**Clips (Bible §11–§12):**
- Take the Mixamo whitelist (~110 clips; Idle 6, Locomotion 40, Hang/shimmy 8, Falls/landings 10, …) and nothing else. That protects the ≤ 60 MB DB (target 40).
- Export as FBX "Without Skin" at 30 fps. Retarget in Blender to the GJ shared humanoid skeleton, fix foot slide and mark root motion.
- Clean up only the Owner's Rokoko Vision and Move.ai trial captures in Cascadeur.
- On import into Unity, use a Humanoid rig, loop the cyclic clips, and tag each clip with verb + surface metadata in a `MoveClip`.
- Author warp targets **once per contact clip** (hand and foot contact frames). The Tier 0 sounds fire on those same frames (Bible §9).
- Record exact Mixamo clip names in Bible §16 Field notes (Bible §11 asks gj-gameplay to verify names on import).

**DB build and report:** measure size and search cost, and write `qa/motion-db-report.md` (Bible §12 step 5; REVIEW_RUBRIC D2 requires updating it whenever clips change).

**Spike (M1-MOVE-01, Bible §13):**
- Run 5 minutes of scripted play (run loops, 20 mantles, 10 falls) on a current and an older iPhone.
- Pass means ≥ 30 fps p99, animation ≤ 4 ms and DB ≤ 60 MB. Then motion matching is locked for v1.
- Fail means blend trees + inertialization, and an ADR-0004 update by AUTH.
- On either path, warping must land hands within **0.05 A** on 20 of 20 test edges.
- These are targets, not merge gates (AUTH #003).

**Inertialization:** the Bollo method is the default. Dead blending (Holden) is a cheap alternative worth measuring in the spike. Use critically damped springs for camera and blend smoothing.

## 5. Camera rules (Bible §8, DESIGN_SYSTEM decision 5)

- **Default follow:** distance 4A, height 1.6A, look-ahead 0.8A. Base vertical FOV 60°. Framing is +0.2A higher and +5° wider than a typical platformer.
- **Collision:** collision-aware, with a dither-fade on real geometry within 1.5A of the lens.
- **Per verb:**
  - Run/sprint: +0.5A distance, FOV +4°.
  - Jump: no vertical follow for the first 0.2 s.
  - Climb: behind the back at 3A, pitch up 15°.
  - Hang/overhang: pitch down 20°.
  - Fall: hold, then snap-follow on landing.
  - Balance-walk: yaw locked to the edge ±20°.
- **Manual orbit:** one-finger drag on the right half (or the gamepad's right stick). It recentres 2 s after release and never fights the player mid-move.
- **Orientation:** the summit beam and vista sparkle are always drawn on top with depth-fade (also DESIGN_SYSTEM decision 1).
- **Camera constants:** these values need a **camera section in `config/movement.json`, "added by AUTH when M1 introduces it"** (DESIGN_SYSTEM decision 5). Until that AUTH exists, don't hard-code them. Status: **TBD, file the AUTH with M1-GAME-02.**
- **Package:** Cinemachine is **not** in `unity/Packages/manifest.json`. Adding it is a new dependency that needs a justification + pin (SECURITY_CHECKLIST §7.1, §7.3). A custom camera is equally valid.

## 6. Tier 0 feedback and the Tier 1 runtime

**Tier 0 (M1-GAME-03, Bible §9):**
- Every contact answers with sound, particles, haptic and, for big events, camera. Responses are keyed by `SurfaceMaterial` (wood, tile/stone, carpet, fabric, Lego/plastic, paper, metal, glass, plant, curtain) and come from the scene graph (`gj-scenegraph`).
- **Haptics:** light for footsteps at run+ only, medium for grabs and vaults, heavy for hard landings and the flag plant.
- **Camera shake** fires only on hard/recover landings and the flag plant.
- Everything scales with the environment multiplier, so Lego clicks stay tiny and floor booms stay big.
- The haptics toggle, the shake toggle and a visual twin for every sound cue are required (DESIGN_SYSTEM decision 10).

**Audio system (M1-GAME-04, AUTH #022):**
- Every event is layered (transient + body + tail), round-robin with micro-pitch, impact-scaled and contact-frame-locked.
- 3D-spatialized, with the listener just behind the avatar and biased to the camera.
- Category buses (movement/world/tools/UI/music) with sidechain ducking.
- Parametric reverb (RT60, early reflections, damping) computed from room volume and material absorption.
- Sourcing is CC0/royalty-free/self-recorded, with provenance recorded per clip.
- The built-in Unity Audio Mixer + Reverb Zones cost nothing. FMOD or Wwise licensing, or any paid SFX pack, needs an **AUTH** (REVIEW_RUBRIC B3). **Middleware choice: TBD (M1-GAME-04).**

**Tier 1 (M3-GAME-01, SPEC §3.6):**
- Shader-driven displacement only, with **no rigid/soft-body physics** (that's Tier 2, SPEC §5).
- Cushions dent, curtains, plants and paper sway, and cords swing. Keys come from segmentation + material labels produced by `services/reactivity`.
- Verb/tool reactions: wall-run dust scuff, rappel curtain sway, grapple twine sway.
- Tier 1 must hold 30 fps on the older reference iPhone with Tier 0 on (M3 exit, suggested evidence).
- Per-object displacement parameter format: **TBD** until the M1-DATA-01 schemas and M1-SCEN-02 labels land.

## 7. The 30 fps budget (SPEC §6, Bible §2, Design Skills rule 27)

- **Targets:**
  - 60 fps on current iPhones (ProMotion up to 120 Hz).
  - Automatic quality tiers toward **30 fps** on older ones, with no model excluded (AUTH #003).
  - The Bible's "2023 mid-tier Android" reference device is read as the Owner's older iPhone (Bible §16, 2026-09-15).
- **Hard sub-budgets:** animation + IK + warping ≤ 4 ms/frame; motion DB ≤ 60 MB; ≤ 2 IK chains beyond the feet; HUD in one overlay pass within the top 8 %; no full-screen blur in play.
- **Biggest shared cost: the splat.** The iOS Metal depth sort is the #1 program risk (M1-UNITY-01; aras-p issue #226). Budget gameplay assuming the splat takes most of the GPU, and coordinate on the LOD knobs, which live in one ScriptableObject (M0-UNITY-02 AT-5).
- **Tools:**
  - The debug overlay's saved performance report (M0-UNITY-04).
  - Profiler + Frame Timing Manager on device, never in the Editor.
  - Custom `ProfilerMarker`s per movement layer.
- **Burst:**
  - Burst is disabled on the Linux iOS export lane.
  - A macOS lane with Burst AOT enabled exists for perf/TestFlight builds (M3-UNITY-01, done).
  - Measure the motion-matching job on a Burst-on build.
- **Code hygiene:** no per-frame allocations in intent, query or selection code.
- **Measurements are evidence, not gates** (SPEC §11). They go in the PR (REVIEW_RUBRIC D1) and in Bible §16 Field notes.

## 8. Journey elements, time trials and the diorama

- **Beacon, route markers, vista sparkle:** follow DESIGN_SYSTEM decision 1 (thin light, low saturation, no solid geometry, on top with depth-fade). Placement comes from `environment_spec.json` (M1-GAME-01 AT-2). The schema is **TBD in M1-DATA-01**.
- **Time trials (M4-GAME-02):**
  - Ghost replay for the UX.
  - A time is accepted only if it clears the validator's theoretical minimum for that route. The check reuses M1-SCEN-05 and the same `movement.json` constants, with no duplicated numbers.
  - Telemetry sanity checks and rate limits (SECURITY_CHECKLIST §10.3).
  - Assist runs are tagged, never excluded (DESIGN_SYSTEM decision 10).
- **Diorama view:** the environment as a floating tiny world with the tiny avatar (SPEC §3.11). The shrink transition is the one signature hero animation, with a Reduce Motion cross-fade (DESIGN_SYSTEM decision 3).

## 9. Mistakes to avoid

- Typing a threshold (0.5A, 100 ms, 4A camera distance) into C# instead of reading `MovementConfig` (REVIEW_RUBRIC E2). The numbers are *initial* and M1 telemetry will retune them.
- Editing Bible §3/§5/§10 or `movement.json` without an AUTH. Measured contradictions go to Bible §16.
- Colliding against the splat, or letting splat and collision mesh drift out of alignment.
- Upward or sideways assembly references (Selection calling into Intent, tools patching the core). Tools come in only through `IVerbProvider`.
- Tuning feel in the Editor and shipping mush on device. Profile and feel-test on a real iPhone.
- A motion-matching search every frame, or a DB that grows past the Bible §11 whitelist.
- Camera snaps, camera fighting the player mid-move, or shake on ordinary landings.
- Unlogged assets: a Mixamo clip whose name isn't recorded, a sound without provenance, an asset-store package without version and licence.
- Adding a package (Cinemachine, FMOD, a KCC asset) without a pin, justification and licence check, or with spend but no AUTH.
- Physics in Tier 1. Anything that needs rigid or soft bodies is Tier 2 research.
- Making the gameplay stricter than the validator. The validator allows 85 % of max, so the controller must reach 100 %.

## 10. Checklists

**Pre-PR (gameplay):**
- [ ] Branch `ticket/<id>-<slug>`; ticket JSON updated (status, branch, pr, history) (REVIEW_RUBRIC B1, H3).
- [ ] Every required AT has evidence (test name, CI job, file path) (A1).
- [ ] `grep` shows no movement or camera literal in C#; everything comes from `MovementConfig` (M0-UNITY-03 AT-7).
- [ ] Assembly references point only downward (E1); new verbs register through `IVerbProvider`.
- [ ] EditMode/PlayMode tests pass locally and in the `unity-tests` workflow.
- [ ] CSharpier lint green (M0-UNITY-01 AT-6).
- [ ] Expected effect on SPEC §6 stated. Overlay report or Profiler screenshot from an iPhone attached when available (D1; Design Skills §4).
- [ ] Clip changes → `qa/motion-db-report.md` updated (D2). Clip names → Bible §16.
- [ ] New packages pinned in `manifest.json` + `packages-lock.json` with a licence line (SECURITY_CHECKLIST §7).
- [ ] Screenshots or clip attached; `gj-qa-release` visual pass requested (Design Skills §4).
- [ ] Assist, haptics and shake toggles respected; a visual twin exists for any new sound cue (DESIGN_SYSTEM decision 10).

**Per new verb:** trigger thresholds from Bible §3/§10 · surface classes from Bible §4 · camera rule from §8 · feedback row from §9 · warp targets authored · validator transition exists and agrees at the 85 % margin (the scenegraph owner reviews) · works on touch and gamepad · feels right on the Owner's iPhone (Bible §0 bar, suggested).

## 11. Pointers

`design/MOVEMENT_BIBLE.md` · `ADRs/0004-movement-architecture.md` · `config/movement.json` + `config/movement.schema.json` + `services/traversal/movement.py` · `unity/Assets/StreamingAssets/movement.json` · `unity/Packages/manifest.json` (Unity 6000.0.84f1, URP 17.0.4, Input System 1.20.0, Animation Rigging 1.4.1, Test Framework 1.6.0) · `design/proposals/movement-v1-expansion.md`, `sound-reactivity-v1.md`, `ios-splat-render-v1.md`, `decision-5-play-layout-options.md` · `.github/workflows/unity-tests.yml`, `ios-build.yml` · tickets M0-MOVE-01, M0-UNITY-03/04, M1-MOVE-01/02, M1-GAME-01..04, M1-UNITY-01, M3-MOVE-01, M3-GAME-01, M4-GAME-02.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | Unity is pinned at 6000.0.84f1. Cinemachine isn't installed. Camera constants need a `movement.json` camera section by AUTH (DESIGN_SYSTEM decision 5). Burst AOT is only on the macOS lane (M3-UNITY-01). Stud climb is polished before free climb (Bible §6.3). The movement assemblies don't exist yet (M0-UNITY-03 open). | gj-operator expanded RESOURCES.md to 104 link-checked entries and rewrote SKILLS.md around the AT-2 topics (M0-SKILL-04). |
