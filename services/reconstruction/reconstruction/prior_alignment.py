"""Align a per-frame prior map with the image nerfstudio actually trains on (M1-PIPE-03).

nerfstudio 1.1.5 ``FullImageDatamanager`` undistorts every PERSPECTIVE frame whose COLMAP
camera has distortion (SIMPLE_RADIAL / RADIAL / OPENCV): principal point shifted by -0.5,
``cv2.getOptimalNewCameraMatrix(alpha=0)``, ``cv2.undistort`` and a crop to the ROI. A depth
prior computed on the raw frame and merely resized to the render is therefore off by the
distortion warp plus the crop (CPU check 2026-10-06: up to ~2 px on Winchester, ~5 px on the
bedroom). :func:`align_map_to_nerfstudio` applies the same transform to the map, at the
map's own resolution.

The COLMAP camera reader is standard library; the warp needs numpy + OpenCV (present in
the GPU image via nerfstudio). Fisheye models are refused (nerfstudio takes another path).
"""

from __future__ import annotations

import struct
from pathlib import Path

# COLMAP camera model id -> (name, parameter count)
CAMERA_MODELS = {
    0: ("SIMPLE_PINHOLE", 3),
    1: ("PINHOLE", 4),
    2: ("SIMPLE_RADIAL", 4),
    3: ("RADIAL", 5),
    4: ("OPENCV", 8),
    5: ("OPENCV_FISHEYE", 8),
    8: ("SIMPLE_RADIAL_FISHEYE", 4),
    9: ("RADIAL_FISHEYE", 5),
}


def read_colmap_cameras(model_dir: Path) -> dict[int, dict]:
    """``{camera_id: {model, width, height, params}}`` from ``cameras.bin`` or ``.txt``."""
    out: dict[int, dict] = {}
    binary, text = model_dir / "cameras.bin", model_dir / "cameras.txt"
    if binary.exists():
        with binary.open("rb") as fh:
            (n,) = struct.unpack("<Q", fh.read(8))
            for _ in range(n):
                cid, mid, w, h = struct.unpack("<iiQQ", fh.read(24))
                name, count = CAMERA_MODELS.get(mid, (f"MODEL_{mid}", 0))
                if not count:
                    raise ValueError(f"unsupported COLMAP camera model id {mid}")
                params = list(struct.unpack(f"<{count}d", fh.read(8 * count)))
                out[cid] = {"model": name, "width": w, "height": h, "params": params}
    elif text.exists():
        for line in text.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            cid, name, w, h, *params = line.split()
            out[int(cid)] = {
                "model": name,
                "width": int(w),
                "height": int(h),
                "params": [float(p) for p in params],
            }
    return out


def find_model_dir(sparse: Path) -> Path | None:
    """``sparse`` itself or its largest numbered sub-model, whichever holds cameras."""
    for d in [sparse, *sorted(p for p in sparse.glob("*") if p.is_dir())]:
        if (d / "cameras.bin").exists() or (d / "cameras.txt").exists():
            return d
    return None


def opencv_intrinsics(camera: dict) -> tuple[list[float], list[float]] | None:
    """``([fx, fy, cx, cy], [k1, k2, p1, p2, k3])`` for a distorted PERSPECTIVE camera.

    ``None`` when the camera has no distortion (nerfstudio leaves those frames untouched).
    Same mapping as nerfstudio's colmap_utils + _undistort_image reorder.
    """
    m, p = camera["model"], camera["params"]
    if m in ("SIMPLE_PINHOLE", "PINHOLE"):
        return None
    if m == "SIMPLE_RADIAL":
        k = [p[0], p[0], p[1], p[2]], [p[3], 0.0, 0.0, 0.0, 0.0]
    elif m == "RADIAL":
        k = [p[0], p[0], p[1], p[2]], [p[3], p[4], 0.0, 0.0, 0.0]
    elif m == "OPENCV":
        k = [p[0], p[1], p[2], p[3]], [p[4], p[5], p[6], p[7], 0.0]
    else:
        raise ValueError(f"prior alignment does not support {m} (fisheye path)")
    return None if not any(k[1]) else k


def align_map_to_nerfstudio(prior_map, camera: dict):
    """Warp + crop a raw-frame map (any resolution, same aspect) like nerfstudio's image.

    Returns a float32 map covering exactly the undistorted ROI the trainer renders, at the
    input map's scale. Maps of undistorted cameras are returned unchanged.
    """
    import cv2
    import numpy as np

    intr = opencv_intrinsics(camera)
    if intr is None:
        return prior_map
    (fx, fy, cx, cy), (k1, k2, p1, p2, k3) = intr
    big_w, big_h = int(camera["width"]), int(camera["height"])
    k_mat = np.array([[fx, 0, cx - 0.5], [0, fy, cy - 0.5], [0, 0, 1.0]])
    dist = np.array([k1, k2, p1, p2, k3, 0, 0, 0], dtype=float)
    new_k, (rx, ry, rw, rh) = cv2.getOptimalNewCameraMatrix(k_mat, dist, (big_w, big_h), 0)
    m = np.asarray(prior_map, dtype=np.float32)
    sx, sy = m.shape[1] / big_w, m.shape[0] / big_h
    out_w, out_h = max(1, round(rw * sx)), max(1, round(rh * sy))
    oy, ox = np.mgrid[0:out_h, 0:out_w].astype(np.float64)
    # output pixel centre -> undistorted full-res pixel (OpenCV integer-centre convention)
    ux = (ox + 0.5) / sx - 0.5 + rx
    uy = (oy + 0.5) / sy - 0.5 + ry
    x = (ux - new_k[0, 2]) / new_k[0, 0]
    y = (uy - new_k[1, 2]) / new_k[1, 1]
    r2 = x * x + y * y
    radial = 1 + k1 * r2 + k2 * r2 * r2 + k3 * r2**3
    xd = x * radial + 2 * p1 * x * y + p2 * (r2 + 2 * x * x)
    yd = y * radial + p1 * (r2 + 2 * y * y) + 2 * p2 * x * y
    raw_x = xd * fx + (cx - 0.5)
    raw_y = yd * fy + (cy - 0.5)
    map_x = ((raw_x + 0.5) * sx - 0.5).astype(np.float32)
    map_y = ((raw_y + 0.5) * sy - 0.5).astype(np.float32)
    return cv2.remap(m, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
