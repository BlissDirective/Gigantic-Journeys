# gj-scenegraph — Working Handbook

Remit: turn a reconstructed room into a playable graph — mesh cleanup, surface/affordance labeling, traversal graph, summit/route/vista generation, and the deterministic reachability validator. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- Tickets M1-SCEN-01..05; schemas frozen by M1-DATA-01 (scene-graph, traversal-graph, environment-spec). Journey generation = SPEC §3.4 (AUTH #023).
- Movement constants are the contract: `config/movement.json` (loader `services/traversal/movement.py`, schema `config/movement.schema.json`). The validator checks reachability **against these constants** — never hardcode.

## Principles
- **Determinism.** The reachability validator (M1-SCEN-05) must be deterministic and reused by leaderboards (plausibility floor, AUTH #026) — same inputs, same verdict.
- **Never a dead end.** Route generation guarantees a completable path (retry → template fallback). Beat 1 = T0 ground set only; twist = signature/tool beat; a required tool must be taught earlier (never beat 1).
- **Relative difficulty per environment** + a global difficulty score kept as metadata for later absolute filtering.
- **Physics-honest affordances.** Reachability derives from movement.json (jump height/distance, reach, grapple/pole/wall-run) with the 0.85 safety margin (`with_margin`).

## Techniques
- Mesh cleanup: hole fill, ceiling cap, floater removal before labeling (M1-SCEN-01).
- Surface classification + scale inference + material/semantic labels (M1-SCEN-02) feed affordances.
- Affordance library → traversal-graph edges carry verb + tier (T0–T3) + cost + prerequisites (M1-SCEN-03).
- 3D Gaussian segmentation (Gaussian Grouping lineage) for object/affordance separation.

## Pitfalls
- Scale drift from SfM → wrong reach/jump verdicts; validate scale (known-size references) before route grading.
- Splat geometry ≠ collision geometry — gameplay uses the derived Open3D **mesh** for physics; keep them consistent.
- Letting a required tool gate the summit without teaching it earlier → unfair/unsolvable route (validator must catch).

## Checklist
Mesh watertight ✓ · scale sane ✓ · affordances tiered ✓ · ≥2 routes ✓ · summit reachable per movement.json+margin ✓ · vista scored ✓ · deterministic validator green ✓.

## Pointers
`config/movement.json` + `services/traversal/` · SPEC §3.4 · `design/proposals/journey-route-generation-v1.md` · tickets M1-SCEN-01..05, M1-DATA-01.
