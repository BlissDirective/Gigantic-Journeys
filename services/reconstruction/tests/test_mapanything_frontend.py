"""MapAnything feed-forward front-end (item 6): licence gate, pose handoff, SfM port.

Standard library only -- the model itself (torch / mapanything) is never imported here.
"""

import json
import math
import random

import pytest
from reconstruction import (
    ArkitCapture,
    ArkitFrame,
    ArkitIntrinsics,
    FeedForwardSfM,
    MockFeedForward,
    ReconstructionConfig,
    ReconstructionError,
    ScanInput,
    Source,
    select_sfm,
)
from reconstruction.arkit_poses import ARKIT_POSES_FILENAME, colmap_pose, quaternion_from_rotation
from reconstruction.feedforward_frontend import (
    apply_sim3,
    camera_center,
    sim3_align,
    trajectory_error,
)
from reconstruction.licenses import (
    COUNSEL_PENDING,
    EXCLUDED_COMPONENTS,
    MANIFEST,
    Component,
    LicenseError,
    assert_commercial_safe,
)
from reconstruction.mapanything_frontend import (
    MAPANYTHING_MODEL_ID,
    MAPANYTHING_REVISION,
    SHIP_STATUS,
    MapAnythingReconstructor,
    assemble_result,
    check_model_id,
    flip_camera_axes,
    rank_confidence,
)

K = ArkitIntrinsics(fx=900.0, fy=900.0, cx=480.0, cy=270.0, width=960, height=540)


def _rot(axis, angle):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    x, y, z = x / n, y / n, z / n
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    return (
        (t * x * x + c, t * x * y - s * z, t * x * z + s * y),
        (t * x * y + s * z, t * y * y + c, t * y * z - s * x),
        (t * x * z - s * y, t * y * z + s * x, t * z * z + c),
    )


def _c2w(rot, centre):
    return (
        *rot[0], centre[0], *rot[1], centre[1], *rot[2], centre[2], 0.0, 0.0, 0.0, 1.0
    )  # fmt: skip


def _orbit(n=6):
    poses = []
    for i in range(n):
        a = 2 * math.pi * i / n
        poses.append(_c2w(_rot((0, 1, 0), a), (2.0 * math.sin(a), 1.5, 2.0 * math.cos(a))))
    return poses


# --- licence gate ----------------------------------------------------------------------


def test_only_pinned_apache_checkpoint_is_accepted():
    assert check_model_id(MAPANYTHING_MODEL_ID) == "facebook/map-anything-apache"
    for nc in ("facebook/map-anything", "facebook/map-anything-v1"):
        with pytest.raises(LicenseError, match="CC-BY-NC"):
            check_model_id(nc)
    with pytest.raises(LicenseError):
        check_model_id("someone/map-anything-apache-mirror")
    with pytest.raises(LicenseError, match="revision"):
        check_model_id(MAPANYTHING_MODEL_ID, revision="main")


def test_reconstructor_refuses_noncommercial_before_any_import(tmp_path):
    with pytest.raises(LicenseError):
        MapAnythingReconstructor(tmp_path, model_id="facebook/map-anything")
    rec = MapAnythingReconstructor(tmp_path)  # constructing never imports torch
    assert rec.revision == MAPANYTHING_REVISION


def test_mapanything_is_counsel_pending_not_in_manifest():
    assert SHIP_STATUS == "blocked-pending-counsel"
    names = {c.name for c in MANIFEST}
    assert all(c.name not in names for c in COUNSEL_PENDING)
    assert any("map-anything-apache" in c.name for c in COUNSEL_PENDING)
    nc = next(n for n in EXCLUDED_COMPONENTS if n.startswith("MapAnything CC-BY-NC"))
    with pytest.raises(LicenseError):
        assert_commercial_safe((*MANIFEST, Component(nc, "Apache-2.0", "x")))


# --- pose handoff ----------------------------------------------------------------------


def test_flip_is_an_involution_and_matches_colmap_pose():
    rng = random.Random(3)
    for _ in range(5):
        rot = _rot(
            (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(0.1, 1)), rng.uniform(-3, 3)
        )
        arkit = _c2w(rot, (rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-3, 3)))
        assert flip_camera_axes(flip_camera_axes(arkit)) == pytest.approx(arkit)
        cv = flip_camera_axes(arkit)  # OpenCV cam->world
        r_cv = ((cv[0], cv[1], cv[2]), (cv[4], cv[5], cv[6]), (cv[8], cv[9], cv[10]))
        r_wc = tuple(tuple(r_cv[j][i] for j in range(3)) for i in range(3))
        q_expect = quaternion_from_rotation(r_wc)
        centre = camera_center(cv)
        t_expect = tuple(-sum(r_wc[i][j] * centre[j] for j in range(3)) for i in range(3))
        q, t = colmap_pose(arkit)
        sign = (
            1.0
            if q[0] * q_expect[0] + sum(a * b for a, b in zip(q[1:], q_expect[1:], strict=True)) > 0
            else -1.0
        )
        assert [sign * x for x in q] == pytest.approx(q_expect, abs=1e-9)
        assert t == pytest.approx(t_expect, abs=1e-9)


def test_rank_confidence():
    assert rank_confidence([]) == []
    assert rank_confidence([5.0]) == [1.0]
    assert rank_confidence([3.0, 1.0, 2.0]) == [1.0, 0.0, 0.5]


def test_sim3_recovers_known_similarity():
    rng = random.Random(7)
    src = [(rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-2, 2)) for _ in range(10)]
    truth = (2.5, _rot((0.3, 1.0, -0.2), 1.1), (0.4, -1.0, 3.0))
    dst = [apply_sim3(truth, p) for p in src]
    s, r, t = sim3_align(src, dst)
    assert s == pytest.approx(2.5, rel=1e-9)
    assert t == pytest.approx(truth[2], abs=1e-9)
    for row, row_t in zip(r, truth[1], strict=True):
        assert row == pytest.approx(row_t, abs=1e-9)
    err = trajectory_error(src, dst)
    assert err["ate_rmse"] < 1e-9 and err["sim3_scale"] == pytest.approx(2.5)
    with pytest.raises(ReconstructionError):
        sim3_align(src[:2], dst[:2])


def test_assemble_moves_points_into_the_arkit_world():
    prior = _orbit()
    # The model answered in its own world: arbitrary similarity of the ARKit world.
    sim = (0.5, _rot((1, 2, 3), 0.7), (5.0, -2.0, 1.0))
    pred_arkit = []
    for m in prior:
        rot = ((m[0], m[1], m[2]), (m[4], m[5], m[6]), (m[8], m[9], m[10]))
        r_sim = sim[1]
        r_new = tuple(
            tuple(sum(r_sim[i][k] * rot[k][j] for k in range(3)) for j in range(3))
            for i in range(3)
        )
        pred_arkit.append(_c2w(r_new, apply_sim3(sim, camera_center(m))))
    pred_cv = [flip_camera_axes(m) for m in pred_arkit]
    world_pt = (0.3, 1.0, -0.5)
    points = [(apply_sim3(sim, world_pt), (10, 20, 30), 4.0), ((0.0, 0.0, 0.0), (0, 0, 0), 1.0)]
    names = [f"f{i:03d}.jpg" for i in range(len(prior))]
    result, diag = assemble_result(names, K, pred_cv, points, prior_poses=prior)
    assert diag["aligned_to_prior"] and diag["prior_centre_rmse_m"] < 1e-9
    assert diag["sim3_scale"] == pytest.approx(2.0)
    assert result.points[0].xyz == pytest.approx(world_pt, abs=1e-9)
    assert [p.confidence for p in result.points] == [1.0, 0.0]
    assert result.frames[2].cam_to_world == pytest.approx(prior[2])
    assert result.metric and result.conditioned_on_arkit


def test_assemble_without_prior_uses_model_poses():
    poses = _orbit(3)
    result, diag = assemble_result(
        ["a", "b", "c"], K, [flip_camera_axes(m) for m in poses], [((1, 2, 3), (1, 1, 1), 1.0)]
    )
    assert not diag["aligned_to_prior"] and not result.metric
    assert result.frames[1].cam_to_world == pytest.approx(poses[1])
    with pytest.raises(ValueError):
        assemble_result(["a"], K, poses[:2], [])


# --- SfM port --------------------------------------------------------------------------


def _scan(tmp_path, n=3, arkit=True):
    images = tmp_path / "capture" / "images"
    images.mkdir(parents=True)
    poses = _orbit(n)
    for i in range(n):
        (images / f"f{i:03d}.jpg").write_bytes(b"\xff\xd8")
    if arkit:
        frames = [
            {
                "name": f"f{i:03d}.jpg",
                "intrinsics": {
                    "fx": 900,
                    "fy": 900,
                    "cx": 480,
                    "cy": 270,
                    "width": 960,
                    "height": 540,
                },
                "cam_to_world": list(poses[i]),
            }
            for i in range(n)
        ]
        (images.parent / ARKIT_POSES_FILENAME).write_text(json.dumps({"frames": frames}))
    return ScanInput(scan_id="s", image_dir=images, image_count=n, source=Source.CORPUS), poses


def _sfm(**kw):
    return FeedForwardSfM(
        lambda _d: MockFeedForward(), mapper_name="mapanything", ship_status=SHIP_STATUS, **kw
    )


def test_counsel_pending_sfm_refuses_outside_internal_eval(tmp_path):
    scan, _ = _scan(tmp_path)
    with pytest.raises(ReconstructionError, match="AUTH #049"):
        _sfm().run(scan, tmp_path / "work")
    assert not (tmp_path / "work").exists()


def test_arkit_conditioned_run_writes_gated_model(tmp_path):
    scan, poses = _scan(tmp_path)
    out = _sfm(internal_eval=True, confidence_floor=0.5).run(scan, tmp_path / "work")
    assert out.sparse_dir == tmp_path / "work" / "sparse" / "0"
    assert out.registered_images == 3
    st = out.stats
    assert st["mapper"] == "mapanything" and st["conditioned_on_arkit"] and st["metric"]
    assert st["seed_points"] == 2 and st["seed_points_raw"] == 3  # 0.25-confidence point gated
    assert st["ship_status"] == "blocked-pending-counsel" and st["internal_eval"]
    cams = (out.sparse_dir / "cameras.txt").read_text().splitlines()
    assert cams[-1].startswith("3 PINHOLE 960 540 900 900 480 270")
    pts = [ln for ln in (out.sparse_dir / "points3D.txt").read_text().splitlines() if ln[:1] != "#"]
    assert len(pts) == 2


def test_unconditioned_run_needs_intrinsics(tmp_path):
    scan, _ = _scan(tmp_path, arkit=False)
    with pytest.raises(ReconstructionError, match="intrinsics"):
        _sfm(internal_eval=True).run(scan, tmp_path / "w1")
    out = _sfm(internal_eval=True, intrinsics=K).run(scan, tmp_path / "w2")
    assert out.registered_images == 3 and not out.stats["conditioned_on_arkit"]


def test_explicit_capture_and_floor_validation(tmp_path):
    scan, poses = _scan(tmp_path, arkit=False)
    cap = ArkitCapture(frames=[ArkitFrame(f"f{i:03d}.jpg", K, poses[i]) for i in range(3)])
    out = _sfm(internal_eval=True, capture=cap).run(scan, tmp_path / "w")
    assert out.stats["conditioned_on_arkit"]
    with pytest.raises(ReconstructionError):
        _sfm(confidence_floor=1.0)


def test_selector_and_config_default_off():
    assert ReconstructionConfig().sfm == "colmap"
    assert ReconstructionConfig(sfm="mapanything").sfm == "mapanything"
    sfm = select_sfm("mapanything")
    assert isinstance(sfm, FeedForwardSfM)
    assert sfm.ship_status == "blocked-pending-counsel" and not sfm.internal_eval
    assert select_sfm("mapanything", internal_eval=True).internal_eval


# --- A/B helpers: COLMAP reference IO + front-end metrics -------------------------------


def test_colmap_pose_round_trip_and_intrinsics():
    from reconstruction.mapanything_frontend import colmap_to_arkit_c2w, intrinsics_from_colmap

    for m in _orbit(4):
        q, t = colmap_pose(m)
        assert colmap_to_arkit_c2w(q, t) == pytest.approx(m, abs=1e-12)
    k = intrinsics_from_colmap(
        {"model": "SIMPLE_RADIAL", "width": 1600, "height": 900, "params": [1200, 800, 450, 0.01]}
    )
    assert (k.fx, k.fy, k.cx, k.cy, k.width) == (1200, 1200, 800, 450, 1600)
    k = intrinsics_from_colmap(
        {"model": "OPENCV", "width": 10, "height": 8, "params": [5, 6, 4, 3, 0, 0, 0, 0]}
    )
    assert (k.fx, k.fy) == (5, 6)
    with pytest.raises(ValueError):
        intrinsics_from_colmap(
            {"model": "OPENCV_FISHEYE", "width": 1, "height": 1, "params": [1] * 8}
        )


def test_read_colmap_images_bin_and_txt(tmp_path):
    import struct

    from reconstruction.prior_alignment import read_colmap_images

    recs = [
        ("a.jpg", 1, (1.0, 0.0, 0.0, 0.0), (0.1, 0.2, 0.3)),
        ("b.jpg", 2, (0.0, 1.0, 0.0, 0.0), (1, 2, 3)),
    ]
    b = tmp_path / "bin"
    b.mkdir()
    with (b / "images.bin").open("wb") as fh:
        fh.write(struct.pack("<Q", len(recs)))
        for i, (name, cid, q, t) in enumerate(recs, start=1):
            fh.write(struct.pack("<I7dI", i, *q, *t, cid) + name.encode() + b"\0")
            fh.write(struct.pack("<Q", 1) + struct.pack("<ddq", 1.0, 2.0, -1))
    t_dir = tmp_path / "txt"
    t_dir.mkdir()
    lines = ["# header"]
    for i, (name, cid, q, t) in enumerate(recs, start=1):
        lines += [f"{i} {' '.join(map(str, q))} {' '.join(map(str, t))} {cid} {name}", "1 2 -1"]
    (t_dir / "images.txt").write_text("\n".join(lines) + "\n")
    for d in (b, t_dir):
        got = read_colmap_images(d)
        assert set(got) == {"a.jpg", "b.jpg"}
        assert got["b.jpg"][0] == 2 and got["b.jpg"][1] == (0.0, 1.0, 0.0, 0.0)
        assert got["a.jpg"][2] == pytest.approx((0.1, 0.2, 0.3))


def test_frontend_metrics_pose_error_and_density():
    from reconstruction.feedforward_frontend import frontend_metrics, occupied_voxels

    ref = {f"f{i}": m for i, m in enumerate(_orbit(8))}
    sim = (3.0, _rot((0, 0, 1), 0.4), (1.0, 2.0, 3.0))
    pred = {}
    for name, m in ref.items():
        c = apply_sim3(sim, camera_center(m))
        pred[name] = (1, 0, 0, c[0], 0, 1, 0, c[1], 0, 0, 1, c[2], 0, 0, 0, 1)
    pred["extra"] = pred["f0"]
    ref_pts = [(0.1 * i, 0.0, 0.0) for i in range(40)]
    seed = [apply_sim3(sim, p) for p in ref_pts]
    out = frontend_metrics(pred, ref, seed, ref_pts)
    assert out["frames_shared"] == 8 and out["frames_pred"] == 9
    assert out["ate_rmse"] < 1e-9 and out["sim3_scale"] == pytest.approx(1 / 3)
    assert out["seed_occupied_voxels"] == out["ref_occupied_voxels"]
    assert occupied_voxels([(0, 0, 0), (0.05, 0, 0), (1.5, 0, 0)], 1.0) == 2
    assert "ate_rmse" not in frontend_metrics({"a": pred["f0"]}, ref, [], [])
