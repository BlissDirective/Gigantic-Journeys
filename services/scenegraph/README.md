# `services/scenegraph/` — the scene-graph stage (M1-SCEN)

Owner: gj-scenegraph. Turns a reconstructed room into the frozen data contracts the
game and journey generator consume: **mesh cleanup → surface classification →
affordance/traversal graph → summit/route/vista generation → the deterministic
reachability validator** (M1-SCEN-01…05).

The downstream stages emit and consume the `data/schemas/` contracts
(`scene_graph`, `traversal_graph`, `environment_spec`) once frozen (M1-DATA-01).

## M1-SCEN-01 — mesh cleanup (this module)
Traversal-quality pass on the reconstruction's collision OBJ (already
outlier-cleaned + decimated by `services/reconstruction`). It makes the mesh
**watertight** so the character cannot fall out:
- **floater removal** — drop disconnected components below a fraction of the mesh (the largest is always kept);
- **hole fill** — close the small gaps reconstruction leaves in walls/floor;
- **ceiling cap** — fill the open top of an inside-out room scan;
- large intentional openings (doorways, windows) are left alone unless `--fill-all-holes`.

Pure **standard library** — it runs on the decimated OBJ with no Open3D/numpy, so
it is deterministic, fast, GPU-free, and testable on synthetic meshes.

### Run
```bash
python -m scenegraph.cli in.obj out.obj --stats out.stats.json --up-axis y
```
Config knobs: `--min-component-fraction`, `--max-hole-edges`, `--ceiling-band`,
`--up-axis {x,y,z}`, `--fill-all-holes`. The stats JSON records per-step counts
(floaters removed, holes filled, ceiling capped, watertight).

### Layout
- `scenegraph/mesh.py` — `Mesh` + Wavefront OBJ read/write, edge/boundary helpers.
- `scenegraph/cleanup.py` — `CleanupConfig`, `clean_mesh`, floater removal, hole fill, ceiling cap.
- `scenegraph/cli.py` — the command above.
- `tests/` — synthetic-mesh unit tests (floater / hole / ceiling / watertight / OBJ round-trip).

### Acceptance (M1-SCEN-01)
AT-2 (unit tests on synthetic meshes) + AT-3 (deps pinned; pure stdlib → pip-audit
clean) are met here. AT-1 (before/after renders on 3 corpus rooms) runs once the
Operator can execute reconstruction on the corpus (needs the corpus scans + GPU).
