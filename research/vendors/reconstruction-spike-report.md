# Reconstruction Spike Report (M1-CAPT-03)

`research/vendors/reconstruction-spike-report.md` · Skeleton created 2026-09-24 · Fill during the spike. Deliverable for **M1-CAPT-03** (ADR-0005 / AUTH #030; funded to $100 by **AUTH #031**). Companion analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`.

> **Spike order (Owner decision 2026-09-24): render-path first.** Reconstruction (gsplat) is the de-risked half; the iOS Metal splat render is the #1 program risk. Prove correct 30 fps splats on a physical iPhone *before* investing further in the pipeline. Sections are ordered accordingly.

## 0. Environment
- GPU host (provider / instance / $/hr): **Modal** serverless, scale-to-zero (AUTH #033), `gpu="A10G"` (24 GB, sm_86) + 8 CPU cores (hard limit 8 since 2026-09-26) + 16 GiB, 1 h timeout. A10G $1.10/hr, CPU $0.0473/core-hr, memory $0.008/GiB-hr (`modal billing rates`), each billed per second as max(reserved, used) (see §2).
- Container image (from `services/reconstruction/Dockerfile`, built by Modal `Image.from_dockerfile`, context `services/reconstruction/`): `im-U9j4YPYmNpw5ClLjVEzhES` (built 2026-09-25 in 1042 s, mostly the gsplat CUDA compile). Base `nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`.
- Pinned tool versions (since 2026-09-26): **COLMAP 4.1.1 CUDA 12.9** (conda-forge `cuda_129ha585b08_4` + `openimageio=3.1`, micro-arch level x86_64_v3, in `/opt/colmap`; GLOMAP's global mapper is built in as `colmap global_mapper`); smoke run 2026-09-25 used COLMAP 3.7 (Ubuntu apt, no CUDA, CPU SIFT); gsplat 1.4.0 (CUDA extension compiled at build from the `v1.4.0` tag, sm 8.0/8.6/8.9); nerfstudio 1.1.5; torch 2.4.1+cu124 / torchvision 0.19.1; open3d 0.18.0; numpy 1.26.4; Python 3.11 (deadsnakes, `/opt/venv`); Node 22 + `@playcanvas/splat-transform` 3.6.4.
- Input data (public dataset first, then corpus): **Mip-NeRF 360 `room`**, `images_4` (311 images, **779×519**; an earlier note said ~1557×1038, which is `images_2`), public benchmark (`--source public`). No corpus scan yet.
- Image layering (2026-09-26): one cached Modal layer per `# modal-layer:` Dockerfile section (base → torch → gsplat → nerfstudio → colmap); the `reconstruction/` package is mounted at start. Code edits: **no rebuild** (verified: the final runs started straight away after the code changes); COLMAP-layer edit: 49 s + 7 s; a full cold build: ~20 min, billed ~$0.13 CPU.

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
| COLMAP / GLOMAP | COLMAP 4.1.1 CUDA (conda-forge; GLOMAP = `colmap global_mapper`); was 3.7 apt CPU on 2026-09-25 | BSD-3-Clause | SfM |
| gsplat / Splatfacto | gsplat 1.4.0 / nerfstudio 1.1.5 | Apache-2.0 | trainer |
| splat-transform | @playcanvas/splat-transform 3.6.4 | MIT | compression |
| Open3D | 0.18.0 | MIT | collision mesh |

Per-scan GPU time & cost:

| Scan | Images | SfM (min) | Train (min) | Compress+mesh (min) | GPU-hr | Rate $/hr | **$/scan** |
|---|---|---|---|---|---|---|---|
| `smoke` (Mip-NeRF 360 room, A10G, 2026-09-25) | 311 (`images_4`), 311/311 registered | ~16.2 (extract 0.15 + exhaustive match 11.5 + mapper 4.3, all CPU) | ~6 (15k iters, ~20 ms/iter) + export | <1 | 0.381 (1371 s pipeline wall) | 1.10 | **$0.42** GPU-only (`cost.json`); **$0.86** actual Modal metered (A10G $0.421 + CPU $0.366 + memory $0.069) |
| `room-R` / `room-R2` (same room, A10G, 2026-09-26, **new default**: CUDA COLMAP, GPU SIFT + GPU exhaustive match + incremental mapper) | 311, 311/311 registered | 3.0 avg (extract 0.08 + match 0.3 + mapper 2.7) | ~6.5 (incl. export + eval) | 0.2 | 0.162 (582 s avg pipeline wall) | 1.10 | **$0.26** full (GPU+CPU+memory; `cost.json` $0.260 avg vs Modal metered $0.263 avg) |

### Smoke run log (2026-09-25, Modal, Operator)
- Command: `modal run services/reconstruction/modal_app.py --images ./data/mipnerf360/room/images_4 --scan-id smoke --source public --sfm colmap --rate 1.10` (app `ap-KTh8ClZJ5PXmMFCPgefcNY`).
- Wall time: 40 min 40 s end to end locally, of which ~17 min was a full image rebuild (`im-U9j4YPYmNpw5ClLjVEzhES`, 1042 s); pipeline wall inside the container (what `cost.json` bills as `gpu_seconds`) was **1371 s (22.9 min)**. With a cached image, expect about 24 min end to end.
- Outputs (`./out/`, not committed): `smoke.spz` 8.0 MB (431,684 Gaussians, SH degree 3, SPZ v4), `smoke.obj` 36.3 MB (Poisson depth 9: 233,799 vertices / 470,328 triangles), `cost.json` (`package_bytes` 44.3 MB, `within_budget: true` vs 150 MB).
- `cost.json`: `{"splat_count": 431684, "format": "spz", "package_bytes": 44326888, "within_budget": true, "gpu_seconds": 1371.26, "rate_per_hour_usd": 1.1, "usd": 0.419}`.
- **Cost-model gap:** `cost.json` prices the pipeline wall time at the GPU rate only. On Modal, the 8 reserved CPU cores (needed because apt COLMAP runs SIFT on CPU) cost almost as much as the A10G. Actual metered cost was about 2× the sheet. The GPU sat idle for the ~16 min of CPU SfM.
- Build notes (fixed in `5a25f89`): (1) Modal's Dockerfile parser rejected the exec-form `CMD` because a JSON string was continued with `\<newline>` ("error unescaping string: UnrecognizedEscape"); the CMD is now one line. (2) The unscoped npm `splat-transform` does not exist; the package is `@playcanvas/splat-transform` and 3.x needs Node ≥ 22. (3) gsplat 1.4.0 on PyPI is a JIT-only wheel (kernels would compile on billed GPU time), its sdist lacks `glm`, and prebuilt wheels are cp310-only, so the extension is compiled at image build from the git tag. (4) torchvision pinned from the cu124 index so nerfstudio cannot replace torch; numpy 1.26.4 for open3d 0.18. (5) nerfstudio 1.1.5 (latest) has no MCMC strategy / `max-gs-num`, so the 2M splat budget is **not enforced** (default densification gave 432K). The trainer uses the `colmap` dataparser and `--vis tensorboard`, because the default viewer never exits. (6) Modal rebuilds the **whole** Dockerfile when any `COPY`'d source changes: a `reconstruction/` code edit costs a ~17 min rebuild.
- Follow-ups: ~~CUDA COLMAP + GLOMAP~~, ~~sequential/vocab-tree matching~~, ~~price CPU+memory in `cost.json`~~, ~~split the Modal image~~ (all done 2026-09-26, see below); MCMC budget cap (newer Splatfacto or gsplat `simple_trainer`); `libopengl0` to silence pymeshlab plugin warnings (harmless).

### SfM speed-up: baseline vs A (GPU COLMAP) vs B (GLOMAP) — 2026-09-26 (Operator)
Goal: cut SfM time and cost without regressing splat quality. Same input for every run: Mip-NeRF 360 `room`, `images_4` (311 images), `--source public`, A10G + 8 cores + 16 GiB on Modal, one image (`services/reconstruction/Dockerfile`, COLMAP 4.1.1 CUDA), trainer unchanged (Splatfacto, 15k iterations). Quality comes from `ns-eval` on the 39 held-out views (every 8th image), which is now part of every run. Cost is the full GPU + CPU + memory figure: `cost.json` (new meter) and Modal's metered bill per app agreed within about 3%. Runs were repeated because SfM and training are not bit-deterministic. **Values are averages over the runs listed.**

| | **Baseline** (2026-09-25) | **A: GPU COLMAP**, `auto` → exhaustive, incremental (**winner, new default**) | A, `sequential` matcher, incremental | **B: GLOMAP** (`colmap global_mapper`), sequential |
|---|---|---|---|---|
| Runs | `smoke` (1) | `room-R`, `room-R2` (2) | `room-A`, `room-default`, `room-A3` (3) | `room-B`, `room-B2` (2) |
| SIFT features / matching | CPU / CPU exhaustive | GPU / GPU exhaustive | GPU / GPU sequential (15 overlap + quadratic + vocab-tree loop detection) | GPU / GPU sequential (same) |
| Extract / match / map (s) | 9 / 690 / 258 | 4.5 / 18.2 / 158.8 | 5.2 / 14.0 / 132.1 | 4.7 / 13.8 / 171.4 (+ 3.0 view-graph calibration) |
| **SfM wall** | **~972 s (16.2 min)** | **182 s (3.0 min), 5.3× faster** | 152 s (2.5 min) | 193 s (3.2 min) |
| **Pipeline wall** | **1371 s (22.9 min)** | **582 s (9.7 min), 2.4× faster** | 564 s (9.4 min) | 631 s (10.5 min) |
| **Full cost / scan** (Modal metered) | **$0.86** (cost.json said $0.42, GPU only) | **$0.26 (−70%)** | $0.26 | $0.29 |
| Registered images | 311/311 | 311/311 | 311/311 | 311/311 |
| Sparse points / mean track length | not recorded | 38.7K / 9.63 | 32.9K / 9.09 | 31.5K / 9.19 |
| Mean reprojection error | not recorded | 0.585 px | 0.490 px | 0.418 px |
| **PSNR / SSIM / LPIPS** (held-out) | not measured (no eval then) | **31.30 / 0.932 / 0.092** (31.32, 31.27) | 30.75 / 0.922 / 0.105 (31.12, **30.14**, 30.99) | 31.16 / 0.930 / 0.093 (31.16, 31.16) |
| Splats (SPZ MB) | 431,684 (8.0) | 428.6K–430.9K (7.9) | 427K–432K (7.7–8.1) | 424K–434K (7.8) |
| Package (SPZ + OBJ, ≤150 MB) | 44.3 MB | 35.1–38.3 MB | 43.8–55.5 MB | 11.6–41.3 MB |

**SfM-only sweep** (`--bench`, one container, one GPU feature extraction of 9.0 s; $0.46): every matcher × mapper registered 311/311 images in 1 model.

| Matcher (GPU) | match (s) | incremental: map s / total SfM s / points / reproj px | global: map s (incl. calibration) / total SfM s / points / reproj px |
|---|---|---|---|
| exhaustive (48K pairs) | 18.5 | 165.9 / 193.4 / 38.7K / 0.587 | 184.2 / 211.7 / 33.0K / 0.493 |
| sequential + loop detection | 13.4 | 125.6 / 148.1 / 32.9K / 0.492 | 159.9 / 182.3 / 31.5K / 0.415 |
| vocab_tree (100 NN) | 47.1 | 142.7 / 198.8 / 38.2K / 0.584 | 157.4 / 213.5 / 33.3K / 0.497 |

**What we learned.**
1. **GPU matching removes the bottleneck.** Exhaustive matching fell from about 11.5 min (CPU) to 18 s. For 311 images the mapper is now about 85% of SfM time, so a "smarter" matcher only saves seconds.
2. **The sequential matcher is fastest, but its quality was less stable.** It saved about 30 s of SfM (the mapper runs faster on the sparser graph). One of its 3 full runs scored 1.2 dB PSNR (SSIM −0.02) below exhaustive, even though its SfM statistics looked normal (311/311 registered, 0.49 px). Exhaustive scored 31.3 dB in both runs.
3. **The vocab-tree matcher** cost more matching time than exhaustive at this size (47 s) and gained nothing.
4. **GLOMAP (B) lost on this scene.** With the same matches, the global mapper was 19–34 s slower than incremental. In the full runs, B was +48 s pipeline, +$0.02–0.03 per scan, and −0.14 dB PSNR against A with exhaustive matching. Its lower reprojection error comes from stricter track filtering (fewer points) and did not show up in the renders. Global SfM is expected to pay off on much larger captures, not a 311-image room.
5. **Run-to-run variance** with an identical config is about ±0.1 dB for exhaustive and GLOMAP, and up to 1 dB for sequential. Compare configs over at least 2 runs.

**Decision.**
- **Winner: A.** It uses CUDA COLMAP 4.1.1 with GPU SIFT extraction and GPU matching, and COLMAP's incremental mapper. It is now the `modal_app.py` default (`--sfm colmap --matcher auto`).
- **Matcher policy:** `auto` = GPU **exhaustive** up to 500 images (about 50 s of matching at 500 by the O(n²) scaling) and **sequential** with vocab-tree loop detection beyond that, for long ordered video captures.
- **Result against the baseline:** SfM 16.2 → 3.0 min (5.3×), pipeline 22.9 → 9.7 min (2.4×), full cost $0.86 → $0.26 per room (−70%), with the same matcher/mapper algorithm as the baseline, so no quality regression is expected. It also had the best PSNR of the tested configs.
- **B stays selectable** with `--sfm glomap`. That is free to keep, since it shares the COLMAP front end. `--matcher sequential|exhaustive|vocab_tree` and `--no-gpu-features` stay selectable as well.

**Other changes in this pass.**
- `cost.json` now prices GPU + CPU + memory. A background meter reads the container's cgroup CPU and memory counters and bills max(reserved, used) per second. It reports `usd` (total), `gpu_usd`, `cpu_usd`, `memory_usd`, `usage`, `stage_seconds`, `sfm` statistics and `quality`.
- CPU now has a hard limit of 8 cores. The baseline's CPU COLMAP had burst to about 20 cores, which is why CPU cost nearly equalled GPU cost.
- The Modal image is layered: code edits no longer rebuild it.
- Two conda-forge COLMAP pitfalls are fixed in the Dockerfile: the undeclared OpenImageIO 3.1 dependency, and AVX-512 builds that crashed with SIGILL on a non-AVX-512 host (the first B attempt, $0.006).
- A `--bench` SfM-only sweep was added.
- License note: the conda COLMAP build dynamically links Qt 5 (LGPL-3.0) and FreeImage for its GUI and image I/O, as the apt 3.7 build did. It runs server-side only and is never distributed, so this is unchanged from before and not a blocker. Flagged for the license manifest review.

**Spend for this pass:** $2.47 Modal metered on 2026-09-26 (`modal billing report --for today`): one full image build, one SfM sweep, 7 full runs, one SIGILL-aborted run, and one crash-looping start (an in-container Dockerfile read, fixed before any GPU work). All of it was covered by the monthly credits (billed $0), and the month to date is about $3.6 against the $20 limit.

**Still open.**
- Training (about 6.5 of the 9.7 min) is now the main cost. Options are fewer iterations, an MCMC splat cap (nerfstudio 1.1.5 still does not enforce 2M), or a newer gsplat trainer.
- The Poisson collision mesh size swings from 3.8 to 46 MB for the same config. Poisson depth is relative to the bounding box, so far-away floater splats coarsen it. The mesher needs outlier removal and a bounding-box crop.
- The matcher/mapper choice beyond 500 frames (sequential + incremental vs GLOMAP) should be re-benchmarked on the first long video corpus capture.

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
