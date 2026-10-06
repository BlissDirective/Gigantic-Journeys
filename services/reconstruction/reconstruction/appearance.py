"""Per-image appearance transform for photometric drift (Splatfacto-W method).

capture-render-quality-v1 (external-synthesis-builds.md). Over a 3-4 minute handheld
sweep the phone's auto-exposure and auto-white-balance drift, so the same wall is a
different colour in different frames; vanilla 3DGS bakes that inconsistency into floaters
and muddy colour. Splatfacto-W (Apache-2.0, in Nerfstudio) gives each training image a
learned appearance embedding feeding a small colour transform, absorbing the drift; at
inference an unseen view renders in a canonical appearance (identity transform).

This module is the deterministic contract + the transform math (an affine 3x3 colour
matrix + bias per image, identity by default). The embedding/MLP that predicts the matrix
is learned (GPU/Operator); this pins how it is applied and how novel views default.
Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

RGB = tuple[float, float, float]
Mat3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

IDENTITY: Mat3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
ZERO_BIAS: RGB = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class AffineColor:
    """An affine colour transform ``out = clamp(matrix @ rgb + bias)``."""

    matrix: Mat3 = IDENTITY
    bias: RGB = ZERO_BIAS


def apply_affine_color(rgb: RGB, xf: AffineColor, *, clamp: bool = True) -> RGB:
    """Apply an affine colour transform to one RGB triple (channels in [0, 1])."""
    m, b = xf.matrix, xf.bias
    out = (
        m[0][0] * rgb[0] + m[0][1] * rgb[1] + m[0][2] * rgb[2] + b[0],
        m[1][0] * rgb[0] + m[1][1] * rgb[1] + m[1][2] * rgb[2] + b[1],
        m[2][0] * rgb[0] + m[2][1] * rgb[1] + m[2][2] * rgb[2] + b[2],
    )
    if clamp:
        out = tuple(max(0.0, min(1.0, c)) for c in out)  # type: ignore[assignment]
    return out  # type: ignore[return-value]


@dataclass
class AppearanceModel:
    """Per-image appearance transforms; unseen images render canonically (identity)."""

    per_image: dict[str, AffineColor] = field(default_factory=dict)

    def set_image(self, image_id: str, xf: AffineColor) -> None:
        self.per_image[image_id] = xf

    def transform_for(self, image_id: str | None) -> AffineColor:
        """The transform for a training image, or the canonical identity for a novel view."""
        if image_id is None:
            return AffineColor()
        return self.per_image.get(image_id, AffineColor())

    def apply(self, image_id: str | None, rgb: RGB, *, clamp: bool = True) -> RGB:
        return apply_affine_color(rgb, self.transform_for(image_id), clamp=clamp)
