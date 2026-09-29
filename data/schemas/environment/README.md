# Environment schemas (M1-DATA-01): scene_graph, traversal_graph and environment_spec v1.0.0

**Status: FROZEN by AUTH #037 (2026-09-29).** Drafted by gj-operator on 2026-09-29 (overnight worker) for
gj-scenegraph, with gj-gameplay and gj-platform as reviewers; secondary review by the Coordinator (AUTH #027)
on 2026-09-29. These files are the frozen v1.0.0 contract the M1-SCEN chain writes and the Unity loader
(M1-GAME-01) reads. Any change now needs its own design-change AUTH, cited as `APPROVED #n`, exactly like the
telemetry and correction schemas one level up. This set stays in its own `environment/` subdirectory (self-
contained schemas + `fixtures/` + `check_consistency.py` + `tests/`) so its fixture globbing does not collide
with the flat telemetry/correction fixtures in `data/schemas/`.

Two field-level items were frozen as-drafted, surfaced to the Owner, and **resolved (Owner re-confirmed
AUTH #037 on 2026-09-29)** — both stay as frozen:

- **`crouch` is tier T0** (a beat-1-legal verb), asserted by `tests/test_m1_schemas.py`; it extends the
  SPEC §3.4 T0 set with crouch. **Kept at T0.**
- **Vault variant names** are `speed-vault`, `kong-vault`, `lazy-vault` (AUTH #021), now the **canonical**
  names (superseding the decision-packet's step/speed/kong wording); M1-MOVE-02's C# verb set implements
  these three names. No fixture depends on a vault verb, so nothing else changes.

## Files

| File | What |
|---|---|
| `scene_graph.json` | Classified, measured surfaces (Bible §4 classes, §9 materials) in A units, plus the scale multiplier and method, frame conventions (A, +y up, left-handed like Unity), bounds, floor and spawn. Output of M1-SCEN-01/02. |
| `traversal_graph.json` | Nodes (stance / hang / climb / anchor, plantable flag) and directed edges: verb, tier (T0–T3, enforced per verb), distance, rise, `margin_used` ≤ 0.85, cost, commit flag, and the entry/surface prerequisites the validator checked (tool, min speed, run-up, plant window, wall length, anchor ledge). It carries the sha256 of the `movement.json` it was validated against. Output of M1-SCEN-03 and the M1-SCEN-05 validator. |
| `environment_spec.json` | The playable contract: package-relative asset names (never URLs or bucket paths), spawn, summit (with `true_peak`), 1–3 routes and up to 3 vistas, plus generation metadata (seed, retries, template fallback, validator margin and hash). Each route has four beats (introduce → develop → twist → resolve), or two (introduce → resolve) for the template fallback. Beat 1 is always T0-only and teaches nothing. Routes also record relative difficulty plus a global difficulty score (AUTH #023), highest tier, distinct T2+ verbs, tightest margin, total climb, commit points, a required tool and a par time. |
| `check_consistency.py` | Cross-document rules a schema cannot express: ids resolve; routes chain from spawn to summit; beat `max_tier` and `teaches` match their edges; route metrics match their path; ranks are 1..n with non-decreasing global difficulty; the summit is plantable; no node stands on `void`; ids, scale, capture mode and movement hash agree across the three files; a required tool is taught in beat 2+ before it is needed. |
| `fixtures/` | A synthetic desk tabletop (8 surfaces, 10 nodes, 12 edges, 2 routes, 2 vistas), a template-fallback spec and a room variant; 15 invalid fixtures (unknown class, URL field, metres frame, tier mismatch, over-margin, grapple without an anchor, relaxed margin, beat 1 not T0, beat 1 teaching, 3 beats, 1 route without fallback, asset URL, T2 vista, 4 vistas and so on). |
| `tests/test_m1_schemas.py` | 51 pytest cases. They cover fixture accept/reject, closed objects and constrained strings, the surface enum equal to Bible §4 (parsed from the Bible), T0 equal to the SPEC §3.4 set, a 0.85 margin, the fixture hash equal to the current `config/movement.json`, and 16 consistency mutations. |

## Design choices to review

1. **Everything in A units, env-local, +y up, left-handed.** Unity consumes this without conversion.
   `scale.metres_per_A` records the real size for any debugging or tuning.
2. **Verb → tier is fixed in the schema** (SPEC §3.4). The choices a reviewer should check:
   - `sprint-jump` is **T1**. SPEC §3.4 lists only standing and running jumps in T0.
   - `balance-walk` is **T1**, next to precision jump.
   - `crouch` is **T0**.
   - `climb-up` (the ledge top-out) is **T2** with the climb family.
   - The vault variants are `speed-vault`, `kong-vault` and `lazy-vault` (AUTH #021 "vault variants"; names to confirm with M1-MOVE-02).
3. **Graph edges are directed.** A two-way link is two edges, because drops and climbs are asymmetric.
4. **Assets are package-relative names.** A published spec never leaks a user id or a bucket path (the
   storage layout is `{user_id}/{environment_id}/…`, AUTH #034).
5. **Template fallback is explicit** (`generation.template_fallback`, per-route flag, one two-beat route), so
   the "never a dead end" guarantee (SPEC §3.4) is visible in the data and in telemetry.
6. **`vistas` allows 0–3.** SPEC says three. A tiny environment may yield fewer valid T0–T1 vantages, and the
   generator should not invent one. Reviewers may prefer `minItems: 3` with a fallback rule instead.
7. **No player-recorded challenge routes yet.** That is an additive 1.1.0 field in M4 (M4-GAME-02).
8. **Not in scope:** Tier 1 reactivity parameters (M3-GAME-01) and audio material banks (M1-GAME-04). Both
   key off `surface.material` and `surface.class`, which are here.

## AT mapping (tickets/M1-DATA-01.json)

- AT-1: surfaces (Bible §4), A-unit measurements, scale multiplier, edges (verb, tier, difficulty), and
  summit, routes and vistas with a per-segment beat. **Met by the draft.**
- AT-2: fixtures validate and invalid ones are rejected. **Met.** "The validator and a Unity loader both parse
  the same fixture": the Python side is `check_consistency.py`. The Unity loader lands with M1-GAME-01 and
  should parse `fixtures/valid/*.desk-tabletop.json` in an EditMode test.
- AT-3: needs the AUTH (APPROVED #n) and the README version row. **Met** — frozen under AUTH #037 (2026-09-29);
  version rows added to `data/schemas/README.md`.
- AT-4: gj-gameplay and gj-platform review. **Met** — cross-review completed; the one BLOCKER it found (the
  teach-before-use check only fired on the rank-1 route) is fixed in `check_consistency.py`
  (`tool is None and tools`), so any route that uses a tool without declaring `required_tool` now fails.
