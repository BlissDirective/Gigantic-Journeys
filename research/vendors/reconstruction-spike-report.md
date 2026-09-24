# Reconstruction Spike Report (M1-CAPT-03)

`research/vendors/reconstruction-spike-report.md` · Skeleton created 2026-09-24 · Fill during the spike. Deliverable for **M1-CAPT-03** (ADR-0005 / AUTH #030; funded to $100 by **AUTH #031**). Companion analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`.

> **Spike order (Owner decision 2026-09-24): render-path first.** Reconstruction (gsplat) is the de-risked half; the iOS Metal splat render is the #1 program risk. Prove correct 30 fps splats on a physical iPhone *before* investing further in the pipeline. Sections are ordered accordingly.

## 0. Environment
- GPU host (provider / instance / $/hr): _TODO_
- Container image digest (from `services/reconstruction/Dockerfile`): _TODO_
- Pinned tool versions (COLMAP, GLOMAP, gsplat, nerfstudio, open3d, splat-transform): _TODO_
- Input data (public dataset first, then corpus): _TODO_

## 1. iOS render path — the #1 risk (do this first)
- Renderer under test (aras-p/UnityGaussianSplatting MIT, or native Metal plugin / MetalSplatter MIT): _TODO_
- Metal depth-sort approach (issue #226 workaround: tile-local bitonic sort / native plugin / key-narrowing + splat budget): _TODO_
- Device(s) + iOS version: _TODO_
- **Result — correct depth-sorted splats on a physical iPhone? Y/N**: _TODO_
- fps @ splat count (target 30 fps @ ~1–2.5M splats): _TODO_
- Screens/video: _TODO_
- Verdict + remaining render work: _TODO_

## 2. Reconstruction quality & cost (AT-1)
Stack + licenses (must be MIT/BSD/Apache-2.0; INRIA 3DGS/SuGaR excluded — enforced by `reconstruction.licenses`):

| Component | Version | License | Role |
|---|---|---|---|
| COLMAP / GLOMAP | _TODO_ | BSD-3-Clause | SfM |
| gsplat / Splatfacto | _TODO_ | Apache-2.0 | trainer |
| splat-transform | _TODO_ | MIT | compression |
| Open3D | _TODO_ | MIT | collision mesh |

Per-scan GPU time & cost:

| Scan | Images | SfM (min) | Train (min) | Compress+mesh (min) | GPU-hr | Rate $/hr | **$/scan** |
|---|---|---|---|---|---|---|---|
| _TODO_ | | | | | | | |

## 3. Package size & fps (AT-2, suggested — SPEC §11)

| Scan | Splat count | Format | Package MB (≤150 target) | iPhone fps (30 target) |
|---|---|---|---|---|
| _TODO_ | | | | |

## 4. Managed bridge (AT-3) — conditional, likely N/A
Per **AUTH #030**, a managed bridge is used only under a **written no-train + DPA + data-residency** commitment on file (`legal/vendors/`). The cost analysis found Luma discontinued reconstruction and Kiri publishes no such tier, so the expected outcome is **no bridge; self-host is the sole path**.
- Terms obtained? _TODO (default: no)_
- Bridge stood up? _TODO (default: no)_

## 5. Decision note (AT-4)
- Self-host vs bridge recommendation for the M1 pipeline: _TODO_
- iOS splat-render risk assessment + chosen mitigation: _TODO_
- Serverless vs spot/reserved GPU for early production: _TODO_
- Feeds an **ADR-0005 addendum** (needs Owner AUTH) if the direction firms up: _TODO_
