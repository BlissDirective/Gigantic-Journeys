"""Splatfacto-W per-image appearance transform."""

import pytest
from reconstruction.appearance import AffineColor, AppearanceModel, apply_affine_color


def test_identity_is_a_noop():
    assert apply_affine_color((0.2, 0.4, 0.6), AffineColor()) == pytest.approx((0.2, 0.4, 0.6))


def test_affine_matrix_and_bias():
    xf = AffineColor(
        matrix=((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), bias=(0.0, 0.1, 0.0)
    )
    assert apply_affine_color((0.25, 0.5, 0.5), xf, clamp=False) == pytest.approx((0.5, 0.6, 0.5))


def test_clamp_keeps_channels_in_range():
    xf = AffineColor(bias=(5.0, -5.0, 0.0))
    assert apply_affine_color((0.5, 0.5, 0.5), xf) == pytest.approx((1.0, 0.0, 0.5))


def test_model_known_vs_novel_view():
    m = AppearanceModel()
    bright = AffineColor(bias=(0.2, 0.2, 0.2))
    m.set_image("img-7", bright)
    assert m.apply("img-7", (0.1, 0.1, 0.1)) == pytest.approx((0.3, 0.3, 0.3))
    # a novel / unseen view renders canonically (identity)
    assert m.apply("unseen", (0.1, 0.1, 0.1)) == pytest.approx((0.1, 0.1, 0.1))
    assert m.apply(None, (0.1, 0.1, 0.1)) == pytest.approx((0.1, 0.1, 0.1))
