# Proposal — Journey generation v1: summit, routes, vistas

**Status: PROPOSAL for Owner review · 2026-09-19 · Coordinator.** Rationale doc (not a decision). Deepens SPEC §3.4 and the M1 scene tickets (M1-SCEN-03 affordance library + traversal-graph export, M1-SCEN-04 summit/route/vista generation, M1-SCEN-05 deterministic validator); adopting it is a design-change **AUTH** touching SPEC §3.4 and, downstream, the frozen `data/schemas/` (traversal_graph, environment_spec) via M1-DATA-01. Completes the v1 design arc: this is the layer that turns a reconstructed room + a movement vocabulary (`movement-v1-expansion.md`) + reactivity (`sound-reactivity-v1.md`) into an actual **journey**.

## 0. Thesis
The captured place is the star; **the journey is what makes it a game and not a diorama.** Journey generation has one job: from a scanned room or tabletop, deterministically produce a *reachable* summit, two or three *fair, rising-difficulty* routes shaped as real level design, and three *view-worthy* vistas — with a hard guarantee that **every published route is actually completable** and the environment is **never a dead end**. Three principles:
- **Reachability is law.** A route exists only if the deterministic validator proves every transition is achievable under `config/movement.json` at the 85% margin. No "probably makeable." The validator is the single source of truth shared by generator and controller (Bible §10 contract).
- **Level design, not a path finder.** Routes are shaped introduce → develop → twist → resolve (Design Skills rule 22 / kishōtenketsu), so a generated journey *teaches* and *pays off* — a safe first mantle, a section that teaches one move, one "aha" use of the real environment, then the summit.
- **Never a dead end.** Retries then a template fallback guarantee that any scannable environment yields at least one completable journey, so the create → play → publish loop never breaks on the player.

## 1. The pipeline (where journey-gen sits)
Scene graph (M1-SCEN-01/02) → **affordance library** (M1-SCEN-03) → **traversal graph** (M1-SCEN-03) → **journey generation** (M1-SCEN-04) → **deterministic validator** (M1-SCEN-05) → `environment_spec` (frozen schema). Each stage is deterministic and inspectable.

### 1.1 Affordance library (M1-SCEN-03) — one source of truth
Maps each Bible §4 surface class → the verbs it affords, in **one place** consumed by both graph export and the validator (no duplicated logic). Sketch:

| Surface class | Affords (verbs) |
|---|---|
| walkable-hard / -soft | walk, jog, run, sprint, land, dive-roll, slide |
| walkable-narrow | balance-walk, crouch |
| ledge | mantle, hang, shimmy, ledge-to-ledge jump, controlled/hang-drop, **grapple anchor** |
| rung / stud | rung / stud climb |
| textured-vertical | free climb, **wall-run** (if run ≥ 3.0A), tic-tac |
| pole | pole climb |
| overhang | overhang hang-traverse, **rappel anchor** |
| slope | run (≤25°), slide (25–60°) |
| wall-smooth | **blocks climb** — passable only via tic-tac rebound, **grapple-ascend to an anchor above**, or **wall-run** across |
| soft-hanging | swing, **grapple twine interaction** |
| void | **crossed only by** running/precision jump (≤ cap), ledge-to-ledge, **grapple-swing**, **pole-vault**, dive |

### 1.2 Traversal graph (M1-SCEN-03)
Nodes = stable stances/holds (a spot the avatar can be at rest or in controlled transit). Edges = a **single verb transition** between two nodes, tagged with: `verb`, `capability cost` (distance/height/angle in A-units), `entry prerequisites` (min speed, plant window), `surface prerequisites`, and a **difficulty tier** (below). Grapple/pole-vault/wall-run edges are added the same way any verb edge is — the tools are just verb providers (`IVerbProvider`, Bible §14), so the generator treats them uniformly. This is why the grapple "massively expands the reachable graph": it adds void-crossing, wall-smooth-passing, and safe-descent edges the core set can't produce.

## 2. Difficulty model (the grading that makes "rising difficulty" real)
Every edge gets a **verb tier**; every route gets a **difficulty score** derived from its edges. This is what lets the generator produce 2–3 routes of genuinely *rising* difficulty and keep beat 1 simple.

**Verb tiers (edge grading):**
- **T0 — ground locomotion (the beat-1 set):** walk, jog, run, step-up, hop-over, mantle, standing/running jump. *Nothing else is allowed in beat 1.*
- **T1 — basic parkour:** vault (+ kong/speed/underbar variants), precision jump, controlled drop, hang-and-drop, slide, **dive-roll**.
- **T2 — climbing + advanced:** ledge shimmy, rung / stud / free / pole / overhang climb, ledge-to-ledge, wall-push, **tic-tac**.
- **T3 — high-skill + tools:** **wall-run**, **grapple** (swing / ascend / rappel), **pole-vault**, and any transition sitting near the 85% margin (slip-risk / max-reach commits).

**Route difficulty score** = weighted blend of: the **highest tier** used, the **count of distinct advanced (T2+) verbs**, the **tightest margin** on the route (how close its hardest transition sits to the 85% cap), **total climb height + traverse distance**, and the **number of commit points** (no-coyote gaps, max-reach holds, tool releases). The generator sorts candidate routes by this score and picks a spread (easy / medium / hard).

## 3. Summit designation (M1-SCEN-04)
1. Build the traversal graph from the reachable set (flood-fill from the spawn/landing node using only *validated* edges).
2. **Summit = the highest node in the reachable set** (by world-up, scaled) with a plantable stance (a ledge/surface the flag animation fits). Reaching it plants the flag; the summit **beacon is visible from the start** and drawn on top with depth-fade (Bible §8) so orientation is never lost.
3. If the absolute-highest point of the room is **not** in the reachable set, the summit is the highest point that *is* — see the tools fork (§8) and fallback (§7), which decide whether tools are allowed to lift that ceiling.

## 4. Route generation (M1-SCEN-04) — level design, not just paths
For the designated summit, search the validated graph for candidate spawn→summit paths, then **shape and grade** them:

**Beat structure (Design Skills rule 22 / kishōtenketsu), per segment:**
- **Beat 1 — introduce (T0 only):** a safe on-ramp — walk/jog/run + a first step-up/hop-over/mantle. **Hard rule: only walk, jog, run, jump, step-up, hop-over, mantle** (SPEC §3.4, Bible §10). No climbing, no tools, no dive/tic-tac/wall-run. The validator *enforces* this (property test).
- **Beat 2 — develop:** teach exactly **one** new move in a low-stakes spot — the easy route introduces one T1 verb (a first vault or dive-roll) or one gentle climb; harder routes teach a T2 climb.
- **Beat 3 — twist:** the "aha" — the signature use of *this real environment*: a bookshelf climb, the gap between couch and table, a Lego turret. On the **hard route** this is where a **tool beat** or a committing climb lands — a **grapple swing** across a void, a **pole-vault** over a gap, a **wall-run** along a shelf face — the highest production-value moment.
- **Beat 4 — resolve:** the final approach and the summit + flag plant.

**Route spread (2–3 of rising difficulty):**
- **Route A (easy):** lowest score; T0–T1; the reliable path everyone can finish.
- **Route B (medium):** adds a T2 climb or a signature environment move in beat 3.
- **Route C (hard, if the environment supports it):** T2–T3; features the tools / wall-run / tightest-margin commits; skippable if the environment is too simple to yield a distinct third (then ship 2).

Beat 1 stays T0 on **every** route — the on-ramp is always gentle; difficulty rises after.

## 5. Vista selection (M1-SCEN-04)
Three vantage points **chosen for the view, not for difficulty** (Design Skills rule 22). Score candidate nodes by:
- **Viewshed** — how much of the environment (and the summit beacon) is visible from the node (openness / low occlusion).
- **Framing** — elevation + a clear sightline; the diorama reads well in photo mode.
- **Accessibility** — reachable at **low-to-moderate** difficulty (T0–T1, off a short detour); vistas are rewards, not gauntlets.
- **Spread** — the three are spatially separated (not three angles on one spot).

Reaching a vista opens **photo mode**; the vista **sparkle** is drawn on top with depth-fade (Bible §8).

## 6. The deterministic validator (M1-SCEN-05) — the real gate
A pure, deterministic reachability check; the same code validates generated routes, player-recorded challenge routes, and drives the summit flood-fill.
- **Accept an edge only if** the verb's required distance/height/angle ≤ **85% of the `movement.json` maximum** for that verb (the 15% margin), **and** entry prerequisites hold (e.g. wall-run `minEntrySpeed` 3.0 + wall run-length ≥ `minWallRunA` 3.0A; dive `minSpeed` 2.4; pole-vault `minRunSpeed` 2.4 within `plantWindowSec` and gap ≤ `maxGapA` 3.0; grapple anchor within `reachA` 6.0 with `anchorMinLedgeA` 0.1), **and** surface prerequisites hold.
- **Loads shared constants** via `services/traversal/movement.py` (M0-MOVE-01) — **no duplicated numbers**; `config/movement.json` is the single source (and is CI-checked parse-equal to Bible §10).
- **Reviewed by gj-gameplay** so validator and runtime controller agree on what's makeable — a route the validator passes must be one the controller can actually execute at the same thresholds.
- **Property tests (M1-SCEN-05 AT):** an unreachable summit is rejected; a gap **just over** 85% of max distance is rejected and one **just under** is accepted; a beat-1 segment containing any non-T0 verb is rejected.

## 7. Robustness — "never a dead end"
Target (M1-SCEN-04 AT-3): **8/10 corpus rooms produce a reachable summit + ≥2 valid routes with no manual fixes.** When generation can't hit that on a given scan:
1. **Retry (×3)** with progressively relaxed *shaping* (not the margin — the margin is fixed at 85%): drop the route target 3→2, loosen beat-3 "signature move" preference, accept a longer/simpler path, lower the summit to the next-highest plantable reachable node.
2. **Template fallback:** a guaranteed-simple **single "explore" route** — a monotonic, validated climb from spawn to the highest core-reachable plantable node, beat structure collapsed to introduce→resolve. Always solvable, so the loop never breaks. The environment is still publishable; it just ships one gentle route instead of a graded spread.

The **grapple's global availability** is the biggest robustness lever: it turns many otherwise-unsolvable scans (a smooth-walled desk, a room of chasms) into fully playable environments — which is exactly why the tools fork below matters for the 8/10 target.

## 8. Two genuine design forks (need your call before editing SPEC §3.4)

### Fork 1 — Are traversal tools ever *required* to reach the summit, or always *optional*?
The grapple/pole-vault/wall-run enormously expand the reachable graph. The question is whether the **easiest** route to the summit may *depend* on a tool.
- **(A) Optional-only (recommended):** the summit and **Route A (easy)** must be reachable with **core parkour alone**; tools/wall-run only open **additional or harder** routes and shortcuts. Pros: never soft-locks a player who hasn't mastered the grapple; the game stays learnable; difficulty is honest. Cons: on tool-only environments (a smooth-walled desk) the *summit height* is capped to what core parkour can reach, so some scans yield a lower summit than their true peak.
- **(B) Tools may be required:** the summit can sit behind a mandatory grapple/pole-vault beat when that's the only way up. Pros: more environments reach their *true* peak; hits the 8/10 target more easily; showcases the tools. Cons: a player must know the tool to finish at all; risk of a beat-1-friendly on-ramp leading to a hard-gated finish. (Mitigation if you pick B: guarantee the tool is *taught* in an earlier beat before it's *required*, and never in beat 1.)
- Recommendation: **(A)** — it matches "great platformer, forgiving, learnable," and tools become a source of *expressive* harder routes rather than gates. This is the safer identity; B is defensible if you want maximum "every real place reaches its summit."

### Fork 2 — Is route difficulty graded **per-environment (relative)** or on a **global (absolute) scale**?
This affects the ranked global database (§3.7) and difficulty-filtered browsing.
- **(A) Per-environment relative (recommended, matches current SPEC "rising difficulty"):** every environment always offers 2–3 routes of rising difficulty *within itself*, whatever its absolute floor. Pros: every environment gives a full, satisfying spread; simplest for the player. Cons: an "easy" route in a complex bookshelf may be objectively harder than a "hard" route on a plain desk — labels aren't comparable across environments.
- **(B) Global absolute tiers (beginner / intermediate / expert):** difficulty is graded on one global scale; some environments only offer expert routes, some only beginner. Pros: difficulty labels mean the same everywhere → better global ranking, matchmaking, and "find me a beginner run." Cons: some environments have *no* easy route (and the generator can't invent one), which can feel like missing content.
- Recommendation: **(A)** for v1 (it's what SPEC already implies and it never leaves an environment feeling empty), and record a **global difficulty score** as *metadata* on each route so a future version can add absolute filtering without a redesign. This gets B's ranking benefit later at no v1 cost.

## 9. Governance — what adopting this changes (AUTH-gated)
- **SPEC §3.4** — deepen with: the difficulty tier model (T0–T3), the beat-per-tier rules (beat 1 = T0 only; the twist as the tool/signature beat), the tools-required-vs-optional decision (Fork 1), the difficulty-grading decision (Fork 2), the vista scoring criteria, and the retry→template-fallback guarantee.
- **`data/schemas/` (frozen, via M1-DATA-01)** — the `environment_spec` / `traversal_graph` fields this implies: per-edge `verb` + `tier` + `capability cost` + `prerequisites`; per-route `beat[]` + `difficulty score`; `summit`, `vistas[]`, `challenge_routes[]`. Schema changes carry the same AUTH.
- **Tickets** — no new tickets needed; this **sharpens the acceptance criteria** of the existing M1-SCEN-03/04/05 (affordance table, tier model, beat-1 enforcement property test, vista scoring, fallback). I'll fold the specifics into those three tickets on your answer.

## 10. Decision needed before editing the protected docs
Answer **Fork 1** (tools required vs optional) and **Fork 2** (relative vs absolute difficulty). On your answers I'll file the AUTH, deepen SPEC §3.4, note the downstream `data/schemas/` fields for M1-DATA-01, and sharpen M1-SCEN-03/04/05. Unless you object, I'll adopt the **T0–T3 difficulty model**, the **beat-per-tier structure**, the **vista scoring**, and the **retry→template-fallback** guarantee as specified.
