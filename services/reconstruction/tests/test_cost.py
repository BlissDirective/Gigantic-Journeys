"""Cost accounting and spend-cap enforcement (M1-CAPT-02 AT-2, AUTH #031)."""

import datetime as dt

import pytest
from reconstruction import CostLedger, SpendCapError, estimate_usd

DAY = dt.date(2026, 9, 24)


def test_estimate_uses_worst_case_hours():
    # 0.75 h * $2/h = $1.50
    assert estimate_usd(2.0) == pytest.approx(1.50)


def test_scan_cost_usd():
    ledger = CostLedger()
    cost = ledger.record("s1", gpu_seconds=1800, rate_per_hour_usd=2.0, day=DAY)
    # half an hour at $2/h
    assert cost.usd == pytest.approx(1.0)
    assert ledger.spike_total_usd() == pytest.approx(1.0)
    assert ledger.daily_total_usd(DAY) == pytest.approx(1.0)


def test_guard_passes_under_caps():
    ledger = CostLedger()
    ledger.guard(estimate_usd(1.0), DAY)  # $0.75, well under both caps


def test_guard_blocks_spike_cap():
    ledger = CostLedger(spike_cap_usd=0.10)
    with pytest.raises(SpendCapError, match="spike cap"):
        ledger.guard(estimate_usd(1.0), DAY)


def test_guard_blocks_daily_cap():
    ledger = CostLedger(spike_cap_usd=1000.0, daily_cap_usd=0.10)
    with pytest.raises(SpendCapError, match="daily cap"):
        ledger.guard(estimate_usd(1.0), DAY)


def test_daily_cap_is_per_day():
    ledger = CostLedger(daily_cap_usd=2.0)
    # $1.50 on an earlier day does not block a run on DAY.
    ledger.record("s0", gpu_seconds=2700, rate_per_hour_usd=2.0, day=dt.date(2026, 9, 23))
    ledger.guard(estimate_usd(2.0), DAY)  # $1.50 on DAY, under the $2 daily cap
