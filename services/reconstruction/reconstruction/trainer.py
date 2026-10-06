"""Gaussian-splat trainer adapters (gsplat primary, Brush secondary).

Real adapters run inside the CUDA container; importing this module never
requires them. Tests use ``fakes.FakeTrainer``. The pipeline is trainer-agnostic
(analysis 2026-09-24): gsplat first, Brush slots in behind the same Protocol.
"""

from __future__ import annotations

import json
import os
import subprocess  # noqa: S404 - orchestrating trusted CLI tools by fixed argv
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import (
    CameraPoses,
    ReconstructionConfig,
    ReconstructionError,
    SplatModel,
    read_ply_vertex_count,
)
from .splat_ops import STATS_ENV
from .tools import require


class TrainerError(ReconstructionError):
    """Raised when training fails to produce a splat."""


class Trainer(Protocol):
    """Train a Gaussian splat from registered poses to a fixed splat budget."""

    def train(
        self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig
    ) -> SplatModel: ...


@dataclass(frozen=True)
class TrainProfile:
    """Splatfacto schedule for one ``ns-train`` run.

    nerfstudio's Splatfacto defaults are tuned for 30k iterations. The first
    15k default here kept them unscaled: splitting ran to the very last step,
    full resolution only from step 6000 and the position learning rate was only
    half-decayed at the end. ``scaled(iterations)`` rescales every step-based
    knob to the run length (spike report, "Training speed-up"). ``in_training_eval``
    keeps nerfstudio's periodic evals / checkpoints (every 100 / 1000 / 2000
    steps), which cost ~20% of the train stage and are not used: the held-out
    eval runs once after training (``ns_finish``).
    """

    name: str
    iterations: int
    extra_args: tuple[str, ...] = ()
    in_training_eval: bool = False
    # "default": Splatfacto's DefaultStrategy (split/clone/prune, growth-limited at the
    # budget by ns_train_capped, then hard-capped by ns_finish). "mcmc": gsplat's
    # MCMCStrategy (3DGS as MCMC) capped at ``config.splat_budget`` for the whole run,
    # i.e. the model is optimised *at* the device budget instead of pruned down to it.
    strategy: str = "default"

    @classmethod
    def upstream(cls, iterations: int, name: str = "") -> TrainProfile:
        """nerfstudio's unscaled 30k schedule, cut at ``iterations`` (old default)."""
        return cls(name or f"upstream-{iterations // 1000}k", iterations, in_training_eval=True)

    @classmethod
    def scaled(cls, iterations: int, name: str = "", *extra: str) -> TrainProfile:
        """Splatfacto's step-based schedule scaled from 30k to ``iterations``.

        Scaled: stop of splitting (half the run), resolution doubling, SH
        degree steps, screen-size culling stop, position-LR decay (to the end
        of the run). Kept: warmup (500) and the opacity reset period (3000
        steps); scaling those too made each reset's refine pause
        (``num_images + refine_every`` steps) eat most of a short run.
        """
        f = iterations / 30_000

        def steps(n: int) -> str:
            return str(max(1, round(n * f)))

        args = (
            "--pipeline.model.stop-split-at",
            steps(15_000),
            "--pipeline.model.resolution-schedule",
            steps(3_000),
            "--pipeline.model.sh-degree-interval",
            steps(1_000),
            "--pipeline.model.stop-screen-size-at",
            steps(4_000),
            "--optimizers.means.scheduler.max-steps",
            str(iterations),
            *extra,
        )
        return cls(name or f"scaled-{iterations // 1000}k", iterations, args)

    def ns_train_args(self) -> list[str]:
        args = ["--max-num-iterations", str(self.iterations)]
        if not self.in_training_eval:
            # 0 disables each periodic hook; the final checkpoint is always saved.
            args += [
                "--steps-per-eval-image",
                "0",
                "--steps-per-eval-batch",
                "0",
                "--steps-per-eval-all-images",
                "0",
                "--steps-per-save",
                "0",
            ]
        return [*args, *self.extra_args]


# Densify a bit more eagerly than Splatfacto's 0.0008 gradient threshold: on
# the room it bought back most of the LPIPS a 10k run loses, at no extra time.
DENSE_ARGS = ("--pipeline.model.densify-grad-thresh", "0.0006")

# The profiles benchmarked on Mip-NeRF 360 room (spike report, "Training
# speed-up"); DEFAULT_PROFILE is the pipeline default.
PROFILES: dict[str, TrainProfile] = {
    p.name: p
    for p in (
        TrainProfile.upstream(15_000),
        TrainProfile("upstream-15k-noeval", 15_000),
        TrainProfile.scaled(15_000),
        TrainProfile.scaled(12_000),
        TrainProfile.scaled(10_000),
        TrainProfile.scaled(10_000, "scaled-10k-dense", *DENSE_ARGS),
        TrainProfile.scaled(7_000),
        TrainProfile.scaled(5_000),
    )
}
DEFAULT_PROFILE = "scaled-10k-dense"

# Display-quality retrain recipes (M1-UNITY-01 splat room v3), all nerfstudio
# 1.1.5 Splatfacto flags: the full 30k schedule; gsplat's antialiased
# rasterizer (Mip-Splatting-style 2D filter, kills aliasing shimmer and the
# over-thin splats that blow up when seen from a new distance); a per-image
# bilateral grid (Bilateral Guided Radiance Field Processing) that absorbs the
# video's exposure / white-balance drift during training only, so it is not
# baked into the splat colours as bright and dark patches; scale regularisation
# (caps the max/min axis ratio, fewer needles). ``-camopt`` also refines the
# camera poses (SO3xR3), which sharpens a video SfM with small pose errors.
QUALITY_ARGS = (
    "--pipeline.model.rasterize-mode",
    "antialiased",
    "--pipeline.model.use-bilateral-grid",
    "True",
    "--pipeline.model.use-scale-regularization",
    "True",
)
CAMOPT_ARGS = ("--pipeline.model.camera-optimizer.mode", "SO3xR3")
QUALITY_PROFILES: dict[str, TrainProfile] = {
    p.name: p
    for p in (
        TrainProfile.scaled(30_000, "quality-30k", *QUALITY_ARGS),
        TrainProfile.scaled(30_000, "quality-30k-camopt", *QUALITY_ARGS, *CAMOPT_ARGS),
    )
}
PROFILES.update(QUALITY_PROFILES)

# Train-at-budget (M1-PIPE-02 phase 2a, AUTH #045): the quality recipe with gsplat's
# MCMC strategy capped at ``ReconstructionConfig.splat_budget`` (400K for the A15
# display path) for the whole run. The owner-room-01 shipped package kept 400K of a
# 1.46M-splat model by a post-train prune with no fine-tuning (822K splats dropped for
# the budget alone); here the optimiser places the 400K splats itself. nerfstudio 1.1.5
# Splatfacto has no MCMC option, so ns_train_capped swaps the strategy in
# (``install_mcmc``), with the MCMC opacity / scale regularisers of the paper.
# Measured on owner-room-01 (2026-10-05, same 29 held-out views): this profile scored
# PSNR 24.10 / SSIM 0.930 / LPIPS 0.171, below ``quality-30k`` with
# ``splat_budget=400_000`` (DefaultStrategy growth-limited at the budget by
# ns_train_capped: 24.85 / 0.942 / 0.124), which is the train-at-budget recipe in use;
# the post-train-pruned package that shipped in build 58 scored 12.92 / 0.613 / 0.500.
BUDGET_PROFILES: dict[str, TrainProfile] = {
    p.name: p
    for p in (
        TrainProfile(
            "quality-30k-mcmc",
            30_000,
            TrainProfile.scaled(30_000, "", *QUALITY_ARGS).extra_args,
            strategy="mcmc",
        ),
    )
}
PROFILES.update(BUDGET_PROFILES)


_NO_GROWTH_LIMIT = 2**62


class GsplatTrainer:
    """gsplat via nerfstudio Splatfacto, then a hard splat cap, eval and export.

    1. ``ns-train splatfacto`` (``reconstruction.ns_train_capped``: densification
       stops growing at ``config.splat_budget``) with the colmap dataparser at
       the capture's native resolution and the ``profile``'s schedule.
       ``--vis tensorboard`` keeps the run headless and lets it exit when done.
    2. ``reconstruction.ns_finish``: one model load that hard-caps the splat
       count to ``config.splat_budget`` (by importance), scores the held-out
       views (``evaluate``; the colmap dataparser holds out every 8th image) and
       writes the PLY. Metrics are PSNR / SSIM / LPIPS of the *capped* model.

    With ``evaluate`` (default) one rendered view (ground truth | render) is kept
    as ``preview_image``. Eval failures never fail the run: the splat is the
    deliverable, metrics are best-effort (on an eval error the export is
    retried without eval).
    """

    def __init__(
        self,
        evaluate: bool = True,
        profile: TrainProfile | str | None = None,
        growth_limit: bool = True,
        score_plys: tuple[tuple[str, Path], ...] = (),
    ) -> None:
        self.evaluate = evaluate
        # Extra PLYs (name, path) scored on the same held-out views after training,
        # e.g. the currently shipped package's splat, for a like-for-like before/after.
        self.score_plys = tuple(score_plys)
        # False only to exercise the post-train hard cap alone (stress bench).
        self.growth_limit = growth_limit
        if isinstance(profile, str):
            if profile not in PROFILES:
                raise TrainerError(f"unknown train profile {profile!r}; one of {sorted(PROFILES)}")
            profile = PROFILES[profile]
        self.profile = profile

    def profile_for(self, config: ReconstructionConfig) -> TrainProfile:
        """The explicit profile, else the default recipe at ``config.train_iters``.

        The default recipe is ``DEFAULT_PROFILE`` (scaled schedule + ``DENSE_ARGS``);
        another ``train_iters`` rescales it to that length.
        """
        if self.profile is not None:
            return self.profile
        default = PROFILES[DEFAULT_PROFILE]
        if config.train_iters == default.iterations:
            return default
        return TrainProfile.scaled(config.train_iters, "", *DENSE_ARGS)

    def train(self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig) -> SplatModel:
        python = sys.executable
        out = work_dir / "gsplat"
        out.mkdir(parents=True, exist_ok=True)
        image_dir = poses.image_dir or poses.sparse_dir.parent.parent / "images"
        profile = self.profile_for(config)
        growth = out / "growth.json"
        started = time.monotonic()
        subprocess.run(
            [
                python,
                "-m",
                "reconstruction.ns_train_capped",
                "--budget",
                str(config.splat_budget if self.growth_limit else _NO_GROWTH_LIMIT),
                *(["--mcmc-cap", str(config.splat_budget)] if profile.strategy == "mcmc" else []),
                "--",
                "splatfacto",
                "--data",
                str(work_dir),
                "--output-dir",
                str(out),
                "--experiment-name",
                poses.scan_id,
                "--timestamp",
                "run",
                *profile.ns_train_args(),
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
            env={**os.environ, STATS_ENV: str(growth)},
        )
        metrics: dict = {
            "profile": profile.name,
            "strategy": profile.strategy,
            "iterations": profile.iterations,
            "train_s": round(time.monotonic() - started, 2),
        }
        if growth.exists():
            metrics["growth"] = json.loads(growth.read_text(encoding="utf-8"))
        configs = sorted(out.rglob("config.yml"))
        if not configs:
            raise TrainerError(f"ns-train produced no config.yml under {out}")
        preview = _finish(
            python, configs[-1], out, config.splat_budget, self.evaluate, metrics, self.score_plys
        )
        ply = out / "splat.ply"
        if not ply.exists():
            raise TrainerError(f"expected splat PLY not produced: {ply}")
        count = read_ply_vertex_count(ply)
        if count > config.splat_budget:
            raise TrainerError(f"splat cap violated: {count} > {config.splat_budget}")
        return SplatModel(
            scan_id=poses.scan_id,
            ply_path=ply,
            splat_count=count,
            metrics=metrics,
            preview_image=preview,
        )


def parse_eval_json(path: Path) -> dict[str, float]:
    """PSNR / SSIM / LPIPS (+ std) from an ``ns-eval`` / ``ns_finish`` output file."""
    results = json.loads(path.read_text(encoding="utf-8")).get("results", {})
    return {
        key: round(float(results[key]), 4)
        for key in ("psnr", "ssim", "lpips", "psnr_std", "ssim_std", "lpips_std")
        if key in results
    }


def _finish(
    python: str,
    config: Path,
    out: Path,
    budget: int,
    evaluate: bool,
    metrics: dict,
    score_plys: tuple[tuple[str, Path], ...] = (),
) -> Path | None:
    """Run ``ns_finish`` (cap + eval + export); on an eval failure, export only."""
    renders = out / "eval_renders"
    scoring: list[str] = []
    for name, path in score_plys:
        scoring += ["--score-ply", f"{name}={path}"]
    cmd = [
        python,
        "-m",
        "reconstruction.ns_finish",
        "--load-config",
        str(config),
        "--output-dir",
        str(out),
        "--budget",
        str(budget),
    ]
    started = time.monotonic()
    try:
        if not evaluate:
            raise _SkipEval
        subprocess.run([*cmd, "--eval", "--renders", str(renders), *scoring], check=True)
    except (_SkipEval, subprocess.CalledProcessError, OSError) as exc:
        if not isinstance(exc, _SkipEval):
            metrics["eval_error"] = str(exc)[:300]
        subprocess.run(cmd, check=True)
    metrics["finish_s"] = round(time.monotonic() - started, 2)
    report_path = out / "finish.json"
    if not report_path.exists():
        return None
    report = json.loads(report_path.read_text(encoding="utf-8"))
    for key in ("trained_splats", "capped_splats", "cap_applied", "exported_splats"):
        if key in report:
            metrics[key] = report[key]
    for key in ("load_s", "cap_s", "eval_s", "export_s"):
        if key in report:
            metrics[key] = report[key]
    metrics.update(parse_eval_json(report_path))
    scored = report.get("scored_plys")
    if scored:
        metrics["scored_plys"] = scored
    if "eval_views" not in report:
        return None
    metrics["eval_views"] = report["eval_views"]
    views = sorted(renders.glob("*")) if renders.is_dir() else []
    return views[len(views) // 2] if views else None


class _SkipEval(Exception):
    """Internal: evaluation disabled."""


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
