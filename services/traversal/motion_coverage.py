"""Motion-coverage metric for Experiment B (M2-RES-01, AUTH #043 #8) — Brain-B reference.

Experiment B augments the clip database **offline** so the matcher has a clip for every
(verb × geometry) the corpus traversal graphs actually demand. This module makes "coverage"
concrete and measurable so the augmentation (Operator/GPU) has a before/after target:

* :func:`demanded_grid` — the distinct (verb, distance-bin, rise-bin) cells the real routes need.
* :func:`coverage` — what fraction of the demanded cells a clip inventory serves, and the gaps.
* :func:`coverage_delta` — baseline vs augmented, and which gap cells the augmentation closed.

A clip "inventory" is modelled as the set of cells it can serve within the matcher's warp
tolerance (the Operator's pipeline builds that set from the real clips). Derived/reference only —
no frozen schema or ``movement.json`` change. Named ``motion_coverage`` (not ``coverage``) to avoid
shadowing the coverage.py PyPI package. Standard library only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import affordances

# Demand bins, chosen around the movement.json reach constants (A units). A cell is a coarse
# (verb, distance band, signed-rise band) bucket — fine enough to drive clip generation, coarse
# enough that one good clip (motion-warped) covers the cell.
_DIST_BINS: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0)
_RISE_BINS: tuple[float, ...] = (-3.0, -1.5, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)

# (verb, distance-bin index, rise-bin index)
Cell = tuple[str, int, int]


def _bin(value: float, bins: tuple[float, ...]) -> int:
    """Index of the first bin edge ``value`` is below; ``len(bins)`` if it is above them all."""
    for i, edge in enumerate(bins):
        if value < edge:
            return i
    return len(bins)


def coverage_cell(edge: dict) -> Cell:
    """The demand cell an edge falls in. Raises on an unknown verb or a missing reach field."""
    verb = edge["verb"]
    if verb not in affordances.VERB_TIER:
        raise ValueError(f"unknown verb {verb!r}")
    return (
        verb,
        _bin(float(edge["distance_A"]), _DIST_BINS),
        _bin(float(edge["rise_A"]), _RISE_BINS),
    )


def edges_of_graphs(graphs: list[dict]) -> list[dict]:
    """Flatten the edges of several traversal graphs (e.g. one per corpus room)."""
    return [e for g in graphs for e in g["edges"]]


def demanded_grid(edges: list[dict]) -> dict[Cell, int]:
    """Map each demand cell to how many edges land in it (the corpus's motion demand)."""
    out: dict[Cell, int] = {}
    for e in edges:
        cell = coverage_cell(e)
        out[cell] = out.get(cell, 0) + 1
    return out


@dataclass(frozen=True)
class CoverageReport:
    demanded: int  # distinct demanded cells
    covered: int
    fraction: float
    gaps: tuple[Cell, ...]  # demanded cells with no clip, sorted


def coverage(demanded: dict[Cell, int] | set[Cell], inventory: set[Cell]) -> CoverageReport:
    """How much of the demanded grid the clip ``inventory`` covers, and the uncovered gaps."""
    dem = set(demanded)
    covered = dem & inventory
    gaps = tuple(sorted(dem - inventory))
    fraction = len(covered) / len(dem) if dem else 1.0
    return CoverageReport(len(dem), len(covered), fraction, gaps)


@dataclass(frozen=True)
class CoverageDelta:
    before: CoverageReport
    after: CoverageReport
    gaps_closed: tuple[Cell, ...]


def coverage_delta(
    demanded: dict[Cell, int] | set[Cell], baseline: set[Cell], augmented: set[Cell]
) -> CoverageDelta:
    """Baseline vs augmented coverage, and which demanded gap cells the augmentation closed."""
    before = coverage(demanded, baseline)
    after = coverage(demanded, augmented)
    closed = tuple(sorted(set(before.gaps) - set(after.gaps)))
    return CoverageDelta(before, after, closed)


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) < 2:
        print("usage: python -m motion_coverage <traversal_graph.json> [more.json ...]")
        raise SystemExit(2)
    graphs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:]]
    grid = demanded_grid(edges_of_graphs(graphs))
    print(f"{len(grid)} demanded cells across {len(graphs)} graph(s):")
    for cell, n in sorted(grid.items()):
        print(f"  {cell[0]:<16} dist-bin {cell[1]} rise-bin {cell[2]}  x{n}")
