# M0-UNITY-03 — traversal controller scaffold — build notes and QA pass

2026-09-28, gj-operator (overnight worker; Builder work, then the gj-qa-release hat per `qa/VISUAL_QA.md`).
Delivered as a direct commit to `main` (the fast-forward model, AUTH #006/#007; Operator precedent), so this
file carries the QA verdict (§8) instead of a PR comment.

## What was built
- **Seven assemblies** under `unity/Assets/GiganticJourneys/Movement/` (Bible §2, ADR-0004), bottom to top:
  `GJ.Movement.Shared` → `GJ.Intent` → `GJ.TraversalQuery` → `GJ.AnimationSelection` → `GJ.MotionWarping` →
  `GJ.Procedural` → `GJ.Movement.Controller` (composition root). References point only downward.
  Animation selection, warping and procedural are **empty seams** in M0 (interfaces + no-op implementations):
  the capsule has no animation, and M1-MOVE-01 / M1 contact verbs fill them.
- **`GJ.Movement.Shared`**: `MovementConfig` (typed, every movement.json key 1:1, strict: a missing, unknown,
  duplicate or wrongly-typed key is a `MovementConfigException` naming the dotted path; own small RFC 8259
  reader `StrictJson`, because JsonUtility silently ignores missing/extra keys and no JSON package is
  installed), `MovementConfigLoader` (reads `StreamingAssets/movement.json` at
  `RuntimeInitializeOnLoad(BeforeSceneLoad)`; a bad file is logged and the controller disables itself),
  `MovementScale` (A ↔ world; Bible §1 gravity), `JumpBallistics`, `IVerbProvider` + `VerbContext` /
  `VerbProposal` / `VerbPriority`, string verb ids (so M1/M3 providers add verbs without editing an enum),
  `MoveClip` ScriptableObject stub, and **`ProvisionalTuning`** (see AT-7).
- **`GJ.Intent`**: `IntentFrame`, `IIntentSource`, `IntentAggregator` (strongest stick wins, any jump counts),
  `GaitSelector` (Bible §3.1 bands, sprint after run held 1.5 s, gait cap for balance-walk/crouch later),
  `JumpTiming` (coyote `jump.coyoteMs`, buffer `jump.bufferMs`, assist `assist.coyoteMs`; no double jump),
  `TrajectoryPredictor` (0.6 s), `FloatingStick` + `TouchLayout` (left-third floating stick, 72 pt jump pad
  low-right in the safe area, iOS points from dpi), `GamepadIntentSource` (Input System: gamepad left stick +
  south button, WASD/space for the Editor) and `TouchIntentSource` (Input System `Touchscreen`).
- **`GJ.TraversalQuery`**: `VerbRegistry` (highest priority wins, later registration wins ties, duplicate ids
  rejected) and `LocomotionVerbProvider` (idle/walk/jog/run/sprint; standing/running/sprint jump held for the
  whole committed arc; airborne → fall after 0.35 s).
- **`GJ.Movement.Controller`**: `LocomotionMotor` (A units, no Unity physics, EditMode-steppable: gait speed from
  movement.json, committed ballistic jumps solved from jump.* height/distance, no air control),
  `TraversalController` (CharacterController sized in A: height `avatarHeightA`, step offset
  `verticals.stepUp`, slope limit `slopes.runMaxDeg`), `FollowCamera` (fixed-yaw follow: 4A/1.6A, 0.8A
  look-ahead, run +0.5A/+4°, no vertical follow for 0.2 s of a jump), `TouchControlsView` (UI Toolkit visuals).
- **Test scene** `Assets/Scenes/MovementTest.unity` (built by `Assets/Editor/Movement/MovementTestScene.cs`,
  idempotent, menu *Gigantic Journeys/Build Movement Test Scene*): a 12 m flat floor at 1:12 (1 A = 0.1458 m),
  1 A distance stripes, the capsule, the follow camera. Added to Build Settings (index 1; the boot scene is
  unchanged).
- **M0-MOVE-01 remainder**: the C# loader above plus the C#/Python agreement check: `services/traversal/movement.py`
  gained `flatten()` + `--write-fixture`; both `test_flatten_matches_shared_fixture` (pytest) and
  `MovementConfigTests.CSharpAndPython_AgreeOnEveryConstant_SharedFixture` (EditMode) compare against
  `services/traversal/tests/fixtures/movement_expected.json` (67 constants).

## Design decisions made (reviewable)
- **Gravity.** Bible §1 "g = 9.81 × (1/scale) × 0.8" is read with *scale* = the environment multiplier
  (12): world g = 9.81/12 × 0.8 = 0.654 m/s², i.e. 4.48 A/s² for a 1.75 m avatar. A standing jump
  (1.1 A) then lasts 1.40 s: "slightly floaty". `MovementScaleTests.Gravity_FollowsBibleSection1` pins it.
- **Jump shape.** Heights and distances are met exactly by solving the launch velocity per jump
  (vertical from height and g, horizontal = distance / air time), so ground speed does not change the arc.
  With no stick input a jump goes straight up (height only). Walk counts as "standing"; jog and run take the
  running jump; sprint takes the sprint distance (3.0 A) at the running height.
- **No acceleration curve** until motion matching supplies one (M1-MOVE-01): gait speed is applied directly,
  which is what makes AT-3 exact.
- **Run → sprint.** By Bible §3.1 run held 1.5 s *becomes* sprint, so a 5 s run is only measurable with a gait
  cap (`LocomotionMotor.MaxGait`; the same cap will serve balance-walk and crouch in M1). The AT-3 tests cap
  the run capsule at Run. Double-tap-to-sprint is not implemented (no Bible timing value).

## Tests (local, Unity 6000.0.84f1, `-batchmode -nographics`)
| Suite | Result | File |
|---|---|---|
| EditMode | **95/95 passed** (61 new) | `M0-UNITY-03/editmode-results.xml` |
| PlayMode | **17/17 passed** (6 new) + 1 explicit evidence capture (skipped in CI) | `M0-UNITY-03/playmode-results.xml` |
| pytest (services/traversal) | 7/7 passed (1 new) | — |

PlayMode log (real CharacterController physics, 60 fps target):
```
[M0-UNITY-03 AT-3] Walk: 1.200 A/s over 5.02 s (target 1.2)
[M0-UNITY-03 AT-3] Jog: 2.400 A/s over 5.02 s (target 2.4)
[M0-UNITY-03 AT-3] Run: 3.600 A/s over 5.02 s (target 3.6)
[M0-UNITY-03 AT-3] Sprint: 4.500 A/s over 5.02 s (target 4.5)
[M0-UNITY-03 AT-4] standing jump: height 1.100 A, distance 1.228 A
[M0-UNITY-03 AT-4] running jump: height 1.200 A, distance 2.406 A
```

## Acceptance tests
| AT | Level | Status | Evidence |
|---|---|---|---|
| AT-1 assemblies, downward refs | required | **Met** | 7 asmdefs; `MovementArchitectureTests.AllLayerAssembliesExist`, `AsmdefReferences_PointOnlyDownward`, `CompiledAssemblies_PointOnlyDownward` (actual IL references), `SharedAssembly_HoldsTheContractTypes` |
| AT-2 strict movement.json load | required | **Met** | `MovementConfigTests.*`: `ShippedFile_LoadsIntoTypedFields`, `StartupConfig_IsTheShippedFile`, `EveryJsonLeaf_IsReadIntoATypedField`, `MissingKey_IsAHardError_NamingThePath`, `MissingSection_IsAHardError`, `ExtraKey_IsAHardError_NamingThePath`, `ExtraTopLevelKey_IsAHardError`, `WrongType_IsAHardError`, `DuplicateKey_AndMalformedJson_AreHardErrors`, `MissingFile_IsAHardError` |
| AT-3 speeds within 2 % over 5 s | suggested | **Met** | PlayMode `WalkJogRunSprint_Over5Seconds_WithinTwoPercent` (log above: 0.0 % error); EditMode `LocomotionMotorTests.GroundSpeed_Over5Seconds_WithinTwoPercent` ×3, `Sprint_Over5Seconds_WithinTwoPercent` |
| AT-4 jumps ± 5 %, coyote 100 ms, buffer 120 ms | suggested | **Met** | EditMode `StandingJump_…`, `RunningJump_…`, `SprintJump_Distance3A_…`, `JogJump_IsARunningJump`; intent layer `IntentLayerTests.Coyote_JumpAfterWalkingOffAnEdge` (50/95 ms fire, 105/200 ms do not), `Coyote_DoesNotGrantASecondJump`, `Buffer_PressBeforeLandingFiresOnLanding` (50/115 ms fire, 125/300 ms do not), `Buffer_IsConsumedOnce`, `Windows_ComeFromMovementJson`; motor `BufferedJump_FiresOnLanding_InTheMotor`; PlayMode `StandingAndRunningJump_HeightAndDistance_WithinFivePercent` |
| AT-5 touch stick + jump, gamepad, one intent layer | required | **Met in Editor (simulated devices); device clip pending** | `qa/evidence/M0-UNITY-03/01`, `02`; PlayMode `Gamepad_DrivesTheIntentLayer`, `Touch_FloatingStickAndJumpPad_DriveTheSameIntentLayer`; EditMode `Aggregator_…`, `FloatingStick_…`, `TouchLayout_…`. Pending: a ≤ 30 s clip on an Owner iPhone with a Bluetooth controller |
| AT-6 SPEC §6 targets on iPhone | suggested | **Not measured** | Needs a TestFlight build (TestFlight upload is blocked on the Admin-role ASC key, PROGRESS Owner item 13) |
| AT-7 no hard-coded movement/camera constant | required | **Met for every movement.json constant; intent/camera numbers pending AUTH** | `qa/reports/M0-UNITY-03/at7-literal-grep.txt`; test `MovementArchitectureTests.NoMovementOrCameraLiteral_OutsideTheConfig`. The Bible §3.1/§8 stick-band and camera numbers have no movement.json section yet (protected path), so they live in one file, `ProvisionalTuning.cs`; proposed AUTH: `governance/auth-requests/M0-UNITY-03-movement-json-intent-camera.md` |

## QA pass (gj-qa-release hat, `qa/VISUAL_QA.md` gameplay checklist)
- Capsule grounded, no jitter on the flat floor; faces travel direction; camera keeps the capsule centred
  with the look-ahead; no clipping at 1:12 (near plane 0.01 m in the scene).
- Touch: the stick floats to the first touch in the left third, knob tracks the drag, releases on lift;
  the jump pad highlights while held. Placeholder styling (white/black alpha) until the M0-DSGN-02 tokens.
- Findings (non-blocking): **D1 (S3)** touch controls are not yet repositionable/resizable (DESIGN_SYSTEM
  decision 5 binding constraint; not in this ticket's ATs) → BACKLOG. **D2 (S4)** double-tap sprint not
  implemented (no Bible timing value). **D3 (S4)** Android reads StreamingAssets from a jar, so `File.ReadAllText`
  fails there; Android is not a v1 target (AUTH #003), noted in code.
- Verdict: **PASS WITH DEFECTS** (none blocking). Privacy: synthetic scene only.

## Follow-up 2026-09-29: D1 (control customization) and the resize-safe touch layout
gj-operator, as an overnight follow-up to QA finding D1 and the BACKLOG item from the M1-DUO-01 research.
It was delivered as a direct commit to `main`.

**What changed**
- `GJ.Intent/ControlCustomization.cs`: the runtime half of DESIGN_SYSTEM decision 5's "Customization" (Settings › Controls).
  - Fields: button size 56–96 pt, idle opacity 0.2–1 (default 0.6), a left-handed mirror, and a drag offset for the jump pad.
  - JSON with a version field, clamped. Empty, malformed, newer-version or non-finite data falls back to the default.
  - Persisted by `ControlCustomizationStore` in PlayerPrefs (`gj.controls.v1`) with `Reset()`.
  - The range constants live in `ProvisionalTuning.Touch`, which is what the no-literals architecture test requires.
- `TouchLayout` applies the customization.
  - Left-handed puts the stick zone on the right third and the jump pad low-left, mirrored exactly.
  - The drag offset points toward the screen centre in either hand.
  - The pad is clamped inside the safe area and clear of the stick zone.
  - The old two-argument constructor still gives exactly the default layout.
- `TraversalController` loads the saved customization; `TouchControlsView` uses its idle opacity.
- **Resize-safe:** `TouchIntentSource` cancels an active floating stick when the safe area changes (Duo fold or unfold, Split View, rotation). It ignores that touch until it lifts, so the stick never keeps an origin in stale coordinates. A fresh touch takes the stick in the new layout. This covers BACKLOG item (a).

**Tests** (local, Unity 6000.0.84f1, `-batchmode -nographics`)
- EditMode: **151/151 passed**, 17 new in `ControlCustomizationTests`.
  - Default equals the uncustomized layout.
  - Size clamps to 56 and 96.
  - Exact left-handed mirror.
  - Drag offset works in both hands.
  - Extreme offsets stay inside the safe area and clear of the stick zone.
  - JSON round trip and clamping; bad or newer data falls back to the default; non-finite values fall back.
  - Store save, load and reset.
  - `GeometryDiffers`.
- PlayMode: **18/18 passed** plus 1 explicit evidence capture, with 1 new test: `Touch_GeometryChangeMidDrag_CancelsTheStickUntilTheTouchLifts`.

**Still to build:** the Settings › Controls screen itself (drag-to-reposition editor, sliders, live preview). It needs the UI
Toolkit tokens from M0-DSGN-02; the mockup is `design/proposals/mockups/settings.html?state=controls`. The contextual
action button, once it exists, takes the same size and offset model.
