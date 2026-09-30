# `services/packages/`

Owner: gj-platform

The environment package format (splat, collision mesh, scene graph, traversal graph,
environment_spec manifest, thumbnail) and — later — CDN delivery with signed URLs (M4-PLAT-01).

## Now (M1-GAME-01 loader prep — contract + tests)

- **`CONTRACT.md`** — the loader contract the Unity runtime (gj-gameplay) implements: the
  package layout, the load order, and the beacon / route-marker / vista placement rules
  (DESIGN_SYSTEM §1).
- **`package.py`** — the reference implementation: `assemble` writes a package from a
  scene_graph + traversal_graph + environment_spec triple + assets; `validate` runs the
  same checks the loader must (manifest + graph schemas, binary assets present, and the
  three documents cross-consistent via the frozen `check_consistency`). It is the
  conformance spec the C# loader is checked against.
- **Golden fixture** — `unity/Assets/GiganticJourneys/Tests/Environments/desk-tabletop/`, a
  complete package assembled from the frozen desk-tabletop fixtures, for the C# EditMode
  loader test. Its binary assets are presence-only stubs; real corpus packages supply
  loadable assets for the render test (AT-2).
- **`tests/test_package.py`** — the reference validator on the frozen triple, the committed
  golden validating, a drift guard (golden docs == frozen fixtures), and the failure modes
  (missing asset, missing manifest, inconsistent triple).

CDN delivery, signed URLs, unpublish, and the free-tier cap are M4-PLAT-01, added later.
