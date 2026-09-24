"""Typed data contracts for the reconstruction pipeline (M1-CAPT-03, ADR-0005).

Standard library only, so the orchestration and its tests run on any machine
with no GPU and no third-party packages. The heavy tools (COLMAP/GLOMAP,
gsplat, Open3D, splat-transform) live behind the adapters in the sibling
modules and are invoked only inside the CUDA container (see Dockerfile).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path

MiB = 1024 * 1024


class ReconstructionError(Exception):
    """Base class for every error the reconstruction package raises."""


class Format(enum.Enum):
    """Splat container formats the pipeline can emit."""

    PLY = "ply"
    SPZ = "spz"
    SOG = "sog"


class Source(enum.Enum):
    """Provenance of a scan; gates what may leave our own infrastructure."""

    PUBLIC = "public"  # public benchmark dataset (no privacy constraint)
    CORPUS = "corpus"  # Owner-supplied, consented test corpus
    USER = "user"  # a real user's home scan (never sent to a third-party trainer)


# Sources allowed to leave our own infrastructure (e.g. to a rented Modal GPU).
# Real user scans never do (ADR-0005 / AUTH #030).
OFFSITE_SOURCES = frozenset({Source.PUBLIC, Source.CORPUS})


def require_offsite_source(source: str | Source) -> Source:
    """Return ``source`` as a Source if it may run off-site; else raise.

    Only public benchmark data and the Owner's consented corpus may be sent to
    third-party compute. ``user`` (or any unknown value) is rejected.
    """
    try:
        parsed = source if isinstance(source, Source) else Source(source)
    except ValueError:
        parsed = None
    if parsed not in OFFSITE_SOURCES:
        allowed = ", ".join(sorted(s.value for s in OFFSITE_SOURCES))
        raise ReconstructionError(
            f"source {source!r} may not be sent to off-site compute; allowed: {allowed} "
            "(real user scans never leave our infrastructure, ADR-0005 / AUTH #030)"
        )
    return parsed


@dataclass(frozen=True)
class ScanInput:
    """A capture bundle handed to the pipeline."""

    scan_id: str
    image_dir: Path
    image_count: int
    source: Source

    def __post_init__(self) -> None:
        if not self.scan_id:
            raise ReconstructionError("scan_id must be non-empty")
        if self.image_count <= 0:
            raise ReconstructionError("image_count must be positive")


@dataclass(frozen=True)
class CameraPoses:
    """Registered camera poses + sparse cloud produced by structure-from-motion."""

    scan_id: str
    sparse_dir: Path
    registered_images: int


@dataclass(frozen=True)
class SplatModel:
    """A trained Gaussian splat (uncompressed PLY)."""

    scan_id: str
    ply_path: Path
    splat_count: int


@dataclass(frozen=True)
class CompressedSplat:
    """A splat compressed for delivery (.spz / .sog)."""

    scan_id: str
    path: Path
    fmt: Format
    size_bytes: int
    splat_count: int


@dataclass(frozen=True)
class CollisionMesh:
    """A low-poly mesh derived for gameplay physics."""

    scan_id: str
    path: Path
    triangle_count: int
    size_bytes: int


@dataclass(frozen=True)
class EnvironmentPackage:
    """The deliverable for one environment: compressed splat + collision mesh."""

    scan_id: str
    splat: CompressedSplat
    mesh: CollisionMesh

    @property
    def total_size_bytes(self) -> int:
        return self.splat.size_bytes + self.mesh.size_bytes


@dataclass(frozen=True)
class ReconstructionConfig:
    """Tunables for one reconstruction run.

    Defaults target a room at <=150 MB / 30 fps on iPhone: a fixed splat budget
    (gsplat MCMC) plus SPZ compression (analysis 2026-09-24).
    """

    splat_budget: int = 2_000_000
    train_iters: int = 15_000
    compress_format: Format = Format.SPZ
    sfm: str = "glomap"
    max_package_bytes: int = 150 * MiB

    def __post_init__(self) -> None:
        if self.splat_budget <= 0:
            raise ReconstructionError("splat_budget must be positive")
        if self.train_iters <= 0:
            raise ReconstructionError("train_iters must be positive")
        if self.sfm not in ("glomap", "colmap"):
            raise ReconstructionError(f"unknown sfm backend: {self.sfm!r}")
        if self.max_package_bytes <= 0:
            raise ReconstructionError("max_package_bytes must be positive")


def read_ply_vertex_count(path: Path) -> int:
    """Return the vertex (splat) count declared in a PLY header.

    Reads only the ASCII header, which is valid for both ascii and binary PLY,
    so it never loads the whole file.
    """
    with path.open("rb") as fh:
        if fh.readline().strip() != b"ply":
            raise ReconstructionError(f"not a PLY file: {path}")
        for _ in range(10_000):
            line = fh.readline()
            if not line or line.strip() == b"end_header":
                break
            parts = line.split()
            if len(parts) == 3 and parts[0] == b"element" and parts[1] == b"vertex":
                return int(parts[2])
    raise ReconstructionError(f"no 'element vertex' in PLY header: {path}")
