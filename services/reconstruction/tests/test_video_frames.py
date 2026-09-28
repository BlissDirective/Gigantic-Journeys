"""Video -> frame-set planning for the open-video corpus (M1-PIPE-01)."""

import pytest
from reconstruction.video_frames import (
    LONG_CLIP_MAX_FRAMES,
    Segment,
    plan_rate,
    segments_from_meta,
    select_sharpest,
)


def _meta(*ranges, duration=100.0):
    return {
        "id": "rooms/x",
        "duration_s": duration,
        "recommended_segments": [{"clip_start_s": a, "clip_end_s": b} for a, b in ranges],
    }


def test_segments_use_recommended_ranges_only_sorted():
    segs = segments_from_meta(_meta((50, 60), (0, 10), (70, 70.2)))
    assert segs == (Segment(0, 10), Segment(50, 60))  # sub-0.5 s sliver dropped


def test_segments_fall_back_to_whole_clip():
    assert segments_from_meta({"duration_s": 12.0}) == (Segment(0.0, 12.0),)


def test_short_clip_is_capped_by_max_fps():
    plan = plan_rate(_meta((0, 20)))
    assert plan.target_fps == pytest.approx(2.0)
    assert plan.candidate_fps == pytest.approx(6.0)
    assert plan.expected_frames == 40


def test_long_clip_is_capped_by_frame_budget():
    plan = plan_rate(_meta((0, 200)))
    assert plan.max_frames == 300
    assert plan.expected_frames == 300
    very_long = plan_rate(_meta((0, 659)))
    assert very_long.max_frames == LONG_CLIP_MAX_FRAMES
    assert very_long.expected_frames <= LONG_CLIP_MAX_FRAMES
    assert plan_rate(_meta((0, 659)), max_frames=150).expected_frames <= 150


def test_select_sharpest_per_window_never_straddles_segments():
    scores = [[1, 5, 2, 9, 3], [4, 4, 8]]
    assert select_sharpest(scores, oversample=3) == [(0, 1), (0, 3), (1, 2)]


def test_select_sharpest_drops_blurry_windows():
    scores = [[100, 90, 110, 2, 1, 3, 95, 99, 100]]
    assert select_sharpest(scores, oversample=3) == [(0, 2), (0, 8)]
