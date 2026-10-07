"""Feed-forward reconstruction front-end: metric point maps + poses -> splat init.

capture-render-quality-v1 (external-synthesis-builds.md). The commercial-safe way to
replace the brittle COLMAP SIFT + GLOMAP stage is a feed-forward transformer that regresses
dense metric point maps + poses in one pass: **MapAnything** (facebook/map-anything-apache,
Apache-2.0) which can be *conditioned on known intrinsics/poses* -- so we feed it GJ's ARKit
metric poses to lock scale -- or **VGGT-1B-Commercial** (custom commercial licence, counsel).

This module is the port + the bridge, both GPU-free: a ``FeedForwardReconstructor`` Protocol,
a deterministic ``MockFeedForward`` for tests, and ``write_frontend_model`` which turns the
model's output into the exact COLMAP model the trainer reads -- reusing ``arkit_poses``'s
writer and gating seed points by confidence (the feed-forward analogue of the scene-graph
confidence gate). The model inference itself is cloud-GPU (Operator). Standard library only.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .arkit_poses import (
    ARKIT_POSES_FILENAME,
    ArkitCapture,
    ArkitFrame,
    ArkitIntrinsics,
    ArkitSeedPoint,
    parse_arkit_capture,
    write_colmap_model,
)
from .models import CameraPoses, ReconstructionError, ScanInput

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class FFFrame:
    """One view the front-end solved: image name, intrinsics, metric cam->world (16, row-major)."""

    name: str
    intrinsics: ArkitIntrinsics
    cam_to_world: tuple[float, ...]


@dataclass(frozen=True)
class FFPoint:
    """A predicted 3D point with a per-point confidence in [0, 1]."""

    xyz: Vec3
    rgb: tuple[int, int, int] = (128, 128, 128)
    confidence: float = 1.0


@dataclass(frozen=True)
class FeedForwardResult:
    """Dense metric reconstruction from a feed-forward pass."""

    frames: list[FFFrame]
    points: list[FFPoint] = field(default_factory=list)
    metric: bool = False  # True when the output is in real metres
    conditioned_on_arkit: bool = False  # True when ARKit poses/intrinsics were fed in


class FeedForwardReconstructor(Protocol):
    """A model: frames -> poses + a dense point map (optionally ARKit-conditioned)."""

    name: str

    def reconstruct(
        self,
        frame_names: list[str],
        intrinsics: ArkitIntrinsics,
        *,
        prior_poses: list[tuple[float, ...]] | None = None,
    ) -> FeedForwardResult: ...


def result_to_capture(result: FeedForwardResult, *, confidence_floor: float = 0.0) -> ArkitCapture:
    """Convert a feed-forward result into an ``ArkitCapture``, dropping low-confidence points."""
    frames = [ArkitFrame(f.name, f.intrinsics, f.cam_to_world) for f in result.frames]
    points = [
        ArkitSeedPoint(xyz=p.xyz, rgb=p.rgb)
        for p in result.points
        if p.confidence >= confidence_floor
    ]
    return ArkitCapture(frames=frames, points=points)


def write_frontend_model(
    result: FeedForwardResult, model_dir: Path, *, confidence_floor: float = 0.0
) -> int:
    """Write the COLMAP model the trainer reads; returns the seed-point count kept."""
    capture = result_to_capture(result, confidence_floor=confidence_floor)
    write_colmap_model(capture, model_dir)
    return len(capture.points)


def _identity_pose(i: int) -> tuple[float, ...]:
    # A camera stepping along +x, looking down -z (a trivial deterministic fallback pose).
    return (1, 0, 0, float(i), 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


class MockFeedForward:
    """Deterministic stand-in for a real feed-forward model (tests / dry runs; no GPU)."""

    name = "mock-feedforward"

    def reconstruct(
        self,
        frame_names: list[str],
        intrinsics: ArkitIntrinsics,
        *,
        prior_poses: list[tuple[float, ...]] | None = None,
    ) -> FeedForwardResult:
        frames: list[FFFrame] = []
        for i, name in enumerate(frame_names):
            c2w = prior_poses[i] if prior_poses is not None else _identity_pose(i)
            frames.append(FFFrame(name, intrinsics, tuple(float(x) for x in c2w)))
        # A tiny seed cloud with mixed confidence, so gating is exercised.
        points = [
            FFPoint((0.0, 0.0, -1.0), (210, 190, 170), 0.92),
            FFPoint((0.4, 0.1, -1.2), (120, 120, 120), 0.80),
            FFPoint((0.9, 0.0, -1.0), (90, 90, 90), 0.25),  # low-confidence -> gated out
        ]
        conditioned = prior_poses is not None
        return FeedForwardResult(
            frames=frames, points=points, metric=conditioned, conditioned_on_arkit=conditioned
        )


# --- pose metrics (pure Python): Sim(3) alignment + absolute trajectory error ----------

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")


def _jacobi_eigen4(a: list[list[float]]) -> tuple[list[float], list[list[float]]]:
    """Eigen-decompose a symmetric 4x4 matrix (cyclic Jacobi): (values, column eigenvectors)."""
    a = [row[:] for row in a]
    v = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for _ in range(64):
        off = sum(a[i][j] ** 2 for i in range(4) for j in range(4) if i != j)
        if off < 1e-22:
            break
        for p in range(3):
            for q in range(p + 1, 4):
                if abs(a[p][q]) < 1e-300:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                sn = t * c
                for k in range(4):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p], a[k][q] = c * akp - sn * akq, sn * akp + c * akq
                for k in range(4):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k], a[q][k] = c * apk - sn * aqk, sn * apk + c * aqk
                for k in range(4):
                    vkp, vkq = v[k][p], v[k][q]
                    v[k][p], v[k][q] = c * vkp - sn * vkq, sn * vkp + c * vkq
    return [a[i][i] for i in range(4)], v


def sim3_align(src: list[Vec3], dst: list[Vec3]) -> tuple[float, tuple[Vec3, Vec3, Vec3], Vec3]:
    """Least-squares similarity (s, R, t) with ``dst ~= s * R @ src + t`` (Horn 1987, quaternions).

    Used to compare a feed-forward trajectory with a COLMAP/ARKit reference (they live in
    different world frames and, without metric conditioning, different scales).
    """
    n = len(src)
    if n != len(dst) or n < 3:
        raise ReconstructionError("sim3_align needs >= 3 matched points")
    ms = tuple(sum(p[i] for p in src) / n for i in range(3))
    md = tuple(sum(p[i] for p in dst) / n for i in range(3))
    a = [tuple(p[i] - ms[i] for i in range(3)) for p in src]
    b = [tuple(p[i] - md[i] for i in range(3)) for p in dst]
    m = [[sum(a[k][i] * b[k][j] for k in range(n)) for j in range(3)] for i in range(3)]
    (sxx, sxy, sxz), (syx, syy, syz), (szx, szy, szz) = m
    nmat = [
        [sxx + syy + szz, syz - szy, szx - sxz, sxy - syx],
        [syz - szy, sxx - syy - szz, sxy + syx, szx + sxz],
        [szx - sxz, sxy + syx, -sxx + syy - szz, syz + szy],
        [sxy - syx, szx + sxz, syz + szy, -sxx - syy + szz],
    ]
    vals, vecs = _jacobi_eigen4(nmat)
    best = max(range(4), key=lambda i: vals[i])
    qw, qx, qy, qz = (vecs[r][best] for r in range(4))
    rot = (
        (1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qw * qz), 2 * (qx * qz + qw * qy)),
        (2 * (qx * qy + qw * qz), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qw * qx)),
        (2 * (qx * qz - qw * qy), 2 * (qy * qz + qw * qx), 1 - 2 * (qx * qx + qy * qy)),
    )
    ra = [tuple(sum(rot[i][j] * p[j] for j in range(3)) for i in range(3)) for p in a]
    den = sum(x * x for p in a for x in p)
    scale = sum(ra[k][i] * b[k][i] for k in range(n) for i in range(3)) / den if den else 1.0
    rms = tuple(sum(rot[i][j] * ms[j] for j in range(3)) for i in range(3))
    t = tuple(md[i] - scale * rms[i] for i in range(3))
    return scale, rot, t  # type: ignore[return-value]


def apply_sim3(sim: tuple[float, tuple[Vec3, Vec3, Vec3], Vec3], p: Vec3) -> Vec3:
    scale, rot, t = sim
    return tuple(scale * sum(rot[i][j] * p[j] for j in range(3)) + t[i] for i in range(3))  # type: ignore[return-value]


def camera_center(cam_to_world: tuple[float, ...]) -> Vec3:
    return (cam_to_world[3], cam_to_world[7], cam_to_world[11])


def trajectory_error(pred: list[Vec3], ref: list[Vec3]) -> dict:
    """ATE after Sim(3): RMSE / median in the reference's units, plus the fitted scale."""
    sim = sim3_align(pred, ref)
    errs = sorted(math.dist(apply_sim3(sim, p), r) for p, r in zip(pred, ref, strict=True))
    rmse = math.sqrt(sum(e * e for e in errs) / len(errs))
    return {"ate_rmse": rmse, "ate_median": errs[len(errs) // 2], "sim3_scale": sim[0]}


def occupied_voxels(points: list[Vec3], voxel: float) -> int:
    """Distinct ``voxel``-sized cells hit by ``points`` (init-coverage proxy)."""
    if voxel <= 0:
        raise ReconstructionError("voxel must be positive")
    return len(
        {
            (math.floor(x / voxel), math.floor(y / voxel), math.floor(z / voxel))
            for x, y, z in points
        }
    )


def frontend_metrics(
    pred_c2w: dict[str, tuple[float, ...]],
    ref_c2w: dict[str, tuple[float, ...]],
    seed_points: list[Vec3],
    ref_points: list[Vec3],
) -> dict:
    """Item-6 A/B front-end metrics: pose error vs a reference + init density.

    Pose error is the Sim(3)-aligned ATE on shared frames, also relative to the reference
    camera extent E (bbox diagonal). Density counts seed points and occupied E/60 voxels
    (the floater-proxy grid) for the candidate (moved into the reference frame) and the
    reference sparse cloud.
    """
    shared = sorted(set(pred_c2w) & set(ref_c2w))
    out: dict = {
        "frames_pred": len(pred_c2w),
        "frames_ref": len(ref_c2w),
        "frames_shared": len(shared),
    }
    ref_c = [camera_center(ref_c2w[n]) for n in shared]
    if len(shared) >= 3:
        pred_c = [camera_center(pred_c2w[n]) for n in shared]
        err = trajectory_error(pred_c, ref_c)
        lo = [min(c[i] for c in ref_c) for i in range(3)]
        hi = [max(c[i] for c in ref_c) for i in range(3)]
        extent = math.dist(lo, hi) or 1.0
        sim = sim3_align(pred_c, ref_c)
        moved = [apply_sim3(sim, p) for p in seed_points]
        voxel = extent / 60.0
        out.update(
            err,
            camera_extent=extent,
            ate_rel_extent=err["ate_rmse"] / extent,
            voxel=voxel,
            seed_points=len(seed_points),
            ref_points=len(ref_points),
            seed_occupied_voxels=occupied_voxels(moved, voxel),
            ref_occupied_voxels=occupied_voxels(ref_points, voxel),
        )
    return out


# --- the SfM port ---------------------------------------------------------------------


class FeedForwardSfM:
    """SfM-port adapter over a ``FeedForwardReconstructor`` (``run(scan, work_dir)``).

    With an ``arkit_poses.json`` beside the images, the model is conditioned on ARKit's
    metric poses + intrinsics and the written COLMAP model keeps the ARKit per-frame
    intrinsics; otherwise ``intrinsics`` must be given (e.g. from a COLMAP reference) and the
    model's own poses are used. Seed points are confidence-gated; Splatfacto initialises
    from them exactly as on the ARKit path (``sparse/0/points3D.txt``).

    ``ship_status`` other than ``"cleared"`` refuses to run unless ``internal_eval`` -- a
    counsel-pending model (AUTH #049) may only produce internal-debug artifacts, which the
    caller deletes after scoring (AUTH #047).
    """

    def __init__(
        self,
        make_reconstructor: Callable[[Path], FeedForwardReconstructor],
        *,
        mapper_name: str,
        ship_status: str,
        internal_eval: bool = False,
        confidence_floor: float = 0.1,
        intrinsics: ArkitIntrinsics | None = None,
        capture: ArkitCapture | None = None,
    ) -> None:
        if not 0.0 <= confidence_floor < 1.0:
            raise ReconstructionError("confidence_floor must be in [0, 1)")
        self._make = make_reconstructor
        self.mapper_name = mapper_name
        self.ship_status = ship_status
        self.internal_eval = internal_eval
        self.confidence_floor = confidence_floor
        self._intrinsics = intrinsics
        self._capture = capture

    def _arkit(self, scan: ScanInput) -> ArkitCapture | None:
        if self._capture is not None:
            return self._capture
        path = scan.image_dir.parent / ARKIT_POSES_FILENAME
        if path.exists():
            return parse_arkit_capture(json.loads(path.read_text(encoding="utf-8")))
        return None

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        if self.ship_status != "cleared" and not self.internal_eval:
            raise ReconstructionError(
                f"sfm {self.mapper_name!r} is {self.ship_status} (AUTH #049): "
                "internal-eval only; pass internal_eval=True and delete the artifacts"
            )
        arkit = self._arkit(scan)
        if arkit is not None:
            names = [f.name for f in arkit.frames]
            intrinsics = arkit.frames[0].intrinsics
            prior = [f.cam_to_world for f in arkit.frames]
        else:
            if self._intrinsics is None:
                raise ReconstructionError(
                    f"sfm {self.mapper_name!r}: no {ARKIT_POSES_FILENAME} and no intrinsics given"
                )
            names = sorted(
                p.name for p in scan.image_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES
            )
            intrinsics, prior = self._intrinsics, None
        if not names:
            raise ReconstructionError(f"sfm {self.mapper_name!r}: no frames in {scan.image_dir}")
        started = time.monotonic()
        result = self._make(scan.image_dir).reconstruct(names, intrinsics, prior_poses=prior)
        wall = time.monotonic() - started
        if arkit is not None:  # keep ARKit's per-frame intrinsics (may vary with focus)
            by_name = {f.name: f.intrinsics for f in arkit.frames}
            result = FeedForwardResult(
                frames=[
                    FFFrame(f.name, by_name.get(f.name, f.intrinsics), f.cam_to_world)
                    for f in result.frames
                ],
                points=result.points,
                metric=result.metric,
                conditioned_on_arkit=result.conditioned_on_arkit,
            )
        model = work_dir / "sparse" / "0"
        kept = write_frontend_model(result, model, confidence_floor=self.confidence_floor)
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=model,
            registered_images=len(result.frames),
            image_dir=scan.image_dir,
            stats={
                "mapper": self.mapper_name,
                "input_images": scan.image_count,
                "registered_images": len(result.frames),
                "seed_points": kept,
                "seed_points_raw": len(result.points),
                "confidence_floor": self.confidence_floor,
                "conditioned_on_arkit": result.conditioned_on_arkit,
                "metric": result.metric,
                "ship_status": self.ship_status,
                "internal_eval": self.internal_eval,
                "sfm_s": round(wall, 3),
            },
        )
