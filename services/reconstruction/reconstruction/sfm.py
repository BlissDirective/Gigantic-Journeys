"""Structure-from-motion adapters (COLMAP / GLOMAP).

The real adapters shell out to the SfM binaries inside the CUDA container and
are exercised during the M1-CAPT-03 spike; importing this module never requires
them. Tests use ``fakes.FakeSfM``.
"""

from __future__ import annotations

import struct
import subprocess  # noqa: S404 - orchestrating trusted CLI tools by fixed argv
from pathlib import Path
from typing import Protocol

from .models import CameraPoses, ReconstructionError, ScanInput
from .tools import require


class SfM(Protocol):
    """Turn a set of images into registered camera poses + a sparse cloud."""

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses: ...


def _count_registered(model_dir: Path) -> int:
    """Read the registered-image count from a COLMAP binary model (images.bin)."""
    images_bin = model_dir / "images.bin"
    if not images_bin.exists():
        return 0
    with images_bin.open("rb") as fh:
        (num,) = struct.unpack("<Q", fh.read(8))
    return int(num)


def _sift_flags(use_gpu: bool) -> tuple[list[str], list[str]]:
    """COLMAP SIFT extraction/matching GPU flags.

    ``use_gpu=False`` is required for a COLMAP built without CUDA (e.g. the
    Ubuntu 22.04 apt package in our Dockerfile): its GPU SIFT path falls back to
    OpenGL, which needs a display and fails on a headless GPU host.
    """
    flag = "1" if use_gpu else "0"
    return ["--SiftExtraction.use_gpu", flag], ["--SiftMatching.use_gpu", flag]


class GlomapSfM:
    """Global SfM: COLMAP feature/match front-end, GLOMAP global mapper.

    ~3.5x faster than incremental COLMAP at comparable accuracy
    (arXiv 2407.20219); the default for throughput. The command sequence is
    finalized on the GPU box during the spike.
    """

    def __init__(self, use_gpu: bool = True) -> None:
        self.use_gpu = use_gpu

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        colmap = require("colmap")
        glomap = require("glomap")
        extract_flags, match_flags = _sift_flags(self.use_gpu)
        db = work_dir / "database.db"
        sparse = work_dir / "sparse"
        sparse.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                colmap,
                "feature_extractor",
                "--database_path",
                str(db),
                "--image_path",
                str(scan.image_dir),
                # One capture = one device/lens: share intrinsics across images.
                "--ImageReader.single_camera",
                "1",
                *extract_flags,
            ],
            check=True,
        )
        subprocess.run(
            [colmap, "exhaustive_matcher", "--database_path", str(db), *match_flags],
            check=True,
        )
        subprocess.run(
            [
                glomap,
                "mapper",
                "--database_path",
                str(db),
                "--image_path",
                str(scan.image_dir),
                "--output_path",
                str(sparse),
            ],
            check=True,
        )
        model = sparse / "0"
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=model,
            registered_images=_count_registered(model),
            image_dir=scan.image_dir,
        )


class ColmapSfM:
    """Incremental SfM with COLMAP (fallback for hard scenes)."""

    def __init__(self, use_gpu: bool = True) -> None:
        self.use_gpu = use_gpu

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        colmap = require("colmap")
        extract_flags, match_flags = _sift_flags(self.use_gpu)
        db = work_dir / "database.db"
        sparse = work_dir / "sparse"
        sparse.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                colmap,
                "feature_extractor",
                "--database_path",
                str(db),
                "--image_path",
                str(scan.image_dir),
                # One capture = one device/lens: share intrinsics across images.
                "--ImageReader.single_camera",
                "1",
                *extract_flags,
            ],
            check=True,
        )
        subprocess.run(
            [colmap, "exhaustive_matcher", "--database_path", str(db), *match_flags],
            check=True,
        )
        subprocess.run(
            [
                colmap,
                "mapper",
                "--database_path",
                str(db),
                "--image_path",
                str(scan.image_dir),
                "--output_path",
                str(sparse),
            ],
            check=True,
        )
        model = sparse / "0"
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=model,
            registered_images=_count_registered(model),
            image_dir=scan.image_dir,
        )


SFM_CHOICES = ("colmap", "glomap")


def select_sfm(name: str, *, use_gpu: bool = True) -> SfM:
    """Return the SfM adapter for ``name`` ("colmap" or "glomap")."""
    if name == "glomap":
        return GlomapSfM(use_gpu=use_gpu)
    if name == "colmap":
        return ColmapSfM(use_gpu=use_gpu)
    raise ReconstructionError(f"unknown sfm {name!r}; expected one of {SFM_CHOICES}")
