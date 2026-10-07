"""Per-frame monocular depth-prior cache for training (capture-render-quality-v1 item 3).

Runs a ``depth_prior.DepthPrior`` (Depth Anything V2 **Small**, Apache-2.0, in the GPU
container) over a capture's frames and writes one map per frame for
``ns_train_capped.install_depth_normal``. The output is relative **disparity** (Depth
Anything's native output: larger = nearer); the trainer aligns it to the rendered / ARKit
reference with ``depth_prior``'s scale/shift contract before using it.

Licence gate (AUTH #049): only the Small checkpoint may be used. Base / Large / Giant are
CC-BY-NC and raise ``LicenseError`` -- they are method-only, never run in this pipeline.

Map format (stdlib, no numpy needed to write or test): ``<stem>.depth.f32`` = two uint32
(height, width) then height*width float32, little-endian. ``prior.json`` records the model,
licence, kind and frame list. Writing / reading the grid is standard library only; the
model adapter imports transformers / PIL lazily.
"""

from __future__ import annotations

import json
import struct
from array import array
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from .depth_prior import DepthPrior
from .licenses import LicenseError

SUFFIX = ".depth.f32"
# Commercial-safe checkpoints only (AUTH #049). Key = config value.
DEPTH_MODELS: dict[str, tuple[str, str]] = {
    "depth-anything-v2-small": ("depth-anything/Depth-Anything-V2-Small-hf", "Apache-2.0"),
}
# Hub revision baked into the image (Dockerfile "depth-prior" layer); keep the two in sync.
DEPTH_MODEL_REVISIONS = {"depth-anything-v2-small": "5426e4f0f36572d16453bbda7a8389317b1bef99"}
# CC-BY-NC weights (method-only, AUTH #049 boundary). Any of these names is refused.
NON_COMMERCIAL_DEPTH_MODELS = frozenset(
    {
        "depth-anything-v2-base",
        "depth-anything-v2-large",
        "depth-anything-v2-giant",
        "depth-anything/Depth-Anything-V2-Base-hf",
        "depth-anything/Depth-Anything-V2-Large-hf",
        "depth-anything/Depth-Anything-V2-Giant-hf",
    }
)


def model_repo(name: str) -> str:
    """Hub repo for a config model name; refuses non-commercial / unknown weights."""
    if name in NON_COMMERCIAL_DEPTH_MODELS or "large" in name.lower() or "giant" in name.lower():
        raise LicenseError(f"{name!r} is non-commercial (CC-BY-NC); method-only (AUTH #049)")
    if name not in DEPTH_MODELS:
        raise LicenseError(f"unknown depth model {name!r}; allowed: {sorted(DEPTH_MODELS)}")
    return DEPTH_MODELS[name][0]


def write_map(out_dir: Path, stem: str, grid) -> Path:
    """Write one map. ``grid`` = rows of floats (stdlib) or a 2-D numpy array (fast path)."""
    path = out_dir / f"{stem}{SUFFIX}"
    if hasattr(grid, "shape") and hasattr(grid, "astype"):  # numpy, no per-pixel Python
        if len(grid.shape) != 2:
            raise ValueError("map must be 2-D")
        h, w = (int(v) for v in grid.shape)
        with path.open("wb") as fh:
            fh.write(struct.pack("<II", h, w))
            fh.write(grid.astype("<f4").tobytes())
        return path
    h = len(grid)
    w = len(grid[0]) if h else 0
    data = array("f", (float(v) for row in grid for v in row))
    if len(data) != h * w:
        raise ValueError("grid must be rectangular")
    if data.itemsize != 4:
        raise RuntimeError("float32 array expected")
    with path.open("wb") as fh:
        fh.write(struct.pack("<II", h, w))
        if struct.pack("=I", 1) != struct.pack("<I", 1):
            data.byteswap()
        fh.write(data.tobytes())
    return path


def read_map_grid(directory: Path, stem: str) -> list[list[float]] | None:
    """Stdlib reader (tests / tools). ``None`` when the frame has no map."""
    path = directory / f"{stem}{SUFFIX}"
    if not path.exists():
        return None
    raw = path.read_bytes()
    h, w = struct.unpack("<II", raw[:8])
    data = array("f")
    data.frombytes(raw[8 : 8 + 4 * h * w])
    if struct.pack("=I", 1) != struct.pack("<I", 1):
        data.byteswap()
    return [list(data[i * w : (i + 1) * w]) for i in range(h)]


def read_map(directory: Path, stem: str):
    """numpy ``[H, W]`` float32 reader for the trainer (container). ``None`` if missing."""
    import numpy as np

    path = directory / f"{stem}{SUFFIX}"
    if not path.exists():
        return None
    h, w = struct.unpack("<II", path.read_bytes()[:8])
    return np.fromfile(path, dtype="<f4", offset=8, count=h * w).reshape(h, w)


def build_cache(
    images: Iterable[Path],
    out_dir: Path,
    prior: DepthPrior,
    load_image: Callable[[Path], Sequence[Sequence[float]]],
    *,
    model: str = "depth-anything-v2-small",
    align: Callable | None = None,
    aligned_to: str = "",
) -> dict:
    """Predict + write one map per image; return (and write) the ``prior.json`` manifest.

    ``align`` (e.g. ``prior_alignment.align_map_to_nerfstudio`` bound to the COLMAP camera)
    maps each raw-frame prediction onto the image the trainer actually renders.
    """
    model_repo(model)  # licence gate before any inference
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for path in sorted(images):
        pred = prior.predict(load_image(path))
        write_map(out_dir, path.stem, align(pred) if align else pred)
        frames.append(path.stem)
    manifest = {
        "model": model,
        "repo": DEPTH_MODELS[model][0],
        "license": DEPTH_MODELS[model][1],
        "prior": prior.name,
        "kind": "disparity",
        "aligned_to": aligned_to or ("custom" if align else "raw frame (no undistortion)"),
        "frames": frames,
    }
    (out_dir / "prior.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


class DepthAnythingV2Small:
    """``DepthPrior`` adapter for Depth Anything V2 Small (Apache-2.0) via transformers.

    GPU container only. ``predict`` takes a PIL image (``load_pil``) and returns relative
    disparity (numpy, model resolution).
    """

    name = "depth-anything-v2-small"

    def __init__(self, device: str = "cuda") -> None:
        from transformers import pipeline

        self._pipe = pipeline(
            "depth-estimation",
            model=model_repo(self.name),
            revision=DEPTH_MODEL_REVISIONS[self.name],
            device=device,
        )

    def predict(self, image):
        """Relative disparity at the model's native resolution (~518 px short side) as a
        float32 numpy array; the trainer resizes it to each render (bilinear)."""
        out = self._pipe(image)["predicted_depth"]
        return out.squeeze().float().cpu().numpy()


def load_pil(path: Path):
    from PIL import Image

    return Image.open(path).convert("RGB")
