"""Commercial-license manifest for the reconstruction stack.

Every component the pipeline may invoke must carry an MIT / BSD / Apache-2.0
license (SECURITY_CHECKLIST §7.3). The non-commercial INRIA 3DGS reference
implementation and SuGaR are excluded by ADR-0005 and must never enter the
stack; ``assert_commercial_safe`` is the machine check that keeps them out.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import ReconstructionError


class LicenseError(ReconstructionError):
    """Raised when a component violates the commercial-license policy."""


ALLOWED_LICENSES = frozenset({"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0"})

# Known non-commercial components that must never appear in the manifest.
EXCLUDED_COMPONENTS = frozenset(
    {
        "INRIA 3DGS (graphdeco-inria/gaussian-splatting)",
        "SuGaR",
    }
)


@dataclass(frozen=True)
class Component:
    """One tool in the pipeline and the license it ships under."""

    name: str
    license: str
    role: str


MANIFEST: tuple[Component, ...] = (
    Component("COLMAP", "BSD-3-Clause", "structure-from-motion (incremental)"),
    Component("GLOMAP", "BSD-3-Clause", "structure-from-motion (global, default)"),
    Component("gsplat", "Apache-2.0", "gaussian-splat trainer (primary)"),
    Component("Nerfstudio/Splatfacto", "Apache-2.0", "training pipeline over gsplat"),
    Component("Brush", "Apache-2.0", "gaussian-splat trainer (secondary, wgpu)"),
    Component("Open3D", "MIT", "collision-mesh derivation"),
    Component("splat-transform", "MIT", "PLY -> SPZ/SOG compression"),
    Component("spz", "MIT", "compressed splat container (Niantic)"),
)


def assert_commercial_safe(
    manifest: tuple[Component, ...] = MANIFEST,
) -> tuple[Component, ...]:
    """Validate ``manifest`` against the policy; return it unchanged if clean."""
    intruders = {c.name for c in manifest} & EXCLUDED_COMPONENTS
    if intruders:
        raise LicenseError(f"non-commercial component(s) present: {sorted(intruders)}")
    for component in manifest:
        if component.license not in ALLOWED_LICENSES:
            raise LicenseError(f"{component.name} has non-allowed license {component.license!r}")
    return manifest
