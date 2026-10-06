"""ARKit metric poses -> COLMAP sparse model: skip SfM for the splat trainer.

Open-knowledge synthesis (feed-forward reconstruction literature, incl. Fast3R's
single-pass pose regression; see design/proposals/external-synthesis-builds.md). The
idea we keep is *architecture-level and license-free*: hand the splat trainer camera
poses + a seed point cloud directly, instead of recovering them with the slow,
brittle COLMAP SIFT + GLOMAP global-mapper stage. No external code, weights, or model
outputs are used.

On iOS we already have something better than a learned feed-forward net for the pose
half: **ARKit tracks metric camera poses during the scan** (world transform per frame,
gravity-aligned, in real metres). This adapter converts that capture bundle into the
exact COLMAP text model (``cameras.txt`` / ``images.txt`` / ``points3D.txt``) the
nerfstudio ``colmap`` dataparser reads, so Splatfacto initialises from real poses with
no SfM run at all. Because the poses are metric, the splat lands at true scale --
fixing the up-to-scale ambiguity the DUSt3R/Fast3R family has -- and because it is pure
on-device-origin data, it suits a real USER scan that may never leave our infra
(ADR-0005 / AUTH #030).

Coordinate handoff: ARKit camera space is +x right, +y up, -z forward (OpenGL-style)
in a right-handed world; COLMAP stores world-to-camera [R|t] with +x right, +y down,
+z forward. We transpose cam->world to world->camera and flip the y/z camera axes.

Standard library only; deterministic. Importing this never requires a GPU or COLMAP.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from .models import CameraPoses, ReconstructionError, ScanInput

# A capture bundle places the ARKit track beside its ``images/`` dir under this name.
ARKIT_POSES_FILENAME = "arkit_poses.json"

Mat3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class ArkitIntrinsics:
    """Pinhole intrinsics for one frame, in pixels (ARKit ``camera.intrinsics``)."""

    fx: float
    fy: float
    cx: float
    cy: float
    width: int
    height: int

    def __post_init__(self) -> None:
        if min(self.fx, self.fy) <= 0.0:
            raise ReconstructionError("fx, fy must be positive")
        if self.width <= 0 or self.height <= 0:
            raise ReconstructionError("width, height must be positive")


@dataclass(frozen=True)
class ArkitFrame:
    """One captured frame: its image name, intrinsics, and metric camera pose.

    ``cam_to_world`` is a 4x4 matrix in **row-major** order (16 floats). ARKit's
    ``simd_float4x4`` is column-major, so the capture exporter transposes it before
    writing the bundle.
    """

    name: str
    intrinsics: ArkitIntrinsics
    cam_to_world: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ReconstructionError("frame name must be non-empty")
        if len(self.cam_to_world) != 16:
            raise ReconstructionError(
                f"cam_to_world must have 16 elements (row-major 4x4), got {len(self.cam_to_world)}"
            )


@dataclass(frozen=True)
class ArkitSeedPoint:
    """A world-space seed point (ARKit feature point or depth-derived) for splat init."""

    xyz: Vec3
    rgb: tuple[int, int, int] = (128, 128, 128)

    def __post_init__(self) -> None:
        if any(not 0 <= c <= 255 for c in self.rgb):
            raise ReconstructionError("rgb channels must be in [0, 255]")


@dataclass(frozen=True)
class ArkitCapture:
    """The ARKit track for one scan: per-frame poses + an optional seed cloud."""

    frames: list[ArkitFrame]
    points: list[ArkitSeedPoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.frames:
            raise ReconstructionError("an ARKit capture needs at least one frame")


# --- pose math (pure Python) ---------------------------------------------------


def _rotation_and_center(cam_to_world: tuple[float, ...]) -> tuple[Mat3, Vec3]:
    """Split a row-major 4x4 cam->world matrix into its 3x3 rotation and world center."""
    m = cam_to_world
    rot: Mat3 = (
        (m[0], m[1], m[2]),
        (m[4], m[5], m[6]),
        (m[8], m[9], m[10]),
    )
    center: Vec3 = (m[3], m[7], m[11])
    return rot, center


def _matvec(r: Mat3, v: Vec3) -> Vec3:
    return (
        r[0][0] * v[0] + r[0][1] * v[1] + r[0][2] * v[2],
        r[1][0] * v[0] + r[1][1] * v[1] + r[1][2] * v[2],
        r[2][0] * v[0] + r[2][1] * v[1] + r[2][2] * v[2],
    )


def quaternion_from_rotation(r: Mat3) -> tuple[float, float, float, float]:
    """Unit quaternion (qw, qx, qy, qz) from a 3x3 rotation matrix (COLMAP order)."""
    (m00, m01, m02), (m10, m11, m12), (m20, m21, m22) = r
    trace = m00 + m11 + m22
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        qw, qx, qy, qz = 0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        qw, qx, qy, qz = (m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        qw, qx, qy, qz = (m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        qw, qx, qy, qz = (m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s
    norm = math.sqrt(qw * qw + qx * qx + qy * qy + qz * qz) or 1.0
    return (qw / norm, qx / norm, qy / norm, qz / norm)


def colmap_pose(cam_to_world: tuple[float, ...]) -> tuple[tuple[float, float, float, float], Vec3]:
    """Convert an ARKit cam->world pose to a COLMAP (qvec, tvec) world->camera pose.

    Returns ((qw, qx, qy, qz), (tx, ty, tz)). Metric translation is preserved.
    """
    rot_cw, center = _rotation_and_center(cam_to_world)
    # world->camera rotation is the transpose of cam->world.
    rot_wc: Mat3 = (
        (rot_cw[0][0], rot_cw[1][0], rot_cw[2][0]),
        (rot_cw[0][1], rot_cw[1][1], rot_cw[2][1]),
        (rot_cw[0][2], rot_cw[1][2], rot_cw[2][2]),
    )
    t_wc = _matvec(rot_wc, center)
    t_wc = (-t_wc[0], -t_wc[1], -t_wc[2])
    # Flip y, z to go from ARKit/OpenGL camera axes to COLMAP/OpenCV camera axes.
    rot_colmap: Mat3 = (
        (rot_wc[0][0], rot_wc[0][1], rot_wc[0][2]),
        (-rot_wc[1][0], -rot_wc[1][1], -rot_wc[1][2]),
        (-rot_wc[2][0], -rot_wc[2][1], -rot_wc[2][2]),
    )
    t_colmap: Vec3 = (t_wc[0], -t_wc[1], -t_wc[2])
    return quaternion_from_rotation(rot_colmap), t_colmap


# --- bundle parsing + COLMAP model writing -------------------------------------


def parse_arkit_capture(data: dict) -> ArkitCapture:
    """Parse the ``arkit_poses.json`` document into an ``ArkitCapture``."""
    frames_in = data.get("frames")
    if not isinstance(frames_in, list) or not frames_in:
        raise ReconstructionError("arkit capture: 'frames' must be a non-empty list")
    frames: list[ArkitFrame] = []
    for raw in frames_in:
        intr = raw.get("intrinsics", {})
        frames.append(
            ArkitFrame(
                name=str(raw.get("name", "")),
                intrinsics=ArkitIntrinsics(
                    fx=float(intr["fx"]),
                    fy=float(intr["fy"]),
                    cx=float(intr["cx"]),
                    cy=float(intr["cy"]),
                    width=int(intr["width"]),
                    height=int(intr["height"]),
                ),
                cam_to_world=tuple(float(x) for x in raw["cam_to_world"]),
            )
        )
    points: list[ArkitSeedPoint] = []
    for raw in data.get("points", []) or []:
        xyz = tuple(float(x) for x in raw["xyz"])
        if len(xyz) != 3:
            raise ReconstructionError("seed point 'xyz' must have 3 elements")
        rgb = tuple(int(c) for c in raw.get("rgb", (128, 128, 128)))
        points.append(ArkitSeedPoint(xyz=xyz, rgb=rgb))  # type: ignore[arg-type]
    return ArkitCapture(frames=frames, points=points)


def _fmt(x: float) -> str:
    return f"{x:.9g}"


def write_colmap_model(capture: ArkitCapture, model_dir: Path) -> None:
    """Write ``cameras.txt`` / ``images.txt`` / ``points3D.txt`` from the ARKit track.

    One PINHOLE camera per frame (intrinsics may vary frame to frame). Image records
    carry no 2D keypoints; the seed cloud is written with empty tracks -- enough for
    the trainer's SfM-free point initialisation.
    """
    model_dir.mkdir(parents=True, exist_ok=True)

    cam_lines = [
        "# Camera list with one line of data per camera:",
        "#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]",
    ]
    img_lines = [
        "# Image list with two lines of data per image:",
        "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME",
        "#   POINTS2D[] as (X, Y, POINT3D_ID)",
    ]
    for i, frame in enumerate(capture.frames, start=1):
        k = frame.intrinsics
        cam_lines.append(
            f"{i} PINHOLE {k.width} {k.height} {_fmt(k.fx)} {_fmt(k.fy)} {_fmt(k.cx)} {_fmt(k.cy)}"
        )
        (qw, qx, qy, qz), (tx, ty, tz) = colmap_pose(frame.cam_to_world)
        img_lines.append(
            f"{i} {_fmt(qw)} {_fmt(qx)} {_fmt(qy)} {_fmt(qz)} "
            f"{_fmt(tx)} {_fmt(ty)} {_fmt(tz)} {i} {frame.name}"
        )
        img_lines.append("")  # no 2D keypoints

    pt_lines = [
        "# 3D point list with one line of data per point:",
        "#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)",
    ]
    for j, pt in enumerate(capture.points, start=1):
        x, y, z = pt.xyz
        r, g, b = pt.rgb
        pt_lines.append(f"{j} {_fmt(x)} {_fmt(y)} {_fmt(z)} {r} {g} {b} 0")

    (model_dir / "cameras.txt").write_text("\n".join(cam_lines) + "\n", encoding="utf-8")
    (model_dir / "images.txt").write_text("\n".join(img_lines) + "\n", encoding="utf-8")
    (model_dir / "points3D.txt").write_text("\n".join(pt_lines) + "\n", encoding="utf-8")


class ArkitSfM:
    """SfM-free pose source: emit a COLMAP model from an ARKit capture bundle.

    Satisfies the ``sfm.SfM`` port (``run(scan, work_dir) -> CameraPoses``). Construct
    with an explicit ``capture`` (tests, direct use) or leave it ``None`` to load
    ``arkit_poses.json`` from beside the scan's image dir (the factory path).
    """

    mapper_name = "arkit"

    def __init__(self, capture: ArkitCapture | None = None) -> None:
        self._capture = capture

    def _load(self, scan: ScanInput) -> ArkitCapture:
        if self._capture is not None:
            return self._capture
        poses_path = scan.image_dir.parent / ARKIT_POSES_FILENAME
        if not poses_path.exists():
            raise ReconstructionError(f"arkit sfm: no capture provided and {poses_path} is missing")
        return parse_arkit_capture(json.loads(poses_path.read_text(encoding="utf-8")))

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        capture = self._load(scan)
        model = work_dir / "sparse" / "0"
        write_colmap_model(capture, model)
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=model,
            registered_images=len(capture.frames),
            image_dir=scan.image_dir,
            stats={
                "mapper": self.mapper_name,
                "input_images": scan.image_count,
                "registered_images": len(capture.frames),
                "seed_points": len(capture.points),
                "sfm_s": 0.0,  # no SfM run: poses come straight from ARKit
            },
        )
