"""Coverage-metric tests (Experiment B, M2-RES-01) — on the frozen desk-tabletop graph."""

import json
from pathlib import Path

import motion_coverage as mc
import pytest

REPO = Path(__file__).resolve().parents[3]
FIX = REPO / "data" / "schemas" / "environment" / "fixtures" / "valid"


def _graph():
    return json.loads((FIX / "traversal_graph.desk-tabletop.json").read_text(encoding="utf-8"))


def test_demanded_grid_counts_every_edge():
    g = _graph()
    grid = mc.demanded_grid(g["edges"])
    assert sum(grid.values()) == len(g["edges"])  # every edge lands in exactly one cell
    assert 0 < len(grid) <= len(g["edges"])  # distinct cells, no more than edges


def test_coverage_cell_bins_a_known_edge():
    # edge-1 is walk, distance 7.5 A (above the top distance bin), rise 0.0 (the 0..0.5 band)
    edge1 = next(e for e in _graph()["edges"] if e["id"] == "edge-1")
    assert mc.coverage_cell(edge1) == ("walk", 7, 4)


def test_full_inventory_covers_everything():
    grid = mc.demanded_grid(_graph()["edges"])
    rep = mc.coverage(grid, set(grid))
    assert rep.fraction == 1.0
    assert rep.gaps == ()
    assert rep.covered == rep.demanded == len(grid)


def test_empty_inventory_covers_nothing():
    grid = mc.demanded_grid(_graph()["edges"])
    rep = mc.coverage(grid, set())
    assert rep.fraction == 0.0
    assert set(rep.gaps) == set(grid)


def test_partial_inventory_reports_gaps():
    grid = mc.demanded_grid(_graph()["edges"])
    one = next(iter(grid))
    rep = mc.coverage(grid, {one})
    assert rep.covered == 1
    assert one not in rep.gaps
    assert len(rep.gaps) == len(grid) - 1


def test_coverage_delta_counts_closed_gaps():
    grid = mc.demanded_grid(_graph()["edges"])
    d = mc.coverage_delta(grid, baseline=set(), augmented=set(grid))
    assert d.before.fraction == 0.0
    assert d.after.fraction == 1.0
    assert set(d.gaps_closed) == set(grid)  # augmentation closed every gap


def test_edges_of_graphs_merges_demand():
    g = _graph()
    one = mc.demanded_grid(mc.edges_of_graphs([g]))
    two = mc.demanded_grid(mc.edges_of_graphs([g, g]))
    assert set(one) == set(two)  # same cells
    assert sum(two.values()) == 2 * sum(one.values())  # doubled demand


def test_unknown_verb_rejected():
    with pytest.raises(ValueError):
        mc.coverage_cell({"verb": "backflip", "distance_A": 1.0, "rise_A": 0.0})
