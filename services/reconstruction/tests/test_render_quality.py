"""Render-quality config knobs + the Splatfacto flag mapping (gsplat antialiased / MCMC)."""

import pytest
from reconstruction import ReconstructionConfig, ReconstructionError
from reconstruction.render_quality import RASTERIZE_FLAG, STRATEGY_FLAG, splatfacto_quality_args


def test_defaults_preserve_classic_behaviour():
    args = splatfacto_quality_args(ReconstructionConfig())
    assert args == [RASTERIZE_FLAG, "classic"]


def test_antialiased_and_mcmc_emit_both_flags():
    cfg = ReconstructionConfig(rasterize_mode="antialiased", densify_strategy="mcmc")
    args = splatfacto_quality_args(cfg)
    assert RASTERIZE_FLAG in args and "antialiased" in args
    assert STRATEGY_FLAG in args and "mcmc" in args


def test_config_rejects_unknown_values():
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(rasterize_mode="nope")
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(densify_strategy="nope")
