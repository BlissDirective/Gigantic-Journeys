"""CLI: classify a cleaned collision OBJ into scene_graph.json (M1-SCEN-02).

    python -m scenegraph.scene_cli cleaned.obj scene_graph.json \\
        --env-id 3c2b1a09-8f7e-4d6c-b5a4-938271605f4e --capture-mode tabletop \\
        --scale-multiplier 12 --scale-method inferred-studs --collision-out collision.obj

Scale (multiplier + method) comes from the capture bundle's metric scale, not guessed
here. The material/semantic vision pass is deferred (SPEC §3.3, self-hosted), so this
emits geometric classes with material ``unknown``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .mesh import read_obj, write_obj
from .scene import CaptureMeta, build_scene_graph


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1-SCEN-02 surface classification")
    ap.add_argument("input", help="cleaned collision mesh (.obj) from M1-SCEN-01")
    ap.add_argument("output", help="scene_graph.json to write")
    ap.add_argument("--env-id", required=True, help="environments.id (UUID)")
    ap.add_argument("--capture-mode", required=True, choices=["room", "tabletop"])
    ap.add_argument("--scale-multiplier", type=float, default=12.0)
    ap.add_argument(
        "--scale-method",
        default="default",
        choices=["default", "inferred-furniture", "inferred-studs", "inferred-other"],
    )
    ap.add_argument("--collision-out", help="reordered collision OBJ (surface triangle runs)")
    a = ap.parse_args(argv)

    mesh = read_obj(Path(a.input))
    meta = CaptureMeta(
        environment_id=a.env_id,
        capture_mode=a.capture_mode,
        scale_multiplier=a.scale_multiplier,
        scale_method=a.scale_method,
    )
    doc, collision = build_scene_graph(mesh, meta)
    Path(a.output).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    if a.collision_out:
        write_obj(collision, Path(a.collision_out))
    print(f"{len(doc['surfaces'])} surfaces -> {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
