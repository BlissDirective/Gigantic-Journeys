# `services/reconstruction/`

Area: CAPT · Pipeline code: **M1-CAPT-03** (Builder) · ADR-0005 / AUTH #030 (self-host committed + prioritized) · Spike funded to $100 by AUTH #031.

Self-hosted Gaussian-splat reconstruction: a capture bundle becomes a compressed splat (`.spz`/`.sog`) plus a collision mesh, on our own infrastructure. Replaces the retired Luma integration (ADR-0005). **Raw media never enters git.**

## Pipeline

```
ScanInput ─▶ SfM (COLMAP/GLOMAP) ─▶ train (gsplat/Brush) ─▶ compress (.spz/.sog) ─▶ mesh (Open3D) ─▶ EnvironmentPackage
```

Two hard gates run before any GPU work (`pipeline.run_pipeline`):
1. **License gate** (`licenses.assert_commercial_safe`) — every component MIT/BSD/Apache-2.0; INRIA 3DGS and SuGaR are excluded (ADR-0005, SECURITY_CHECKLIST §7.3).
2. **Spend cap** (`cost.CostLedger.guard`) — the $50/day cap (SECURITY_CHECKLIST §8.5) and the $100 spike cap (AUTH #031); a run that would cross either never starts.

## Architecture

Trainer- and backend-agnostic via dependency-injected adapters (analysis 2026-09-24 → **gsplat first**, pluggable, Brush second):

| Stage | Protocol | Real adapter (container) | Test/dry-run fake |
|---|---|---|---|
| SfM | `sfm.SfM` | `ColmapSfM` (default: CUDA COLMAP 4.1, GPU SIFT + GPU matching (`auto`: exhaustive ≤500 images, else sequential) + incremental mapper), `GlomapSfM` (`colmap global_mapper`) | `fakes.FakeSfM` |
| Train | `trainer.Trainer` | `GsplatTrainer` (nerfstudio Splatfacto; default profile `scaled-10k-dense`; hard splat cap = growth limit `ns_train_capped` + post-train prune `ns_finish`), `BrushTrainer` | `fakes.FakeTrainer` |
| Compress | `compress.Compressor` | `SplatTransformCompressor` | `fakes.FakeCompressor` |
| Mesh | `mesh.Mesher` | `Open3DMesher` (splat cleaning per `splat_ops.MeshFilter` + Poisson + crop + decimation to 100K triangles) | `fakes.FakeMesher` |

The `reconstruction` package and its tests are **standard-library only** and run with no GPU (`ns_train_capped.py` / `ns_finish.py` run inside the container and import torch / nerfstudio only when executed; the rules they apply are pinned in `splat_ops.py` and its tests). The heavy tools live only in the CUDA container (`Dockerfile`); the fakes let the whole pipeline be exercised in CI.

## Run

- **Tests (no GPU):** `pytest services/reconstruction` (CI runs this repo-wide).
- **Dry run (no GPU):** `python -m reconstruction.spike --images <dir> --scan-id room1 --dry-run` — exercises the whole pipeline with the fakes and writes a cost sheet.
- **Spike (GPU box):** build the container, fetch a public dataset (`DATASETS.md` / `reconstruction.fetch_dataset`), then `python -m reconstruction.spike --images <scene>/images --trainer gsplat --rate <gpu $/hr>` (defaults: `--sfm colmap --matcher auto`; `--sfm glomap` for the global mapper). Compute target: **serverless GPU** (RunPod-flex / Modal, ~$1/scan, scale-to-zero) under the $100 cap (AUTH #031).
- **Open-video corpus on Modal (M1-PIPE-01):** `modal run services/reconstruction/modal_app.py --corpus all --out ./out/corpus --previews ./out/previews` reconstructs the M0-OWNER-01 open-license clips straight from the private `gj-corpus` volume (no media leaves Modal): `extract_clip_frames` (CPU, ffmpeg) decodes only each clip's `recommended_segments` at ≤2 fps (≤300 frames, 400 for clips >240 s), downscales to 1600 px and keeps the sharpest frame per window (`reconstruction/video_frames.py`); `reconstruct_clip` (A10G) runs SfM with **GLOMAP + sequential matching + 4096 SIFT features** (video defaults; `--corpus-sfm` / `--corpus-matcher` / `--max-features` / `--max-fps` override) and the default training profile, and writes `<slug>.spz`, `splat.ply`, `collision.obj`, `sparse/`, `renders/`, `preview.jpg`, `run.json` to `gj-corpus:/open-video-recon/<slug>/`. A pre-flight projection stops the job before any GPU work if it would cross `--budget` (default $18, `--spent` adds what is already spent); every clip is hard-capped at 30 min of GPU. Results: `corpus/open_video_recon_results.json`, `qa/reports/M1-CAPT-03-open-video-recon.md`.
- **On Modal (Operator, recommended host):** `modal run services/reconstruction/modal_app.py --images <dir> --scan-id <id> --source public` (public/corpus only; ~7 min / ~$0.19 for a 311-image room on A10G; `--gpu L40S` ~5.5 min / ~$0.23; `--profile`, `--splat-budget`, `--cpu` for experiments; `--bench` = SfM-only matcher × mapper sweep, `--train-bench-profiles` = training-only sweep, `--mesh-splats` = CPU mesh-rules sweep) — scale-to-zero GPU in Modal's cloud, image built from the `Dockerfile`. Account + token + caps setup: `OPERATOR_RUNBOOK.md`.

## Corpus intake (M0-CAPT-01)

The Owner's day-one corpus (M0-OWNER-01) is uploaded through a signed, expiring link into the private `gj-corpus` Modal volume. It is stripped of GPS, EXIF, XMP, QuickTime location and device tags in a Modal container (`tools/strip_metadata.py`: lossless remux, re-verified with ExifTool and ffprobe) and recorded in `corpus/manifest.json` (schema `corpus/manifest.schema.json`). The capture guide, the Owner's upload steps, the Operator commands (`tools/corpus_intake.py`), storage and retention are in **`corpus/README.md`**. Modal app: `corpus_intake_app.py`; upload page: `tools/intake_web.py`.

## Context
- Cost & trainer analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`
- Spike report (fill during the spike, **render-path first**): `research/vendors/reconstruction-spike-report.md`
- Backend decision: `ADRs/0005-reconstruction-selfhost-and-avatar-onprem.md`
- Operator runbook (Modal host, account + token): `OPERATOR_RUNBOOK.md` · Modal entrypoint: `modal_app.py`
