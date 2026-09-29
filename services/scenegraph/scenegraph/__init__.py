"""Scene-graph stage (M1-SCEN). Turns a reconstructed room into the frozen data
contracts the game and journey generator consume.

- M1-SCEN-01: traversal-quality mesh cleanup — floater removal, hole fill, and a
  ceiling cap — producing a watertight collision mesh (``cleanup``).
- M1-SCEN-02: surface classification — segment the cleaned mesh into planar patches,
  give each a Bible §4 class + A-unit measurements, and emit ``scene_graph.json``
  (``segment`` / ``classify`` / ``scene``). The material/semantic vision pass is a
  deferred, self-hosted port (SPEC §3.3).

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
]
