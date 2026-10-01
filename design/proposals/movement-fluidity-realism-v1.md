# Movement fluidity & realism — v1 enhancement pack

**Proposal · 2026-09-30 · Builder/Coordinator (AUTH #027) · requests AUTH #043**

Owner directive (this session): *"Proceed to spec+build"* items #1, #2, #3, #5, #6 from the
fluidity/realism discussion, and *"Plan and spec #8 for now"* (learned/physics motion — a v2
candidate if it adds significant v1 cost).

This proposal specs the whole pack, splits it into **Brain A** (the Unity/C# runtime controller)
and **Brain B** (the deterministic Python analysis in `services/traversal/`), and marks exactly
what needs the Owner's `APPROVED #043`. It follows the discipline used all milestone: **build and
test the deterministic Python halves here; spec + reference-validate the C# halves for
gj-gameplay/the Operator (I cannot validate C# in this environment); touch no frozen v1.0.0 schema;
gate every merge on green CI.**

---

## 0. What this changes (at a glance)

| # | Enhancement | Primary home | Brain B (I build now) | Brain A (Operator/gj-gameplay) | `movement.json`? |
|---|---|---|---|---|---|
| 1 | Stride/speed warping (kill foot-sliding) | Unity anim | stride-scale reference math + tests | stride-warp on the locomotion clips | **new `locomotion` block** |
| 2 | Anticipation from the traversal graph | split | **`anticipation.py` reference planner + tests** | procedural reach/lean/gaze layer | new `anticipation` block |
| 3 | Procedural weight — landing absorption + impact | Unity anim/cam | fall→tier→absorption reference + tests | absorption curve + camera dip | new `landingResponse` block |
| 5 | Normal-aware contact IK | Unity anim | (contract only; normals derived at runtime) | hand/foot IK conforms to surface normal | none |
| 6 | Miniature realism levers | split (feel + render) | scale-aware cadence reference + tests | cadence/accel + tilt-shift/DoF/motion-blur | new `locomotion`/`scale` keys; render = URP volume |
| 8 | Learned / physics-based motion | research | — (spike spec only) | — | none (v1); research track |

**AUTH-gated (needs `APPROVED #043`):** the `movement.json` additions (a **6-file lockstep** +
a C# `MovementConfig` migration — Operator-gated, see §3), the **locked Movement Bible** edits
(§2, §3, §5, §8, §10), and a **DESIGN_SYSTEM** camera note for the miniature look (§6). **Not
AUTH-gated:** the new Brain-B Python reference modules and their tests (new files, no protected
path, no schema change).

**Nothing here unfreezes a v1.0.0 schema (AUTH #037).** Anticipation and contact normals are
*derived at runtime / provided as reference*, never added to the frozen `traversal_graph` /
`environment_spec`.

---

## 1. Principles & constraints (why the design looks the way it does)

- **The goal is believability, not literal realism.** For a 1:12 character in a giant real room the
  target is **weight, flow, and aliveness**. Item #6 deliberately trades some literal realism for
  those cues; that is the point, and it's a tunable dial, not a fixed value.
- **Two brains must never disagree.** Brain A (runtime feel) and Brain B (offline reachability +
  journey) already share `config/movement.json` via a checksum handshake and the 0.85 reach margin.
  Every enhancement that adds a constant adds it to `movement.json` so both brains read the same
  number; where I compute a reference here, the C# must match it (agreement-fixture pattern,
  `services/traversal/tests/fixtures/movement_expected.json`).
- **Mobile budget is the hard limit (Bible §2).** Reference device 30 fps floor; animation + IK +
  warping ≤ **4 ms/frame**; motion DB ≤ **60 MB**; ≤ 2 IK chains beyond feet. Per AUTH #003 these
  are **targets measured on the Owner's iPhones, never merge gates** — but they bound the design.
  Every item below carries a cost estimate against this budget.
- **Freeze discipline (AUTH #037).** The three environment schemas are frozen v1.0.0. This pack adds
  **no fields** to them. Anything "new data" is either derived at runtime by Brain A from the
  existing `traversal_graph`/collision mesh, or produced by a **new, separate** Brain-B reference
  module (not a stored package asset — the `environment_spec` assets block is frozen too).
- **`movement.json` is a lockstep, and its C# side is Operator-gated.** See §3. This is why the
  tuning changes here are *specced and authorized now but executed with the C# migration*, exactly
  as AUTH #036 (intent/camera) is already handled.

---

## 2. The build items

Each item: **what**, **why it helps here**, **A/B split**, **params**, **C# CONTRACT**, **cost**,
**acceptance**.

### #1 — Stride / speed warping (kill all foot-sliding)

**What.** Continuously scale the playing locomotion clip's stride length and playback so foot-plant
timing matches the avatar's *actual* ground speed every frame — on flats, slopes, accel/decel, and
turns. Distinct from the already-planned *motion warping* (which aligns hands/feet to a contact
edge); this is warping the *cyclic* locomotion itself.

**Why here.** Foot-sliding is the #1 "cheap/floaty" tell. On procedurally-generated routes the
avatar is constantly changing speed (edge-aware slowdown, accel out of a mantle), so a fixed run
cycle *will* slide without this. Highest realism-per-byte on the list.

**A/B split.** ~100% Brain A (Unity animation). Brain B contributes the **reference formula** and
test vectors so the feel matches the validator's assumptions about locomotion speed.

**Params (`movement.json` → new `locomotion` block, §3).** `refStrideA` (stride length the base
clips were authored at, in A-units), `strideWarpMin`/`strideWarpMax` (clamp on the warp ratio so an
extreme speed doesn't distort the pose), `footPlantLockRadiusA` (IK lock radius so a planted foot
never drifts).

**C# CONTRACT.** Each frame: `strideScale = clamp(groundSpeed / (refCadence · refStrideA),
strideWarpMin, strideWarpMax)`; drive clip time by `strideScale`; lock each planted foot with foot
IK inside `footPlantLockRadiusA` until toe-off. On slopes, project stride onto the surface plane.
Reference: `services/traversal/locomotion_ref.py::stride_scale(...)` (this pack).

**Cost.** Negligible CPU (one scalar + existing foot IK). No DB growth.

**Acceptance.** AT: over 60 s of scripted variable-speed play on a corpus room, measured foot-slip
≤ a small threshold at every speed (Operator, on-device/EditMode). Brain-B unit tests pin
`stride_scale` monotonic in speed and clamped.

### #2 — Anticipation driven by the traversal graph

**What.** The avatar *telegraphs* the next move: begins reaching a hand toward the next hold, leans
into the next gap, plants the lead foot, and shifts gaze to the landing — **before** contact. This
is what makes AC/Uncharted traversal read as fluid ("the character knows where it's going").

**Why here — our unfair advantage.** Brain B already computes the whole route graph, so it knows the
*next* 1–2 edges and their contact geometry. We can feed that forward instead of reacting frame-by-
frame. No other traversal game gets this for free.

**A/B split.** Brain B **builds the reference planner now** (`services/traversal/anticipation.py`):
given a `traversal_graph` + a selected route, emit per-edge **anticipation hints**:
- `from`/`to` node, `verb`, `contact_point` (A-space, from the target node + surface),
- `reach_target` (+ surface `normal`) for pre-reach hand IK,
- `look_at` (gaze target: the landing / next edge / summit),
- `lead_time_s` (how early to start, from edge distance ÷ entry speed + a per-verb constant),
- `plant_foot` (lead foot for vault/jump/mantle).

Brain A consumes these (recompute at runtime from the graph, or read the reference) to drive a thin
**procedural anticipation layer** on top of animation: pre-reach, spine lean, gaze, foot choice.

**Freeze-safe.** Emitted as a **derived reference**, not stored in the frozen package (mirrors
`reach.py`, which validates rather than persists). If we later decide to *bake* hints into the
package we'd freeze a new companion schema under its own AUTH — out of scope here.

**Params (`movement.json` → new `anticipation` block).** `leadTimeSec` per category
(jump/vault/climb/land), `reachStartDistA`, `gazeLeadSec`, `maxConcurrentReaches` (≤ the 2-IK
budget).

**C# CONTRACT.** For the active route, look ahead within `leadTimeSec`; when within
`reachStartDistA` of a `to` with a hand contact, blend a pre-reach IK pose toward `reach_target`
oriented to `normal`; bias gaze to `look_at` `gazeLeadSec` ahead; select `plant_foot`. Never exceed
`maxConcurrentReaches`.

**Cost.** Brain A: one look-ahead query + up to 2 IK chains (already budgeted). Brain B: offline,
free.

**Acceptance.** Brain-B: deterministic hints on the desk-tabletop fixture, unit-tested (lead-time
monotonic in distance, reach target on the correct surface, gaze targets valid nodes, hints only for
edges in the route). Brain A: visible pre-reach/gaze on 20 test edges (Operator).

### #3 — Procedural weight — landing absorption + impact response

**What.** Replace fixed landing clips with a **continuous absorption**: on ground contact, compress
(knee/hip bend + torso dip) and recover over a short window scaled by fall height and surface class,
with a matching **camera dip** and a brief control-recovery beat. Extends the existing landing tiers
(`landing.soft`/`roll`/`hard`).

**Why here.** Weight is the strongest believability cue there is; "you feel the landing" is the line
between grounded and balloon-like — and it pairs with the miniature read (#6).

**A/B split.** Mostly Brain A. Brain B owns the **mapping** fall-height → tier → absorption amount
(it already computes fall heights and landing tiers in `reach.py`), as reference + tests.

**Params (`movement.json` → new `landingResponse` block).** `absorbTimeSec`, `recoverTimeSec`,
`maxCrouchFraction` (max compression as a fraction of avatar height), `camDipA` (camera dip
distance), `softSurfaceExtra` (extra give on `walkable-soft`), and the control-lock window
`controlLockSec` per tier (soft/roll/hard). Absorption scales with the landing tier already in
`landing`.

**C# CONTRACT.** On land, read the tier from fall height (`landing` thresholds); compress by
`min(maxCrouchFraction, k·tier)` over `absorbTimeSec`, recover over `recoverTimeSec`; dip the camera
by `camDipA·tier`; hold full control for `controlLockSec[tier]`. Soft surfaces add
`softSurfaceExtra` and suppress the hard-landing stumble. Reference:
`services/traversal/locomotion_ref.py::landing_response(fall_A, surface_class, cfg)`.

**Cost.** Negligible CPU (procedural pose offset + camera lerp). No DB growth.

**Acceptance.** Brain-B: reference returns rising absorption with fall height, extra give on soft,
correct tier boundaries — unit-tested. Brain A: falls of 1/3/5 A read as soft/roll/hard with
distinct weight (Operator).

### #5 — Normal-aware contact IK

**What.** Hand/foot IK conforms to the **orientation** of the real scanned surface at the contact
point (aligns to the surface normal), not just its position — so a grab on your bookshelf sits flat
against the shelf's face, a foot on a tilted book plants along the slope.

**Why here.** Every surface is real, arbitrary geometry; position-only IK looks pasted-on. Cheap,
high fidelity.

**A/B split.** ~100% Brain A. **Normals are derived at runtime** (raycast against the collision
mesh at the contact point) — **no schema change, no `movement.json` change.** Brain B contributes
the `normal` field in #2's anticipation hints (from the surface it already knows) as a hint/fast
path.

**C# CONTRACT.** At a contact, raycast the collision mesh at `contact_point`; orient the effector to
the hit `normal` (clamped to a max wrist/ankle deviation so it never breaks the pose); position via
existing IK. Prefer the anticipation-hint `normal` when present to avoid a cast.

**Cost.** ≤ 1 short raycast per active contact; within budget. No DB growth.

**Acceptance.** Hand/foot alignment on a flat, a tilted, and a curved test surface (Operator).

### #6 — Miniature realism levers (the identity dial)

**What.** The cues that sell "tiny, real, weighty": **higher step cadence**, **snappier
accelerations**, a **tilt-shift / depth-of-field "miniature" camera look**, and **scale-aware motion
blur**.

**Why here — and the one real decision.** Physics scales with size: a pendulum/step period ∝ √L, so
a true 1:12 body would step **√12 ≈ 3.5×** faster than a human — comedic at the extreme. The tasteful
move is a **partial** scaling plus the camera optics that trigger the brain's "this is a miniature"
response (tilt-shift is literally why toy-world photos read as toys). **Gravity already scales**
(`gravity = 9.81 · (1/scale) · 0.8`; the `0.8` is the fantasy-float knob), so we can gain the
miniature read from cadence/accel/optics **without** giving up the giant-fantasy float. This is a
reversible tuning dial — I propose defaults and two variants for the Operator to A/B on device.

**A/B split.**
- *Feel* (Brain A + `movement.json`): `locomotion.cadenceScale` (step-rate multiplier),
  `locomotion.accelTimeSec` / `decelTimeSec` (time-to-speed — snappier), reusing the `locomotion`
  block from #1. Brain B owns a scale-aware cadence reference (cadence ∝ 1/√scale, bounded).
- *Render* (Brain A, **not** `movement.json`): a URP post-process **"miniature" volume** — tilt-shift
  via depth-of-field with a narrow focus band at the avatar's height, and **scale-aware motion blur**
  (shutter tuned to the faster small-scale motion). Referenced from Bible §8 + a DESIGN_SYSTEM camera
  note; it's rendering config, so it lives in a Unity volume profile, not the movement contract.

**Proposed values (tunable; the identity dial).**

| Lever | "More miniature-real" (default, Owner 2026-10-01) | "Keep the fantasy" (variant) |
|---|---|---|
| `gravityScale` | 0.9 | 0.8 |
| `locomotion.cadenceScale` | 1.9 | 1.5 |
| `locomotion.accelTimeSec` | 0.10 | 0.14 |
| DoF / tilt-shift strength | pronounced | subtle |
| motion-blur amount | medium | low |

**Owner decision (2026-10-01): ship "more miniature-real" as the v1 default.** Keep-the-fantasy
ships as the one-line variant swap, and the Operator still A/Bs both on a real device to confirm the
device-perf tier that enables the optics. Full √12 cadence remains documented as the "max realism"
end, not proposed.

**C# CONTRACT.** Cadence drives the stride-warp `refCadence` (ties into #1); accel/decel replace any
hard-coded locomotion smoothing; the miniature volume is a URP `VolumeProfile` toggled per camera
with focus tracked to the avatar. Reference: `locomotion_ref.py::cadence_for_scale(scale, cfg)`.

**Cost.** Cadence/accel: free. DoF + motion blur: **mobile-sensitive** — these are the only items
here with real GPU cost. Spec: half-res/mobile DoF, motion blur capped, both **auto-tiered off on
low-end devices** (AUTH #003 quality tiers). This is the item to watch on-device.

**Acceptance.** Two profiles selectable; on-device the "miniature" read is present without dropping
below the fps floor on the quality tier that enables it (Operator).

---

## 3. `movement.json` additions — the lockstep (Operator-gated)

Any `movement.json` change is a **6-file lockstep** plus a **C# `MovementConfig` migration**, and the
**strict C# loader rejects unknown keys** — so the JSON and the C# must land *together* or the Unity
build breaks. This is identical to **AUTH #036** (intent/camera), which is **still pending
execution**. Therefore these additions are **authorized under #043 now but executed by the Operator
in one coordinated change**, ideally **bundled with the pending #036 migration** so there is a single
C# migration, not three.

The lockstep (all must move together, byte-consistent where required):
1. `config/movement.json` — add the blocks below.
2. `config/movement.schema.json` — add matching definitions (`additionalProperties:false`, typed, required).
3. `design/MOVEMENT_BIBLE.md` §10 JSON block — **byte-equal** to `config/movement.json` (the `movement-sync` gate enforces this).
4. `services/traversal/movement.py` — add the mirroring frozen dataclasses (strict loader).
5. `services/traversal/tests/fixtures/movement_expected.json` — regenerate via `python services/traversal/movement.py --write-fixture`.
6. `unity/Assets/StreamingAssets/movement.json` — byte-identical copy (gate-enforced).
7. **C# `MovementConfig`** (+ any consumers) — new fields; Operator/Unity, validated by `MovementConfigFixtureTests`.

Proposed new blocks (values are the "more miniature-real" defaults from §2, Owner 2026-10-01; all tunable):

```jsonc
"locomotion": {                 // #1, #6
  "refStrideA": 0.9,            // stride length the base run clip was authored at (A)
  "refCadence": 2.6,            // base step rate (steps/s) before cadenceScale
  "cadenceScale": 1.9,          // #6 miniature step-rate multiplier (more-real default)
  "accelTimeSec": 0.10,         // #6 time to reach target speed (snappier)
  "decelTimeSec": 0.10,
  "strideWarpMin": 0.6,         // #1 clamp on stride-scale
  "strideWarpMax": 1.8,
  "footPlantLockRadiusA": 0.05  // #1 planted-foot IK lock
},
"anticipation": {               // #2
  "leadTimeSec": { "jump": 0.35, "vault": 0.30, "climb": 0.40, "land": 0.25 },
  "reachStartDistA": 1.2,
  "gazeLeadSec": 0.5,
  "maxConcurrentReaches": 2     // ≤ the 2-IK-chain budget
},
"landingResponse": {            // #3
  "absorbTimeSec": 0.12,
  "recoverTimeSec": 0.22,
  "maxCrouchFraction": 0.35,
  "camDipA": 0.15,
  "softSurfaceExtra": 0.5,
  "controlLockSec": { "soft": 0.0, "roll": 0.15, "hard": 0.3 }
}
```

(Item #5 needs **no** `movement.json` change; #6's optics are a URP volume, not `movement.json`.)

---

## 4. #8 — Learned / physics-based motion (plan + spec; v1-vs-v2)

Two frontier directions, planned now, **recommended as a v2-targeted research spike**, not v1 code.

**8a — Learned motion matching / neural motion synthesis.** Compress the motion DB and *generalize*
transitions we never captured (Learned Motion Matching, Holden et al.; motion VAEs; phase/diffusion
motion models). This is where "analyze motion → usable motion" becomes real. **v1 cost if adopted
now:** high — new training pipeline, on-device inference budget risk, and it would move the already-
planned classic motion-matching spike (M1-MOVE-01, Bible §13). **Recommendation:** research spike
only; keep v1 on classic motion matching.

**8b — Physics-based / RL controllers (DeepMimic-style).** A controller that *figures out* how to
traverse your specific desk — the holy grail for procedural levels. **v1 cost if adopted now:** very
high — RL training infra, hard real-time mobile story (you'd distill/bake), significant schedule
risk. **Recommendation:** research north-star; not v1.

**Proposed spike (fits the existing Tier-2 research line — AUTH #040, $500/mo already approved; GPU
via #039 RunPod).** Ticket `M2-RES-01` (area `RES`, owner gj-operator), **deferred — created
when the spike is scheduled**:
- Reproduce a learned-motion-matching baseline on our ~110-clip whitelist; measure DB size vs classic
  and transition quality.
- Prototype one physics-tracked verb (e.g., mantle) in sim; assess adaptivity to novel edges.
- **Deliverable:** a go/no-go memo with a mobile-inference cost estimate and a v2 recommendation.
- **Gate:** touches no v1 code path; v1 ships classic motion matching regardless.

**Net:** #8 stays out of the v1 critical path and its cost; the spike de-risks it for v2 on budget
that already exists. If the Owner wants #8 *in v1*, that's a separate scope+cost decision.

---

## 5. What I build & test in this environment now (Brain B)

New files, no protected path, no schema change — buildable and CI-testable here:

- **`services/traversal/anticipation.py`** (#2) — the reference anticipation planner + a small CLI,
  consuming a frozen `traversal_graph` + a route from `journey.py`. Deterministic; stdlib-only.
- **`services/traversal/locomotion_ref.py`** (#1, #3, #6) — pure reference functions:
  `stride_scale`, `landing_response`, `cadence_for_scale`. These are the C# agreement contracts;
  they read the proposed constants (defaulted here until the `movement.json` lockstep lands).
- **`services/traversal/tests/test_anticipation.py`**, **`test_locomotion_ref.py`** — unit tests
  (determinism, monotonicity, clamps, tier boundaries, hints-only-on-route).
- **`services/packages/CONTRACT.md`** and/or a new **`services/traversal/MOVEMENT_RUNTIME_CONTRACT.md`**
  — the C# CONTRACTs from §2, so gj-gameplay implements against a written spec (the M1-GAME-01
  pattern).

These give the Operator exact, tested reference behavior to match, and prove the Brain-B logic before
any Unity work.

---

## 6. Locked-doc edits required (under AUTH #043)

- **`design/MOVEMENT_BIBLE.md`** (locked; §3/§5/§10 are the "change-together-under-AUTH" set):
  - **§2 Architecture** — add stride-warp to the Animation-selection row; add an **Anticipation**
    sub-layer (Intent already predicts 0.6 s — extend it to graph-fed pre-reach/gaze); note
    normal-aware contact IK in the Procedural row.
  - **§3** — feel notes: stride-warped locomotion; anticipation telegraphing; cadence/accel for scale.
  - **§5** — procedural landing absorption + camera dip (extends the fall/landing tiers).
  - **§8 Camera** — landing camera dip; the **miniature look** (tilt-shift DoF + scale-aware motion
    blur), auto-tiered.
  - **§10** — the new `movement.json` blocks (with #036; byte-equal to the JSON — the lockstep).
  - **§16 Field notes** — an append recording AUTH #043 (the one edit path that needs no full re-lock).
- **`design/DESIGN_SYSTEM.md`** — a camera note referencing the miniature look for the play screen
  (consistent with §5/§8 orientation rules from AUTH #042). Small; cite as Refinement (AUTH #043).

The Bible/`movement.json`/DESIGN_SYSTEM edits are **applied with the Operator-coordinated C#
migration** (§3), keeping the doc internally consistent (no §3 key that isn't in §10/JSON yet).

## 7. Tickets

- **M1-MOVE-03** (gj-gameplay) — Stride/speed warping (#1). Dep: M1-MOVE-01 (anim stack), `locomotion` block.
- **M1-MOVE-04** (gj-gameplay) — Anticipation layer (#2), consuming `anticipation.py`. Dep: M1-SCEN-04, M1-MOVE-01.
- **M1-MOVE-05** (gj-gameplay) — Procedural landing/weight + camera dip (#3). Dep: M1-MOVE-01.
- **M1-MOVE-06** (gj-gameplay) — Normal-aware contact IK (#5). Dep: M1-GAME-01 (collision mesh at runtime).
- **M1-MOVE-07** (gj-gameplay) — Miniature levers: cadence/accel + URP miniature volume (#6). Dep: #1.
- **M1-MOVE-08** (claude-builder) — Brain-B reference: `anticipation.py` + `locomotion_ref.py` + tests + CONTRACT (this pack builds it).
- **M2-RES-01** (gj-operator) — Learned/physics motion spike (#8), Tier-2 (AUTH #040/#039). v2-targeted; **deferred, not created yet** (created when the spike is scheduled).

(Exact IDs/fields validated against `tickets/SCHEMA.json` when created.)

## 8. Risk, budget, rollback

- **Mobile budget:** #1/#2/#3/#5 are procedural/scalar or ≤2 IK chains — comfortably inside the
  4 ms/60 MB budget, no DB growth. **#6 optics (DoF + motion blur) are the only GPU-cost items** —
  spec'd half-res/capped and auto-tiered off on low-end devices.
- **Reversibility:** every feel value is a `movement.json` constant (revert = edit a number);
  every layer sits on top of the existing controller behind a flag (revert = disable the layer);
  the identity dial is two profiles. Nothing is one-way.
- **Freeze/lockstep safety:** no v1.0.0 schema field added; the `movement.json` change lands as one
  Operator-coordinated migration (bundled with #036) so the strict C# loader never sees a half-applied
  contract.
- **Capability boundary (honest):** I cannot build/validate C# here. Brain B (this pack) is built and
  tested here; Brain A is specced with written CONTRACTs + tested reference vectors for
  gj-gameplay/the Operator, validated in Unity — the same split used for M1-GAME-01.

## 9. AUTH request — #043

Requesting the Owner's `APPROVED #043` for **movement fluidity & realism v1 (items #1, #2, #3, #5,
#6; #8 as a v2-targeted research spike)**, specifically authorizing:
1. The **`movement.json` additions** in §3 (`locomotion`, `anticipation`, `landingResponse`) and the
   matching **6-file lockstep + C# `MovementConfig` migration**, executed by the Operator (bundled
   with the pending #036).
2. The **Movement Bible** edits in §6 (§2, §3, §5, §8, §10, §16) and the **DESIGN_SYSTEM** camera note.
3. The new **Brain-B reference modules** + tickets in §5/§7 (no protected path; buildable now).

Type: design-change (`config/movement.json` + `movement.schema.json` + Bible §3/§5/§8/§10 +
`design/DESIGN_SYSTEM.md`). Cost: **$0** (all free-tier/procedural; #8 spike on the existing Tier-2
line, no new spend). Reversible: yes.
