"""CLI: clean a reconstruction collision OBJ into a watertight traversal mesh.

python -m scenegraph.cli in.obj out.obj --stats out.stats.json --up-axis y
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cleanup import CleanupConfig, clean_mesh
from .mesh import read_obj, write_obj


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1-SCEN-01 mesh cleanup")
    ap.add_argument("input", help="reconstruction collision mesh (.obj)")
    ap.add_argument("output", help="cleaned watertight mesh (.obj)")
    ap.add_argument("--stats", help="optional path to write the stats JSON")
    ap.add_argument("--up-axis", default="y", choices=["x", "y", "z"])
    ap.add_argument("--min-component-fraction", type=float, default=0.02)
    ap.add_argument("--max-hole-edges", type=int, default=40)
    ap.add_argument("--ceiling-band", type=float, default=0.15)
    ap.add_argument("--fill-all-holes", action="store_true")
    a = ap.parse_args(argv)

    mesh = read_obj(Path(a.input))
    cfg = CleanupConfig(
        min_component_fraction=a.min_component_fraction,
        max_hole_edges=a.max_hole_edges,
        up_axis=a.up_axis,
        ceiling_band=a.ceiling_band,
        fill_all_holes=a.fill_all_holes,
    )
    cleaned, stats = clean_mesh(mesh, cfg)
    write_obj(cleaned, Path(a.output))
    payload = json.dumps(stats.as_dict(), indent=2)
    if a.stats:
        Path(a.stats).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
