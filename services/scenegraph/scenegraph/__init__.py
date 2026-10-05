"""Scene-graph stage (M1-SCEN). Turns a reconstructed room into the frozen data
contracts the game and journey generator consume.

- M1-SCEN-01: traversal-quality mesh cleanup — floater removal, hole fill, and a
  ceiling cap — producing a watertight collision mesh (``cleanup``).
- M1-SCEN-02: surface classification — segment the cleaned mesh into planar patches,
  give each a Bible §4 class + A-unit measurements, and emit ``scene_graph.json``
  (``segment`` / ``classify`` / ``scene``). The material/semantic vision pass is a
  self-hosted port (SPEC §3.3); its survey contract + the ``SurveyVisionLabeler`` that
  drives M1-SCEN-02 labels and the M3-GAME-01 object set live in ``vision_survey``.

Downstream stages (traversal graph -> reachability validator -> route generation)
build on data/schemas/environment.
"""

from __future__ import annotations

from .classify import (
    GeometricStub,
    SceneConfig,
    VisionLabel,
    VisionLabeler,
    classify_patch,
    measure_patch,
)
from .cleanup import (
    CleanupConfig,
    CleanupStats,
    boundary_loops,
    clean_mesh,
    fill_holes,
    remove_floaters,
)
from .mesh import Mesh, MeshError, read_obj, write_obj
from .scene import CaptureMeta, build_scene_graph
from .segment import Patch, segment_planar
from .vision_runner import (
    MockVisionModel,
    VisionModel,
    VisionSurveyError,
    labeler_from_model,
    run_vision_pass,
)
from .vision_survey import (
    SceneSurvey,
    SurveyObject,
    SurveySurface,
    SurveyVisionLabeler,
    classify_separability,
    normalize_material,
    normalize_semantic,
    parse_survey,
    segmented_objects,
    validate_survey,
)

__all__ = [
    # mesh
    "Mesh",
    "MeshError",
    "read_obj",
    "write_obj",
    # cleanup (M1-SCEN-01)
    "CleanupConfig",
    "CleanupStats",
    "clean_mesh",
    "remove_floaters",
    "fill_holes",
    "boundary_loops",
    # classification (M1-SCEN-02)
    "Patch",
    "segment_planar",
    "SceneConfig",
    "VisionLabel",
    "VisionLabeler",
    "GeometricStub",
    "classify_patch",
    "measure_patch",
    "CaptureMeta",
    "build_scene_graph",
    # vision-pass survey (M1-SCEN-02 labels + M3-GAME-01 objects)
    "SceneSurvey",
    "SurveySurface",
    "SurveyObject",
    "SurveyVisionLabeler",
    "normalize_material",
    "normalize_semantic",
    "classify_separability",
    "segmented_objects",
    "validate_survey",
    "parse_survey",
    # vision-pass runner (M1-SCEN-02 + M3-GAME-01)
    "VisionModel",
    "MockVisionModel",
    "VisionSurveyError",
    "run_vision_pass",
    "labeler_from_model",
]
