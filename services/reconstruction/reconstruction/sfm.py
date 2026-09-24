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

from .models import CameraPoses, ScanInput
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


class GlomapSfM:
    """Global SfM: COLMAP feature/match front-end, GLOMAP global mapper.

    ~3.5x faster than incremental COLMAP at comparable accuracy
    (arXiv 2407.20219); the default for throughput. The command sequence is
    finalized on the GPU box during the spike.
    """

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        colmap = require("colmap")
        glomap = require("glomap")
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
            ],
            check=True,
        )
        subprocess.run(
            [colmap, "exhaustive_matcher", "--database_path", str(db)],
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
        )


class ColmapSfM:
    """Incremental SfM with COLMAP (fallback for hard scenes)."""

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        colmap = require("colmap")
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
            ],
            check=True,
        )
        subprocess.run(
            [colmap, "exhaustive_matcher", "--database_path", str(db)],
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
        )
