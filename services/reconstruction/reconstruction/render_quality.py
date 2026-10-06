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

from .models import ReconstructionConfig

# Confirmed against nerfstudio==1.1.5 SplatfactoModelConfig.rasterize_mode.
RASTERIZE_FLAG = "--pipeline.model.rasterize-mode"
# Own-args flag for reconstruction.ns_train_capped (not an ns-train / Splatfacto flag).
MCMC_CAP_FLAG = "--mcmc-cap"
# Draft Brain-B name kept for grep/docs. Not emitted on the 1.1.5 pin — see module doc.
STRATEGY_FLAG = "--pipeline.model.strategy"


def splatfacto_quality_args(config: ReconstructionConfig) -> list[str]:
    """Extra ns-train args for the config's rasterize_mode (may be empty-safe)."""
    return [RASTERIZE_FLAG, config.rasterize_mode]


def ns_train_capped_own_args(config: ReconstructionConfig, budget: int) -> list[str]:
    """Own-side ``ns_train_capped`` args for densify_strategy (before the ``--``)."""
    if config.densify_strategy == "mcmc":
        return [MCMC_CAP_FLAG, str(budget)]
    return []
