"""Resolve an external CLI tool on PATH, or fail with a clear pointer.

Shared by the real adapters so a missing binary produces one actionable error
("run inside the container") rather than an opaque FileNotFoundError.
"""

from __future__ import annotations

import shutil

from .models import ReconstructionError


class ToolNotFoundError(ReconstructionError):
    """A required external tool is not installed on PATH."""


def require(tool: str) -> str:
    """Return the resolved path to ``tool`` or raise ToolNotFoundError."""
    path = shutil.which(tool)
    if path is None:
        raise ToolNotFoundError(
            f"{tool!r} not found on PATH; run inside the reconstruction "
            "container (services/reconstruction/Dockerfile)"
        )
    return path
