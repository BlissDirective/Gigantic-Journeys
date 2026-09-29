# `services/traversal/`

Owner: gj-scenegraph (validator), gj-gameplay (constants)

The traversal layer: from a classified scene graph to a validated traversal graph and,
next, routes. Loads `config/movement.json` (M0-MOVE-01) as the single source of movement
constants — no number is duplicated here. Pure standard library, deterministic.

## Modules

| File | Ticket | What |
|---|---|---|
| `movement.py` | M0-MOVE-01 | Loader for `config/movement.json` into typed frozen dataclasses; `MARGIN` (0.85) and `with_margin`. The shared C#/Python agreement fixture lives in `tests/fixtures/`. |
| `affordances.py` | M1-SCEN-03 | **The affordance library — the one place** (M1-SCEN-03 AT-3, M1-SCEN-05 AT-3): the verb→tier table (mirrors the frozen `traversal_graph` schema), the Bible §4 class→verb matrix, the per-verb reach model against `MovementConfig`, and each verb's required prerequisites. Tool verbs (grapple, pole-vault, wall-run) are ordinary entries with their movement.json prerequisites (AT-4). |
| `graph.py` | M1-SCEN-03 | Export a `traversal_graph.json` from a `scene_graph.json`: place nodes on the classified surfaces (stance / hang / climb / anchor), propose a directed edge for every reachable pair using only verbs the source surface's class enables (AT-2), each accepted at the 85 % margin. |
| `reach.py` | M1-SCEN-05 | The deterministic reachability validator every route must pass: re-checks each transition against `movement.json` at the 85 % margin (never trusting the graph's recorded margin), and enforces the route rules — segments chain, beat 1 is T0-only, and a tool may be required only if an earlier beat (never beat 1) taught it. |
| `graph_cli.py` | M1-SCEN-03 | `python services/traversal/graph_cli.py scene_graph.json traversal_graph.json` |

## Contracts

Reads `scene_graph.json` and writes `traversal_graph.json`, both frozen v1.0.0 in
`data/schemas/environment/` (M1-DATA-01, AUTH #037). The graph records the sha256 of the
`movement.json` it validated against, so the environment_spec validator (M1-SCEN-04/05) and
the Unity controller can prove they agree on the same constants.

## Scope now

M1-SCEN-03 (graph export) and M1-SCEN-05 (validator) are built and tested on the frozen
schema + synthetic scene graphs (incl. the desk-tabletop fixture). Route / summit / vista
generation (M1-SCEN-04) builds on `reach.validate_route`. Corpus evidence (labelled graphs
on real reconstructions) rides the Operator's reconstruction runs.
