# Environment package — loader contract (M1-GAME-01)

What the Unity runtime loads to play one reconstructed environment. `package.py` in this
directory is the **reference implementation** of the parse + validation below; the C#
loader (`unity/`, gj-gameplay) must agree with it, and the golden fixture at
`unity/Assets/GiganticJourneys/Tests/Environments/desk-tabletop/` is its EditMode input.

## Layout

A package is a directory (on device / in the CDN object, M4-PLAT-01). `environment_spec.json`
is the **fixed entry point / manifest**; every other file is named by the package-relative
string in its `assets` block — never a URL, bucket path, or user id (SPEC §3.9, AUTH #034):

```
environment_spec.json      # manifest (frozen schema environment_spec v1.0.0)
scene_graph.json           # assets.scene_graph   (scene_graph v1.0.0)
traversal_graph.json       # assets.traversal_graph (traversal_graph v1.0.0)
splat.spz                  # assets.splat         (3D Gaussian splat)
collision.glb              # assets.collision_mesh (watertight collision mesh)
thumbnail.webp             # assets.thumbnail
```

(The frozen desk-tabletop spec uses exactly these names; a real package's names come from
its own `assets` block — always read them there, never hard-code.)

## Load order (the C# loader)

1. Read `environment_spec.json`; confirm `schema_version == "1.0.0"`.
2. Resolve the five asset filenames from `assets`. Reject a name that is not package-relative.
3. Load `scene_graph.json` and `traversal_graph.json`. `frame` is fixed **A units, +y up,
   left-handed** — consume directly, no conversion. Verify `traversal_graph.movement.config_sha256`
   matches the `movement.json` the build shipped (the controller and the graph must agree).
4. Render the splat (`assets.splat`) and load the collision mesh (`assets.collision_mesh`);
   `surface.mesh.{submesh,triangle_start,triangle_count}` maps a scene-graph surface to its
   triangles in the collision mesh.
5. Place the goals (below). A valid package loads with **no console errors** (AT-1).

A package from the pipeline is already validated (M1-SCEN-05 + the cross-document checker),
so the runtime may trust it; a sideloaded/dev package should be run through `package.validate`
(or its C# equivalent) first.

## Placement (DESIGN_SYSTEM §1, Bible §8) — AT-2

- **Summit beacon** at `summit.position`, visible from the spawn, drawn on top with
  depth-fade so orientation is never lost. `summit.true_peak == false` means the highest
  point was unreachable and the highest reachable plantable point was used.
- **Route markers**, shown only when a route is selected: walk the selected route's
  `beats[].edge_ids` in order, resolve each edge in `traversal_graph.edges`, and draw a
  marker polyline through the edges' `from`/`to` node positions (`traversal_graph.nodes`).
- **Vista sparkles** at each `vistas[].position` (0–3), the sparkle glyph; `access_tier`
  is T0/T1 (vistas are rewards, not gauntlets).
- All markers share the restrained on-top, depth-faded treatment (DESIGN_SYSTEM §1); the
  beam carries summit orientation, never the HUD (DESIGN_SYSTEM §5).

## Spawn

Spawn the avatar at `spawn.position` facing `spawn.facing_deg`, on `spawn.node_id`
(a `traversal_graph` node). Positions are environment-local A units.

## Scope of this prep

Contract + reference validator + golden fixture only (no unverified C#): the runtime
loader and rendering are gj-gameplay's, validated in Unity. The golden fixture's binary
assets (`splat.spz`, `collision.glb`, `thumbnail.webp`) are **presence-only stubs** — a
parse/contract test checks they exist under the declared names; a real corpus package
(the Operator's reconstruction runs) supplies loadable assets for the AT-2 render test.
