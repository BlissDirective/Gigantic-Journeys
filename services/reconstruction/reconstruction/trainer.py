"""Gaussian-splat trainer adapters (gsplat primary, Brush secondary).

Real adapters run inside the CUDA container; importing this module never
requires them. Tests use ``fakes.FakeTrainer``. The pipeline is trainer-agnostic
(analysis 2026-09-24): gsplat first, Brush slots in behind the same Protocol.
"""

from __future__ import annotations

import subprocess  # noqa: S404 - orchestrating trusted CLI tools by fixed argv
from pathlib import Path
from typing import Protocol

from .models import (
    CameraPoses,
    ReconstructionConfig,
    ReconstructionError,
    SplatModel,
    read_ply_vertex_count,
)
from .tools import require


class TrainerError(ReconstructionError):
    """Raised when training fails to produce a splat."""


class Trainer(Protocol):
    """Train a Gaussian splat from registered poses to a fixed splat budget."""

    def train(
        self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig
    ) -> SplatModel: ...


class GsplatTrainer:
    """gsplat / Splatfacto with MCMC densification to a fixed splat budget.

    Trains via ``ns-train splatfacto`` then exports a PLY. Exact flags are pinned
    against the container's nerfstudio version during the spike.
    """

    def train(self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig) -> SplatModel:
        ns_train = require("ns-train")
        ns_export = require("ns-export")
        out = work_dir / "gsplat"
        subprocess.run(
            [
                ns_train,
                "splatfacto",
                "--data",
                str(poses.sparse_dir.parent),
                "--max-num-iterations",
                str(config.train_iters),
                "--pipeline.model.strategy",
                "mcmc",
                "--pipeline.model.max-gs-num",
                str(config.splat_budget),
                "--output-dir",
                str(out),
            ],
            check=True,
        )
        subprocess.run(
            [
                ns_export,
                "gaussian-splat",
                "--load-config",
                str(out / "config.yml"),
                "--output-dir",
                str(out),
            ],
            check=True,
        )
        ply = out / "splat.ply"
        if not ply.exists():
            raise TrainerError(f"expected splat PLY not produced: {ply}")
        return SplatModel(
            scan_id=poses.scan_id, ply_path=ply, splat_count=read_ply_vertex_count(ply)
        )


class BrushTrainer:
    """Brush (Apache-2.0, wgpu): CUDA-free trainer for heterogeneous GPU fleets.

    Secondary adapter (ADR-0005 / analysis). Command finalized during the spike.
    """

    def train(self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig) -> SplatModel:
        brush = require("brush")
        out = work_dir / "brush"
        out.mkdir(parents=True, exist_ok=True)
        ply = out / "export.ply"
        subprocess.run(
            [
                brush,
                str(poses.sparse_dir.parent),
                "--total-steps",
                str(config.train_iters),
                "--max-splats",
                str(config.splat_budget),
                "--export-path",
                str(ply),
            ],
            check=True,
        )
        if not ply.exists():
            raise TrainerError(f"brush did not produce {ply}")
        return SplatModel(
            scan_id=poses.scan_id, ply_path=ply, splat_count=read_ply_vertex_count(ply)
        )
