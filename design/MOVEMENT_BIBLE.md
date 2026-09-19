# Gigantic Journeys — Movement Bible

`/design/MOVEMENT_BIBLE.md` · v1.0 · September 14, 2026 · Owner: BlissDirective
Authority: second only to `SPEC.md`. Owned by `gj-gameplay`; `gj-scenegraph` consumes Sections 3–5 and 10 for the traversal validator. Changes to Sections 3, 5, or 10 require an AUTH REQUEST (design-change).

**Spend lock (AUTH #001, approved as amended Sept 14):** free-tier pipeline plus Motion Warping: Climb & Interact ($19.99). Ultimate Traversal Anims, traceur capture via Move.ai, MxM commercial license, and any suit are deferred to V2 pending v1 results.

---

## 0. Why this document exists

In Gigantic Journeys the world is captured and the goals are generated. The avatar's body is the only thing we author, so the fluidity, weight, and responsiveness of movement is the production value. Every clip, constant, and rule that shapes how the avatar moves lives here. If a behavior isn't in the Bible, it isn't in the game.

Design intent in one line: **a real person, 15 cm tall, parkouring through a real place, with the weight and hesitation of a real body and the responsiveness of a great platformer.**

---

## 1. Units and scale

- **A = one avatar height.** Default avatar is 1.75 m real → 14.6 cm in-world at 1:12. All trigger thresholds are in A so they survive the per-environment scale multiplier and body-height variation from the parametric fit.
- Real-object examples at 1:12 (adult avatar): coffee table lip 0.45 m → **3.1A**; couch seat 0.45 m → **3.1A**; couch arm 0.65 m → **4.5A**; dining chair seat 0.46 m → **3.2A**; chair crossbar spacing 0.15 m → **1.0A**; book spine step 0.02 m → **0.14A**; Lego stud pitch 8 mm → **0.055A**, Lego brick height 9.6 mm → **0.066A**.
- Consequence: in a room the avatar mostly *climbs* (furniture is 3–5A); on a tabletop it mostly *runs, hops, and stud-climbs*. Both must feel native.
- Gravity is scaled so jump arcs read as human at the avatar's size: **g = 9.81 × (1/scale) × 0.8** (slightly floaty for readability; tunable, see Section 10).

---

## 2. Architecture

Five layers, bottom to top. Each is a separate Unity assembly so V2 tools can add verbs without touching the core.

| Layer | Responsibility | v1 implementation (free) | Fallback |
|---|---|---|---|
| **Intent** | Reads input (virtual stick, jump, contextual action, controller), predicts a trajectory 0.6 s ahead | Custom C# | — |
| **Traversal query** | Casts against the collision mesh and the traversal graph to find the best available verb for the current intent (Section 3 thresholds) | Custom C#, shares `movement.json` with the validator | — |
| **Animation selection** | Locomotion and transitions via motion matching; contact verbs via tagged clips | Open MIT motion matching (jlpm22) with inertialized blending; evaluate the community MxM fork in parallel | Blend trees + inertialization if the M1 spike misses budget |
| **Motion warping** | Stretches contact clips so hands and feet land exactly on the real edge | Kinemation Motion Warping: Climb & Interact | Root-motion scaling + IK |
| **Procedural** | Foot IK on uneven splat geometry, hand IK on holds, look-at (summit beam, vistas, ledges before a jump), spine lean, secondary motion, Tier 0 feedback triggers | Unity Animation Rigging + custom | — |

**Mobile budgets (reference device: 2023 mid-tier Android, 30 fps floor):**
- Motion database ≤ **60 MB** compressed on device (target 40). Achieved by 30 fps clip sampling, quaternion compression, and trimming Mixamo to the whitelist in Section 11.
- Animation + IK + warping CPU ≤ **4 ms/frame**. Motion matching search runs on a job every 3rd frame with inertialized blending covering the gap.
- Max 2 simultaneous IK chains beyond feet.

---

## 3. Verb taxonomy

Each verb: trigger geometry (in A), input, source, and the feel rule that makes it read. "Warp" = motion-warped contact clip. Verbs marked **P** are procedural in v1 (no bespoke clip).

### 3.1 Locomotion
| Verb | Trigger | Input | Source | Feel |
|---|---|---|---|---|
| Idle | no input 0.4 s | — | Mixamo idle + breathing | Weight shift every 4–7 s; environmental reactions after 6 s (Section 7) |
| Walk | stick < 40% | stick | Mixamo | Used near edges automatically (edge-aware slowdown) |
| Jog | stick 40–85% | stick | Mixamo | Default speed |
| Run | stick > 85% | stick | Mixamo | Lean into turns, slight camera pull-back |
| Sprint | run held 1.5 s or double-tap | stick | Mixamo | +25% speed, wider turn radius, longer jump; drains no stamina in v1 |
| Plant-turn / stop | input reversal or release | stick | Motion matching selects | Never slides on hard surfaces; slides 0.2A on smooth ones |
| Edge balance-walk | walkable width < 0.5A | auto | Mixamo balance/tightrope + arm IK | Arms out, speed capped at walk, stick deadzone widens |
| Crouch / low crawl | headroom < 1.1A | auto | Mixamo crouch walk | Auto-enters under shelves and overhangs |

### 3.2 Small verticals (each distinct; no airborne jump unless stated)
| Verb | Trigger (obstacle height h, depth d) | Input | Source | Feel |
|---|---|---|---|---|
| Step-up | h < 0.25A | none (auto) | Procedural foot IK | Never interrupts run |
| Hop-over | 0.25A ≤ h < 0.5A, d < 1A | none at jog+, or jump tap | Mixamo "jump over" family, warped | Feet clear, hands never touch, no air time beyond a step |
| Vault | 0.5A ≤ h < 0.9A, d < 1.5A | jump tap while moving toward | Mixamo vault, warped | One hand plants on the top surface; speed preserved; variants kong/dash, speed, underbar (AUTH #021) |
| Mantle | 0.9A ≤ h < 1.4A | move into + jump, or auto on contact at jog+ | Mixamo climb-up, warped | Two-hand pull, knee plant, 0.5 s; speed lost |
| Climb-up | h ≥ 1.4A | move into | enters climb state (Section 6) | — |

### 3.3 Jumps (committed air moves)
| Verb | Trigger | Input | Source | Feel |
|---|---|---|---|---|
| Standing jump | jump tap, speed < walk | jump | Mixamo | Height 1.1A, distance 1.2A |
| Running jump | jump tap at jog+ | jump | Mixamo running jump | Height 1.2A, distance 2.4A (sprint 3.0A) |
| Precision jump | jump released early over a target < 0.6A wide | jump (short press) | running jump, shortened arc | Arc damped 30%; look-at target |
| Ledge-to-ledge | from hang, jump toward a ledge within 1.5A | jump while hanging | Mixamo hang-hop, warped | Auto-catch if hands pass within 0.15A of the edge |
| Wall-push | jump while touching a wall, moving away | jump | Mixamo wall-jump-ish, warped | One rebound; may chain into wall-run or tic-tac (AUTH #021) |
| Wall-run (AUTH #021) | run into a flat vertical with ≥ 3A of run at run+ | auto on contact at run+ | Mixamo wall-run, warped | Short lateral/upward run ≤ 1.2 s, gravity dampened; exits to jump, mantle, or fall (`movement.json` `wallRun`) |
| Tic-tac (AUTH #021) | jump while touching a wall to redirect or gain height | jump | Mixamo wall-jump variant, warped | +0.8A height / +1.2A distance; one per wall (`movement.json` `ticTac`) |
| Coyote time | left an edge < 100 ms ago | jump | — | Jump still fires |
| Jump buffer | pressed jump < 120 ms before landing | jump | — | Fires on landing |

### 3.4 Descents and landings
See Section 5 for tiers.
| Verb | Trigger | Input | Source |
|---|---|---|---|
| Controlled drop | walk off edge, drop < 1.5A | stick over edge | Mixamo step-down / soft land |
| Hang-and-drop | crouch at edge or hold contextual action | action | Mixamo hanging idle → drop |
| Slide | incline 25–60°, speed ≥ jog | auto; action to slide on flat | Mixamo slide; procedural on soft surfaces |
| Dive / dive-roll (AUTH #021) | jump forward at jog+, or dive off a ledge | jump (forward) | Mixamo dive-roll, warped |
| Fall | airborne > 0.35 s | — | Mixamo falling idle |
| Land (4 tiers) | ground contact | — | Section 5 |

### 3.5 Contextual action (one button)
The right-thumb action button shows only when a verb is available: grab ledge, drop from hang, slide, sit on vista marker, plant flag. Never two options at once; the traversal query resolves priority: **plant flag > grab > drop > slide**.

---

### 3.6 Traversal tools (v1, AUTH #021 — the `IVerbProvider` layer)

Real, 1:1-scale objects the avatar **carries and uses** as gear, found diegetically in the captured scene. They are the sole SPEC §4 exception to "no synthetic game objects" (character-carried gear only; still no *placed* game objects). Each tool registers verbs through `IVerbProvider` (§2, §14) without touching the core. v1 adopts two:

**Safety pin + twine — grapple.** Aim at a valid anchor within `grapple.reachA` (≈6A); the traversal query highlights anchors (any `ledge`/`overhang`/`pole`/graspable object edge for swing & rappel; any reachable top surface for ascend). Three modes:
- *Swing* (`grapple-swing`): press the pin into the anchor; momentum-preserving pendulum (hang pose + look-at the landing); auto-unhook on arrival, reel + coil to the back.
- *Ascend* (`grapple-climb`): throw the pin to a top target; climb the twine hand-over-hand; unmount at the top (pin appears stuck), reel + coil. Makes `wall-smooth` passable via an anchor above.
- *Rappel* (`grapple-rappel`): press the pin into a ledge/overhang edge; controlled descent; auto-unhook at the base, reel + coil.

Tool state machine: `Stowed (coiled on back)` → `Aim` → `Deploy (mount/throw)` → `Verb` → `Release (auto-unhook)` → `Reel` → `Coil` → `Stowed`. Feedback (§9): metal pin *thunk*/*ting*, fiber twine creak/*zip*. Constants: `movement.json` `grapple`.

**Matchstick — pole-vault** (`vault-pole`): at jog+, plant the matchstick and vault over a gap (≤ `poleVault.maxGapA`) or up to a height (≤ `poleVault.maxHeightA`); the stick is left behind or reclaimed. Constants: `movement.json` `poleVault`.

Validator/journey impact: grapple and pole-vault add transitions to the reachability graph (§10 contract) — voids become crossable, smooth walls passable, tall drops safe — so the route generator may author "grapple beats." Both tools are always available in v1, so they are global capabilities the generator can rely on. Deferred tools (glider, piton/picks, rubber-band spring, rope/zipline) remain V2 (§14), added later through the same layer with no core change.

## 4. Surface class × verb matrix

Surface classes come from `gj-scenegraph`. This matrix is what "the environment is interactive" means in v1.

| Surface class | Real examples | Enabled verbs | Blocked | Notes |
|---|---|---|---|---|
| **walkable-hard** | wood floor, table top, tile | all locomotion, jumps, hard-surface slide | — | Loudest footsteps |
| **walkable-soft** | rug, cushion, bed | locomotion (−10% speed), soft landing bonus, no slide | sprint on deep-pile | Tier 1 dent on cushion/bed |
| **walkable-narrow** | shelf edge, chair back top, book stack edge | balance-walk, precision jump | run, sprint | Width < 0.5A |
| **ledge** | table lip, shelf front, book spine (≥ 0.1A) | grab, hang, shimmy, mantle, ledge-to-ledge | — | Hand IK to edge |
| **rung** | chair crossbars, shelf brackets, blinds slats, ladder-like spacing 0.6–1.2A | rung climb | — | Section 6.2 |
| **stud** | Lego surfaces, pegboard, grille | stud climb (P), stud walk | slide | Section 6.3 |
| **textured-vertical** | bookshelf face, woven fabric, wicker, curtain | free climb (P), stamina-free in v1 | — | Section 6.4 |
| **pole** | lamp stand, table leg, cable, curtain rod (Ø 0.2–0.8A) | pole climb (P), pole slide-down | — | Section 6.5 |
| **overhang** | underside of shelf/table with graspable edge | hang traverse | — | Section 6.6 |
| **slope** | book ramp, cushion side, ramp 25–60° | slide, slope run (< 25°) | balance | Slide auto at speed |
| **wall-smooth** | painted wall, glass, cabinet door | wall-push, wall-run (≥ 3A), grapple-ascend | climb | Passable via a grapple anchor above or a wall-run; else forces route search (AUTH #021) |
| **soft-hanging** | curtain, plant fronds, paper, cord | brush-through (Tier 1 sway), grab if rope-like | stand | Never load-bearing |
| **void** | gaps to floor, off-table edge | fall | — | Off-table fall on tabletop = respawn |
| **hazard-none** | — | — | — | v1 has no damage; falls cost time only |

---

## 5. Fall and landing tiers

Fall height measured from launch or leave-edge point to contact.

| Tier | Height | Result | Clip | Feel |
|---|---|---|---|---|
| Soft | < 1.5A | continue moving | Mixamo soft land | Knees dip, no speed loss |
| Roll | 1.5–3.0A **and** moving forward | roll, keep 60% speed | Mixamo fall-to-roll | Hold forward to roll; neutral stick = hard land instead |
| Hard | 3.0–5.0A, or roll declined | stagger 0.6 s, speed to zero | Mixamo hard landing | Camera shake, dust burst, heavy haptic |
| Recover | > 5.0A | ragdoll blend 0.4 s → get-up 1.2 s | Mixamo falling → get-up | Time penalty only; no damage in v1 |
| Soft-surface bonus | any tier onto walkable-soft | tier −1 | — | Cushions make you brave |

Off-table or into-void falls on tabletop environments respawn at the last stable surface after a 1.5 s fade.

---

## 6. Climb families

All climbs use hand IK on detected holds and motion warping on entry/exit clips. Stamina is not in v1; difficulty comes from route finding and precision, not endurance. Every climb family exposes the same three inputs: stick = move along holds, jump = leap to a hold/ledge within reach, action = drop.

### 6.1 Ledge hang and shimmy
Entry: jump toward a ledge or drop from above. Mixamo hanging idle, braced-hang shimmy left/right, climb-up. Corner turns at ledge ends (warped). Max shimmy speed 0.8A/s.

### 6.2 Rung climb
Entry: move into a `rung` surface. Hands and feet snap to detected rungs; Mixamo ladder climb retimed to the detected spacing (0.6–1.2A) via warping. Dismount top via mantle, bottom via drop. Chair legs with crossbars are the canonical case.

### 6.3 Stud climb (procedural)
Entry: move into `stud` vertical. No bespoke clip in v1: a two-beat procedural cycle places alternating hand/foot IK targets on the stud grid (pitch 0.055A, so holds are dense), body kept 0.15A off the wall, with the Mixamo braced-hang pose as the base. Speed 0.6A/s vertical, 0.8A/s lateral; can traverse under Lego overhangs one row deep. This is the signature tabletop verb; polish it before free climb.

### 6.4 Textured free climb (procedural)
Entry: move into `textured-vertical`. Same procedural cycle as stud climb with sparser, noisier holds sampled from mesh curvature; speed 0.4A/s; slips (Section 7) possible on `curtain`. Bookshelf faces use book spines as ledges first (Section 6.1) and free climb only between them.

### 6.5 Pole climb (procedural)
Entry: move into `pole`. Wrap pose (base: Mixamo braced hang, arms and legs IK'd around the cylinder), 0.5A/s up, slide-down on action with a fabric/wood squeal per material. Table legs are the canonical room case, lamp stands the tabletop one.

### 6.6 Overhang hang-traverse
Entry: from a ledge hang, stick toward the underside of a `overhang`. Hanging-idle pose with hand IK on the edge; 0.5A/s; drop on action; leap to ledge on jump.

### 6.7 Slips and catches
On `curtain`, wet-look surfaces, or when leaping to a hold at > 90% reach: 15% chance of a slip animation (Mixamo stumble/falling blend) with a 0.3 s catch window on the next hold below; catching costs speed, missing enters the fall tiers. Off by default in Assist mode.

---

## 7. Reactions and idle personality (locked: reactive)

Triggered by proximity and dwell, never blocking input; any input cancels within one frame with inertialized blend.

| Situation | After | Reaction | Source |
|---|---|---|---|
| Standing still | 6 s | Look around, weight shift; look-at nearest vista or summit beam | Mixamo idle variants + look-at |
| At an edge, drop > 3A below | 3 s | Peer over, toe forward, lean back | Owner capture (Rokoko Vision) |
| Next to `soft-hanging` | contact | Brush hand through (Tier 1 sway) | Owner capture |
| On walkable-soft (cushion) | 8 s | Sit, then lie back after 20 s | Owner capture |
| Below a ledge > 2A | 4 s | Look up, size it, half-reach | Owner capture |
| Summit within 5A | approach | Look-at beam, slight pace increase | look-at only |
| Vista reached | — | Hands on hips, slow head turn, photo mode opens | Owner capture |
| Flag planted | — | Plant, two-hand raise, small hop | Move.ai trial hero clip |
| Long fall survived | recover | Dust-off, shake head | Owner capture |
| Tabletop: on Lego | idle 6 s | Tap a stud with a toe, look at it | Owner capture |

Owner capture list (Rokoko Vision, single camera, plain wall, 10 takes each): peer-over, brush-through, sit-and-lie, look-up-and-reach, hands-on-hips, dust-off, stud-tap, wind-up crouch before a big jump. ~40 minutes total.

Move.ai iPhone trial (hero clips, up to trial limit): flag plant sequence, running jump with arms, hard landing stagger, roll.

Each reaction carries a matched sound and, where apt, a Tier 1 soft reaction (a brush-through sways the curtain; a cushion sit dents it) per §9 and SPEC §3.6 (AUTH #022).

---

## 8. Camera rules per verb

- Third person, follow distance 4A, height 1.6A, look-ahead 0.8A in travel direction; collision-aware with dither-fade on occluding real geometry within 1.5A of the lens.
- Run/sprint: distance +0.5A, slight FOV widen (+4°).
- Jump: no vertical follow for the first 0.2 s (arc readability), then catch up.
- Climb: camera swings behind the avatar's back facing the surface, distance 3A, pitch up 15°; shows holds above.
- Hang/overhang: pitch down 20° so the drop is visible.
- Fall: hold position, track avatar; snap-follow only on landing.
- Balance-walk: locks yaw to the edge direction ±20°.
- Manual: one-finger drag on the right half orbits; auto-recenters 2 s after release. Never fights the player mid-move.
- Summit beam and vista sparkle are always drawn on top with depth-fade so orientation is never lost.

---

## 9. Feedback matrix (Tier 0), material × event

Every contact answers with sound, particles, haptic, and (for big events) camera.

| Material | Footstep | Land soft / hard | Grab | Slide |
|---|---|---|---|---|
| wood | knock, low | thud / boom + dust | creak | squeak |
| tile/stone | click, bright | tap / crack + grit | scrape | screech |
| carpet/rug | muffled thump | puff / thump + fibers | rustle | shush |
| fabric/cushion | soft pat | poof / whump + lint (Tier 1 dent) | rustle | slow shush |
| Lego/plastic | click, hollow | clack / clatter | click | zip |
| paper/cardboard | crinkle | crunch | tear-ish | hiss |
| metal | ting | clang + spark | ring | screech |
| glass | tink | tap / crack (visual only) | squeak | skid |
| plant | leaf rustle | rustle + petal | rustle (Tier 1 sway) | — |
| curtain | — | — | swish (Tier 1 sway) | slide swish |

Haptics: light for footsteps (only at run+), medium for grabs and vaults, heavy for hard landings and flag plant. Camera shake only on hard/recover landings and flag plant. All feedback scales with the environment scale multiplier so Lego clicks stay tiny and floor booms stay big.

**Sound system (AUTH #022).** The matrix extends to every v1 verb and tool: the vault family, tic-tac, wall-run (continuous surface scrape), dive-roll, the climb families (per-hand/foot ticks), and the tools — grapple (pin mount *thunk*/*ting*, twine creak/whip, swing whoosh, reel zip, coil pat) and matchstick pole-vault (plant thunk + shaft flex). Rules: every event is **layered** (transient + body + tail), **round-robin with micro-pitch** randomization, **impact-scaled** in gain and brightness, and fired on the **same contact frames motion-warping targets**. Audio is **3D-spatialized** (listener just behind the avatar, biased to the camera) over a scale-appropriate **ambience bed**, mixed on category buses (movement / world / tools / UI / music) with sidechain **ducking** so a critical cue always reads. **Scale-aware acoustics:** a parametric reverb (RT60 / early reflections / damping) is computed from the reconstructed room's volume and average material absorption, so each captured place has its own acoustic. **Music is restrained** (ambient bed + sparse stings; the §3 transition theme). Everything — pitch, gain, reverb size, particle size, haptic strength — scales with the environment multiplier. Sourcing is CC0 / royalty-free or self-recorded foley (no encumbered audio).

---

## 10. Tuning constants — `movement.json`

Single source of truth for both the controller and the traversal validator. Values are initial; M1 telemetry tunes them.

```json
{
  "avatarHeightA": 1.0,
  "speeds": { "walk": 1.2, "jog": 2.4, "run": 3.6, "sprint": 4.5, "shimmy": 0.8, "rung": 0.9, "stud": 0.6, "freeClimb": 0.4, "pole": 0.5, "overhang": 0.5 },
  "jump": { "standingHeight": 1.1, "standingDistance": 1.2, "runningHeight": 1.2, "runningDistance": 2.4, "sprintDistance": 3.0, "precisionDamping": 0.3, "coyoteMs": 100, "bufferMs": 120, "ledgeCatchRadius": 0.15 },
  "verticals": { "stepUp": 0.25, "hopOver": 0.5, "vault": 0.9, "mantle": 1.4, "vaultMaxDepth": 1.5, "hopMaxDepth": 1.0 },
  "landing": { "soft": 1.5, "roll": 3.0, "hard": 5.0, "softSurfaceTierBonus": 1 },
  "slopes": { "runMaxDeg": 25, "slideMinDeg": 25, "slideMaxDeg": 60 },
  "reach": { "ledgeToLedge": 1.5, "holdReach": 1.1, "slipChanceAtMaxReach": 0.15 },
  "narrowWidthA": 0.5,
  "crouchHeadroomA": 1.1,
  "gravityScale": 0.8,
  "assist": { "coyoteMs": 200, "jumpBonus": 0.2, "slipsOff": true, "autoGrab": true },
  "dive": { "minSpeed": 2.4, "distanceA": 2.0, "rollAboveA": 1.5 },
  "ticTac": { "reboundHeightA": 0.8, "reboundDistanceA": 1.2, "maxChain": 1 },
  "wallRun": { "minWallRunA": 3.0, "maxDurationSec": 1.2, "speed": 3.6, "minEntrySpeed": 3.0, "gravityDampen": 0.5 },
  "poleVault": { "plantWindowSec": 0.25, "minRunSpeed": 2.4, "maxGapA": 3.0, "maxHeightA": 2.0 },
  "grapple": { "reachA": 6.0, "swingSpeed": 3.0, "swingMaxArcDeg": 120, "ascendSpeed": 0.7, "rappelSpeed": 1.0, "deploySec": 0.4, "reelSec": 0.6, "anchorMinLedgeA": 0.1, "snapAssistA": 0.3 }
}
```

Validator contract: a route segment is valid only if every transition is achievable under these constants with a 15% margin (85% of max reach/distance), and beat 1 uses only walk/jog/run/jump/step-up/hop-over/mantle.

---

## 11. Clip sourcing map (free tier)

Search terms are Mixamo library queries; `gj-gameplay` verifies exact names on import and records them here.

| Family | Mixamo search terms | Count target | Gap handling |
|---|---|---|---|
| Idle | idle, breathing idle, look around | 6 | — |
| Locomotion | walking, jogging, running, sprint, turn, stop, strafe | 40 (trim from ~120) | Motion matching needs starts/stops/turns; take all variants |
| Crouch | crouch walk, crouch idle | 6 | — |
| Balance | walking on beam, tightrope | 3 | Arm IK layer |
| Hop/vault | jump over, vault, hurdle | 6 | Warp to obstacle |
| Mantle/climb-up | climbing up wall, climb up, mantle | 4 | Warp |
| Hang/shimmy | hanging idle, braced hang, hang hop left/right, braced hang shimmy | 8 | Corner turn = mirrored + warped |
| Ladder/rung | climbing ladder, ladder up/down | 4 | Retime to rung spacing |
| Jumps | jump, running jump, long jump, wall jump | 8 | Precision = shortened arc |
| Falls/landings | falling idle, falling to landing, hard landing, falling to roll, stumble, getting up | 10 | Tiers per Section 5 |
| Slide | running slide, sliding | 3 | Procedural on soft |
| Celebrate/plant | victory, cheer, kneel | 3 (plus Move.ai hero) | — |
| Reactions | — | 0 | Owner Rokoko Vision capture (Section 7) |
| Stud/free/pole/overhang climb | — | 0 | Procedural (Section 6.3–6.6) on braced-hang base |

Whitelist total ≈ 110 clips before the motion-matching locomotion set. Everything else in Mixamo is excluded to protect the 60 MB budget.

---

## 12. Pipeline

1. Export Mixamo clips as FBX, "Without Skin," 30 fps, on the standard Mixamo skeleton.
2. Blender: retarget to the GJ shared humanoid skeleton (from the avatar pipeline), fix foot sliding, mark root motion, export FBX.
3. Cascadeur Basic: physics cleanup on Owner and Move.ai captures only.
4. Unity import: Humanoid rig, loop poses where cyclic, tag clips with verb + surface metadata (ScriptableObject `MoveClip`).
5. Motion matching database build; measure size and search cost; store report in `/qa/motion-db-report.md`.
6. Motion warping targets authored once per contact clip (hand and foot contact frames).
7. Feedback matrix wired via `SurfaceMaterial` events; Tier 1 hooks emitted for `gj-scenegraph`'s segmentation.

---

## 13. M1 spike spec (decides motion matching vs blend trees)

Ticket `M1-MOVE-01`, owner `gj-gameplay`, QA `gj-qa-release`.
- Build the ≈110-clip database with the open motion matcher; deploy to the reference Android device.
- Test scene: one real room splat + collision mesh from the corpus, placeholder capsule replaced by a Mixamo test character on the shared skeleton.
- Measure over 5 minutes of scripted play (run loops, 20 mantles, 10 falls): average and 99th-percentile frame time, animation CPU ms, database size, memory.
- Pass: ≥ 30 fps p99, animation ≤ 4 ms, DB ≤ 60 MB. Then motion matching is locked for v1.
- Fail: implement blend-tree locomotion with inertialization; motion matching moves to V2 with the MxM commercial license as a candidate line item.
- Either path: Motion Warping on mantle/vault/hang must land hands within 0.05A of the edge on 20 of 20 test edges.

---

## 14. V2 hooks: tools as verb layers

The controller exposes `IVerbProvider`; each tool registers verbs and their trigger queries without modifying the core.

**Promoted to v1 (AUTH #021, §3.6):** the safety-pin **grapple** (swing/ascend/rappel) and the matchstick **pole-vault**. The hooks below remain V2, added later through the same layer:
- **Parachute/glider** (found feather): replaces fall tiers above 3A with a glide state; landing always soft.
- **Climbing picks/suction** (bobby-pin piton): promotes `wall-smooth` to `textured-vertical`.
- **Spring shoes** (rubber-band launcher): jump constants ×1.5 in `movement.json` override scope.
- **Rope/zipline** (thread spool): player-placed `pole`/`soft-hanging` that is load-bearing.

Deferred content also includes the Ultimate Traversal set, traceur-captured parkour clips, stamina, and damage. (Wall-run is promoted to v1, AUTH #021.)

---

## 15. Reference library

Movement design: Steve Swink, *Game Feel*; GMTK "Why Does Celeste Feel So Good to Play?"; Maddy Thorson's Celeste movement notes; GDC "50 Game Camera Mistakes" (Nesky); Astro Bot and Super Mario Odyssey movement talks; Assassin's Creed Unity parkour system talk; Mirror's Edge first-person movement talk (for weight and hesitation cues); Zelda BotW/TotK climbing design analyses; Uncharted 4 traversal talk (ledge grab forgiveness).
Animation tech: Motion Matching (Ubisoft, Clavet, GDC 2016); Learned Motion Matching (Holden et al.); Motion Warping (Epic docs and Kinemation docs); Inertialization (Bollo, GDC 2018); Unity Animation Rigging samples.
Human movement: WFPF and Storror parkour footage (vault, roll, precision families); Kong vault and speed vault breakdowns; rock-climbing technique videos for hand/foot alternation (stud and free climb procedural reference); toddler-scale environments in stop-motion films for how small bodies move through big furniture.
Capture and cleanup: Rokoko Vision docs; Move.ai iPhone quickstart; Cascadeur Basic tutorials; Mixamo to Unity Humanoid retargeting guides.

---

## 16. Field notes

(Bots append contradictions, measured values, and clip-name corrections here; Owner reviews at each checkpoint.)

- 2026-09-15 (Coordinator, AUTH #003): v1 ships on the iOS App Store only. The §2 reference device (2023 mid-tier Android, 30 fps floor) and the §13 pass/fail thresholds are read as targets measured on the Owner's iPhones, never as merge gates; quality tiers scale per device. SPEC.md §11 governs.
- 2026-09-18 (Coordinator, AUTH #021): Movement v1 expansion — new verbs (dive-roll, tic-tac, vault variants, wall-run) and the v1 traversal-tools layer (safety-pin grapple: swing/ascend/rappel; matchstick pole-vault) via `IVerbProvider`; edits to §3.2–§3.6, §4, §10, §14. New `movement.json` blocks: `dive`, `ticTac`, `wallRun`, `poleVault`, `grapple`. Tools are the SPEC §4 diegetic character-gear exception. Rationale: `design/proposals/movement-v1-expansion.md`.
- 2026-09-19 (Coordinator, AUTH #022): Sound design + environment reactivity — §9 extended with the sound system (layering, contact-frame timing, scale-aware acoustic reverb, 3D spatialization, mix buses, restrained adaptive music) covering the new verbs and tools; §7 reactions now carry sound + Tier 1 soft reactions. Applied to SPEC §3.6. Rationale: `design/proposals/sound-reactivity-v1.md`.
