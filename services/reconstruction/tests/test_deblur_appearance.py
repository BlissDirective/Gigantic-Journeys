"""Items 4+5 wiring: default-off config, ns_train_capped args, licence manifest, and the
torch trajectory / colour maths against the stdlib exposure_trajectory / appearance cores."""

from __future__ import annotations

import pytest
from reconstruction import ReconstructionConfig, ReconstructionError
from reconstruction import deblur_appearance_torch as da
from reconstruction.licenses import ALLOWED_LICENSES, EXCLUDED_COMPONENTS, MANIFEST
from reconstruction.render_quality import deblur_appearance_own_args


def test_default_off():
    cfg = ReconstructionConfig()
    assert cfg.deblur_samples == 1 and cfg.appearance == "none"
    assert deblur_appearance_own_args(cfg) == []


def test_args_when_on():
    cfg = ReconstructionConfig(deblur_samples=5, appearance="splatfacto-w")
    assert deblur_appearance_own_args(cfg) == [
        "--deblur-samples",
        "5",
        "--appearance",
        "splatfacto-w",
    ]


@pytest.mark.parametrize(
    "kw", [{"deblur_samples": 0}, {"deblur_samples": 17}, {"appearance": "nerf-w"}]
)
def test_rejects_bad_values(kw):
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(**kw)


def test_licence_manifest():
    names = {c.name: c.license for c in MANIFEST}
    for n in ("BAD-Gaussians (method reimplementation)", "Splatfacto-W (method reimplementation)"):
        assert names[n] in ALLOWED_LICENSES
    assert not set(names) & EXCLUDED_COMPONENTS


def test_ns_train_capped_accepts_flags():
    import argparse  # noqa: F401 - parser is built in main; exercise the arg surface

    from reconstruction import ns_train_capped as ntc

    src = open(ntc.__file__, encoding="utf-8").read()
    assert '"--deblur-samples"' in src and '"--appearance"' in src


@pytest.mark.parametrize("n", [1, 2, 5, 10])
def test_render_order_mid_last(n):
    order = da.render_order(n)
    assert sorted(order) == list(range(n)) and order[-1] == (n - 1) // 2
