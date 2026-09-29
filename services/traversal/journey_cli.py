"""CLI: generate environment_spec.json from scene_graph + traversal_graph (M1-SCEN-04).

    python services/traversal/journey_cli.py scene_graph.json traversal_graph.json \\
        environment_spec.json [--seed 0]

Every route is validated by the M1-SCEN-05 reachability validator before the spec is
written; generation fails loudly rather than emitting an unreachable journey.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import journey


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1-SCEN-04 journey generation")
    ap.add_argument("scene_graph", help="scene_graph.json (M1-SCEN-02)")
    ap.add_argument("traversal_graph", help="traversal_graph.json (M1-SCEN-03)")
    ap.add_argument("output", help="environment_spec.json to write")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)

    scene = json.loads(Path(a.scene_graph).read_text(encoding="utf-8"))
    graph = json.loads(Path(a.traversal_graph).read_text(encoding="utf-8"))
    try:
        spec = journey.generate_environment_spec(scene, graph, seed=a.seed)
    except journey.JourneyError as exc:
        print(f"journey generation failed: {exc}", file=sys.stderr)
        return 1
    Path(a.output).write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    tf = " (template fallback)" if spec["generation"]["template_fallback"] else ""
    print(f"{len(spec['routes'])} routes, {len(spec['vistas'])} vistas -> {a.output}{tf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
