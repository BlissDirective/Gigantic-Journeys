"""End-to-end reconstruction orchestration with dependency-injected adapters.

The pipeline is trainer- and backend-agnostic: tests inject the fakes, the
container injects the real COLMAP/GLOMAP + gsplat/Brush + Open3D adapters. Two
hard gates run before any GPU work: the commercial-license check and the spend
cap.
"""

from __future__ import annotations

import datetime as dt
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from . import licenses
from .compress import Compressor
from .cost import (
    MODAL_CPU_CORE_HOUR_USD,
    MODAL_MEMORY_GIB_HOUR_USD,
    CostLedger,
    ResourceMeter,
    ResourceUsage,
    ScanCost,
    estimate_usd,
)
from .mesh import Mesher
from .models import CameraPoses, EnvironmentPackage, ReconstructionConfig, ScanInput, SplatModel
from .sfm import SfM
from .trainer import Trainer


@dataclass(frozen=True)
class ReconstructionRun:
    """The outcome of one pipeline run."""

    package: EnvironmentPackage
    cost: ScanCost
    within_budget: bool
    # Wall seconds per stage: sfm / train / compress / mesh.
    stage_seconds: dict[str, float] = field(default_factory=dict)
    poses: CameraPoses | None = None
    model: SplatModel | None = None
    usage: ResourceUsage | None = None


def run_pipeline(
    scan: ScanInput,
    config: ReconstructionConfig,
    *,
    sfm: SfM,
    trainer: Trainer,
    compressor: Compressor,
    mesher: Mesher,
    work_dir: Path,
    ledger: CostLedger,
    gpu_rate_per_hour_usd: float,
    day: dt.date | None = None,
    clock: Callable[[], float] = time.monotonic,
    meter: ResourceMeter | None = None,
    cpu_rate_per_core_hour_usd: float = MODAL_CPU_CORE_HOUR_USD,
    memory_rate_per_gib_hour_usd: float = MODAL_MEMORY_GIB_HOUR_USD,
) -> ReconstructionRun:
    """Run SfM -> train -> compress -> mesh, recording cost and budget status.

    With a ``meter`` (the reserved CPU cores / memory of the host), the cost adds
    CPU + memory priced as billed (``max(reserved, used)``) to the GPU time;
    without one, the cost is GPU-only (tests, dry runs).
    """
    day = day or dt.date.today()
    work_dir.mkdir(parents=True, exist_ok=True)

    # Fail fast on licensing and spend before any GPU work. The estimate prices
    # the reserved CPU + memory too when they are known.
    licenses.assert_commercial_safe()
    hourly = gpu_rate_per_hour_usd
    if meter is not None:
        hourly += meter.cores * cpu_rate_per_core_hour_usd
        hourly += meter.memory_gib * memory_rate_per_gib_hour_usd
    ledger.guard(estimate_usd(hourly), day)

    if meter is not None:
        meter.start()
    # One clock read per stage boundary: t[0] start ... t[4] end.
    t = [clock()]
    poses = sfm.run(scan, work_dir)
    t.append(clock())
    model = trainer.train(poses, work_dir, config)
    t.append(clock())
    compressed = compressor.compress(model, work_dir, config)
    t.append(clock())
    mesh = mesher.derive(model, work_dir)
    t.append(clock())
    names = ("sfm", "train", "compress", "mesh")
    stages = {name: round(t[i + 1] - t[i], 2) for i, name in enumerate(names)}
    gpu_seconds = t[-1] - t[0]
    usage = meter.stop() if meter is not None else None

    package = EnvironmentPackage(scan_id=scan.scan_id, splat=compressed, mesh=mesh)
    cost = ledger.record(
        scan.scan_id,
        gpu_seconds,
        gpu_rate_per_hour_usd,
        day=day,
        cpu_usd=usage.cpu_usd(cpu_rate_per_core_hour_usd) if usage else 0.0,
        memory_usd=usage.memory_usd(memory_rate_per_gib_hour_usd) if usage else 0.0,
    )
    within_budget = package.total_size_bytes <= config.max_package_bytes
    return ReconstructionRun(
        package=package,
        cost=cost,
        within_budget=within_budget,
        stage_seconds=stages,
        poses=poses,
        model=model,
        usage=usage,
    )
