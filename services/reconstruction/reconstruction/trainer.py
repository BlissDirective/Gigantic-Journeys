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
    """gsplat via nerfstudio Splatfacto (``ns-train splatfacto``), then a PLY export.

    Reads the COLMAP model directly (nerfstudio's ``colmap`` dataparser) at the
    capture's native resolution. nerfstudio 1.1.5 (the latest release) exposes
    only gsplat's default densification strategy, so ``config.splat_budget`` is
    not enforced here yet (MCMC with a hard cap needs a newer Splatfacto or
    gsplat's own trainer); the resulting splat count is recorded instead.
    ``--vis tensorboard`` keeps the run headless and lets it exit when done
    (the default web viewer keeps the process alive after training).
    """

    def train(self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig) -> SplatModel:
        ns_train = require("ns-train")
        ns_export = require("ns-export")
        out = work_dir / "gsplat"
        image_dir = poses.image_dir or poses.sparse_dir.parent.parent / "images"
        subprocess.run(
            [
                ns_train,
                "splatfacto",
                "--data",
                str(work_dir),
                "--output-dir",
                str(out),
                "--experiment-name",
                poses.scan_id,
                "--timestamp",
                "run",
                "--max-num-iterations",
                str(config.train_iters),
                "--vis",
                "tensorboard",
                "colmap",
                "--colmap-path",
                str(poses.sparse_dir.resolve()),
                "--images-path",
                str(image_dir.resolve()),
                "--downscale-factor",
                "1",
            ],
            check=True,
        )
        configs = sorted(out.rglob("config.yml"))
        if not configs:
            raise TrainerError(f"ns-train produced no config.yml under {out}")
        subprocess.run(
            [
                ns_export,
                "gaussian-splat",
                "--load-config",
                str(configs[-1]),
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
