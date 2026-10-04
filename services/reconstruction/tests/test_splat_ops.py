"""Splat cap and mesh-cleaning rules (pure Python; the container mirrors them)."""

import math

import pytest
from reconstruction import ReconstructionError
from reconstruction.ns_finish import ply_fields, ply_header
from reconstruction.splat_ops import (
    MeshFilter,
    cap_keep_indices,
    growth_headroom,
    importance,
    inside,
    percentile,
    robust_bounds,
    sigmoid,
)


def test_importance_prefers_opaque_and_large_splats():
    big = importance(2.0, [math.log(0.1)] * 3)
    faint = importance(-4.0, [math.log(0.1)] * 3)
    tiny = importance(2.0, [math.log(0.001)] * 3)
    assert big > faint and big > tiny
    # Area of the two largest axes: the smallest axis does not matter.
    assert importance(0.0, [0.0, 0.0, -9.0]) == pytest.approx(0.5)
    assert sigmoid(-800.0) == pytest.approx(0.0) and sigmoid(800.0) == pytest.approx(1.0)


def test_hard_cap_keeps_the_most_important_splats():
    scores = [0.5, 0.9, 0.1, 0.9, 0.3]
    assert cap_keep_indices(scores, 2) == [1, 3]
    assert cap_keep_indices(scores, 3) == [0, 1, 3]
    assert cap_keep_indices(scores, 10) == [0, 1, 2, 3, 4]
    with pytest.raises(ReconstructionError):
        cap_keep_indices(scores, 0)


def test_stress_cap_on_a_synthetic_scene_over_budget():
    # 20k splats, budget 2k: the cap holds exactly and keeps the top scores.
    n, budget = 20_000, 2_000
    scores = [importance((i % 97) / 10 - 5, [-(i % 13) / 3, -(i % 7) / 2, -4.0]) for i in range(n)]
    keep = cap_keep_indices(scores, budget)
    assert len(keep) == budget
    floor = min(scores[i] for i in keep)
    dropped = set(range(n)) - set(keep)
    assert all(scores[i] <= floor for i in dropped)


def test_growth_headroom():
    assert growth_headroom(10, 15) == 5
    assert growth_headroom(15, 15) == 0
    assert growth_headroom(20, 15) == 0


def test_percentile_matches_numpy_linear():
    vals = [5.0, 1.0, 3.0, 2.0, 4.0]
    assert percentile(vals, 0) == 1.0
    assert percentile(vals, 100) == 5.0
    assert percentile(vals, 50) == 3.0
    assert percentile(vals, 10) == pytest.approx(1.4)
    with pytest.raises(ReconstructionError):
        percentile([], 50)


def test_robust_bounds_crop_far_away_strays():
    room = [(x / 10, y / 10, z / 10) for x in range(10) for y in range(10) for z in range(10)]
    strays = [(500.0, 0.0, 0.0), (0.0, -800.0, 0.0)]
    box = robust_bounds(room + strays, 1.0, 0.05)
    assert all(inside(p, box) for p in room)
    assert not any(inside(p, box) for p in strays)


def test_mesh_filter_defaults_and_validation():
    rules = MeshFilter()
    assert rules.bounds_mode == "dense"
    assert rules.min_opacity_logit == pytest.approx(0.0)  # alpha 0.5
    assert MeshFilter(min_opacity=0.0).min_opacity_logit == -math.inf
    with pytest.raises(ReconstructionError):
        MeshFilter(min_opacity=1.0)
    with pytest.raises(ReconstructionError):
        MeshFilter(target_triangles=0)
    with pytest.raises(ReconstructionError):
        MeshFilter(bounds_mode="sphere")


def test_ply_layout_matches_nerfstudio_export():
    fields = ply_fields(45)  # SH degree 3
    assert fields[:9] == ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2"]
    assert fields[9] == "f_rest_0" and fields[53] == "f_rest_44"
    assert fields[-8:] == ["opacity", "scale_0", "scale_1", "scale_2"] + [
        f"rot_{i}" for i in range(4)
    ]
    header = ply_header(3, fields, "1.1.5").decode()
    assert "element vertex 3\n" in header and header.endswith("end_header\n")
    assert header.count("property float") == 62


def test_display_prune_drops_faint_giant_and_needle_splats():
    from reconstruction.splat_ops import DisplayPrune, display_shape_keep

    rules = DisplayPrune()
    cap, floor = math.log(0.02), math.log(0.005)
    ok = [math.log(0.004)] * 3
    assert display_shape_keep(2.0, ok, rules, cap, floor)
    assert not display_shape_keep(-5.0, ok, rules, cap, floor), "faint"
    assert not display_shape_keep(2.0, [math.log(0.05), -6.0, -6.0], rules, cap, floor), "giant"
    needle = [math.log(0.01), math.log(0.0002), math.log(0.0002)]
    assert not display_shape_keep(2.0, needle, rules, cap, floor), "needle"
    small_needle = [math.log(0.004), math.log(0.0001), math.log(0.0001)]
    assert display_shape_keep(2.0, small_needle, rules, cap, floor), "tiny streaks stay"
    with pytest.raises(ReconstructionError):
        DisplayPrune(max_anisotropy=1.0)
    with pytest.raises(ReconstructionError):
        DisplayPrune(budget=0)
