"""End-to-end orchestration with the no-GPU fakes."""

import datetime as dt

import pytest
from reconstruction import (
    CostLedger,
    FakeCompressor,
    FakeMesher,
    FakeSfM,
    FakeTrainer,
    ReconstructionConfig,
    ScanInput,
    Source,
    SpendCapError,
    run_pipeline,
)

DAY = dt.date(2026, 9, 24)
MiB = 1024 * 1024


def _clock(values):
    it = iter(values)
    return lambda: next(it)


def _scan(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    return ScanInput(scan_id="room1", image_dir=images, image_count=180, source=Source.CORPUS)


def test_happy_path_produces_package_within_budget(tmp_path):
    ledger = CostLedger()
    run = run_pipeline(
        _scan(tmp_path),
        ReconstructionConfig(),
        sfm=FakeSfM(),
        trainer=FakeTrainer(splat_count=1_800_000),
        compressor=FakeCompressor(size_bytes=64 * MiB),
        mesher=FakeMesher(),
        work_dir=tmp_path / "work",
        ledger=ledger,
        gpu_rate_per_hour_usd=1.0,
        day=DAY,
        clock=_clock([0.0, 600.0, 3000.0, 3300.0, 3600.0]),
    )
    assert run.within_budget is True
    assert run.package.scan_id == "room1"
    assert run.package.splat.splat_count == 1_800_000
    assert run.package.total_size_bytes == 64 * MiB + run.package.mesh.size_bytes
    assert run.cost.usd == pytest.approx(1.0)  # 1 h at $1/h
    assert run.stage_seconds == {"sfm": 600.0, "train": 2400.0, "compress": 300.0, "mesh": 300.0}
    assert len(ledger.records()) == 1


class _StubMeter:
    """Stands in for ResourceMeter: fixed usage, records start/stop."""

    cores = 8.0
    memory_gib = 16.0

    def __init__(self):
        self.started = False

    def start(self):
        self.started = True
        return self

    def stop(self):
        from reconstruction.cost import ResourceUsage

        # 1 h: 10 cores billed, 20 GiB billed.
        return ResourceUsage(3600.0, 36000.0, 30000.0, 72000.0, 20.0, "test")


def test_metered_run_adds_cpu_and_memory_cost(tmp_path):
    meter = _StubMeter()
    run = run_pipeline(
        _scan(tmp_path),
        ReconstructionConfig(),
        sfm=FakeSfM(),
        trainer=FakeTrainer(),
        compressor=FakeCompressor(),
        mesher=FakeMesher(),
        work_dir=tmp_path / "work",
        ledger=CostLedger(),
        gpu_rate_per_hour_usd=1.0,
        day=DAY,
        clock=_clock([0.0, 900.0, 2700.0, 3000.0, 3600.0]),
        meter=meter,
        cpu_rate_per_core_hour_usd=0.05,
        memory_rate_per_gib_hour_usd=0.01,
    )
    assert meter.started
    assert run.cost.gpu_usd == pytest.approx(1.0)
    assert run.cost.cpu_usd == pytest.approx(0.5)  # 10 core-h x $0.05
    assert run.cost.memory_usd == pytest.approx(0.2)  # 20 GiB-h x $0.01
    assert run.cost.usd == pytest.approx(1.7)


def test_over_budget_is_flagged_not_fatal(tmp_path):
    run = run_pipeline(
        _scan(tmp_path),
        ReconstructionConfig(),
        sfm=FakeSfM(),
        trainer=FakeTrainer(),
        compressor=FakeCompressor(size_bytes=200 * MiB),
        mesher=FakeMesher(),
        work_dir=tmp_path / "work",
        ledger=CostLedger(),
        gpu_rate_per_hour_usd=1.0,
        day=DAY,
        clock=_clock([0.0, 450.0, 900.0, 1350.0, 1800.0]),
    )
    assert run.within_budget is False


def test_spend_cap_halts_before_any_work(tmp_path):
    ledger = CostLedger(spike_cap_usd=0.10)
    work = tmp_path / "work"
    with pytest.raises(SpendCapError):
        run_pipeline(
            _scan(tmp_path),
            ReconstructionConfig(),
            sfm=FakeSfM(),
            trainer=FakeTrainer(),
            compressor=FakeCompressor(),
            mesher=FakeMesher(),
            work_dir=work,
            ledger=ledger,
            gpu_rate_per_hour_usd=1.0,
            day=DAY,
            clock=_clock([0.0, 600.0, 3000.0, 3300.0, 3600.0]),
        )
    assert ledger.records() == ()
    # Nothing was trained: no splat/mesh artifacts were written.
    assert not list(work.glob("*.ply"))
    assert not list(work.glob("*.obj"))
