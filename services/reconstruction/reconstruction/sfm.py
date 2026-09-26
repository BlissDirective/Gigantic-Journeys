"""Structure-from-motion adapters (COLMAP incremental / GLOMAP global).

The real adapters shell out to the COLMAP binary inside the CUDA container
(COLMAP 4.1, CUDA build; see Dockerfile); importing this module never requires
it. Tests use ``fakes.FakeSfM``.

Both adapters share the COLMAP front end (SIFT extraction + matching, on the GPU
when ``use_gpu``) and differ only in the mapper:

* ``ColmapSfM`` — incremental ``colmap mapper``. **Default.**
* ``GlomapSfM`` — ``colmap view_graph_calibrator`` + ``colmap global_mapper``:
  the GLOMAP global pipeline, which COLMAP ships natively since 4.0. Kept
  selectable (``--sfm glomap``); on the 311-image benchmark room it was
  ~10-60 s slower than incremental and ~0.15 dB lower PSNR, so not the default.

Default matcher: ``auto`` = GPU ``exhaustive`` up to AUTO_EXHAUSTIVE_MAX_IMAGES
images, else ``sequential`` (+ quadratic overlap + vocab-tree loop detection,
linear in frame count, for long ordered video captures). ``vocab_tree`` suits
large unordered sets.

Every run records per-step wall times and ``colmap model_analyzer`` statistics
(registered images, points, mean reprojection error) in ``CameraPoses.stats``.
"""

from __future__ import annotations

import re
import struct
import subprocess  # noqa: S404 - orchestrating trusted CLI tools by fixed argv
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from .models import CameraPoses, ReconstructionError, ScanInput
from .tools import require

MATCHER_CHOICES = ("auto", "exhaustive", "sequential", "vocab_tree")
# "auto": GPU exhaustive matching up to this many images, sequential beyond.
# On the 311-image room, GPU exhaustive matching took ~18 s and gave the most
# stable splat quality (PSNR 31.3 dB in 2/2 runs; sequential gave 30.1-31.1 dB
# over 3 runs). Its cost grows O(n^2) (~50 s at 500 images on an A10G), so
# long ordered video captures switch to sequential matching.
AUTO_EXHAUSTIVE_MAX_IMAGES = 500
# Sequential matching for ordered captures (walk-around video / photo series):
# each frame is matched to its OVERLAP neighbours (plus quadratic offsets), and
# loop detection (vocab-tree retrieval every LOOP_PERIOD frames) closes the loop
# when an orbit returns to its start.
SEQUENTIAL_OVERLAP = 15
LOOP_PERIOD = 10
LOOP_IMAGES = 30


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


def _largest_model(sparse: Path) -> Path:
    """The sub-model with the most registered images (``sparse/0`` if none found)."""
    models = [d for d in sorted(sparse.iterdir()) if (d / "images.bin").exists()]
    if not models:
        return sparse / "0"
    return max(models, key=_count_registered)


def _gpu_flags(use_gpu: bool) -> tuple[list[str], list[str]]:
    """COLMAP >= 3.12 feature extraction / matching GPU flags.

    ``use_gpu=False`` is required for a COLMAP built without CUDA: its GPU SIFT
    path falls back to OpenGL, which needs a display and fails headless.
    """
    flag = "1" if use_gpu else "0"
    return ["--FeatureExtraction.use_gpu", flag], ["--FeatureMatching.use_gpu", flag]


def resolve_matcher(matcher: str, image_count: int) -> str:
    """Resolve ``auto`` to a concrete matcher for a capture of ``image_count`` images."""
    if matcher not in MATCHER_CHOICES:
        raise ReconstructionError(f"unknown matcher {matcher!r}; expected one of {MATCHER_CHOICES}")
    if matcher != "auto":
        return matcher
    return "exhaustive" if image_count <= AUTO_EXHAUSTIVE_MAX_IMAGES else "sequential"


def _matcher_argv(colmap: str, matcher: str, db: Path, match_flags: list[str]) -> list[str]:
    if matcher == "exhaustive":
        return [colmap, "exhaustive_matcher", "--database_path", str(db), *match_flags]
    if matcher == "sequential":
        return [
            colmap,
            "sequential_matcher",
            "--database_path",
            str(db),
            "--SequentialMatching.overlap",
            str(SEQUENTIAL_OVERLAP),
            "--SequentialMatching.quadratic_overlap",
            "1",
            "--SequentialMatching.loop_detection",
            "1",
            "--SequentialMatching.loop_detection_period",
            str(LOOP_PERIOD),
            "--SequentialMatching.loop_detection_num_images",
            str(LOOP_IMAGES),
            *match_flags,
        ]
    if matcher == "vocab_tree":
        return [colmap, "vocab_tree_matcher", "--database_path", str(db), *match_flags]
    raise ReconstructionError(f"unknown matcher {matcher!r}; expected one of {MATCHER_CHOICES}")


_STAT_PATTERNS = {
    "registered_images": r"Registered images:\s*(\d+)",
    "points": r"Points:\s*(\d+)",
    "observations": r"Observations:\s*(\d+)",
    "mean_track_length": r"Mean track length:\s*([\d.]+)",
    "mean_observations_per_image": r"Mean observations per image:\s*([\d.]+)",
    "mean_reprojection_error_px": r"Mean reprojection error:\s*([\d.]+)",
}


def parse_model_analyzer(text: str) -> dict[str, float]:
    """Pull the headline numbers out of ``colmap model_analyzer`` output."""
    stats: dict[str, float] = {}
    for key, pattern in _STAT_PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            stats[key] = float(value) if "." in value else int(value)
    return stats


def _analyze(colmap: str, model: Path) -> dict[str, float]:
    proc = subprocess.run(
        [colmap, "model_analyzer", "--path", str(model)],
        check=False,
        capture_output=True,
        text=True,
    )
    return parse_model_analyzer(proc.stdout + proc.stderr)


class _ColmapFrontEnd:
    """Shared SIFT extraction + matching; subclasses supply the mapper."""

    mapper_name = ""

    def __init__(
        self,
        use_gpu: bool = True,
        matcher: str = "auto",
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if matcher not in MATCHER_CHOICES:
            raise ReconstructionError(
                f"unknown matcher {matcher!r}; expected one of {MATCHER_CHOICES}"
            )
        self.use_gpu = use_gpu
        self.matcher = matcher
        self._clock = clock

    def _timed(self, timings: dict[str, float], step: str, argv: list[str]) -> None:
        started = self._clock()
        subprocess.run(argv, check=True)
        timings[step] = round(self._clock() - started, 2)

    def _map(
        self, colmap: str, scan: ScanInput, db: Path, sparse: Path, timings: dict[str, float]
    ) -> None:
        raise NotImplementedError

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        colmap = require("colmap")
        extract_flags, match_flags = _gpu_flags(self.use_gpu)
        db = work_dir / "database.db"
        sparse = work_dir / "sparse"
        sparse.mkdir(parents=True, exist_ok=True)
        timings: dict[str, float] = {}
        self._timed(
            timings,
            "extract_s",
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
        )
        matcher = resolve_matcher(self.matcher, scan.image_count)
        self._timed(timings, "match_s", _matcher_argv(colmap, matcher, db, match_flags))
        self._map(colmap, scan, db, sparse, timings)
        model = _largest_model(sparse)
        stats: dict[str, object] = {
            "mapper": self.mapper_name,
            "matcher": matcher,
            "matcher_requested": self.matcher,
            "gpu_features": self.use_gpu,
            **timings,
            "sfm_s": round(sum(timings.values()), 2),
            "input_images": scan.image_count,
            "models": sum(1 for d in sparse.iterdir() if d.is_dir()),
            **_analyze(colmap, model),
        }
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=model,
            registered_images=_count_registered(model),
            image_dir=scan.image_dir,
            stats=stats,
        )


class GlomapSfM(_ColmapFrontEnd):
    """Global SfM: COLMAP front end + the GLOMAP global mapper (``colmap global_mapper``).

    Solves all camera rotations/positions at once (rotation averaging + global
    positioning) instead of registering images one by one. The global mapper
    needs decent focal priors, so ``view_graph_calibrator`` first estimates the
    intrinsics from the two-view geometries (what standalone GLOMAP always did).
    """

    mapper_name = "global"

    def _map(
        self, colmap: str, scan: ScanInput, db: Path, sparse: Path, timings: dict[str, float]
    ) -> None:
        self._timed(
            timings,
            "calibrate_s",
            [colmap, "view_graph_calibrator", "--database_path", str(db)],
        )
        self._timed(
            timings,
            "map_s",
            [
                colmap,
                "global_mapper",
                "--database_path",
                str(db),
                "--image_path",
                str(scan.image_dir),
                "--output_path",
                str(sparse),
            ],
        )


class ColmapSfM(_ColmapFrontEnd):
    """Incremental SfM with COLMAP's ``mapper``."""

    mapper_name = "incremental"

    def _map(
        self, colmap: str, scan: ScanInput, db: Path, sparse: Path, timings: dict[str, float]
    ) -> None:
        self._timed(
            timings,
            "map_s",
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
        )


# Default (spike report 2026-09-26, Mip-NeRF 360 room): incremental COLMAP on
# GPU SIFT + GPU matching ("auto" matcher) beat the GLOMAP global mapper on SfM
# time, cost and splat quality; GLOMAP stays selectable.
SFM_CHOICES = ("colmap", "glomap")
DEFAULT_SFM = "colmap"
DEFAULT_MATCHER = "auto"


def select_sfm(
    name: str = DEFAULT_SFM, *, use_gpu: bool = True, matcher: str = DEFAULT_MATCHER
) -> SfM:
    """Return the SfM adapter for ``name`` ("colmap" or "glomap")."""
    if name == "glomap":
        return GlomapSfM(use_gpu=use_gpu, matcher=matcher)
    if name == "colmap":
        return ColmapSfM(use_gpu=use_gpu, matcher=matcher)
    raise ReconstructionError(f"unknown sfm {name!r}; expected one of {SFM_CHOICES}")


def benchmark_sfm(
    scan: ScanInput,
    work_dir: Path,
    matchers: tuple[str, ...] = ("exhaustive", "sequential", "vocab_tree"),
    mappers: tuple[str, ...] = SFM_CHOICES,
    use_gpu: bool = True,
) -> list[dict]:
    """SfM-only sweep: extract once, then every matcher x mapper on a DB copy.

    Used to pick the matcher/mapper defaults (spike report); one row per
    combination with step timings and model_analyzer numbers. A failing
    combination is recorded with its error instead of aborting the sweep.
    """
    import shutil

    colmap = require("colmap")
    extract_flags, match_flags = _gpu_flags(use_gpu)
    work_dir.mkdir(parents=True, exist_ok=True)
    base_db = work_dir / "features.db"
    front = ColmapSfM(use_gpu=use_gpu)
    extract: dict[str, float] = {}
    front._timed(
        extract,
        "extract_s",
        [
            colmap,
            "feature_extractor",
            "--database_path",
            str(base_db),
            "--image_path",
            str(scan.image_dir),
            "--ImageReader.single_camera",
            "1",
            *extract_flags,
        ],
    )
    rows: list[dict] = []
    for matcher in matchers:
        matched_db = work_dir / f"{matcher}.db"
        shutil.copyfile(base_db, matched_db)
        match: dict[str, float] = {}
        try:
            front._timed(match, "match_s", _matcher_argv(colmap, matcher, matched_db, match_flags))
        except subprocess.CalledProcessError as exc:
            rows.append({"matcher": matcher, "error": f"matcher failed: {exc}"})
            continue
        for name in mappers:
            adapter = select_sfm(name, use_gpu=use_gpu, matcher=matcher)
            db = work_dir / f"{matcher}-{name}.db"
            shutil.copyfile(matched_db, db)
            sparse = work_dir / f"sparse-{matcher}-{name}"
            sparse.mkdir()
            timings = {**extract, **match}
            row: dict = {"matcher": matcher, "mapper": adapter.mapper_name}
            try:
                adapter._map(colmap, scan, db, sparse, timings)
                model = _largest_model(sparse)
                row.update(timings)
                row["sfm_s"] = round(sum(timings.values()), 2)
                row["models"] = sum(1 for d in sparse.iterdir() if d.is_dir())
                row.update(_analyze(colmap, model))
            except subprocess.CalledProcessError as exc:
                row["error"] = f"mapper failed: {exc}"
            rows.append(row)
    return rows
