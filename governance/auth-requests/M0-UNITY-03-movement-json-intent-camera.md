# AUTH request — `movement.json` `intent` + `camera` sections (M0-UNITY-03 AT-7)

> **STATUS: PROPOSED — awaiting the Owner.** Filed by gj-operator, 2026-09-28 (overnight worker). No AUTH
> number assigned; Bots never write the Decisions table. The Coordinator logs it as the next free number
> (currently **#036**) if the Owner approves.

```
AUTH REQUEST (next free #, currently #036)
Type: design-change (protected paths: config/movement.json, config/movement.schema.json,
      design/MOVEMENT_BIBLE.md §10 JSON block — they change together, check_movement_sync.py)
What: Add two sections to movement.json holding the stick/intent and follow-camera numbers that the
      Movement Bible (§2, §3.1, §3.4, §8) and DESIGN_SYSTEM decision 5 already specify in prose.
Why:  M0-UNITY-03 AT-7 (required): "No movement or camera constant is hard-coded; every number comes
      from MovementConfig." Today these values have no home in movement.json, so the controller keeps
      them in ONE file, unity/Assets/GiganticJourneys/Movement/Shared/ProvisionalTuning.cs, guarded by an
      EditMode test. DESIGN_SYSTEM decision 5 already says the camera section is "added by AUTH when M1
      introduces it".
Cost: $0
Reversible: yes (values stay tunable by M1 telemetry)
Waiting on: Owner (approve / change values), then Coordinator (log + Bible §10 edit)
```

## Proposed JSON (appended to the §10 block and config/movement.json; values are the Bible's)

```json
"intent": { "walkMaxStick": 0.40, "jogMaxStick": 0.85, "sprintHoldSec": 1.5, "fallAfterSec": 0.35, "trajectorySec": 0.6, "idleSec": 0.4, "stickDeadzone": 0.1 },
"camera": { "followA": 4.0, "heightA": 1.6, "lookAheadA": 0.8, "runPullBackA": 0.5, "runFovDeg": 4, "baseFovDeg": 60, "jumpHoldSec": 0.2, "climbFollowA": 3.0, "climbPitchDeg": 15, "hangPitchDeg": -20, "balanceYawDeg": 20, "recenterSec": 2.0, "occluderFadeA": 1.5, "blendSec": 0.25 }
```

Sources: Bible §3.1 (walk < 40 %, jog 40–85 %, run > 85 %, sprint after run held 1.5 s, idle after 0.4 s),
§3.4 (fall after 0.35 s airborne), §2 (trajectory 0.6 s), §8 (4A / 1.6A / 0.8A / +0.5A / +4° / 0.2 s /
climb 3A +15° / hang −20° / balance ±20° / recenter 2 s / dither-fade within 1.5A), DESIGN_SYSTEM decision 5
(base vertical FOV 60°). **Two values are new and need the Owner's eye:** `stickDeadzone` 0.1 (the Bible
gives none; the gamepad keeps the Input System default deadzone) and `blendSec` 0.25 (camera smoothing;
the Bible gives none).

Not proposed for movement.json (they are character or environment data, not tuning): the avatar's real
height (1.75 m default, Bible §1; roster data in M2), the capsule radius (0.15 A placeholder until the M2
rig), and the environment multiplier (12 = 1:12; the environment spec in M1).

## On approval (Coordinator + Builder/Operator)
1. Log the Decisions row; edit Bible §10 + `config/movement.json` + `config/movement.schema.json` together;
   `python .github/scripts/copy_movement_to_unity.py`; regenerate the agreement fixture
   (`python services/traversal/movement.py --write-fixture`); add the fields to `services/traversal/movement.py`.
2. Add `IntentSection` / `CameraSection` to `MovementConfig.cs`, point the controller and camera at them,
   and delete `ProvisionalTuning.Intent` / `ProvisionalTuning.Camera`. The AT-7 literal-scan test keeps it honest.
