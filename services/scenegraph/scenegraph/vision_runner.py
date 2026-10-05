"""Run the self-hosted vision pass to label a scene (M1-SCEN-02 + M3-GAME-01).

``vision_survey`` defines the survey *contract*; this is the runnable layer that turns the
reconstruction's own renders into a labelled scene. The vision **model** is self-hosted
(SPEC §3.3 — our own infra, never off-site; corpus-trained, GPU) and is Operator-provided; it
plugs in behind the :class:`VisionModel` port. :class:`MockVisionModel` is a deterministic stand-in
for tests and dry runs; swapping in the real model does not change the wiring.

End to end: ``run_vision_pass`` -> a validated :class:`~vision_survey.SceneSurvey`;
``labeler_from_model`` wraps that in a :class:`~vision_survey.SurveyVisionLabeler` ready to hand to
``scene.build_scene_graph(mesh, meta, labeler=...)``. Standard library only.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .vision_survey import (
    SceneSurvey,
    SurveyVisionLabeler,
    parse_survey,
    validate_survey,
)


class VisionSurveyError(RuntimeError):
    """The model's survey did not validate against the frozen scene_graph enums."""


class VisionModel(Protocol):
    """Port for the self-hosted vision model (SPEC §3.3): render paths -> a survey dict."""

    name: str

    def survey(self, render_paths: Sequence[str]) -> dict: ...


@dataclass
class MockVisionModel:
    """Deterministic stand-in: a fixed survey dict (tests + dry runs; no GPU, no network)."""

    name: str = "mock"
    result: dict | None = None

    def survey(self, render_paths: Sequence[str]) -> dict:
        if self.result is not None:
            return self.result
        return {"schema_version": 1, "scene_name": "mock", "surfaces": [], "objects": []}


def run_vision_pass(
    render_paths: Sequence[str], model: VisionModel, *, strict: bool = True
) -> SceneSurvey:
    """Model renders -> a validated :class:`SceneSurvey`.

    Raises :class:`VisionSurveyError` when the model's output does not conform to the scene_graph
    enums (unless ``strict`` is False, in which case problems are ignored and the survey is returned
    as parsed)."""
    survey = parse_survey(model.survey(list(render_paths)))
    problems = validate_survey(survey)
    if problems and strict:
        raise VisionSurveyError("; ".join(problems))
    return survey


def labeler_from_model(
    render_paths: Sequence[str],
    model: VisionModel,
    *,
    match_radius_A: float = 0.5,
    strict: bool = True,
) -> SurveyVisionLabeler:
    """Run the pass and return a ``VisionLabeler`` for ``build_scene_graph(..., labeler=...)``."""
    survey = run_vision_pass(render_paths, model, strict=strict)
    return SurveyVisionLabeler(survey, match_radius_A)


__all__ = [
    "VisionModel",
    "MockVisionModel",
    "VisionSurveyError",
    "run_vision_pass",
    "labeler_from_model",
]
