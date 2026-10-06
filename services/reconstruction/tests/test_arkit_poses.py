"""ARKit-pose -> COLMAP-model adapter (splat-init without SfM).

Proves the coordinate handoff (metric, ARKit/OpenGL -> COLMAP/OpenCV), the COLMAP
text model it writes, and that the adapter satisfies the SfM port + config/selector.
"""

import json
import math

import pytest
from reconstruction import (
    ArkitCapture,
    ArkitFrame,
    ArkitIntrinsics,
    ArkitSeedPoint,
    ArkitSfM,
    ReconstructionConfig,
    ReconstructionError,
    ScanInput,
    Source,
    parse_arkit_capture,
    select_sfm,
)
from reconstruction.arkit_poses import ARKIT_POSES_FILENAME, colmap_pose

K = ArkitIntrinsics(fx=1000.0, fy=1000.0, cx=320.0, cy=240.0, width=640, height=480)


def _frame(name, cam_to_world):
    return ArkitFrame(name=name, intrinsics=K, cam_to_world=tuple(cam_to_world))


def _identity_at(cx, cy, cz):
    # Row-major cam->world: identity rotation, translation = camera center.
    return (1, 0, 0, cx, 0, 1, 0, cy, 0, 0, 1, cz, 0, 0, 0, 1)


def _rotation_from_quat(q):
    qw, qx, qy, qz = q
    return (
        (1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)),
        (2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)),
        (2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)),
    )


def _recovered_center(q, t):
    # COLMAP world->camera: x_cam = R x_world + t, so camera center = -R^T t.
    r = _rotation_from_quat(q)
    return tuple(-(r[0][i] * t[0] + r[1][i] * t[1] + r[2][i] * t[2]) for i in range(3))


def test_identity_pose_maps_to_x_axis_flip():
    # Identity cam->world at (1,2,3): world->camera is the y/z flip, translation (-1,2,3).
    q, t = colmap_pose(_identity_at(1.0, 2.0, 3.0))
    assert q == pytest.approx((0.0, 1.0, 0.0, 0.0), abs=1e-9)
    assert t == pytest.approx((-1.0, 2.0, 3.0), abs=1e-9)


def test_quaternion_is_unit():
    q, _ = colmap_pose(_identity_at(0.4, -1.1, 2.2))
    assert math.sqrt(sum(c * c for c in q)) == pytest.approx(1.0, abs=1e-9)


def test_metric_center_round_trips_through_a_rotated_pose():
    # Camera at (2,1,-3), yawed 90 deg about world Y (cam->world rotation Ry(90)).
    cam_to_world = (0, 0, 1, 2, 0, 1, 0, 1, -1, 0, 0, -3, 0, 0, 0, 1)
    q, t = colmap_pose(cam_to_world)
    assert _recovered_center(q, t) == pytest.approx((2.0, 1.0, -3.0), abs=1e-6)


def test_parse_capture_reads_frames_and_points():
    data = {
        "frames": [
            {
                "name": "f0.jpg",
                "intrinsics": {
                    "fx": 1000,
                    "fy": 1000,
                    "cx": 320,
                    "cy": 240,
                    "width": 640,
                    "height": 480,
                },
                "cam_to_world": list(_identity_at(0.0, 0.0, 0.0)),
            }
        ],
        "points": [{"xyz": [1.0, 2.0, 3.0], "rgb": [10, 20, 30]}],
    }
    cap = parse_arkit_capture(data)
    assert len(cap.frames) == 1
    assert cap.frames[0].name == "f0.jpg"
    assert cap.points[0].xyz == (1.0, 2.0, 3.0)
    assert cap.points[0].rgb == (10, 20, 30)


def test_bad_transform_length_is_rejected():
    with pytest.raises(ReconstructionError):
        ArkitFrame(name="bad", intrinsics=K, cam_to_world=(1, 2, 3))


def _two_frame_capture():
    return ArkitCapture(
        frames=[_frame("f0.jpg", _identity_at(0, 0, 0)), _frame("f1.jpg", _identity_at(1, 0, 0))],
        points=[ArkitSeedPoint(xyz=(0.5, 0.0, -1.0), rgb=(200, 100, 50))],
    )


def test_run_writes_a_colmap_text_model(tmp_path):
    scan = ScanInput(
        scan_id="scan-1", image_dir=tmp_path / "images", image_count=2, source=Source.CORPUS
    )
    poses = ArkitSfM(_two_frame_capture()).run(scan, tmp_path / "work")
    assert poses.registered_images == 2
    assert poses.sparse_dir == tmp_path / "work" / "sparse" / "0"
    cameras = (poses.sparse_dir / "cameras.txt").read_text()
    images = (poses.sparse_dir / "images.txt").read_text()
    points = (poses.sparse_dir / "points3D.txt").read_text()
    assert "PINHOLE 640 480 1000 1000 320 240" in cameras
    # Two data lines per image (pose line + empty keypoint line), two images.
    assert images.count("f0.jpg") == 1 and images.count("f1.jpg") == 1
    # One seed point written with its colour.
    assert "200 100 50" in points
    assert poses.stats["seed_points"] == 1
    assert poses.stats["sfm_s"] == 0.0


def test_run_loads_bundle_from_disk_when_no_capture_given(tmp_path):
    images_dir = tmp_path / "bundle" / "images"
    images_dir.mkdir(parents=True)
    bundle = {
        "frames": [
            {
                "name": "f0.jpg",
                "intrinsics": {
                    "fx": 800,
                    "fy": 800,
                    "cx": 160,
                    "cy": 120,
                    "width": 320,
                    "height": 240,
                },
                "cam_to_world": list(_identity_at(0.0, 0.0, 0.0)),
            }
        ]
    }
    (tmp_path / "bundle" / ARKIT_POSES_FILENAME).write_text(json.dumps(bundle))
    scan = ScanInput(scan_id="s", image_dir=images_dir, image_count=1, source=Source.CORPUS)
    poses = ArkitSfM().run(scan, tmp_path / "work")
    assert poses.registered_images == 1


def test_missing_bundle_is_a_clear_error(tmp_path):
    scan = ScanInput(
        scan_id="s", image_dir=tmp_path / "images", image_count=1, source=Source.CORPUS
    )
    with pytest.raises(ReconstructionError, match="arkit_poses.json"):
        ArkitSfM().run(scan, tmp_path / "work")


def test_selector_and_config_accept_arkit():
    assert isinstance(select_sfm("arkit"), ArkitSfM)
    assert ReconstructionConfig(sfm="arkit").sfm == "arkit"
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(sfm="nope")
