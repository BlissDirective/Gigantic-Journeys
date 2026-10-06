"""Feed-forward front-end: ARKit conditioning + the point-map -> COLMAP bridge."""

from reconstruction.arkit_poses import ArkitIntrinsics
from reconstruction.feedforward_frontend import (
    MockFeedForward,
    result_to_capture,
    write_frontend_model,
)

K = ArkitIntrinsics(fx=1000.0, fy=1000.0, cx=320.0, cy=240.0, width=640, height=480)
POSE0 = (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
POSE1 = (1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def test_arkit_conditioning_sets_metric_and_echoes_poses():
    m = MockFeedForward()
    res = m.reconstruct(["a.jpg", "b.jpg"], K, prior_poses=[POSE0, POSE1])
    assert res.metric is True and res.conditioned_on_arkit is True
    assert res.frames[1].cam_to_world == tuple(float(x) for x in POSE1)


def test_without_priors_is_not_metric():
    res = MockFeedForward().reconstruct(["a.jpg"], K)
    assert res.metric is False and res.conditioned_on_arkit is False
    assert len(res.frames) == 1


def test_confidence_floor_filters_seed_points():
    res = MockFeedForward().reconstruct(["a.jpg"], K, prior_poses=[POSE0])
    # mock emits 3 points with confidences 0.92, 0.80, 0.25
    assert len(result_to_capture(res).points) == 3
    assert len(result_to_capture(res, confidence_floor=0.5).points) == 2


def test_bridge_writes_colmap_model(tmp_path):
    res = MockFeedForward().reconstruct(["a.jpg", "b.jpg"], K, prior_poses=[POSE0, POSE1])
    kept = write_frontend_model(res, tmp_path / "m", confidence_floor=0.5)
    assert kept == 2
    for f in ("cameras.txt", "images.txt", "points3D.txt"):
        assert (tmp_path / "m" / f).exists()
    assert "a.jpg" in (tmp_path / "m" / "images.txt").read_text()
