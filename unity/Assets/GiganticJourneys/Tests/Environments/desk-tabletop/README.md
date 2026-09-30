# Golden environment package — desk-tabletop (M1-GAME-01 test fixture)

The three JSON documents of an environment package for the Unity EditMode loader test:
`environment_spec.json` (the manifest) plus `scene_graph.json` and `traversal_graph.json`.
Assembled deterministically from the frozen desk-tabletop fixtures in
`data/schemas/environment/fixtures/valid/` by `services/packages/package.py`; a Python test
(`services/packages/tests/test_package.py`) drift-guards them against those fixtures.

**The binary assets are intentionally NOT committed.** `splat.spz`, `collision.glb` and
`thumbnail.webp` are gitignored large-binary formats (and a bogus `.glb` would trip Unity's
asset importer). The loader test materialises tiny presence-only stubs in its setup — the
Python reference does this via `package.assemble`; the C# EditMode setup writes the same
three files (or loads a real corpus package). A render test (AT-2) needs a real corpus
package, not stubs. See `services/packages/CONTRACT.md` for the load order and placement
rules the loader implements.
