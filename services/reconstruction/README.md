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
| SfM | `sfm.SfM` | `GlomapSfM` (default), `ColmapSfM` | `fakes.FakeSfM` |
| Train | `trainer.Trainer` | `GsplatTrainer` (MCMC, fixed budget), `BrushTrainer` | `fakes.FakeTrainer` |
| Compress | `compress.Compressor` | `SplatTransformCompressor` | `fakes.FakeCompressor` |
| Mesh | `mesh.Mesher` | `Open3DMesher` | `fakes.FakeMesher` |

The `reconstruction` package and its tests are **standard-library only** and run with no GPU. The heavy tools live only in the CUDA container (`Dockerfile`); the fakes let the whole pipeline be exercised in CI.

## Run

- **Tests (no GPU):** `pytest services/reconstruction` (CI runs this repo-wide).
- **Dry run (no GPU):** `python -m reconstruction.spike --images <dir> --scan-id room1 --dry-run` — exercises the whole pipeline with the fakes and writes a cost sheet.
- **Spike (GPU box):** build the container, fetch a public dataset (`DATASETS.md` / `reconstruction.fetch_dataset`), then `python -m reconstruction.spike --images <scene>/images --trainer gsplat --sfm colmap --rate <gpu $/hr>` (GLOMAP is not in the image yet). Compute target: **serverless GPU** (RunPod-flex / Modal, ~$1/scan, scale-to-zero) under the $100 cap (AUTH #031).
- **On Modal (Operator, recommended host):** `modal run services/reconstruction/modal_app.py --images <dir> --scan-id <id> --source public --sfm colmap --rate 1.10` (public/corpus only) — scale-to-zero GPU in Modal's cloud, image built from the `Dockerfile`. Account + token + caps setup: `OPERATOR_RUNBOOK.md`.

## Context
- Cost & trainer analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`
- Spike report (fill during the spike, **render-path first**): `research/vendors/reconstruction-spike-report.md`
- Backend decision: `ADRs/0005-reconstruction-selfhost-and-avatar-onprem.md`
- Operator runbook (Modal host, account + token): `OPERATOR_RUNBOOK.md` · Modal entrypoint: `modal_app.py`
