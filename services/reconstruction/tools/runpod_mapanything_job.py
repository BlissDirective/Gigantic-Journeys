"""In-pod item-6 phase-1 job: MapAnything vs the GLOMAP reference, metrics only.

Runs INSIDE a pod prepared by ``runpod_mapanything_setup.sh`` (driven by
``runpod_mapanything.py``). Same logic as ``mapanything_ab_app.frontend_ab`` but on
local room dirs (``frames/`` + the GLOMAP ``sparse/`` + ``run.json`` of the corpus
recon). Corpus (open-licence) rooms only. Internal eval (AUTH #049, counsel-pending):
every artifact is deleted after scoring; only the metrics JSON leaves the pod (AUTH #047).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import time
import traceback
from pathlib import Path

CLIP_ID_RE = r"^(rooms|tabletop)/[a-z0-9][a-z0-9-]*$"
ARMS = ("unconditioned", "pose-conditioned")


def _read_points3d_bin(path: Path) -> list[tuple[float, float, float]]:
    import struct

    out = []
    with path.open("rb") as f:
        (n,) = struct.unpack("<Q", f.read(8))
        for _ in range(n):
            _pid, x, y, z = struct.unpack("<Qddd", f.read(32))
            f.read(3 + 8)  # rgb + error
            (track,) = struct.unpack("<Q", f.read(8))
            f.read(8 * track)
            out.append((x, y, z))
    return out


def _read_points3d_txt(path: Path) -> list[tuple[float, float, float]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            p = line.split()
            out.append((float(p[1]), float(p[2]), float(p[3])))
    return out


def baseline_from_run(run: dict) -> dict:
    pipe = run.get("pipeline") or {}
    return {
        "registered_images": run.get("registered_images"),
        "frames_used": run.get("frames_used"),
        "sfm_stage_s": (pipe.get("stage_seconds") or {}).get("sfm"),
        "sfm_gpu": run.get("gpu"),
        "sfm_config": run.get("config"),
    }


def run_arm(clip_id: str, room: Path, arm: str, rate: float) -> dict:
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

    if not re.match(CLIP_ID_RE, clip_id) or arm not in ARMS:
        raise ValueError(f"bad job {clip_id!r} / {arm!r}")
    slug = clip_id.split("/", 1)[1]
    ref_model = find_model_dir(room / "sparse")
    if ref_model is None:
        raise FileNotFoundError(f"no GLOMAP reference model under {room / 'sparse'}")
    cams, ims = read_colmap_cameras(ref_model), read_colmap_images(ref_model)
    k = intrinsics_from_colmap(cams[next(iter(ims.values()))[0]])
    ref_c2w = {n: colmap_to_arkit_c2w(q, t) for n, (_c, q, t) in ims.items()}
    pts_bin = ref_model / "points3D.bin"
    ref_pts = (
        _read_points3d_bin(pts_bin)
        if pts_bin.exists()
        else _read_points3d_txt(ref_model / "points3D.txt")
    )
    run = json.loads((room / "run.json").read_text(encoding="utf-8"))
    record: dict = {"clip_id": clip_id, "arm": arm, "baseline": baseline_from_run(run)}
    torch.cuda.reset_peak_memory_stats()
    work = Path(tempfile.mkdtemp())
    started = time.monotonic()
    try:
        shutil.copytree(room / "frames", work / "images")
        count = sum(1 for p in (work / "images").iterdir() if p.is_file())
        capture = None
        if arm == "pose-conditioned":
            capture = ArkitCapture(frames=[ArkitFrame(n, k, ref_c2w[n]) for n in sorted(ref_c2w)])
        holder: dict = {}

        def make(image_dir: Path) -> MapAnythingReconstructor:
            holder["r"] = MapAnythingReconstructor(image_dir)
            return holder["r"]

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
            diagnostics=holder["r"].diagnostics,
            metrics=frontend_metrics(pred_c2w, ref_c2w, seed, ref_pts),
            gpu_peak_gib=round(torch.cuda.max_memory_allocated() / 2**30, 2),
        )
    except Exception as exc:  # noqa: BLE001 - record why, keep the batch going
        record.update(status="failed", error=repr(exc)[:500], tb=traceback.format_exc()[-1500:])
    finally:
        shutil.rmtree(work, ignore_errors=True)  # AUTH #047: internal-eval artifacts deleted
    wall = time.monotonic() - started
    record.update(wall_s=round(wall, 1), usd=round(wall / 3600 * rate, 4))
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--room", action="append", default=[], help="<clip id>=<room dir>")
    parser.add_argument("--deadline", type=float, default=0.0)
    args = parser.parse_args(argv)
    out = Path(args.out)
    results: dict = {"rate_per_hour_usd": args.rate, "runs": []}
    for spec in args.room:
        clip_id, room = spec.split("=", 1)
        for arm in ARMS:
            if args.deadline and time.time() > args.deadline:
                results["runs"].append({"clip_id": clip_id, "arm": arm, "status": "skipped"})
            else:
                results["runs"].append(run_arm(clip_id, Path(room), arm, args.rate))
            out.write_text(json.dumps(results, indent=2) + "\n")
            r = results["runs"][-1]
            print(json.dumps({k: r.get(k) for k in ("clip_id", "arm", "status", "wall_s")}))
    # Rooms (frames + GLOMAP reference) are deleted too; only metrics leave the pod.
    for spec in args.room:
        shutil.rmtree(spec.split("=", 1)[1], ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
