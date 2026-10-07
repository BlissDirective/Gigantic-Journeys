"""Map the render-quality config knobs to Splatfacto / gsplat training flags.

capture-render-quality-v1 (external-synthesis-builds.md). Both techniques are already
commercial-safe in gsplat (Apache-2.0): ``antialiased`` rasterize = Mip-Splatting's
opacity-compensation (alias-free at any zoom), and the ``mcmc`` densification strategy
relocates "dead" Gaussians instead of heuristic clone/split (fewer floaters at a fixed
budget). This is the pure config->CLI mapping; the trainer (ns_train_capped, Operator)
passes the result to ns-train / ns_train_capped. The flag strings are centralised so they
track the pinned nerfstudio/gsplat version in one place.

**Pinned nerfstudio 1.1.5 confirmation (M1-PIPE-03 item 1, 2026-10-06):**
- ``--pipeline.model.rasterize-mode`` {classic|antialiased} is a real
  ``SplatfactoModelConfig`` field (default classic). Pass it on the ns-train half.
- ``--pipeline.model.strategy`` is **not** a 1.1.5 Splatfacto config field (always
  builds ``DefaultStrategy``). MCMC on 1.1.5 is gsplat's ``MCMCStrategy`` swapped in by
  ``ns_train_capped.install_mcmc`` when ``--mcmc-cap N`` is set on the *own-args* half.
  Do not pass a strategy flag to ns-train on this pin.

Standard library only.
"""

from __future__ import annotations

from pathlib import Path

from .models import ReconstructionConfig, ReconstructionError

# Confirmed against nerfstudio==1.1.5 SplatfactoModelConfig.rasterize_mode.
RASTERIZE_FLAG = "--pipeline.model.rasterize-mode"
# Own-args flag for reconstruction.ns_train_capped (not an ns-train / Splatfacto flag).
MCMC_CAP_FLAG = "--mcmc-cap"
# Draft Brain-B name kept for grep/docs. Not emitted on the 1.1.5 pin — see module doc.
STRATEGY_FLAG = "--pipeline.model.strategy"
# Own-args flags for the DN-Splatter-style depth/normal losses (items 2+3).
DEPTH_PRIOR_DIR_FLAG = "--depth-prior-dir"
SENSOR_DEPTH_DIR_FLAG = "--sensor-depth-dir"
DN_WEIGHT_SCALE_FLAG = "--dn-weight-scale"
DN_START_STEP_FLAG = "--dn-start-step"
# Fixed locations inside the trainer's work_dir (written by depth_prior_cache.build_cache
# / the ARKit depth exporter before training).
DEPTH_PRIOR_SUBDIR = "depth_prior"
SENSOR_DEPTH_SUBDIR = "sensor_depth"


def splatfacto_quality_args(config: ReconstructionConfig) -> list[str]:
    """Extra ns-train args for the config's rasterize_mode (may be empty-safe)."""
    return [RASTERIZE_FLAG, config.rasterize_mode]


def ns_train_capped_own_args(config: ReconstructionConfig, budget: int) -> list[str]:
    """Own-side ``ns_train_capped`` args for densify_strategy (before the ``--``)."""
    if config.densify_strategy == "mcmc":
        return [MCMC_CAP_FLAG, str(budget)]
    return []


def depth_normal_own_args(config: ReconstructionConfig, work_dir: Path) -> list[str]:
    """Own-side ``ns_train_capped`` args for the depth/normal losses (items 2+3).

    Off (``[]``) unless ``config.depth_prior`` is set. When set, the prior cache must
    already exist (``<work_dir>/depth_prior/prior.json``) -- training silently without it
    would mis-attribute an A/B. ARKit sensor depth is added when its cache exists.
    """
    if config.depth_prior == "none":
        return []
    prior_dir = work_dir / DEPTH_PRIOR_SUBDIR
    if not (prior_dir / "prior.json").exists():
        raise ReconstructionError(
            f"depth_prior={config.depth_prior!r} but no prior cache at {prior_dir}"
        )
    args = [
        DEPTH_PRIOR_DIR_FLAG,
        str(prior_dir),
        DN_WEIGHT_SCALE_FLAG,
        f"{config.depth_prior_weight_scale:g}",
        DN_START_STEP_FLAG,
        str(config.depth_prior_start_step),
    ]
    sensor_dir = work_dir / SENSOR_DEPTH_SUBDIR
    if sensor_dir.is_dir():
        args += [SENSOR_DEPTH_DIR_FLAG, str(sensor_dir)]
    return args
