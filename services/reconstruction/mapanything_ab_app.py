"""Item-6 A/B: MapAnything (Apache) front-end vs the existing COLMAP+GLOMAP models (M1-PIPE-03).

A **separate** Modal app (``gj-mapanything-ab``) so its image -- torch + map-anything + the
4.9 GB checkpoint -- is never built by, and can never break, ``modal_app.py`` runs (the
bedroom reshoot). Phase 1 of qa/evidence/M1-PIPE-03/item6-mapanything-ab-plan.json:
front-end only, no training. Per corpus room it runs ``FeedForwardSfM`` +
``MapAnythingReconstructor`` on the room's extracted frames, compares against the room's
GLOMAP model already on the gj-corpus volume, and records:

* pose error -- Sim(3)-aligned ATE vs the GLOMAP cameras (absolute + / camera extent),
* registration -- frames posed (MapAnything poses every input frame) vs GLOMAP registered,
* init density -- seed points kept + occupied E/60 voxels vs the GLOMAP sparse cloud,
* wall-clock -- front-end seconds (+ model load) vs the GLOMAP run's ``sfm`` stage time.

Arms: ``unconditioned`` (images + GLOMAP intrinsics) and ``pose-conditioned`` (GLOMAP poses
as the stand-in for ARKit metric poses -- corpus video has no ARKit track).

Licence: MapAnything is **counsel-pending (AUTH #049)** -> ``internal_eval=True``; every
model/point artifact is deleted in ``finally`` (AUTH #047); only metrics JSON is kept.
GPU spend: refused unless ``--gpu-go`` (no Modal GPU in October without an Owner go-ahead).

    modal run services/reconstruction/mapanything_ab_app.py            # prints the estimate
    modal run services/reconstruction/mapanything_ab_app.py --gpu-go   # spends (~$0.9)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import modal

_HERE = Path(__file__).resolve().parent
MAPANYTHING_CODE_COMMIT = "3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9"  # == mapanything_frontend
MAPANYTHING_REVISION = "00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a"
GPU = "L40S"
GPU_RATE_PER_HOUR_USD = 1.95  # Modal L40S GPU-only; CPU + memory add ~15%
CPU_CORES = 8.0
MEMORY_MIB = 32768
TIMEOUT_S = 1800
CORPUS_MOUNT = "/corpus"
CORPUS_RECON_ROOT = "open-video-recon"
CLIP_ID_RE = r"^(rooms|tabletop)/[a-z0-9][a-z0-9-]*$"  # same as modal_app.CLIP_ID_RE
AB_CLIPS = (
    "rooms/medieval-great-hall-winchester",
    "rooms/historic-house-eldon-house",
    "rooms/mosque-prayer-hall-umayyad",
    "rooms/lego-paranal-observatory",
)
ARMS = ("unconditioned", "pose-conditioned")
# ~6 min L40S per room x arm (image pull, checkpoint load ~1-2 min, ~150-200 views).
EST_MINUTES_PER_ARM = 6.0

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.5.1", "torchvision==0.20.1", index_url="https://download.pytorch.org/whl/cu124"
    )
    .pip_install(f"git+https://github.com/facebookresearch/map-anything@{MAPANYTHING_CODE_COMMIT}")
    # Bake the pinned Apache checkpoint (+ its DINOv2 torch-hub encoder) into the image.
    .run_commands(
        'python -c "from mapanything.models import MapAnything; MapAnything.from_pretrained('
        f"'facebook/map-anything-apache', revision='{MAPANYTHING_REVISION}')\""
    )
    .env({"PYTHONPATH": "/work"})
    .workdir("/work")
    .add_local_dir(
        _HERE / "reconstruction", "/work/reconstruction", ignore=["**/__pycache__", "**/*.pyc"]
    )
)
app = modal.App("gj-mapanything-ab", image=image)
corpus_volume = modal.Volume.from_name("gj-corpus")


def _check_clip_id(clip_id: str) -> str:
    if not re.match(CLIP_ID_RE, clip_id):
        raise ValueError(f"not a corpus clip id: {clip_id!r}")
    return clip_id.split("/", 1)[1]


def _read_points3d_bin(path: Path) -> list[tuple[float, float, float]]:
    import struct

    pts = []
    with path.open("rb") as fh:
        (n,) = struct.unpack("<Q", fh.read(8))
        for _ in range(n):
            _pid, x, y, z = struct.unpack("<Q3d", fh.read(32))
            fh.read(3 + 8)  # rgb, error
            (track,) = struct.unpack("<Q", fh.read(8))
            fh.seek(8 * track, 1)
            pts.append((x, y, z))
    return pts


def _read_points3d_txt(path: Path) -> list[tuple[float, float, float]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line[:1] != "#" and line.strip():
            f = line.split()
            out.append((float(f[1]), float(f[2]), float(f[3])))
    return out


def estimate_usd(clips: int, arms: int) -> float:
    return round(clips * arms * EST_MINUTES_PER_ARM / 60 * GPU_RATE_PER_HOUR_USD * 1.15, 2)


@app.function(
    gpu=GPU,
    cpu=(CPU_CORES, CPU_CORES),
    memory=MEMORY_MIB,
    timeout=TIMEOUT_S,
    volumes={CORPUS_MOUNT: corpus_volume},
)
def frontend_ab(clip_id: str, arm: str) -> dict:
    """Phase-1 metrics for one corpus room x arm; metrics JSON only survives (AUTH #047)."""
    import shutil
    import tempfile
    import time

    import torch
    from reconstruction import ArkitCapture, ArkitFrame, FeedForwardSfM, ScanInput, Source
    from reconstruction.feedforward_frontend import frontend_metrics
    from reconstruction.mapanything_frontend import (
        MAPPER_NAME,
        SHIP_STATUS,
        MapAnythingReconstructor,
        colmap_to_arkit_c2w,
        intrinsics_from_colmap,
    )
    from reconstruction.prior_alignment import (
        find_model_dir,
        read_colmap_cameras,
        read_colmap_images,
    )

    slug = _check_clip_id(clip_id)
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    corpus_volume.reload()
    src = Path(CORPUS_MOUNT) / CORPUS_RECON_ROOT / slug
    ref_model = find_model_dir(src / "sparse")
    if ref_model is None:
        raise FileNotFoundError(f"no GLOMAP reference model under {src / 'sparse'}")
    cams, ims = read_colmap_cameras(ref_model), read_colmap_images(ref_model)
    k = intrinsics_from_colmap(cams[next(iter(ims.values()))[0]])
    ref_c2w = {n: colmap_to_arkit_c2w(q, t) for n, (_c, q, t) in ims.items()}
    pts_bin, pts_txt = ref_model / "points3D.bin", ref_model / "points3D.txt"
    ref_pts = _read_points3d_bin(pts_bin) if pts_bin.exists() else _read_points3d_txt(pts_txt)
    baseline: dict = {}
    if (src / "run.json").exists():
        run = json.loads((src / "run.json").read_text(encoding="utf-8"))
        baseline = {
            "registered_images": run.get("registered_images"),
            "frames_used": run.get("frames_used"),
            "stage_s": (run.get("pipeline") or {}).get("stage_s"),
        }
    record: dict = {"clip_id": clip_id, "arm": arm, "gpu": GPU, "baseline": baseline}
    work = Path(tempfile.mkdtemp())
    started = time.monotonic()
    try:
        shutil.copytree(src / "frames", work / "images")
        count = sum(1 for p in (work / "images").iterdir() if p.is_file())
        capture = None
        if arm == "pose-conditioned":
            capture = ArkitCapture(frames=[ArkitFrame(n, k, ref_c2w[n]) for n in sorted(ref_c2w)])
        rec_holder: dict = {}

        def make(image_dir: Path) -> MapAnythingReconstructor:
            rec_holder["r"] = MapAnythingReconstructor(image_dir)
            return rec_holder["r"]

        sfm = FeedForwardSfM(
            make,
            mapper_name=MAPPER_NAME,
            ship_status=SHIP_STATUS,
            internal_eval=True,
            intrinsics=k,
            capture=capture,
        )
        poses = sfm.run(ScanInput(slug, work / "images", count, Source.CORPUS), work / "out")
        pred_ims = read_colmap_images(poses.sparse_dir)
        pred_c2w = {n: colmap_to_arkit_c2w(q, t) for n, (_c, q, t) in pred_ims.items()}
        seed = _read_points3d_txt(poses.sparse_dir / "points3D.txt")
        record.update(
            status="ok",
            frames_input=count,
            stats=poses.stats,
            diagnostics=rec_holder["r"].diagnostics,
            metrics=frontend_metrics(pred_c2w, ref_c2w, seed, ref_pts),
            gpu_peak_gib=round(torch.cuda.max_memory_allocated() / 2**30, 2),
        )
    except Exception as exc:  # noqa: BLE001 - record why, keep the batch going
        record.update(status="failed", error=repr(exc))
    finally:
        shutil.rmtree(work, ignore_errors=True)  # AUTH #047: internal-eval artifacts deleted
    wall = time.monotonic() - started
    record.update(wall_s=round(wall, 1), gpu_usd=round(wall / 3600 * GPU_RATE_PER_HOUR_USD, 4))
    out = src / "mapanything-ab"
    out.mkdir(exist_ok=True)
    (out / f"{arm}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    corpus_volume.commit()
    return record


@app.local_entrypoint()
def main(clips: str = ",".join(AB_CLIPS), arms: str = ",".join(ARMS), gpu_go: bool = False) -> None:
    clip_list = [c for c in clips.split(",") if c]
    arm_list = [a for a in arms.split(",") if a]
    for c in clip_list:
        _check_clip_id(c)
    print(
        f"estimate: {len(clip_list)} rooms x {len(arm_list)} arms"
        f" ~= ${estimate_usd(len(clip_list), len(arm_list))}"
    )
    if not gpu_go:
        print("refusing to spend: no Modal GPU without an explicit Owner go-ahead (--gpu-go)")
        return
    jobs = [(c, a) for c in clip_list for a in arm_list]
    for record in frontend_ab.starmap(jobs):
        print(
            json.dumps(
                {k: record.get(k) for k in ("clip_id", "arm", "status", "wall_s", "metrics")}
            )
        )
