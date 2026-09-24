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
from dataclasses import dataclass
from pathlib import Path

from . import licenses
from .compress import Compressor
from .cost import CostLedger, ScanCost, estimate_usd
from .mesh import Mesher
from .models import EnvironmentPackage, ReconstructionConfig, ScanInput
from .sfm import SfM
from .trainer import Trainer


@dataclass(frozen=True)
class ReconstructionRun:
    """The outcome of one pipeline run."""

    package: EnvironmentPackage
    cost: ScanCost
    within_budget: bool


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
) -> ReconstructionRun:
    """Run SfM -> train -> compress -> mesh, recording cost and budget status."""
    day = day or dt.date.today()
    work_dir.mkdir(parents=True, exist_ok=True)

    # Fail fast on licensing and spend before any GPU work.
    licenses.assert_commercial_safe()
    ledger.guard(estimate_usd(gpu_rate_per_hour_usd), day)

    started = clock()
    poses = sfm.run(scan, work_dir)
    model = trainer.train(poses, work_dir, config)
    compressed = compressor.compress(model, work_dir, config)
    mesh = mesher.derive(model, work_dir)
    gpu_seconds = clock() - started

    package = EnvironmentPackage(scan_id=scan.scan_id, splat=compressed, mesh=mesh)
    cost = ledger.record(scan.scan_id, gpu_seconds, gpu_rate_per_hour_usd, day=day)
    within_budget = package.total_size_bytes <= config.max_package_bytes
    return ReconstructionRun(package=package, cost=cost, within_budget=within_budget)
