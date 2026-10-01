# Experiment B — offline clip augmentation: run spec

**M2-RES-01 / Experiment B · 2026-10-01 · Builder (AUTH #027) · runbook for the Operator**
Parent: `research/tier2/learned-physics-motion-2026-10.md` (#8 exploration). Compute: Tier-2
**AUTH #040** ($500/mo) on **AUTH #039** RunPod (Modal fallback). This is the one #8 experiment that
can lift **v1** quality (more/better clips, zero runtime cost). It is **turnkey**: the coverage metric
and the acceptance filter are already built and tested (below); the Operator supplies the generator +
GPU + captures and runs the steps. Nothing here changes `movement.json` or a frozen schema — it only
**adds clips** to the DB.

## 0. Objective & go/no-go
Fill the clip DB so the matcher has an in-tolerance clip for (nearly) every (verb × geometry) the
corpus routes demand. **Go** when, on the corpus set: motion coverage (below) rises materially over
baseline — **target ≥ 0.80 of demanded cells covered, and ≥ 70 % of the baseline gap cells on the P0
verbs closed** — **and** DB ≤ **60 MB** (Bible §2) **and** quality does not regress (warp residual,
foot-skate). Else **no-go** → document and fall back to capturing more real clips. v1 ships classic
motion matching regardless.

## 1. Inputs (exact)
- **Mocap vocabulary (the seed clips).** The ~110-clip whitelist (Bible §11) on the GJ shared skeleton,
  30 fps, retargeted per Bible §12 — the current clip DB. Plus the Owner's **Rokoko Vision / Move.ai**
  captures of the core traversal verbs (P0: `running-jump`, `precision-jump`, `vault`/`speed-vault`/
  `kong-vault`, `mantle`, `climb-up`, `stud-climb`, `controlled-drop`, `dive-roll`). Format = same
  pipeline (FBX, GJ skeleton, 30 fps).
- **Corpus terrain (the demand + the geometry to generate over).** The consented corpus rooms,
  reconstructed (collision mesh + splat) and run through the M1-SCEN chain → **frozen
  `scene_graph.json` + `traversal_graph.json` + `environment_spec.json` per room** (A units, +y up).
  These supply the real (verb, `distance_A`, `rise_A`, surface class, contact points/normals) the
  augmentation must cover. Source: the `gj-corpus` volume / `environments` bucket (never user scans —
  SPEC §3.3).
- **Contracts & pre-built tooling (already in-repo, tested).**
  - `config/movement.json` — the authored reach envelope + the **0.85 margin**.
  - `services/traversal/affordances.py` — `best_affordance` / `verb_margin`: **the acceptance filter**
    (is a (verb, `distance_A`, `rise_A`, context) within the authored envelope?).
  - `services/traversal/motion_coverage.py` — **the coverage metric** (`demanded_grid`, `coverage`,
    `coverage_delta`); see §3.
  - `services/traversal/anticipation.py` — per-edge contact points / `surface_id` for warp targets.

## 2. Augmentation recipe (the steps the Operator runs)
1. **Demand grid.** Collect the edges the corpus **routes** actually play (each `environment_spec`
   route's `beats[].edge_ids` → the `traversal_graph` edges), then
   `motion_coverage.demanded_grid(edges)` → the target cells (verb × distance-bin × rise-bin).
2. **Baseline inventory.** For the current ~110 clips, mark the cells each clip can serve within the
   matcher's **warp tolerance** (hand/foot residual ≤ **0.05 A**, Bible §13 AT). `motion_coverage.coverage(demanded, baseline)` → baseline fraction + **gap cells**.
3. **Generate (per gap cell).** Condition a motion generator on: the base captured clip for that verb +
   the cell geometry (`distance_A`, `rise_A` midpoints) + the real contact points/normals from a
   representative corpus edge in the cell. Emit N seeded variants.
   - *Track 1 (primary, cheaper):* a kinematic model (motion VAE or autoregressive diffusion),
     conditioned on start/goal contacts + verb. (Offline — diffusion is fine off the frame budget.)
   - *Track 2 (hard dynamic verbs):* PARC-style physics augmentation (RL controller improvises the verb
     over the terrain) for physically-plausible variants where Track 1 is weak.
4. **Accept / reject (deterministic — reuses Brain B).** Keep a candidate only if **(a)** it lands
   hands/feet on the real contacts (warp residual ≤ 0.05 A); **(b)** its (verb, `distance_A`, `rise_A`,
   context) is **accepted by `affordances.best_affordance` at the 0.85 margin** — i.e. inside the
   authored reach envelope, so Brain A (runtime) can never drift from Brain B (the validator/journey);
   **(c)** no foot-skate / mesh penetration beyond tolerance. Reject otherwise.
5. **Clean up + retarget (Bible §12).** Blender retarget to the GJ skeleton, Cascadeur cleanup, tag the
   `MoveClip` with verb + surface + cell.
6. **Select under budget.** Greedily add accepted clips that close the most gap cells per MB until gaps
   are exhausted or the DB hits 60 MB.

## 3. Coverage metric (the measurable outcome — already coded)
`services/traversal/motion_coverage.py` (8 tests green on the desk-tabletop graph; graph-source-agnostic,
so it runs on the corpus graphs unchanged):
- `demanded_grid(edges) -> {cell: count}` — the demand (cell = `(verb, dist-bin, rise-bin)`).
- `coverage(demanded, inventory) -> {demanded, covered, fraction, gaps}`.
- `coverage_delta(demanded, baseline, augmented) -> {before, after, gaps_closed}`.

Report, per the go/no-go: **coverage fraction before→after** (overall + per P0 verb), **gaps_closed**,
**DB size MB before/after**, and a **quality** line (mean warp residual, foot-skate rate — must not
regress). Plus a **route-playability** check: every corpus `environment_spec` route beat edge maps to an
in-tolerance clip after augmentation. (The engine runs **now** on the desk-tabletop fixture to validate
the pipeline end-to-end before the corpus is ready.)

## 4. Compute & reproducibility
RunPod (#039), Modal fallback; **fixed seeds**; the generation config + seeds are committed (the clips
are not — see §5). Order of magnitude: a few GPU-days per augmentation round, bounded by the $500/mo
line (#040), pausable. Corpus + our mocap only.

## 5. Outputs
- **Augmented clip set** → the clip-DB bucket, **not committed** (large-binary formats are gitignored,
  like splats; cf. M1-GAME-01's docs-only golden rule).
- **Coverage report** → `research/tier2/experiment-b-report.md` (fraction before/after, gaps_closed, DB
  MB, quality, route-playability).
- **Committed:** the generation config + seeds, and an updated clip-inventory manifest (cells served).
- The acceptance filter + coverage engine are the committed, reproducible gate (`affordances.py`,
  `motion_coverage.py`), so a reviewer can re-derive the accept/reject and coverage numbers.

## 6. IP & safety
Training/seed data = **our own mocap + CC0/licensed clips + the consented corpus only**. **No
third-party footage, no user scans** ever enter generation (legal + SPEC §3.3). Generated clips are
derivative of our own data → clean to ship. Reference footage (Storror/WFPF, Bible §15) stays
inspiration only, never training input.

## 7. Division of labour
- **Pre-built (in-repo, tested, this session):** the coverage metric (`motion_coverage.py`), the
  acceptance filter (`affordances.py`), the contact/warp targets (`anticipation.py`), and this spec.
- **Operator supplies:** the generator (Track 1/2), GPU time, the Owner's captures, and the retarget/
  cleanup pass (Bible §12).

## 8. Dependencies & bootstrap
Needs the **corpus reconstructed** (M1-CAPT-02/03 + the RunPod corpus runs) and **M1-SCEN graphs on the
corpus**, plus the Owner's captures. While the corpus is pending, **bootstrap on the desk-tabletop
fixture**: the coverage engine + acceptance filter already run on it, so the pipeline (demand → baseline
→ generate → accept → coverage delta) can be validated end-to-end on one environment before scaling to
the corpus.
