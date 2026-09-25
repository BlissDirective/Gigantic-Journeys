# Reconstruction Spike Report (M1-CAPT-03)

`research/vendors/reconstruction-spike-report.md` · Skeleton created 2026-09-24 · Fill during the spike. Deliverable for **M1-CAPT-03** (ADR-0005 / AUTH #030; funded to $100 by **AUTH #031**). Companion analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`.

> **Spike order (Owner decision 2026-09-24): render-path first.** Reconstruction (gsplat) is the de-risked half; the iOS Metal splat render is the #1 program risk. Prove correct 30 fps splats on a physical iPhone *before* investing further in the pipeline. Sections are ordered accordingly.

## 0. Environment
- GPU host (provider / instance / $/hr): **Modal** serverless, scale-to-zero (AUTH #033), `gpu="A10G"` (24 GB, sm_86) + `cpu=8`, `memory=16 GiB`, 1 h timeout. A10G listed at ~$1.10/hr; CPU and memory are metered separately (see §2).
- Container image (from `services/reconstruction/Dockerfile`, built by Modal `Image.from_dockerfile`, context `services/reconstruction/`): `im-U9j4YPYmNpw5ClLjVEzhES` (built 2026-09-25 in 1042 s, mostly the gsplat CUDA compile). Base `nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`.
- Pinned tool versions: COLMAP 3.7 (Ubuntu apt, **no CUDA**, SIFT on CPU); GLOMAP not installed; gsplat 1.4.0 (CUDA extension compiled at build from the `v1.4.0` tag, sm 8.0/8.6/8.9); nerfstudio 1.1.5; torch 2.4.1+cu124 / torchvision 0.19.1; open3d 0.18.0; numpy 1.26.4; Python 3.11 (deadsnakes, `/opt/venv`); Node 22 + `@playcanvas/splat-transform` 3.6.4.
- Input data (public dataset first, then corpus): **Mip-NeRF 360 `room`**, `images_4` (311 images, ~1557×1038), public benchmark (`--source public`). No corpus scan yet.

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
| COLMAP / GLOMAP | COLMAP 3.7 (apt, CPU SIFT); GLOMAP not yet | BSD-3-Clause | SfM |
| gsplat / Splatfacto | gsplat 1.4.0 / nerfstudio 1.1.5 | Apache-2.0 | trainer |
| splat-transform | @playcanvas/splat-transform 3.6.4 | MIT | compression |
| Open3D | 0.18.0 | MIT | collision mesh |

Per-scan GPU time & cost:

| Scan | Images | SfM (min) | Train (min) | Compress+mesh (min) | GPU-hr | Rate $/hr | **$/scan** |
|---|---|---|---|---|---|---|---|
| `smoke` (Mip-NeRF 360 room, A10G, 2026-09-25) | 311 (`images_4`), 311/311 registered | ~16.2 (extract 0.15 + exhaustive match 11.5 + mapper 4.3, all CPU) | ~6 (15k iters, ~20 ms/iter) + export | <1 | 0.381 (1371 s pipeline wall) | 1.10 | **$0.42** GPU-only (`cost.json`); **$0.86** actual Modal metered (A10G $0.421 + CPU $0.366 + memory $0.069) |

### Smoke run log (2026-09-25, Modal, Operator)
- Command: `modal run services/reconstruction/modal_app.py --images ./data/mipnerf360/room/images_4 --scan-id smoke --source public --sfm colmap --rate 1.10` (app `ap-KTh8ClZJ5PXmMFCPgefcNY`).
- Wall time: 40 min 40 s end to end locally, of which ~17 min was a full image rebuild (`im-U9j4YPYmNpw5ClLjVEzhES`, 1042 s); pipeline wall inside the container (what `cost.json` bills as `gpu_seconds`) was **1371 s (22.9 min)**. With a cached image, expect about 24 min end to end.
- Outputs (`./out/`, not committed): `smoke.spz` 8.0 MB (431,684 Gaussians, SH degree 3, SPZ v4), `smoke.obj` 36.3 MB (Poisson depth 9: 233,799 vertices / 470,328 triangles), `cost.json` (`package_bytes` 44.3 MB, `within_budget: true` vs 150 MB).
- `cost.json`: `{"splat_count": 431684, "format": "spz", "package_bytes": 44326888, "within_budget": true, "gpu_seconds": 1371.26, "rate_per_hour_usd": 1.1, "usd": 0.419}`.
- **Cost-model gap:** `cost.json` prices the pipeline wall time at the GPU rate only. On Modal, the 8 reserved CPU cores (needed because apt COLMAP runs SIFT on CPU) cost almost as much as the A10G. Actual metered cost was about 2× the sheet. The GPU sat idle for the ~16 min of CPU SfM.
- Build notes (fixed in `5a25f89`): (1) Modal's Dockerfile parser rejected the exec-form `CMD` because a JSON string was continued with `\<newline>` ("error unescaping string: UnrecognizedEscape"); the CMD is now one line. (2) The unscoped npm `splat-transform` does not exist; the package is `@playcanvas/splat-transform` and 3.x needs Node ≥ 22. (3) gsplat 1.4.0 on PyPI is a JIT-only wheel (kernels would compile on billed GPU time), its sdist lacks `glm`, and prebuilt wheels are cp310-only, so the extension is compiled at image build from the git tag. (4) torchvision pinned from the cu124 index so nerfstudio cannot replace torch; numpy 1.26.4 for open3d 0.18. (5) nerfstudio 1.1.5 (latest) has no MCMC strategy / `max-gs-num`, so the 2M splat budget is **not enforced** (default densification gave 432K). The trainer uses the `colmap` dataparser and `--vis tensorboard`, because the default viewer never exits. (6) Modal rebuilds the **whole** Dockerfile when any `COPY`'d source changes: a `reconstruction/` code edit costs a ~17 min rebuild.
- Follow-ups: CUDA COLMAP + GLOMAP (drops ~16 min of CPU SfM and most CPU cost); sequential/vocab-tree matching for video captures; MCMC budget cap (newer Splatfacto or gsplat `simple_trainer`); price CPU+memory in `cost.json`; split the Modal image so code edits don't rebuild gsplat; `libopengl0` to silence pymeshlab plugin warnings (harmless).

## 3. Package size & fps (AT-2, suggested — SPEC §11)

| Scan | Splat count | Format | Package MB (≤150 target) | iPhone fps (30 target) |
|---|---|---|---|---|
| `smoke` (Mip-NeRF 360 room) | 431,684 | SPZ (8.0 MB) + OBJ mesh (36.3 MB) | 44.3 | _TODO (iOS render path, M1-UNITY-01)_ |

## 4. Managed bridge (AT-3) — conditional, likely N/A
Per **AUTH #030**, a managed bridge is used only under a **written no-train + DPA + data-residency** commitment on file (`legal/vendors/`). The cost analysis found Luma discontinued reconstruction and Kiri publishes no such tier, so the expected outcome is **no bridge; self-host is the sole path**.
- Terms obtained? _TODO (default: no)_
- Bridge stood up? _TODO (default: no)_

## 5. Decision note (AT-4)
- Self-host vs bridge recommendation for the M1 pipeline: _TODO_
- iOS splat-render risk assessment + chosen mitigation: _TODO_
- Serverless vs spot/reserved GPU for early production: _TODO_
- Feeds an **ADR-0005 addendum** (needs Owner AUTH) if the direction firms up: _TODO_
