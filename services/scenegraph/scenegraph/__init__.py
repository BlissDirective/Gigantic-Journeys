"""Scene-graph stage (M1-SCEN). Turns a reconstructed room into the frozen data
contracts the game and journey generator consume.

M1-SCEN-01 (this module set): traversal-quality mesh cleanup — floater removal,
hole fill, and a ceiling cap — producing a watertight collision mesh.
Downstream stages (surface classification -> traversal graph -> route generation
-> the deterministic reachability validator) build on data/schemas once frozen.
"""

from __future__ import annotations

from .cleanup import (
    CleanupConfig,
    CleanupStats,
    boundary_loops,
    clean_mesh,
    fill_holes,
    remove_floaters,
)
from .mesh import Mesh, MeshError, read_obj, write_obj

__all__ = [
    "Mesh",
    "MeshError",
    "read_obj",
    "write_obj",
    "CleanupConfig",
    "CleanupStats",
    "clean_mesh",
    "remove_floaters",
    "fill_holes",
    "boundary_loops",
]
