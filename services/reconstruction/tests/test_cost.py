"""Cost accounting and spend-cap enforcement (M1-CAPT-02 AT-2, AUTH #031)."""

import datetime as dt

import pytest
from reconstruction import CostLedger, SpendCapError, estimate_usd
from reconstruction.cost import ResourceMeter, reserved_only_usage

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


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_meter_bills_max_of_reserved_and_used():
    clock = _Clock()
    cpu = {"s": 0.0}
    mem = {"b": 4 * 1024**3}
    meter = ResourceMeter(
        cores=8.0,
        memory_gib=16.0,
        interval=3600.0,  # the background thread never fires during the test
        cpu_reader=lambda: (cpu["s"], "test"),
        mem_reader=lambda: mem["b"],
        clock=clock,
    )
    meter.start()
    # 100 s idle-ish: 2 vCPU busy = 1 core used < 8 reserved; 4 GiB < 16 reserved.
    clock.t, cpu["s"] = 100.0, 200.0
    meter.sample()
    # 100 s burst: 40 vCPU busy = 20 cores > 8 reserved; 24 GiB > 16 reserved.
    clock.t, cpu["s"], mem["b"] = 200.0, 200.0 + 4000.0, 24 * 1024**3
    usage = meter.stop()
    assert usage.source == "test"
    assert usage.wall_seconds == pytest.approx(200.0)
    assert usage.billed_core_seconds == pytest.approx(8 * 100 + 20 * 100)
    assert usage.used_core_seconds == pytest.approx(1 * 100 + 20 * 100)
    assert usage.billed_gib_seconds == pytest.approx(16 * 100 + 24 * 100)
    assert usage.peak_memory_gib == pytest.approx(24.0)
    assert usage.cpu_usd(3600.0) == pytest.approx(2800.0)  # $1/core-s for easy maths


def test_meter_without_counters_bills_the_reservation():
    clock = _Clock()
    meter = ResourceMeter(
        cores=4.0,
        memory_gib=8.0,
        interval=3600.0,
        cpu_reader=lambda: None,
        mem_reader=lambda: None,
        clock=clock,
    )
    meter.start()
    clock.t = 50.0
    usage = meter.stop()
    assert usage.source == "reserved-only"
    assert usage.billed_core_seconds == pytest.approx(200.0)
    assert usage.billed_gib_seconds == pytest.approx(400.0)
    assert reserved_only_usage(50.0, 4.0, 8.0).billed_core_seconds == pytest.approx(200.0)


def test_scan_cost_total_includes_cpu_and_memory():
    ledger = CostLedger()
    cost = ledger.record("s1", 3600, 1.0, day=DAY, cpu_usd=0.4, memory_usd=0.1)
    assert cost.gpu_usd == pytest.approx(1.0)
    assert cost.usd == pytest.approx(1.5)
    assert ledger.spike_total_usd() == pytest.approx(1.5)
