"""CLI: export a traversal_graph.json from a scene_graph.json (M1-SCEN-03).

    python services/traversal/graph_cli.py scene_graph.json traversal_graph.json \\
        [--movement config/movement.json] [--no-tools]

Edges are validated against config/movement.json at the 85 % margin as they are built.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import graph
import movement


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1-SCEN-03 traversal-graph export")
    ap.add_argument("input", help="scene_graph.json (M1-SCEN-02 output)")
    ap.add_argument("output", help="traversal_graph.json to write")
    ap.add_argument("--movement", help="config/movement.json (defaults to the repo copy)")
    ap.add_argument("--no-tools", action="store_true", help="omit grapple / pole-vault edges")
    a = ap.parse_args(argv)

    scene = json.loads(Path(a.input).read_text(encoding="utf-8"))
    config_path = Path(a.movement) if a.movement else movement.DEFAULT_PATH
    cfg = movement.load(config_path)
    tools = frozenset() if a.no_tools else frozenset({"grapple", "pole-vault"})
    doc = graph.build_traversal_graph(scene, cfg=cfg, config_path=config_path, tools=tools)
    Path(a.output).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(f"{len(doc['nodes'])} nodes, {len(doc['edges'])} edges -> {a.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
