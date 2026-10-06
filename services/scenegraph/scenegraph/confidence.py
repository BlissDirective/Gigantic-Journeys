"""Confidence gating for scene-graph surfaces (M1-SCEN-02).

Open-knowledge synthesis (feed-forward reconstruction literature, incl. Fast3R's
per-view confidence maps; see design/proposals/external-synthesis-builds.md). The idea
we keep is license-free and architecture-level: geometry the reconstruction/vision
pass is *unsure of* must not become playable surface. A surface whose confidence is
below a configured floor is demoted to class ``void`` + material ``unknown`` so the
traversal stage never routes the miniature onto hallucinated geometry.

Both ``void`` and ``unknown`` are already members of the frozen ``scene_graph.json``
enums (AUTH #037), so this gate changes no schema. The floor defaults to 0.0
(disabled); the self-hosted vision pass -- which produces per-surface confidence --
sets it. Pure standard library, deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

VOID_CLASS = "void"
UNKNOWN_MATERIAL = "unknown"


@dataclass(frozen=True)
class GateResult:
    """The surface's class/material/semantic after gating, and whether it was demoted."""

    cls: str
    material: str
    semantic: str | None
    gated: bool


def gate_surface(
    cls: str,
    confidence: float,
    material: str,
    semantic: str | None,
    *,
    floor: float,
) -> GateResult:
    """Demote a low-confidence surface to void/unknown; pass others through unchanged.

    ``floor <= 0`` disables the gate. A surface already classed ``void`` is left as is
    (it carries no trust to lose).
    """
    if floor > 0.0 and confidence < floor and cls != VOID_CLASS:
        return GateResult(cls=VOID_CLASS, material=UNKNOWN_MATERIAL, semantic=None, gated=True)
    return GateResult(cls=cls, material=material, semantic=semantic, gated=False)
