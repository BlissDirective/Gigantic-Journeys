# M1-GAME-01: C# environment loader + goal elements (build notes)

2026-10-02, gj-operator. Contract: `services/packages/CONTRACT.md` (reference `services/packages/package.py`).
The ticket stays **in-progress**. Parse, validation and placement are done and verified. Drawing a real
reconstruction needs runtime `.spz`/`.glb` decoding, which is not built yet (see the end of this file).

## What was built (`unity/Assets/GiganticJourneys/Environment/`, assembly `GJ.Environment`)
- **`EnvironmentPackage`** follows the CONTRACT load order. It reads `environment_spec.json` (`schema_version` 1.0.0),
  resolves the five asset names from `assets`, rejects any name that is not a bare package-relative file
  (`..`, `/`, `\`, `:`/schemes, dotfiles) and requires each file to be present. It loads `scene_graph.json` and
  `traversal_graph.json` (each 1.0.0, same `environment_id`, frame A / +y / left-handed, consumed with no
  conversion) and verifies `traversal_graph.movement.config_sha256` against the sha256 of the shipped
  `StreamingAssets/movement.json`. Cross-checks: spawn and summit nodes exist, every route beat edge exists, every
  edge's endpoints exist, every vista node exists, and there are at most 3 vistas. It also maps each surface to its collision-mesh triangles
  (`surface.mesh`). Errors name the field and the file.
- **`GoalPlacement`** gives the spawn yaw (`facing_deg` is Unity Euler y, i.e. atan2(dx, dz) as in
  services/scenegraph), the route polyline (beats → edges → node positions, repeated joints collapsed) and the footprint marks
  (even spacing, alternating feet, heading along the route).
- **`EnvironmentLoader`** (component) builds the scene under its transform: Spawn pose, **summit beam**
  (thin vertical light, on by default, `SetSummitBeam` is the player toggle), **vista sparkles** (0–3) and
  **route footprints** (none until `SelectRoute`, so explorers see none by default). It draws the splat from a bundled
  `GaussianSplatAsset` (with `SplatRenderSettingsApplier`, which also adds the Metal-safe sort from
  M1-UNITY-01) and the collision `MeshCollider` from a bundled `Mesh`.
- **`Resources/GJ/OnTopMarker.shader`** is the shared DESIGN_SYSTEM §1 treatment: additive thin light, no solid
  geometry, `ZTest Always` (always on top). The part behind real geometry fades to 35% when the URP depth
  texture is on. The shapes (beam, sparkle, footprint) are procedural, with no textures. Colours: amberLight beam/sparkle,
  faint paper.cream footprints.

## Evidence (box: Unity 6000.0.84f1, xvfb + Vulkan)
`M1-GAME-01/environment-loader-tests.xml`: **22/22 passed** (`EnvironmentPackageTests`):
- The golden desk-tabletop package (JSON docs plus presence-only binary stubs, as the Python reference does) loads
  against the shipped movement.json. This also proves the M0-UNITY-03 hash refresh: the golden `config_sha256` equals
  sha256(StreamingAssets/movement.json) equals sha256(config/movement.json).
- The same failure modes as package.py are rejected: missing manifest or asset, non-relative names (5 cases), wrong
  schema_version, mismatched environment_id, unknown route edge, malformed JSON, and a stale movement sha.
- Placement: route polyline order, footprint spacing and alternation, spawn yaw.
- The loader builds spawn, beacon, vistas and the hidden route, `SelectRoute` shows and hides it, the beam toggles, and
  there are **no console errors** (AT-1; `LogAssert.NoUnexpectedReceived`). The marker shader compiles (`ShaderUtil.ShaderHasError`).

Screenshot: `qa/evidence/M1-GAME-01/01-golden-goal-markers.png` (beam, sparkles, footprints on the golden package).

## Open
- **Runtime asset decode.** `.spz` → `GaussianSplatAsset` at runtime (aras-p only imports in the Editor) and
  `.glb` → `Mesh` (needs a glTF importer package such as glTFast: a package add with license and pin per
  SECURITY_CHECKLIST §7). Until then the loader logs one info line per asset and places everything else.
  This blocks AT-1 on a corpus package and AT-2's on-device look.
- **AT-2 visuals** need a real corpus package and a device look (beam readable through geometry, depth-fade).
- Putting a scene with a splat into the build list is also what M1-UNITY-01 AT-2 needs for the on-device sort check.
