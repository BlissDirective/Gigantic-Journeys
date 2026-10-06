"""VGGT-SLAM-style submap windowing + loop-closure candidate detection."""

import pytest
from reconstruction.submap import loop_closure_candidates, submap_windows


def test_windows_cover_all_frames_with_overlap():
    w = submap_windows(100, window=40, stride=20)
    assert w[0] == (0, 40)
    assert all(b - a <= 40 for a, b in w)
    assert w[-1][1] == 100  # tail covered
    # every frame index is in some window
    covered = set()
    for a, b in w:
        covered.update(range(a, b))
    assert covered == set(range(100))


def test_small_sequence_is_one_window():
    assert submap_windows(10, window=40, stride=20) == [(0, 10)]


def test_bad_args_raise():
    with pytest.raises(ValueError):
        submap_windows(0, 10, 5)
    with pytest.raises(ValueError):
        submap_windows(10, 0, 5)


def test_loop_closure_finds_similar_nonadjacent_submaps():
    # submap 0 and 3 point the same way; 1 and 2 are orthogonal.
    descriptors = [
        [1.0, 0.0],
        [0.0, 1.0],
        [0.0, 1.0],
        [1.0, 0.0],
    ]
    pairs = loop_closure_candidates(descriptors, threshold=0.9, min_gap=2)
    assert (0, 3) in pairs
    # adjacent pairs (gap < 2) are never returned
    assert all(j - i >= 2 for i, j in pairs)


def test_loop_closure_sorted_best_first():
    descriptors = [[1.0, 0.0], [0.0, 1.0], [0.9, 0.1], [1.0, 0.0]]
    pairs = loop_closure_candidates(descriptors, threshold=0.5, min_gap=2)
    assert pairs[0] == (0, 3)  # most similar pair first
