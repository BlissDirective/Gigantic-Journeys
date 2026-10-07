"""Prior maps follow nerfstudio 1.1.5's undistort + ROI crop (M1-PIPE-03 depth check)."""

import struct

import pytest
from reconstruction.prior_alignment import (
    align_map_to_nerfstudio,
    find_model_dir,
    opencv_intrinsics,
    read_colmap_cameras,
)


def _write_cameras_bin(path, cams):
    with path.open("wb") as fh:
        fh.write(struct.pack("<Q", len(cams)))
        for cid, mid, w, h, params in cams:
            fh.write(struct.pack("<iiQQ", cid, mid, w, h))
            fh.write(struct.pack(f"<{len(params)}d", *params))


def test_reads_binary_and_text_cameras(tmp_path):
    (tmp_path / "0").mkdir()
    _write_cameras_bin(
        tmp_path / "0" / "cameras.bin", [(1, 2, 1600, 900, (1241.6, 800, 450, 0.0049))]
    )
    model = find_model_dir(tmp_path)
    assert model == tmp_path / "0"
    cam = read_colmap_cameras(model)[1]
    assert cam["model"] == "SIMPLE_RADIAL" and (cam["width"], cam["height"]) == (1600, 900)
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "cameras.txt").write_text("# c\n3 PINHOLE 640 480 500 501 320 240\n")
    assert read_colmap_cameras(tmp_path / "t")[3]["params"] == [500, 501, 320, 240]


def test_intrinsics_mapping_matches_nerfstudio():
    simple = {"model": "SIMPLE_RADIAL", "params": [1000.0, 450.0, 800.0, 0.03]}
    assert opencv_intrinsics(simple) == ([1000.0, 1000.0, 450.0, 800.0], [0.03, 0.0, 0.0, 0.0, 0.0])
    opencv = {"model": "OPENCV", "params": [10.0, 11.0, 5.0, 6.0, 0.1, 0.2, 0.01, 0.02]}
    assert opencv_intrinsics(opencv) == ([10.0, 11.0, 5.0, 6.0], [0.1, 0.2, 0.01, 0.02, 0.0])
    assert opencv_intrinsics({"model": "PINHOLE", "params": [1, 1, 0, 0]}) is None
    assert opencv_intrinsics({"model": "SIMPLE_RADIAL", "params": [1, 0, 0, 0.0]}) is None
    with pytest.raises(ValueError):
        opencv_intrinsics({"model": "OPENCV_FISHEYE", "params": [1] * 8})


def test_aligned_map_matches_nerfstudio_training_image():
    """Warping a half-res raw map == nerfstudio's undistorted + cropped full-res frame."""
    np = pytest.importorskip("numpy")
    cv2 = pytest.importorskip("cv2")
    w, h, f, cx, cy, k1 = 320, 180, 200.0, 160.0, 90.0, 0.15
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    raw = (np.sin(xs / 23) + np.cos(ys / 17) + xs / 100).astype(np.float32)
    # nerfstudio 1.1.5 _undistort_image, PERSPECTIVE branch, verbatim steps
    k_mat = np.array([[f, 0, cx - 0.5], [0, f, cy - 0.5], [0, 0, 1.0]])
    dist = np.array([k1, 0, 0, 0, 0, 0, 0, 0], dtype=float)
    new_k, (rx, ry, rw, rh) = cv2.getOptimalNewCameraMatrix(k_mat, dist, (w, h), 0)
    train = cv2.undistort(raw, k_mat, dist, None, new_k)[ry : ry + rh, rx : rx + rw]
    cam = {"model": "SIMPLE_RADIAL", "width": w, "height": h, "params": [f, cx, cy, k1]}
    half = cv2.resize(raw, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    aligned = align_map_to_nerfstudio(half, cam)
    assert abs(aligned.shape[1] - rw / 2) <= 1 and abs(aligned.shape[0] - rh / 2) <= 1
    ref = cv2.resize(train, aligned.shape[::-1], interpolation=cv2.INTER_AREA)
    naive = cv2.resize(half, aligned.shape[::-1], interpolation=cv2.INTER_LINEAR)
    inner = (slice(3, -3), slice(3, -3))
    err_aligned = float(np.abs(aligned - ref)[inner].mean())
    err_naive = float(np.abs(naive - ref)[inner].mean())
    assert err_aligned < err_naive / 4  # half-res: only resampling differences remain
    full = align_map_to_nerfstudio(raw, cam)  # full-res: same pixels as nerfstudio's frame
    assert full.shape == train.shape
    assert float(np.abs(full - train)[inner].mean()) < 1e-3
    pinhole = {"model": "PINHOLE", "width": w, "height": h, "params": [f, f, cx, cy]}
    assert align_map_to_nerfstudio(half, pinhole) is half
