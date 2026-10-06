"""Map the render-quality config knobs to Splatfacto / gsplat training flags.

capture-render-quality-v1 (external-synthesis-builds.md). Both techniques are already
commercial-safe in gsplat (Apache-2.0): ``antialiased`` rasterize = Mip-Splatting's
opacity-compensation (alias-free at any zoom), and the ``mcmc`` densification strategy
relocates "dead" Gaussians instead of heuristic clone/split (fewer floaters at a fixed
budget). This is the pure config->CLI mapping; the trainer (ns_train_capped, Operator)
passes the result to ns-train. The flag strings are centralised so they track the pinned
nerfstudio/gsplat version in one place.

Standard library only.
"""

from __future__ import annotations

from .models import ReconstructionConfig

RASTERIZE_FLAG = "--pipeline.model.rasterize-mode"
# gsplat exposes an MCMC densification strategy; confirm the exact Splatfacto flag/
# value against the pinned nerfstudio version before enabling in CI.
STRATEGY_FLAG = "--pipeline.model.strategy"


def splatfacto_quality_args(config: ReconstructionConfig) -> list[str]:
    """Extra ns-train args for the config's render-quality knobs (may be empty-safe)."""
    args = [RASTERIZE_FLAG, config.rasterize_mode]
    if config.densify_strategy == "mcmc":
        args += [STRATEGY_FLAG, "mcmc"]
    return args
