"""MapAnything (Apache-2.0 variant) as a feed-forward front-end -- default OFF, counsel-pending.

capture-render-quality-v1 item 6. ``MapAnythingReconstructor`` implements the
``feedforward_frontend.FeedForwardReconstructor`` port with Meta's MapAnything, conditioned
on ARKit intrinsics + metric cam->world poses (``is_metric_scale``) so the point map lands
at true scale; ``FeedForwardSfM`` turns its output into the COLMAP model Splatfacto
initialises from. Selected with ``ReconstructionConfig.sfm == "mapanything"`` /
``select_sfm("mapanything", internal_eval=True)``; the default stays COLMAP.

Licence gate (AUTH #049, qa/evidence/M1-PIPE-03/item6-mapanything-licence.json):

* Only ``facebook/map-anything-apache`` at a pinned Hub revision is accepted. The
  CC-BY-NC-4.0 variants (``facebook/map-anything``, ``facebook/map-anything-v1``) are
  refused by ``check_model_id`` -- never loaded, never used, not even for evaluation.
* Even the Apache weights are **blocked pending counsel**: the Apache variant's training
  mix includes ScanNet++ v2 (TUM terms of use: non-commercial research only) and Mapillary
  MPSD (dataset terms unverified). Until counsel clears it, ``SHIP_STATUS`` keeps the SfM
  internal-eval only, and any artifact it produced must be deleted after scoring (#047).

Everything model-related is imported lazily (torch / numpy / PIL / ``mapanything``, all
only in the GPU image); the result assembly below is standard library and CI-tested.
"""

from __future__ import annotations

import math
from pathlib import Path

from .arkit_poses import ArkitIntrinsics
from .feedforward_frontend import (
    FeedForwardResult,
    FeedForwardSfM,
    FFFrame,
    FFPoint,
    Vec3,
    apply_sim3,
    camera_center,
    sim3_align,
)
from .licenses import LicenseError

MAPANYTHING_MODEL_ID = "facebook/map-anything-apache"
# HF Hub commit of facebook/map-anything-apache (license: apache-2.0, 2026-02-04).
MAPANYTHING_REVISION = "00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a"
# facebookresearch/map-anything code commit the adapter was written against (Apache-2.0).
MAPANYTHING_CODE_COMMIT = "3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9"
# CC-BY-NC-4.0 checkpoints: method-only under AUTH #049 -- never load them.
REFUSED_MODEL_IDS = frozenset({"facebook/map-anything", "facebook/map-anything-v1"})
# "cleared" only after counsel confirms the Apache variant's training-data basis.
SHIP_STATUS = "blocked-pending-counsel"
MAPPER_NAME = "mapanything"
DEFAULT_MAX_SEED_POINTS = 300_000


def check_model_id(model_id: str, revision: str = MAPANYTHING_REVISION) -> str:
    """Accept only the pinned Apache-2.0 checkpoint; refuse everything else (AUTH #049)."""
    if model_id in REFUSED_MODEL_IDS:
        raise LicenseError(f"{model_id} is CC-BY-NC-4.0 (AUTH #049): never used")
    if model_id != MAPANYTHING_MODEL_ID:
        raise LicenseError(f"{model_id!r} is not the reviewed checkpoint {MAPANYTHING_MODEL_ID}")
    if revision != MAPANYTHING_REVISION:
        raise LicenseError(f"revision {revision!r} is not the reviewed {MAPANYTHING_REVISION}")
    return model_id


def flip_camera_axes(c2w: tuple[float, ...]) -> tuple[float, ...]:
    """ARKit/OpenGL cam->world <-> OpenCV cam->world (negate camera y, z axes; an involution)."""
    if len(c2w) != 16:
        raise ValueError("cam_to_world must be a row-major 4x4 (16 floats)")
    return tuple(
        -float(c2w[r * 4 + c]) if r < 3 and c in (1, 2) else float(c2w[r * 4 + c])
        for r in range(4)
        for c in range(4)
    )


def colmap_to_arkit_c2w(qvec: tuple, tvec: tuple) -> tuple[float, ...]:
    """COLMAP world->camera (qw, qx, qy, qz), t -> ARKit-convention cam->world (row-major 16)."""
    w, x, y, z = qvec
    r = (
        (1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)),
        (2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)),
        (2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)),
    )
    rt = tuple(tuple(r[j][i] for j in range(3)) for i in range(3))  # cam->world rotation
    c = tuple(-sum(rt[i][j] * tvec[j] for j in range(3)) for i in range(3))
    cv = (*rt[0], c[0], *rt[1], c[1], *rt[2], c[2], 0.0, 0.0, 0.0, 1.0)
    return flip_camera_axes(cv)


def intrinsics_from_colmap(camera: dict) -> ArkitIntrinsics:
    """Pinhole part of a COLMAP camera (distortion ignored: the front-end takes pinhole K)."""
    m, p = camera["model"], camera["params"]
    if m in ("SIMPLE_PINHOLE", "SIMPLE_RADIAL", "RADIAL"):
        fx = fy = p[0]
        cx, cy = p[1], p[2]
    elif m in ("PINHOLE", "OPENCV"):
        fx, fy, cx, cy = p[:4]
    else:
        raise ValueError(f"unsupported camera model for the feed-forward front-end: {m}")
    return ArkitIntrinsics(fx, fy, cx, cy, int(camera["width"]), int(camera["height"]))


def rank_confidence(raw: list[float]) -> list[float]:
    """Map raw (unbounded) model confidences to their percentile rank in [0, 1]."""
    n = len(raw)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    order = sorted(range(n), key=raw.__getitem__)
    out = [0.0] * n
    for rank, i in enumerate(order):
        out[i] = rank / (n - 1)
    return out


def assemble_result(
    frame_names: list[str],
    intrinsics: ArkitIntrinsics,
    pred_c2w_opencv: list[tuple[float, ...]],
    points: list[tuple[Vec3, tuple[int, int, int], float]],
    *,
    prior_poses: list[tuple[float, ...]] | None = None,
    keep_prior_poses: bool = True,
) -> tuple[FeedForwardResult, dict]:
    """Build a ``FeedForwardResult`` (ARKit-convention poses) from flattened model output.

    ``points`` are (world xyz, rgb, raw confidence). With ARKit priors and
    ``keep_prior_poses``, the frames keep the ARKit metric poses and the point map is
    moved into the ARKit world by the Sim(3) fitted on camera centres (robust whichever
    world frame the model answered in). Returns the result and fit diagnostics.
    """
    if len(pred_c2w_opencv) != len(frame_names):
        raise ValueError("one predicted pose per frame expected")
    pred_arkit = [flip_camera_axes(m) for m in pred_c2w_opencv]
    diag: dict = {"aligned_to_prior": False}
    xyz = [p[0] for p in points]
    frame_poses = pred_arkit
    if prior_poses is not None:
        if len(prior_poses) != len(frame_names):
            raise ValueError("one prior pose per frame expected")
        pred_c = [camera_center(m) for m in pred_arkit]
        prior_c = [camera_center(m) for m in prior_poses]
        if len(frame_names) >= 3 and keep_prior_poses:
            sim = sim3_align(pred_c, prior_c)
            xyz = [apply_sim3(sim, p) for p in xyz]
            moved = [apply_sim3(sim, c) for c in pred_c]
            errs = [math.dist(a, b) for a, b in zip(moved, prior_c, strict=True)]
            diag.update(
                aligned_to_prior=True,
                sim3_scale=sim[0],
                prior_centre_rmse_m=math.sqrt(sum(e * e for e in errs) / len(errs)),
            )
        if keep_prior_poses:
            frame_poses = [tuple(float(x) for x in m) for m in prior_poses]
    conf = rank_confidence([p[2] for p in points])
    result = FeedForwardResult(
        frames=[
            FFFrame(n, intrinsics, pose) for n, pose in zip(frame_names, frame_poses, strict=True)
        ],
        points=[
            FFPoint(tuple(x), rgb, c)  # type: ignore[arg-type]
            for x, (_, rgb, _), c in zip(xyz, points, conf, strict=True)
        ],
        metric=prior_poses is not None,
        conditioned_on_arkit=prior_poses is not None,
    )
    return result, diag


class MapAnythingReconstructor:
    """``FeedForwardReconstructor`` backed by ``facebook/map-anything-apache`` (GPU image only)."""

    name = "mapanything-apache"

    def __init__(
        self,
        image_dir: Path,
        *,
        model_id: str = MAPANYTHING_MODEL_ID,
        revision: str = MAPANYTHING_REVISION,
        device: str | None = None,
        max_seed_points: int = DEFAULT_MAX_SEED_POINTS,
        keep_prior_poses: bool = True,
    ) -> None:
        self.model_id = check_model_id(model_id, revision)
        self.revision = revision
        self.image_dir = image_dir
        self.device = device
        self.max_seed_points = max_seed_points
        self.keep_prior_poses = keep_prior_poses
        self.diagnostics: dict = {}

    def reconstruct(
        self,
        frame_names: list[str],
        intrinsics: ArkitIntrinsics,
        *,
        prior_poses: list[tuple[float, ...]] | None = None,
    ) -> FeedForwardResult:
        import numpy as np
        import torch
        from mapanything.models import MapAnything
        from mapanything.utils.image import preprocess_inputs
        from PIL import Image

        device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        views = []
        for i, name in enumerate(frame_names):
            img = np.asarray(Image.open(self.image_dir / name).convert("RGB"))
            h, w = img.shape[:2]
            sx, sy = w / intrinsics.width, h / intrinsics.height  # frames may be downscaled
            k = np.array(
                [
                    [intrinsics.fx * sx, 0.0, intrinsics.cx * sx],
                    [0.0, intrinsics.fy * sy, intrinsics.cy * sy],
                    [0.0, 0.0, 1.0],
                ],
                dtype=np.float32,
            )
            view = {"img": torch.from_numpy(img.copy()), "intrinsics": torch.from_numpy(k)}
            if prior_poses is not None:
                c2w = np.array(flip_camera_axes(prior_poses[i]), dtype=np.float32).reshape(4, 4)
                view["camera_poses"] = torch.from_numpy(c2w)
                view["is_metric_scale"] = torch.tensor([True])
            views.append(view)
        model = MapAnything.from_pretrained(self.model_id, revision=self.revision).to(device)
        model.eval()
        with torch.no_grad():
            preds = model.infer(
                preprocess_inputs(views),
                memory_efficient_inference=True,
                use_amp=device == "cuda",
                amp_dtype="bf16",
                apply_mask=True,
                mask_edges=True,
            )
        poses, xyz, rgb, conf = [], [], [], []
        for pred in preds:
            poses.append(tuple(pred["camera_poses"][0].float().cpu().numpy().reshape(-1).tolist()))
            mask = pred["mask"][0].squeeze(-1).bool().cpu().numpy()
            xyz.append(pred["pts3d"][0].float().cpu().numpy()[mask])
            colours = pred["img_no_norm"][0].float().cpu().numpy()[mask]
            rgb.append(colours * 255.0 if colours.max(initial=0.0) <= 1.0 else colours)
            conf.append(pred["conf"][0].float().cpu().numpy()[mask])
        xyz_a, rgb_a, conf_a = np.concatenate(xyz), np.concatenate(rgb), np.concatenate(conf)
        if len(xyz_a) > self.max_seed_points:  # even stride keeps spatial coverage
            keep = np.linspace(0, len(xyz_a) - 1, self.max_seed_points).astype(np.int64)
            xyz_a, rgb_a, conf_a = xyz_a[keep], rgb_a[keep], conf_a[keep]
        rgb_a = np.clip(rgb_a, 0, 255).astype(np.uint8)
        points = [
            (tuple(map(float, p)), tuple(map(int, c)), float(s))
            for p, c, s in zip(xyz_a, rgb_a, conf_a, strict=True)
        ]
        result, self.diagnostics = assemble_result(
            frame_names,
            intrinsics,
            poses,
            points,  # type: ignore[arg-type]
            prior_poses=prior_poses,
            keep_prior_poses=self.keep_prior_poses,
        )
        self.diagnostics.update(device=device, model=self.model_id, revision=self.revision)
        return result


def mapanything_sfm(
    *,
    internal_eval: bool = False,
    confidence_floor: float = 0.1,
    intrinsics: ArkitIntrinsics | None = None,
    keep_prior_poses: bool = True,
) -> FeedForwardSfM:
    """The ``sfm="mapanything"`` adapter (internal-eval only while ``SHIP_STATUS`` is pending)."""
    return FeedForwardSfM(
        lambda image_dir: MapAnythingReconstructor(image_dir, keep_prior_poses=keep_prior_poses),
        mapper_name=MAPPER_NAME,
        ship_status=SHIP_STATUS,
        internal_eval=internal_eval,
        confidence_floor=confidence_floor,
        intrinsics=intrinsics,
    )
