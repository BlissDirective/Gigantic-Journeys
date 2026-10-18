"""In-pod job: bedroom cleanup stage 2 (M1-PIPE-02, AUTH #051) on Runpod Secure Cloud.

Runs INSIDE a pod prepared by ``runpod_setup.sh`` and driven by ``runpod_bedroom.py``.
Retrains the Owner's bedroom capture (``room-01``, AUTH #046) from its **faces-blurred**
frames and the saved SfM model, so the poses, world frame and held-out views (every 8th
frame) match the shipped package, with the shipping recipe (``quality-30k``,
antialiased, default densify, 400K growth cap) plus items 4+5: BAD-Gaussians deblur
(``--deblur-samples``) and Splatfacto-W appearance (``--appearance splatfacto-w``).

A short smoke run (``--smoke-steps``) goes first: it must finish, export a PLY and show
the deblur/appearance hook applied on training steps; otherwise the full run is not
started. The smoke's step time also projects the full run against ``--deadline``.

Outputs (the only things the launcher copies back): ``results.json`` (metrics only) and
``splat.ply`` (the 400K phone splat). Every other file, including the held-out renders,
stays on the pod's container disk and is deleted with ``--wipe`` before the pod ends.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import time
import traceback
from pathlib import Path

CAPTURE_ID = "room-01"
# Splatfacto's (nerfstudio 1.1.5) default densify gradient threshold. With N deblur
# sub-frames the RGB is the mean of N renders and densify statistics come from the
# mid-exposure render only, so its screen-space gradients are ~1/N of a sharp render's:
# the threshold is divided by N to keep the baseline's densification (and 400K cap use).
SPLATFACTO_DENSIFY_GRAD = 0.0008


def recipe_args(deblur_samples: int) -> tuple[str, ...]:
    from reconstruction.trainer import QUALITY_ARGS

    if deblur_samples <= 1:
        return QUALITY_ARGS
    thresh = f"{SPLATFACTO_DENSIFY_GRAD / deblur_samples:.6g}"
    return (*QUALITY_ARGS, "--pipeline.model.densify-grad-thresh", thresh)


def train_arm(
    frames: Path,
    sparse: Path,
    work: Path,
    profile,
    budget: int,
    deblur: int,
    appearance: str,
    evaluate: bool,
) -> tuple[dict, Path]:
    from reconstruction import CameraPoses, GsplatTrainer, ReconstructionConfig

    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(frames, work / "images")
    shutil.copytree(sparse, work / "out" / "sparse")
    count = sum(1 for p in (work / "images").iterdir() if p.is_file())
    poses = CameraPoses(CAPTURE_ID, work / "out" / "sparse", count, image_dir=work / "images")
    config = ReconstructionConfig(
        splat_budget=budget,
        rasterize_mode="antialiased",
        densify_strategy="default",
        deblur_samples=deblur,
        appearance=appearance,
    )
    model = GsplatTrainer(profile=profile, evaluate=evaluate).train(poses, work / "out", config)
    return {"images": count, "splat_count": model.splat_count, **model.metrics}, model.ply_path


def smoke_ok(rec: dict) -> tuple[bool, str]:
    da = (rec.get("growth") or {}).get("deblur_appearance") or {}
    if rec.get("splat_count", 0) <= 0:
        return False, "no splats exported"
    if da.get("applied_steps", 0) <= 0:
        return False, f"deblur/appearance hook never applied: {da}"
    return True, f"applied_steps={da['applied_steps']}"


def main(argv: list[str] | None = None) -> int:
    from reconstruction.trainer import TrainProfile

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--frames", type=Path, required=True)
    p.add_argument("--sparse", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True, help="results JSON")
    p.add_argument("--ply-out", type=Path, required=True)
    p.add_argument("--work", type=Path, default=Path("/root/gj-work"))
    p.add_argument("--rate", type=float, required=True)
    p.add_argument("--budget", type=int, default=400_000)
    p.add_argument("--deblur-samples", type=int, default=5)
    p.add_argument("--appearance", default="splatfacto-w")
    p.add_argument("--smoke-steps", type=int, default=300)
    p.add_argument("--deadline", type=float, default=0.0, help="epoch s the full run must end by")
    args = p.parse_args(argv)
    res: dict = {
        "capture_id": CAPTURE_ID,
        "auth": "AUTH #051 (Runpod Secure) + #046 + #045",
        "rate_per_hour_usd": args.rate,
        "recipe": {
            "profile": "quality-30k",
            "rasterize_mode": "antialiased",
            "densify_strategy": "default",
            "budget": args.budget,
            "deblur_samples": args.deblur_samples,
            "appearance": args.appearance,
        },
    }

    def save() -> None:
        args.out.write_text(json.dumps(res, indent=2) + "\n")

    t0 = time.monotonic()
    try:
        extra = recipe_args(args.deblur_samples)
        res["recipe"]["ns_train_extra"] = list(extra)
        smoke_profile = TrainProfile.scaled(args.smoke_steps, "smoke", *extra)
        rec, _ = train_arm(
            args.frames,
            args.sparse,
            args.work / "smoke",
            smoke_profile,
            args.budget,
            args.deblur_samples,
            args.appearance,
            evaluate=False,
        )
        ok, why = smoke_ok(rec)
        res["smoke"] = {"ok": ok, "why": why, "wall_s": round(time.monotonic() - t0, 1), **rec}
        save()
        shutil.rmtree(args.work / "smoke", ignore_errors=True)
        if not ok:
            res["status"] = "smoke failed"
            save()
            return 2
        full = TrainProfile.scaled(30_000, "quality-30k-deblur-appearance", *extra)
        # train_s includes ~1-2 min of nerfstudio start-up (dataset load + image cache)
        per_step = max(rec["train_s"] - 90, 0.3 * rec["train_s"]) / max(args.smoke_steps, 1)
        projected = per_step * full.iterations * 1.1 + 600  # + finish / eval / export
        res["projected_full_s"] = round(projected)
        if args.deadline and time.time() + projected > args.deadline:
            res["status"] = "skipped: projected full run passes the pod deadline"
            save()
            return 3
        t1 = time.monotonic()
        rec, ply = train_arm(
            args.frames,
            args.sparse,
            args.work / "full",
            full,
            args.budget,
            args.deblur_samples,
            args.appearance,
            evaluate=True,
        )
        res["full"] = {"wall_s": round(time.monotonic() - t1, 1), **rec}
        for k in ("psnr", "ssim", "lpips"):
            v = rec.get(k)
            if v is None or not math.isfinite(float(v)):
                raise RuntimeError(f"full run has no finite {k}: {v}")
        shutil.copyfile(ply, args.ply_out)
        res["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 - record and report
        res["status"] = "fail"
        res["error"] = f"{type(exc).__name__}: {exc}"[:800]
        res["traceback"] = traceback.format_exc()[-2500:]
    res["job_s"] = round(time.monotonic() - t0, 1)
    res["job_usd"] = round(res["job_s"] / 3600 * args.rate, 4)
    save()
    return 0 if res["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
