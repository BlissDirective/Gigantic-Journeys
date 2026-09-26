# gj-scenegraph — Working Handbook

Remit: turn a reconstructed room or tabletop into a playable, validated environment. That covers mesh cleanup, surface classification, measurement and scale, the affordance library, the traversal graph, summit/route/vista generation, the deterministic reachability validator, the Tier 1 reactivity pipeline (segmentation + displacement parameters) and the Tier 2 physics research track. Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** does almost all of this (Python services and schemas; AGENT_GOVERNANCE §8). The **Operator** handles GUI-only inspection (for example viewing a corpus environment in the Editor) and long GPU research runs. Owned paths (kit §3.2): `services/scenegraph`, `services/traversal` (validator; constants belong to gj-gameplay), `services/reactivity`, `research/tier2`, and `data/schemas/{scene_graph,traversal_graph,environment_spec}.json` (AUTH-gated).

Research list: `projects/skills/scenegraph/RESOURCES.md`.

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, evidence | `agents/grok/README.md` §3–§5 |
| AUTH for schema freezes/changes, `config/movement.json`, and Tier 2 compute spend | `agents/grok/README.md` §6; SECURITY_CHECKLIST §2.5; SPEC §5 |
| Review rows, esp. A6 (determinism), E1 (layer boundaries, typed CLI entry points), E2 (no magic numbers: constants only from `movement.json`), F1/F3 (property tests, hermetic fixtures), H2 (Field notes) | `governance/REVIEW_RUBRIC.md` |
| Vision pass carries no PII or location; Bots see no raw user media | `governance/SECURITY_CHECKLIST.md` §6.5, §10.1, §10.4; M1-SCEN-02 AT-2 |
| Pins, commercial-safe licences (check every research repo's licence before reuse) | `governance/SECURITY_CHECKLIST.md` §7 |
| Units (A), scale examples, gravity | Movement Bible §1 |
| Verb thresholds the graph encodes | Movement Bible §3 (§3.1–3.6 incl. tools) |
| Surface classes × enabled/blocked verbs | Movement Bible §4 |
| Fall tiers (drops the validator may allow) | Movement Bible §5 |
| Climb families and speeds | Movement Bible §6 |
| Tuning constants + validator contract (85 % margin, beat-1 set) | Movement Bible §10; `config/movement.json`; `services/traversal/movement.py` |
| Tools as verb layers (`IVerbProvider`) | Movement Bible §3.6, §14 |
| Route beats and vistas-for-view | Design Skills rule 22 (§3.9). SPEC §3.4 widens the beat-1 set beyond rule 22's "run, jump, mantle"; SPEC wins |
| "Never obscure the room"; the non-photo element language | Design Skills rules 2, 23; DESIGN_SYSTEM decision 1 |
| What v1 is | `SPEC.md` §3.3, §3.4, §3.6, §5 |

## 2. Mesh cleanup (M1-SCEN-01)

- The input is the reconstruction's Open3D Poisson mesh (`services/reconstruction`). The output is a **watertight collision mesh**: holes filled, ceiling capped, floaters removed (M1-SCEN-01 AT-1).
- **Floaters:** cluster connected triangles (Open3D `cluster_connected_triangles`) or DBSCAN the vertices, then drop small, disconnected clusters. Log what you drop and why.
- **Ceiling cap:** detect the dominant upward-facing planes (RANSAC) and the room's up axis. Use ARKit gravity from the upload bundle when present (SPEC §3.1). Cap above the highest walkable plane.
- **Hole fill:** close small boundary loops; leave large openings (doors) as `void`.
- Splat ≠ collision. Gameplay collides with the **mesh**. Keep splat and mesh in the same frame and scale, and check alignment on every fixture.
- Unit tests on synthetic meshes are suggested (AT-2). Pins and `pip-audit` are required (AT-3). Keep heavy geometry deps out of CI requirements unless they are CI-installable (see the reconstruction Dockerfile pattern).

## 3. Surface classification, measurement and scale (M1-SCEN-02)

- **Classes are exactly the Bible §4 set** (SPEC §3.3): walkable-hard, walkable-soft, walkable-narrow, ledge, rung, stud, textured-vertical, pole, overhang, slope, wall-smooth, soft-hanging, void. No new class without a design-change AUTH.
- **Geometric thresholds come from `movement.json`/Bible §3–§4**: narrow width < `narrowWidthA` 0.5A; rung spacing 0.6–1.2A; pole Ø 0.2–0.8A; ledge ≥ 0.1A; slope 25–60° (`slopes`); run max 25°; wall-run needs ≥ `minWallRunA` 3A of wall. Read them from the loader and never re-type them (REVIEW_RUBRIC E2).
- **Measure in metres and A.** Scale inference defaults to 1:12 with a per-environment multiplier. It is tuned for tabletop builds so Lego studs (pitch 0.055A) read as `stud` (SPEC §3.3, Bible §1). Validate scale against known-size references before grading routes: SfM scale drift turns into wrong reach verdicts.
- **Material + semantic labels** come from a vision pass (open-vocabulary detector/segmenter lifted to 3D). Materials map to the Bible §9 list (wood, tile/stone, carpet, fabric, Lego/plastic, paper, metal, glass, plant, curtain) because Tier 0 feedback keys off them.
- Log disagreements with Bible §4 examples to the **Movement Bible §16 Field notes** (M1-SCEN-02 AT-3). That is the only edit allowed without AUTH.
- Output schema-validates against `scene_graph.json` (AT-4). **Schemas are not frozen yet.** `data/schemas/` holds only a README until M1-DATA-01 lands with its own AUTH; exact field names are TBD there.

## 4. Traversal graph and validator (Bible §10 contract)

**Affordance library (M1-SCEN-03).** One mapping in one place, class → enabled verbs per Bible §4. Both the graph export and the validator consume it (AT-3). Tool verbs (grapple swing/ascend/rappel, pole-vault, wall-run) enter through the same mapping, each recording its `movement.json` prerequisites on the edge (AT-4).

**Edges** carry verb, capability cost (distance/height/angle in A), entry + surface prerequisites, and a tier (SPEC §3.4):
- **T0:** walk, jog, run, step-up, hop-over, mantle, standing/running jump.
- **T1:** vault + variants, precision jump, controlled/hang drop, slide, dive-roll.
- **T2:** ledge shimmy; rung/stud/free/pole/overhang climb; ledge-to-ledge; wall-push; tic-tac.
- **T3:** wall-run; grapple swing/ascend/rappel; pole-vault; near-margin commits.

**Validator (M1-SCEN-05).** The validator is the real gate:
- Accept a transition only if the required distance/height ≤ **85 %** of the constant (`movement.with_margin`, `MARGIN = 0.85`), **and** its entry prerequisites hold (for example `wallRun.minEntrySpeed`, `dive.minSpeed`, `poleVault.minRunSpeed`/`plantWindowSec`/`maxGapA`), **and** its surface prerequisites hold (`wallRun.minWallRunA`, `grapple.reachA`, `grapple.anchorMinLedgeA`) (SPEC §3.4, AT-1).
- Load constants only via `services/traversal/movement.py` (AT-3). Movement-sync CI already keeps `config/movement.json` equal to Bible §10 and to `unity/Assets/StreamingAssets/movement.json`.
- **Deterministic.** Same graph + route → same verdict: stable node ordering, deterministic tie-breaking, no wall-clock or unordered-set iteration in decisions (REVIEW_RUBRIC A6). The same code also gates player-recorded challenge routes and the **leaderboard plausibility floor** (SPEC §3.7, M4-GAME-02), so a nondeterministic validator becomes an anti-cheat bug.
- Required property tests (AT-2): unreachable summit; a gap just over vs just under 85 %; the beat-1 restriction; an unmet tool prerequisite; a tool required before it is taught.
- gj-gameplay reviews it so the validator and the controller agree (AT-4).

## 5. Summit, route and vista generation (M1-SCEN-04)

- **Summit:** flood-fill the reachable set from spawn using validated edges only. The summit is the highest reachable node with a plantable stance. Tools may be required to reach it only if taught in an earlier beat of that route, never in beat 1 (SPEC §3.4, AT-5).
- **Routes:** 2–3 per environment with **per-environment rising difficulty**, each also storing a **global difficulty score** as metadata. Beats run introduce → develop → twist → resolve. **Beat 1 = T0 only.** Beat 2 teaches exactly one new move. The twist is the signature use of this real place (the tool beat on the hard route). The route score blends highest tier, count of distinct T2+ verbs, tightest margin, total climb/traverse and commit points (`design/proposals/journey-route-generation-v1.md` §2). **Score weights are TBD** (M1-SCEN-04; tuned on the corpus).
- **Never a dead end:** up to three retries that relax *shaping* only (route count, twist preference, path length, summit height), **never the margin**. Then a **template fallback**: one monotonic, validated explore route (SPEC §3.4, AT-2).
- **Vistas:** three nodes chosen for the view, scored by viewshed (place + summit visible), framing, T0–T1 access on a short detour, and spatial spread (SPEC §3.4, proposal §5).
- **Exit target (suggested):** 8 of 10 corpus rooms yield a reachable summit + ≥ 2 valid routes with no manual fixes (AT-3, SPEC §8 M1 exit). Needs the corpus (M0-OWNER-01).

## 6. Tier 1 pipeline (ships) and Tier 2 research method (does not ship)

**Tier 1** (`services/reactivity`, SPEC §3.6, runtime in M3-GAME-01):
- Segment objects in the splat (the Gaussian Grouping lineage: SAM masks lifted to Gaussians), then attach a material class and **displacement parameters per object**: cushions dent, curtains/plants/paper sway and flutter, cords swing, and tool/verb reactions (wall-run dust scuff, rappel curtain sway, grapple twine).
- **Shader-driven displacement only, no physics** (M3-GAME-01 AT-1). SPEC estimates segmentation compute at about $0.02–0.10 per scan; confirm it on the corpus. Tier 1 must hold the 30 fps target (M3 exit, suggested evidence).

**Tier 2** (`research/tier2`, SPEC §5):
- The question: can true physics on segmented real objects (object–scene decoupling, tet-embedded Gaussians, XPBD) run at mobile frame rates and per-scan cost?
- **Method:** corpus only, never user data. Segment → embed (tet mesh) → simulate ≥ 3 classes (cushion, cloth/curtain, small loose object) → render in the Unity test scene on the reference device. Report R1–R6 with measured values every checkpoint (SPEC §5 table).
- **Budget:** a monthly spend AUTH before any GPU hour ($400–1,000/month line, SPEC §5). M1-RES-01 is `blocked` until that AUTH exists. The charter (M0-SCEN-01) comes first: R1–R6 measurement procedures, the standing-ticket format, the compute AUTH template, and a reading list covering Gaussian Grouping, VR-GS, DecoupledGaussian, tet-embedding, XPBD and 2026 papers (RESOURCES.md groups B and F seed it).
- **Decision point:** the M4 checkpoint decides v1.1, V2 or shelve. Nothing from Tier 2 ships in v1 (SPEC §4).

## 7. Mistakes to avoid

- Hard-coding a threshold (0.5A, 85 %, 3A) instead of reading `movement.json` (REVIEW_RUBRIC E2). The Bible says numbers are *initial*, and M1 telemetry will retune them.
- Relaxing the margin to make a scan "pass". Only shaping relaxes.
- Letting beat 1 include a vault, climb, dive or tool. Design Skills rule 22's shorter list is superseded by SPEC §3.4 and Bible §10.
- A tool required on the summit path but not taught earlier on that route.
- Nondeterminism from Python `set`/`dict` iteration over unsorted keys, float accumulation order, or random seeds in the validator.
- Using a research repo (Gaussian Grouping, SAGA and so on) without a licence check. INRIA-derived code is non-commercial and excluded (ADR-0005). TetGen and CGAL carry copyleft/commercial terms.
- Editing `data/schemas/`, `config/movement.json` or Bible §3/§5/§10 without an AUTH. Measured contradictions go to Field notes.
- Treating the splat as the collision surface.

## 8. Checklists

**Pre-PR:**
- [ ] Every required AT has evidence (test name, CI job, report path).
- [ ] Output schema-validates (once M1-DATA-01 freezes the schemas; until then the fixture shape is documented in the PR).
- [ ] No duplicated movement numbers; constants come through `services/traversal/movement.py`.
- [ ] Determinism: running twice on the same fixture gives identical output (a test is suggested).
- [ ] Property tests cover the M1-SCEN-05 AT-2 cases; fixtures are synthetic and hermetic (F3).
- [ ] Beat-1 = T0 and the tool-taught-earlier rule are enforced by the validator, not just the generator.
- [ ] No PII, location or raw media in labels, logs or reports (C10).
- [ ] New deps are pinned with a licence line; `pip-audit` is clean.
- [ ] gj-gameplay review requested for validator/constant changes.
- [ ] Bible contradictions are logged under §16 Field notes only.

**Per generated environment:** mesh watertight · scale sane vs a known reference · classes from the §4 set · every edge's verb enabled for its source class · summit reachable at 85 % · 2–3 routes with rising score (or template fallback) · beat 1 T0 · vistas scored and spread · global difficulty recorded.

## 9. Pointers

`services/traversal/movement.py` · `config/movement.json` + `config/movement.schema.json` · `design/proposals/journey-route-generation-v1.md` · `design/proposals/movement-v1-expansion.md` · `design/proposals/sound-reactivity-v1.md` (Tier 1 hooks) · tickets M0-SCEN-01, M1-DATA-01, M1-SCEN-01..05, M1-RES-01, M3-GAME-01, M4-GAME-02.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | `data/schemas/` holds only a README (M1-DATA-01 not frozen). `movement.py` exposes `MARGIN = 0.85` and `with_margin`. The validator also underpins the M4 leaderboard plausibility floor, so determinism is an anti-cheat property. Design Skills rule 22's beat-1 list is narrower than SPEC §3.4. | gj-operator expanded RESOURCES.md to 103 link-checked entries and rewrote SKILLS.md by pipeline stage, adding the Tier 1 and Tier 2 methods (M0-SKILL-03). |
