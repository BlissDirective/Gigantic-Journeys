# Proposal — Movement v1 expansion: the full parkour discipline + traversal tools

**Status: PROPOSAL for Owner review · 2026-09-18 · Coordinator.** Rationale doc (not a decision). Adopting any of this is a design-change + milestone-plan **AUTH** touching `SPEC.md` §3.5/§4, the locked `MOVEMENT_BIBLE.md` §3/§4/§10/§14, and `config/movement.json`. Grounded in Movement Bible v1.0 §0 intent: *a real person, 15 cm tall, parkouring through a real place, with the weight and hesitation of a real body and the responsiveness of a great platformer.*

## 0. Intent
The Owner wants v1 movement **as great and expansive as possible**, understands "parkour" as the full discipline (run, jump, vault, roll, climb, swing, precise efficient traversal), and wants a **minimal set of "found real object" tools** starting with a safety-pin grapple. This proposal (a) shows how much parkour is already in the v1 design, (b) proposes verb additions, (c) fully designs the grapple tool + lists other tool candidates, and (d) names the exact governance changes and a low-risk sequencing.

## 1. The v1 parkour vocabulary is already vast

Parkour *is* the v1 movement design. Mapping the discipline to what the Bible already specifies for v1:

| Parkour element | Already in v1 (Bible §) |
|---|---|
| Running / efficient locomotion | idle, walk, jog, run, **sprint**, plant-turn, edge balance-walk, crouch/low-crawl (§3.1) |
| Vaulting | **hop-over, vault, mantle** (§3.2) — the vault family |
| Jumping / precision | standing, running, **precision**, ledge-to-ledge, wall-push, **coyote time + jump buffer** (§3.3) |
| Rolling / landings | controlled drop, hang-and-drop, **slide**, fall, 4 landing tiers incl. **roll** (§3.4, §5) |
| Climbing | ledge hang+**shimmy**, rung, **stud (signature tabletop)**, textured free-climb, **pole**, overhang traverse, slips/catches (§6) |
| Reads-as-real body | motion matching + inertialization, motion warping to real edges, foot/hand IK, reactive idle, weight/hesitation (§2, §7) |
| Platformer forgiveness | coyote 100 ms, jump-buffer 120 ms, ledge auto-catch 0.15A, Assist mode (§3.3, §10) |

That is ~30 distinct verbs and 5 procedural climb families, tuned in A-units so they survive scale. **The v1 core is already a world-class parkour set.** Two things the Owner's list adds that are *not* yet there: **swinging** (grapple — currently a §14 V2 hook) and an explicit **dive**.

## 2. Proposed verb additions (make it even more expansive)

All map to cheap Mixamo/warped clips on the existing architecture; each is an additive verb, not a rewrite.

| Add | What | Cost | Rec |
|---|---|---|---|
| **Dive / dive-roll** | A committed forward dive that chains into a roll on landing (Owner asked "dive"). Great momentum expression off ledges and at speed. | 1 warped clip; feeds the roll tier | **v1** |
| **Tic-tac** | Kick off a `wall-smooth`/vertical to redirect or gain height mid-move — a signature parkour move; extends wall-push. | wall-jump variant + warp | **v1** |
| **Vault variants** | Kong/dash vault, speed vault, underbar (duck-through a gap under a rail) — makes vaulting expressive rather than one animation. | Mixamo vault family | **v1 (polish)** |
| **Wall-run** | Short run across a suitable flat vertical (`wall-smooth`/`textured-vertical` run of ≥ ~3A). **Currently an explicit v1 non-goal** (SPEC §3.5, §4; Bible §3.3/§14) because it is hard to make read on arbitrary real geometry. | bespoke; needs a valid wall segment | **AUTH stretch** — pilot gated on the M1 spike, not a launch blocker |

## 3. Traversal tools — the "found real objects at 1:1" layer

### 3.1 The conceit, and reconciling it with "no synthetic game objects"
The tiny character finds **real, 1:1-scale objects** in the captured scene and uses them as gear. This is a beautiful idea *and* it's diegetic — the objects are real-world items rendered PBR-matched to the scene, not fantasy game props. But a rendered safety pin **is** a non-photo object, and SPEC §4's "**no synthetic game objects**" is a core purity rule. So tools require a **narrow, explicit §4 exception**:

> **Character traversal tools** — real-world objects the avatar *carries and uses* as gear (grapple, pole, etc.), rendered at true 1:1 scale and lighting-matched — are permitted as the **sole exception** to "no synthetic game objects." This does **not** admit placed game objects (coins, platforms, enemies, tokens, markers-as-objects). Tools are the avatar's equipment, in the same category as the avatar itself (the only authored solid).

Recommend adopting exactly that exception — it keeps the "your real place, untouched" magic while allowing the character's gear.

### 3.2 Tool 1 — Safety pin + twine (grapple) [Owner's pick]
Architecturally clean: registers through `IVerbProvider` (Bible §14, ADR-0004) — **adds verbs without touching the core**. Reuses the hang family, a pendulum solver, hand IK, and motion warping.

**Three modes (each a verb), per the Owner's spec:**
- **Swing** (`grapple-swing`): aim at a valid anchor ahead/above within `grapple.reachA`; the character presses the pin into the anchor object/ledge; a **momentum-preserving pendulum** swing (hang pose + look-at the landing); on arrival the pin **auto-unhooks**, and the character **reels in and coils** the twine to their back. Opens: crossing voids/gaps, arcing up to higher ledges.
- **Ascend / throw-up** (`grapple-climb`): throw the pin to a designated **top target** (a shelf lip, a chair seat from the floor); the twine goes taut; the character **climbs the twine hand-over-hand**; at the top the pin **unmounts** (appears stuck in the target), then reel + coil. Opens: smooth/blocked verticals, heights beyond climb range.
- **Rappel** (`grapple-rappel`): press the pin into a ledge/overhang edge; **controlled descent** down the twine; at the base the pin **auto-unhooks**, then reel + coil. Opens: safe descent of tall drops and overhangs.

**The seamless tool state machine** (the detail that sells it):
`Stowed (coiled on back)` → `Aim (valid anchors highlight)` → `Deploy (mount/throw; pin sticks diegetically)` → `Active verb (swing/ascend/rappel)` → `Release (auto-unhook on arrival)` → `Reel (twine retracts)` → `Coil (straps to back)` → `Stowed`. Each transition gets feel via the §9 feedback matrix (new materials: **metal pin** = a satisfying *thunk* on mount, a metallic *ting*; **fiber twine** = taut-line creak, a *zip* on reel).

**UX / controls:** a contextual aim mode consistent with the two-thumb layout (Bible §8, SPEC §3.5): hold the tool button → the traversal query highlights valid anchors in range → point/drag → release to commit. Recommend a **dedicated small tool button that appears only when an anchor is in range** (keeps "one contextual action, never two options at once").

**New `movement.json` block** (`grapple`): `reachA` (≈6A), `swingSpeed`, `swingMaxArcDeg`, `ascendSpeed`, `rappelSpeed`, `deployTime`, `reelTime`, `anchorMinLedgeA`, `snapAssistA`. Shared with the validator so the reachability graph includes grapple transitions.

**Journey-generation impact (large, and good):** the grapple **massively expands the reachable graph** — voids become crossable, `wall-smooth` becomes passable via an anchor above it (this is the answer to the §4 matrix note "wall-smooth blocks climb, forces route search"), tall drops become safe rappels. The validator (Bible §10 contract) gains grapple transitions; the route generator can author **"grapple beats"** (a swing across a chasm as a route twist). Because the tool is always available in v1, it's a global capability the generator can rely on — which also makes many more captured environments fully playable.

### 3.3 Other "found object" tool candidates (Owner asked for unique ideas)
Each is a real 1:1 object mapping to an existing §14 V2 hook, reframed diegetically. Ranked by v1 value:

1. **Matchstick / toothpick — pole vault** (`vault-pole`): plant and vault over a gap or up a height. Very parkour, unique, cheap (one warped clip). **Strong v1 add.**
2. **Rubber band — launcher / trampoline** (spring): anchored between two points to fling across a gap or bounce up. Playful and unique; maps to §14 spring shoes.
3. **Feather — glider** (glide): slows falls and glides across gaps; maps to §14 glider; changes the fall tiers; delightful but adds air-control scope.
4. **Bobby pin / paperclip — piton** (grip): wedged into seams to make a temporary hold on `wall-smooth`; maps to §14 picks. Overlaps grapple-ascend, so lower priority if the grapple ships.
5. **Thread spool — zipline**: anchor twine high→low and ride down — better as a **4th grapple mode** than a separate tool.

**Recommendation:** v1 = **grapple (all three modes)**, optionally **+ the matchstick pole-vault** (highest unique-parkour value, lowest cost). Defer rubber-band / feather / piton / zipline to a fast-follow or V2 — each drops in later through the same `IVerbProvider` layer with **zero core risk**.

## 4. How it must feel (the quality bar)
Real-body weight + hesitation + great-platformer responsiveness. The Bible already nails the forgiveness layer (coyote, buffer, auto-catch, assist). For tools: the grapple must **preserve momentum** (a real pendulum and a satisfying release), the **mount/reel/coil must be tactile**, and **aiming must be forgiving** (generous anchor snap). References to hold the bar: Celeste (feel), Mirror's Edge (weight), AC Unity (parkour routing), Uncharted (ledge-grab forgiveness), and grapple feel from Just Cause / Zelda / Sekiro; tiny-world materiality from Astro Bot / Teardown.

## 5. Scope, sequencing, and the "no rush" advantage
- **Tools are additive** (`IVerbProvider`): validate the **core parkour** first (M1 spike, motion matching vs blend trees), then land the grapple as a verb layer — target **M3** (game loop) or a dedicated movement-quality milestone. No core rework.
- With no schedule pressure, **polish the core to world-class first**, then layer each tool as an isolated, low-risk addition.
- Recommend an explicit **"does it feel amazing" movement-quality gate**, judged by the Owner, distinct from the automated perf gate.

## 6. Governance — what adopting this changes (AUTH-gated)
A single design-change + milestone-plan AUTH would touch:
- **SPEC §3.5** (add traversal tools to the product), **§4** (adopt the narrow character-tools exception to "no synthetic objects"; remove grapple/pole-vault [and any others chosen] from the V2 non-goals; decide wall-run).
- **MOVEMENT_BIBLE §3** (new verbs: dive-roll, tic-tac, vault variants, grapple modes, pole-vault), **§4** (surface × tool matrix), **§10 / `config/movement.json`** (new constant blocks), **§14** (move the adopted tools from V2 hooks to v1; keep the rest V2). *Bible §4 requires an AUTH for §3/§5/§10 changes; movement.json is CI-checked against §10.*
- **New tickets** (movement): grapple verb layer + tool state machine; journey-gen grapple beats; validator grapple transitions; the added verbs; the movement-quality gate.

## 7. Decisions needed before editing the protected docs
1. **Verb adds for v1:** dive-roll, tic-tac, vault variants (recommended yes); **wall-run** (currently excluded — promote as an AUTH stretch gated on the spike, or keep V2?).
2. **Tool set for v1:** grapple only, or **grapple + matchstick pole-vault** (recommended), or a wider set.
3. **Confirm the §4 exception** for diegetic, character-carried tools (required for any tool to exist).

On your answers I'll file the AUTH, update SPEC §3.5/§4, the Bible, and `movement.json`, and write the movement tickets.
