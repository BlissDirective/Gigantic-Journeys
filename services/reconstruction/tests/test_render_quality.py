"""Render-quality config knobs + the Splatfacto flag mapping (gsplat antialiased / MCMC)."""

import pytest
from reconstruction import ReconstructionConfig, ReconstructionError
from reconstruction.render_quality import (
    MCMC_CAP_FLAG,
    RASTERIZE_FLAG,
    STRATEGY_FLAG,
    ns_train_capped_own_args,
    splatfacto_quality_args,
)


def test_defaults_preserve_classic_behaviour():
    args = splatfacto_quality_args(ReconstructionConfig())
    assert args == [RASTERIZE_FLAG, "classic"]
    assert ns_train_capped_own_args(ReconstructionConfig(), 400_000) == []


def test_antialiased_emits_rasterize_flag_and_mcmc_uses_cap():
    cfg = ReconstructionConfig(rasterize_mode="antialiased", densify_strategy="mcmc")
    args = splatfacto_quality_args(cfg)
    assert args == [RASTERIZE_FLAG, "antialiased"]
    # nerfstudio 1.1.5 has no --pipeline.model.strategy; MCMC is --mcmc-cap.
    assert STRATEGY_FLAG not in args
    assert ns_train_capped_own_args(cfg, 400_000) == [MCMC_CAP_FLAG, "400000"]


def test_config_rejects_unknown_values():
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(rasterize_mode="nope")
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(densify_strategy="nope")
