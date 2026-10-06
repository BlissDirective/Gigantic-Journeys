"""Train-short / test-long positional index scheme for a many-view reconstructor."""

import pytest
from reconstruction import PositionalIndexScheme


def test_training_indices_are_distinct_sorted_and_in_range():
    s = PositionalIndexScheme(max_index=256, dim=32)
    idx = s.sample_training_indices(20, seed=1)
    assert len(idx) == 20
    assert len(set(idx)) == 20  # distinct
    assert idx == sorted(idx)
    assert all(0 <= i < 256 for i in idx)


def test_training_indices_are_deterministic_per_seed():
    s = PositionalIndexScheme(max_index=256, dim=32)
    assert s.sample_training_indices(20, seed=7) == s.sample_training_indices(20, seed=7)
    assert s.sample_training_indices(20, seed=7) != s.sample_training_indices(20, seed=8)


def test_too_many_views_for_the_pool_is_rejected():
    s = PositionalIndexScheme(max_index=16, dim=8)
    with pytest.raises(ValueError, match="positional pool"):
        s.sample_training_indices(17, seed=0)


def test_short_batches_still_cover_the_whole_range():
    # 20-view batches over many trials should exercise (nearly) every one of 256 slots.
    s = PositionalIndexScheme(max_index=256, dim=32)
    assert s.training_coverage(num_views=20, trials=400, seed=0) == pytest.approx(1.0)


def test_inference_indices_spread_within_the_trained_range():
    s = PositionalIndexScheme(max_index=256, dim=32)
    idx = s.inference_indices(50)
    assert len(idx) == 50
    assert idx[0] == 0.0 and idx[-1] == pytest.approx(255.0)
    assert idx == sorted(idx)
    assert all(0.0 <= v <= 255.0 for v in idx)


def test_test_long_never_extrapolates_past_the_pool():
    # Far more views than slots: positions are interpolated but stay in [0, max-1].
    s = PositionalIndexScheme(max_index=64, dim=16)
    idx = s.inference_indices(1000)
    assert len(idx) == 1000
    assert idx[0] == 0.0 and idx[-1] == pytest.approx(63.0)
    assert all(0.0 <= v <= 63.0 for v in idx)
    assert all(a <= b for a, b in zip(idx, idx[1:], strict=False))


def test_single_view_inference():
    s = PositionalIndexScheme(max_index=64, dim=16)
    assert s.inference_indices(1) == [0.0]


def test_embedding_shape_bounds_and_determinism():
    s = PositionalIndexScheme(max_index=256, dim=32)
    emb = s.embedding(12.5)
    assert len(emb) == 32
    assert all(-1.0 <= v <= 1.0 for v in emb)
    assert s.embedding(12.5) == emb  # deterministic
    assert s.embedding(13.5) != emb  # distinct positions differ


def test_scheme_validation():
    with pytest.raises(ValueError, match="max_index"):
        PositionalIndexScheme(max_index=1, dim=8)
    with pytest.raises(ValueError, match="dim"):
        PositionalIndexScheme(max_index=16, dim=7)
