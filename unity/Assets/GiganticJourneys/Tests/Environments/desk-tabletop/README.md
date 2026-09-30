# Golden environment package — desk-tabletop (M1-GAME-01 test fixture)

A complete environment package for the Unity EditMode loader test: the
`environment_spec.json` manifest plus the assets it names (`scene_graph.json`,
`traversal_graph.json`, `splat.spz`, `collision.glb`, `thumbnail.webp`).

Assembled deterministically from the frozen desk-tabletop fixtures in
`data/schemas/environment/fixtures/valid/` by `services/packages/package.py`; a Python
test (`services/packages/tests/test_package.py`) guards against drift and re-validates it.
See `services/packages/CONTRACT.md` for the load order and placement rules the loader
implements.

**The binary assets (`splat.spz`, `collision.glb`, `thumbnail.webp`) are presence-only
stubs** — enough for the parse/contract test to confirm they exist under the names the
manifest declares. A render test (AT-2) needs a real corpus package (the Operator's
reconstruction runs), not these stubs. Do not ship this fixture in a build.
