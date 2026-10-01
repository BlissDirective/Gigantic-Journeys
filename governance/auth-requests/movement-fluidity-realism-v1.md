# AUTH request — Movement fluidity & realism v1 (#043)

> **STATUS: APPROVED #043 — Owner instruction, 2026-09-30** ("Proceed to spec+build: [#1, #2, #3,
> #5, #6]; Plan and spec #8"). Full design: `design/proposals/movement-fluidity-realism-v1.md`.

```
AUTH REQUEST (#043)
Type: design-change (protected paths: config/movement.json, config/movement.schema.json,
      design/MOVEMENT_BIBLE.md §2/§3/§5/§8/§10, design/DESIGN_SYSTEM.md)
What: Movement fluidity/realism enhancements beyond the existing plan —
      #1 stride/speed warping, #2 traversal-graph anticipation, #3 procedural landing/weight +
      camera dip, #5 normal-aware contact IK, #6 miniature realism levers (cadence/accel +
      tilt-shift DoF + scale-aware motion blur). #8 (learned/physics motion) = a v2-targeted
      Tier-2 research spike (RES-MOVE-01), not v1 code.
Why:  Owner-directed v1 movement quality lift; all items procedural/tunable and within the
      Bible §2 mobile budget (≤4 ms anim CPU, ≤60 MB DB, 2-IK-chain cap).
Cost: $0 (free-tier/procedural; the #8 spike runs on the existing Tier-2 line, AUTH #040/#039).
Reversible: yes (every value is a movement.json constant; every layer is flag-gated; the
      miniature identity is two swappable profiles).
Waiting on: nothing to authorize (approved). Execution is Operator-gated for the C# half (below).
```

## New `movement.json` blocks (values = the "more miniature-real" defaults, Owner 2026-10-01; tunable)

```json
"locomotion": { "refStrideA": 0.9, "refCadence": 2.6, "cadenceScale": 1.9, "accelTimeSec": 0.10, "decelTimeSec": 0.10, "strideWarpMin": 0.6, "strideWarpMax": 1.8, "footPlantLockRadiusA": 0.05 },
"anticipation": { "leadTimeSec": { "jump": 0.35, "vault": 0.30, "climb": 0.40, "land": 0.25 }, "reachStartDistA": 1.2, "gazeLeadSec": 0.5, "maxConcurrentReaches": 2 },
"landingResponse": { "absorbTimeSec": 0.12, "recoverTimeSec": 0.22, "maxCrouchFraction": 0.35, "camDipA": 0.15, "softSurfaceExtra": 0.5, "controlLockSec": { "soft": 0.0, "roll": 0.15, "hard": 0.3 } }
```

Item #5 needs no `movement.json` change (normals derived at runtime from the collision mesh).
Item #6's optics (tilt-shift DoF + motion blur) are a URP `VolumeProfile`, not `movement.json`.
Item #6 also flips the existing `gravityScale` 0.8 → 0.9 (the more-miniature-real default, Owner
2026-10-01); that key already exists in `movement.json`, so it rides the same lockstep.

## Execution — the `movement.json` lockstep (Operator-gated; bundle with the pending #036)

The strict C# loader rejects unknown keys, so JSON and C# must land together. Do it in **one**
coordinated change, bundled with the still-unexecuted **#036** (intent/camera), so there is a single
C# migration:
1. Edit `config/movement.json` + `config/movement.schema.json` (`additionalProperties:false`, typed,
   required) + the `design/MOVEMENT_BIBLE.md` §10 JSON block **together** (byte-equal JSON —
   `check_movement_sync.py`).
2. `python .github/scripts/copy_movement_to_unity.py` (regenerate the byte-identical Unity copy).
3. `python services/traversal/movement.py --write-fixture` (regenerate the agreement fixture) and add
   the mirroring frozen dataclasses to `services/traversal/movement.py`.
4. Add `LocomotionSection` / `AnticipationSection` / `LandingResponseSection` to `MovementConfig.cs`;
   point the stride-warp, anticipation, and landing systems at them. `MovementConfigFixtureTests`
   keeps C#↔Python honest.
5. Apply the Bible §2/§3/§5/§8 prose edits + the DESIGN_SYSTEM camera note in the same change.

## Buildable now (no protected path — this session)

- `services/traversal/anticipation.py` (+ CLI) — reference anticipation planner (#2).
- `services/traversal/locomotion_ref.py` — `stride_scale` (#1), `landing_response` (#3),
  `cadence_for_scale` (#6) reference math; the C# agreement contracts.
- Tests for both; a `MOVEMENT_RUNTIME_CONTRACT.md` capturing the §2 C# CONTRACTs.
- Tickets M1-MOVE-03..08 + RES-MOVE-01.
