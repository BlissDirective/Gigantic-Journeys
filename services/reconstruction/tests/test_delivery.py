"""Compression budget planner for on-device delivery (SOG / .spz)."""

import pytest
from reconstruction.delivery import estimate_bytes, plan_compression, sh_bytes

MB = 1024 * 1024


def test_estimate_monotonic_in_sh_degree():
    n = 1_000_000
    sizes = [estimate_bytes(n, d) for d in range(4)]
    assert sizes == sorted(sizes)  # higher SH degree -> more bytes
    assert sh_bytes(3) > sh_bytes(0)


def test_generous_budget_keeps_full_sh():
    plan = plan_compression(1_000_000, 150 * MB)
    assert plan.fits and plan.sh_degree == 3


def test_tight_budget_drops_sh_degree():
    plan = plan_compression(1_000_000, 20 * MB)
    assert plan.fits and plan.sh_degree < 3
    assert plan.estimated_bytes <= 20 * MB


def test_impossible_budget_reports_not_fitting_at_degree_zero():
    plan = plan_compression(100_000_000, 1 * MB)
    assert plan.fits is False and plan.sh_degree == 0


def test_validation():
    with pytest.raises(ValueError):
        plan_compression(1000, 0)
    with pytest.raises(ValueError):
        estimate_bytes(1000, 2, codec_factor=0.0)
    with pytest.raises(ValueError):
        sh_bytes(9)
