# Reconstruction Spike Report (M1-CAPT-03)

`research/vendors/reconstruction-spike-report.md` · Skeleton created 2026-09-24 · Fill during the spike. Deliverable for **M1-CAPT-03** (ADR-0005 / AUTH #030; funded to $100 by **AUTH #031**). Companion analysis: `research/vendors/reconstruction-cost-and-trainer-analysis.md`.

> **Spike order (Owner decision 2026-09-24): render-path first.** Reconstruction (gsplat) is the de-risked half; the iOS Metal splat render is the #1 program risk. Prove correct 30 fps splats on a physical iPhone *before* investing further in the pipeline. Sections are ordered accordingly.

## 0. Environment
- GPU host (provider / instance / $/hr): **Modal** serverless, scale-to-zero (AUTH #033), `gpu="A10G"` (24 GB, sm_86) + 8 CPU cores (hard limit 8 since 2026-09-26) + 16 GiB, 1 h timeout. A10G $1.10/hr, CPU $0.0473/core-hr, memory $0.008/GiB-hr (`modal billing rates`), each billed per second as max(reserved, used) (see §2).
- Container image (from `services/reconstruction/Dockerfile`, built by Modal `Image.from_dockerfile`, context `services/reconstruction/`): `im-U9j4YPYmNpw5ClLjVEzhES` (built 2026-09-25 in 1042 s, mostly the gsplat CUDA compile). Base `nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04`.
- Pinned tool versions (since 2026-09-26): **COLMAP 4.1.1 CUDA 12.9** (conda-forge `cuda_129ha585b08_4` + `openimageio=3.1`, micro-arch level x86_64_v3, in `/opt/colmap`; GLOMAP's global mapper is built in as `colmap global_mapper`); smoke run 2026-09-25 used COLMAP 3.7 (Ubuntu apt, no CUDA, CPU SIFT); gsplat 1.4.0 (CUDA extension compiled at build from the `v1.4.0` tag, sm 8.0/8.6/8.9); nerfstudio 1.1.5; torch 2.4.1+cu124 / torchvision 0.19.1; open3d 0.18.0; numpy 1.26.4; Python 3.11 (deadsnakes, `/opt/venv`); Node 22 + `@playcanvas/splat-transform` 3.6.4.
- Input data (public dataset first, then corpus): **Mip-NeRF 360 `room`**, `images_4` (311 images, **779×519**; an earlier note said ~1557×1038, which is `images_2`), public benchmark (`--source public`). Corpus: since 2026-09-28, the 15 open-license open-video clips (`gj-corpus:/open-video/`, `--corpus`; §2, §5).
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
| `room-R` / `room-R2` (same room, A10G, 2026-09-26, SfM default: CUDA COLMAP, GPU SIFT + GPU exhaustive match + incremental mapper) | 311, 311/311 registered | 3.0 avg (extract 0.08 + match 0.3 + mapper 2.7) | ~6.5 (incl. export + eval) | 0.2 | 0.162 (582 s avg pipeline wall) | 1.10 | **$0.26** full (GPU+CPU+memory; `cost.json` $0.260 avg vs Modal metered $0.263 avg) |
| `room-D1` / `D2` / `F1` / `F2` (same room, A10G, 2026-09-26, **current default**: same SfM + `scaled-10k-dense` training, hard splat cap, cleaned mesh) | 311, 311/311 registered | 3.2 avg | 3.5 (incl. cap + eval + export) | 0.2 | 0.115 (413 s avg pipeline wall) | 1.10 | **$0.185** full (`cost.json`; D1/D2 within 2% of Modal metered) |
| **Open-video corpus, 15 clips** (CC-BY stand-in corpus, A10G, 2026-09-28 + pass 3 2026-10-02; GLOMAP, sequential or exhaustive matching per clip; `qa/reports/M1-CAPT-03-open-video-recon.md`) | 43–357 frames per clip | 1.1–14.1 per clip | 5.7–8.5 | ≤0.7 | 0.14–0.39 per clip | 1.10 | **$0.23–0.63 per clip, median $0.29**; $5.04 for the canonical 15 (in-container meter). Runpod RTX 4090 / A6000 measured on 2 of these clips at **$0.055–0.111** (`research/tier2/gpu-providers-2026-09.md` §7) |

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

**Still open** (training and mesh items done in the next section).
- Training (about 6.5 of the 9.7 min) is now the main cost. Options are fewer iterations, an MCMC splat cap (nerfstudio 1.1.5 still does not enforce 2M), or a newer gsplat trainer.
- The Poisson collision mesh size swings from 3.8 to 46 MB for the same config. Poisson depth is relative to the bounding box, so far-away floater splats coarsen it. The mesher needs outlier removal and a bounding-box crop.
- The matcher/mapper choice beyond 500 frames (sequential + incremental vs GLOMAP) should be re-benchmarked on the first long video corpus capture.

### Training speed-up, hard splat cap, stable collision mesh — 2026-09-26 (Operator)
Goal: cut the train stage (about 6.5 of the 9.7 min pipeline) without losing more than about 0.3 dB PSNR against the SfM-pass default (31.30 / 0.932 / 0.092 on the 39 held-out views), enforce the 2M splat budget, and make the collision mesh stable. Same input as above (Mip-NeRF 360 `room`, `images_4`, 311 images, `--source public`), same image (gsplat 1.4.0 / nerfstudio 1.1.5; both still the versions the image pins; nerfstudio 1.1.5 is the latest release, gsplat 1.5.3 is out but Splatfacto 1.1.5 does not expose its MCMC strategy either). A new training-only sweep (`--train-bench-profiles`) runs SfM once and then trains every profile from the **same poses** in parallel containers, so the differences are the trainer's alone.

**Profiling the old 15k train stage** (389 s on A10G): about 220 s of actual iterations (~14.7 ms/iter), about 80 s of nerfstudio's in-training evaluation (one eval image every 100 steps, all 39 eval images every 1000 steps, a checkpoint every 2000 steps; none of it used), about 20 s of start-up (imports, image caching), about 31 s for `ns-export` (nerfstudio's exporter writes the PLY one value at a time) and about 24 s for a separate `ns-eval` that re-loaded the model and the images. The schedule was also the 30k default cut at 15k: splitting ran until the last step, full resolution only from step 6000, and the position learning rate ended half-decayed.

**What changed.**
- `GsplatTrainer` takes a `TrainProfile`. `scaled-N` scales Splatfacto's step-based schedule from 30k to N iterations (stop splitting at N/2; resolution doubling, SH-degree steps and screen-size culling scaled; position-LR decay to the end of the run; warmup and the 3000-step opacity reset kept, because scaling them made each reset's refine pause eat most of a short run). In-training evals and periodic checkpoints are off (the final checkpoint is still written).
- `reconstruction/ns_finish.py` replaces `ns-export` + `ns-eval` with one model load: hard cap, then held-out eval of the capped model, then a vectorized PLY export in nerfstudio's exact layout (same fields, NaN/Inf and 1/255-opacity filters). Export 31 s → 0.1 s; finish step about 23 s in total.
- `--gpu A10G|L4|L40S|A100-40GB` (list price from `GPU_RATES`; `--rate` still overrides) and `--cpu <cores>` on `modal_app.py`; `--profile` and `--splat-budget` for experiments.

**Training sweep** (A10G unless noted; one row per run; train stage = `ns-train` + finish; $ = the training container's whole job incl. compress + mesh, `cost.json` pricing):

| Profile | Iters | PSNR / SSIM / LPIPS | Splats | `ns-train` s | Train stage s | Train container $ |
|---|---|---|---|---|---|---|
| `upstream-15k` (old default, re-run) | 15k | 31.37 / 0.932 / 0.091 | 430K | 364 | 389 | 0.179 |
| `upstream-15k-noeval` (in-training eval off) | 15k | 31.20 / 0.931 / 0.092 | 435K | 284 | 308 | 0.142 |
| `scaled-15k` | 15k | **31.52 / 0.932 / 0.091** | 360K | 266 | 292 | 0.134 |
| `scaled-12k` | 12k | 31.30 / 0.928 / 0.098 | 335K | 205 | 229 | 0.106 |
| `scaled-10k` (3 runs) | 10k | 31.21 avg (31.17 / 31.21 / 31.27) / 0.926 / 0.103 | 299K–304K | 169–199 | 193–233 | 0.089–0.109 |
| **`scaled-10k-dense`** (`densify_grad_thresh` 0.0006) | 10k | 31.23 / 0.929 / 0.095 | 404K | 183 | 207 | 0.097 |
| `scaled-7k` | 7k | 30.67 / 0.917 / 0.121 | 234K | 122 | 147 | 0.070 |
| `scaled-5k` | 5k | 30.15 / 0.908 / 0.141 | 212K | 109 | 140 | 0.069 |

**GPU tier** (`scaled-10k`, same poses): A10G ($1.10/h) 169–199 s `ns-train`, $0.089–0.109 per training job; **L4** ($0.80/h) 215 s, $0.097; **L40S** ($1.95/h) 102 s, $0.093; **A100-40GB** ($2.10/h) 168 s, $0.158. Quality was the same on every tier (31.21–31.25 dB). H100 / B200 / RTX PRO 6000 are not usable without adding their CUDA arch to the gsplat compile.

**Full pipeline runs with the new default** (`scaled-10k-dense`, cap 2M, cleaned mesh):

| Run | GPU / cores | SfM s | Train s | Pipeline s | `cost.json` $ | Modal metered $ | PSNR / SSIM / LPIPS | Splats | SPZ MB | Mesh MB (tris) |
|---|---|---|---|---|---|---|---|---|---|---|
| `room-D1` (percentile-box mesh) | A10G / 8 | 193 | 209 | 410 | 0.183 | 0.186 | 31.33 / 0.930 / 0.095 | 408K | 7.3 | 3.75 (100K) |
| `room-D2` | A10G / 8 | 210 | 206 | 427 | 0.191 | 0.195 | 31.30 / 0.930 / 0.095 | 408K | 7.3 | 3.75 (100K) |
| `room-C4` | A10G / 4 | 222 | 222 | 455 | 0.179 | — | 31.34 / 0.930 / 0.094 | 409K | 7.3 | 3.76 (100K) |
| `room-L40S` | L40S / 8 | 183 | 140 | 331 | 0.226 | 0.231 | 31.23 / 0.932 / 0.096 | 412K | 7.4 | 3.76 (100K) |
| `room-L4` | L4 / 8 | 279 | 277 | 574 | 0.209 | 0.211 | 31.28 / 0.931 / 0.096 | 405K | 7.3 | 3.75 (100K) |
| `room-F1` (final code) | A10G / 8 | 185 | 214 | 414 | 0.185 | — | 31.28 / 0.930 / 0.095 | 407K | 7.3 | 3.78 (100K) |
| `room-F2` (final code) | A10G / 8 | 179 | 212 | 402 | 0.180 | — | 31.28 / 0.930 / 0.095 | 409K | 7.3 | 3.77 (100K) |
| *Old default* (`room-R`/`R2`, avg) | A10G / 8 | 182 | ~389 | 582 | 0.260 | 0.263 | 31.30 / 0.932 / 0.092 | 430K | 7.9 | 27–30 (3.8–46 over all runs) |

**Decision (new default).**
- **Profile `scaled-10k-dense` on A10G** with 8 cores: pipeline 9.7 → **6.9 min (−29%)**, train stage ~389 → ~210 s (−46%), full cost **$0.26 → $0.185 per room (−29%)**, quality **31.30 / 0.930 / 0.095** over 4 A10G/8-core runs (D1, D2, F1, F2: 31.28–31.33 dB; PSNR ±0.00 dB, SSIM −0.002, LPIPS +0.003, i.e. no regression beyond run-to-run noise). It is the `ReconstructionConfig` / `modal_app.py` default (`train_iters=10000`).
- Why not faster: `scaled-7k` saves another ~45 s but loses 0.6 dB PSNR and 0.03 LPIPS, beyond the 0.3 dB allowance. Plain `scaled-10k` costs the same time but has 0.008 worse LPIPS; the denser threshold buys it back with ~100K more splats (still fewer than the old 430K). If quality matters more than time, `--profile scaled-15k` is the best config measured (31.52 dB) and is still 25% faster than the old default.
- Why A10G: L40S is the fastest (5.5 min per room) but costs +20%, because the incremental mapper is CPU-bound, so the GPU idles at $1.95/h during SfM. L4's hosts had slower CPUs (mapper 248 s vs 168–186 s), so it was the slowest (9.6 min) and still not cheaper once CPU and memory are billed for longer. A100 is the most expensive. Use `--gpu L40S` when turnaround matters.
- CPU: the run averages only ~1 core of the 8 reserved. `--cpu 4` saved 4% ($0.179) but added ~37 s (a slower mapper), so the default stays at 8; revisit with a larger capture.

**Hard 2M splat cap (was not enforced).** Two layers, verified with a 200K-budget stress config on the room (whose default run produces about 408K splats):
1. **Growth limit during training** (`reconstruction/ns_train_capped.py`): wraps `ns-train` and patches gsplat's `DefaultStrategy._grow_gs` so a refine step only grows the strongest candidates that fit under the budget. In the stress run it limited 31 refine steps, peaked at exactly 200,000, ended at 198,265 splats and scored **31.05 / 0.920 / 0.117**, −0.28 dB against the uncapped default with half the splats (and a faster train: 155 s).
2. **Hard post-train cap** (`ns_finish`): if the trained model is still over budget, keep the `budget` splats with the highest rendered contribution (blending weight summed over all 272 training views, one render + backward pass per view, 4 s) and drop the rest. The trainer then fails the run if the PLY still has more splats than the budget. Stress test with the growth limit off (`--no-growth-limit`): 408,460 → **200,000 exactly**, 29.17 / 0.900 / 0.126. A static alpha × area score gave only 25.08 dB for the same prune, so it is only the fallback when no cameras are available. A large prune after training (no fine-tuning) costs far more than limiting growth, so the growth limit is the primary mechanism and the prune is the guarantee.
- Unit tests pin the selection rule (`tests/test_splat_ops.py`, including a 20K-splat synthetic stress case), the ns-train/ns_finish argv and the over-budget failure (`tests/test_trainer.py`). The 2M default is far above what the room reaches (408K), so it never triggers there; `cost.json` `quality.growth` / `trained_splats` / `capped_splats` / `cap_applied` show what happened on every run.

**Stable collision mesh.** `Open3DMesher` previously ran Poisson (depth 9) on every splat center, so stray far-away splats stretched Poisson's octree over empty space: 3.8–46 MB for the same config. It now cleans the splats before meshing (`splat_ops.MeshFilter`):
1. Keep splats with opacity ≥ 0.5.
2. Crop to a robust **scene box**: the 1st–99th percentile per axis of the centers that lie in *dense* cells of a 64³ grid (at least half the mean occupied-cell count), plus a 5% margin. Thin floater clouds can't stretch it.
3. Drop splats larger than 2% of the box diagonal.
4. Statistical outlier removal (20 neighbours, 2σ).
5. Voxel-downsample to 1/512 of the diagonal, so point density no longer depends on the splat count.

Poisson then runs on the cleaned points, with normals oriented toward the camera centroid. Low-density vertices (bottom 5%) are removed, the mesh is cropped to the box again, pieces under 1% of the triangles are dropped, and it is decimated to 100K triangles. Per-step counts and the box go to `cost.json` `mesh`. A CPU-only sweep (`--mesh-splats`, $0.02) compared box rules on the 5 same-config full runs (D1, D2, C4, L4, L40S), using symmetric Chamfer distance between the meshes of every run pair (50K sampled points each, scene units; the box is about 1.4 × 3.5 × 1.2 units):

| Box rule | Mesh MB (5 runs) | Box extent, long axis | Chamfer mean (avg / worst pair) | Chamfer p95 (worst pair) | Mesh s |
|---|---|---|---|---|---|
| Old: no cleaning (earlier runs) | 3.8–46 | unbounded | not measured | not measured | ~10 |
| 1–99% percentile box | 3.75–3.76 | 6.9–8.7 | 0.060 / 0.082 | 0.58 | 5 |
| 2–98% percentile box | 3.77–3.78 | 4.1–4.9 | 0.036 / 0.063 | 0.17 | 10 |
| **Dense-cell box (default)** | **3.78–3.79** | **3.4–3.6** | **0.027 / 0.047** | **0.13** | 11 |
| Dense-cell box, stricter cells | 3.79–3.80 | 2.7–2.9 | 0.025 / 0.046 | 0.13 | 14 |

- The dense-cell box halves the run-to-run shape difference compared with a plain percentile box, and pins the box extent. The stricter variant gained almost nothing and starts cutting into the room, so the default is the moderate one.
- The two final verification runs with the committed code (`room-F1`, `room-F2`: full pipeline on A10G) gave meshes of **3.78 MB and 3.77 MB** (99,999 / 100,000 triangles) from 407K / 409K splats. Across every run of this pass (23 meshes, 198K–435K splats, 4 GPU types), meshes were 3.71–3.80 MB. The package (SPZ + OBJ) is now about 11.1 MB instead of 35–55 MB.
- The triangle target pins the size. What the cleaning fixes is *where* the triangles go: they no longer go into shells around floaters, which is what the Chamfer numbers measure. Some variance remains where one run reconstructs a distant region densely and another does not (F1/F2 box long-axis extent 3.2 vs 4.4). That is real scene content, not floaters.

**Cost accuracy.** `cost.json` stayed within 1.2–2.2% of Modal's per-app metered bill (D1 $0.183 vs $0.186, D2 $0.191 vs $0.195, L40S $0.226 vs $0.231, L4 $0.209 vs $0.211). The small gap is container start and upload before the meter starts. `cost.json` now also records the GPU tier and cores (`host`), the training profile and cap counts (`quality`) and the mesh cleaning counts (`mesh`).

**Spend for this pass:** about **$3.55** Modal metered on 2026-09-26 (per-app `modal billing report --for today`): 3 training sweeps (15 profile runs on A10G), 3 GPU-tier runs (L4 / L40S / A100), 3 cap stress runs, 7 full pipeline runs, 1 CPU mesh sweep and one SfM export (reused through `--sparse-cache`). No image rebuild was needed, because the new code is mounted. Everything was covered by the monthly credits (billed $0). The month to date is about $7.2 against the $20 limit.

**Still open.**
- A large post-train prune (no fine-tuning) costs ~2 dB at a 50% cut. If a capture routinely hits the 2M cap, prefer the growth limit alone (it already does) or add a short fine-tune after the prune.
- nerfstudio 1.1.5 has no MCMC strategy and no packed mode. The fixed-budget MCMC densifier and gsplat 1.5's packed rasterization would need gsplat's own trainer or a Splatfacto fork; they were not needed to hit the targets.
- The collision mesh is validated for size and stability, not yet for gameplay collision fit in Unity (M1-UNITY-01).
- The matcher/mapper choice beyond 500 frames still needs a long video capture.

## 3. Package size & fps (AT-2, suggested — SPEC §11)

| Scan | Splat count | Format | Package MB (≤150 target) | iPhone fps (30 target) |
|---|---|---|---|---|
| `smoke` (Mip-NeRF 360 room) | 431,684 | SPZ (8.0 MB) + OBJ mesh (36.3 MB) | 44.3 | _TODO (iOS render path, M1-UNITY-01)_ |
| `room-D1` (same room, current default, 2026-09-26) | 407,983 | SPZ (7.3 MB) + cleaned OBJ mesh (3.8 MB, 100K triangles) | 11.1 | _TODO (M1-UNITY-01)_ |
| Open-video corpus, 15 clips (canonical after pass 3, 2026-10-02) | 170K–780K | SPZ (6–14 MB) + cleaned OBJ mesh (~3.5–3.8 MB, 100K triangles) | 6.8–17.7 | _TODO (M1-UNITY-01, other worker): outputs in `gj-corpus:/open-video-recon/<slug>/` (`splat.ply` for the aras-p importer, `<slug>.spz`, `collision.obj`)_ |

## 4. Managed bridge (AT-3) — conditional, likely N/A
Per **AUTH #030**, a managed bridge is used only under a **written no-train + DPA + data-residency** commitment on file (`legal/vendors/`). The cost analysis found Luma discontinued reconstruction and Kiri publishes no such tier, so the expected outcome is **no bridge; self-host is the sole path**.
- Terms obtained? **No** (2026-10-02). Nothing is filed under `legal/vendors/`. Neither KIRI nor Autodesk APS has given a written no-train + DPA + data-residency commitment, and none was requested (that would be an account or vendor step needing its own AUTH).
- Bridge stood up? **No.** Per AUTH #030 the bridge is skipped, and self-host is the sole reconstruction path. AT-3 is satisfied by the documented skip.

## 5. Decision note (AT-4)

2026-10-02 · gj-operator. Evidence: §2–§3, `qa/reports/M1-CAPT-03-open-video-recon.md` (15-clip corpus,
2 passes), `research/tier2/gpu-providers-2026-09.md` §7 (Runpod benchmark). The direction below is already
locked by **AUTH #032 (ADR-0005 addendum 4)** and **#039**. This note confirms it with measurements and
does not propose a new ADR change.

- **Self-host vs bridge: self-host.**
  - The commercially licensed stack (COLMAP/GLOMAP BSD, gsplat/Splatfacto Apache-2.0, splat-transform
    MIT, Open3D MIT) reconstructed 15/15 corpus clips end to end.
  - 14 of the 15 are usable to some degree: 6 good, 2 usable, 5 partial, 1 weak. One failed (penthouse:
    FPV drone footage, wrong poses).
  - Cost: $0.23–0.63 per clip on Modal A10G, and $0.055–0.111 per scene on Runpod Secure.
  - Every output is a splat under 2M, a 100K-triangle collision mesh, and a package of 7–18 MB.
  - No bridge has the required terms (§4), so there is nothing to weigh against self-host.
- **Capture guidance from the corpus (feeds M1-CAPT-01/04 coaching).** What works: slow, continuous,
  textured walkthroughs and orbits without cuts. What fails or goes partial: fast FPV flight, motion blur,
  low-texture white or glass surfaces, and multi-room tours with hard cuts. The readiness gate (AUTH #025)
  should screen for continuity and blur.
- **Pipeline defaults.**
  - Photo sets: incremental mapper + `--matcher auto`.
  - Video: GLOMAP + 2 fps + 4096 features.
  - Exhaustive matching helps multi-shot clips of ≤ ~400 frames, but it needs a pose-sanity gate
    (pass 3: 6 of 9 clips improved, 3 over-linked). Builder follow-up.
- **iOS splat-render risk: still the #1 program risk, and unchanged by this spike.** It is
  trainer-orthogonal and sits in M1-UNITY-01 (other worker). Mitigations already planned
  (`design/proposals/ios-splat-render-v1.md`):
  - replace aras-p's Metal radix sort with a bitonic or tile-local sort, or fall back to a MetalSplatter
    native plugin;
  - keep the splat budget at or below the measured 170–780K per corpus scene (the 2M cap holds, with
    headroom to tighten it to ~1M for older iPhones);
  - fall back to textured-mesh visuals (ADR-0001 addendum 1).

  The reconstruction side delivers everything the render track consumes: `splat.ply` (3DGS layout, for the
  aras-p importer), `.spz`, and the collision OBJ, per clip in the private volume.
- **Serverless vs spot/reserved for early production: serverless per-scan pods.**
  - **Runpod Secure is primary** (#039): RTX 4090, $0.06–0.11 per scene, 3–4.5× cheaper than Modal at
    equal quality.
  - **Modal is the fallback.** It is also the zero-cash choice while its monthly Starter credit lasts.
  - Reserved capacity only pays at sustained volume, so revisit it at M5 with real scan counts.
  - Open #039 condition: the full-corpus **Runpod batch validation** (cold start, reliability,
    region/data-retention) has run on only 2 clips so far. A full 15-clip batch is estimated at
    **≈ $1.5–2.5** of the $48.57 prepaid balance, inside the existing caps. It was not run this session,
    because Modal credit covered the corpus pass (Modal-first instruction).
- **ADR-0005:** no new addendum is needed. Addendum 4 (AUTH #032) already records gsplat-first, serverless
  GPU and the split render track, and these results support it.
- **What is left before M1-CAPT-03 can close:** AT-2 (suggested; the iOS render on a physical iPhone, owned
  by M1-UNITY-01). With AT-1, AT-3 and AT-4 met, the ticket goes **in-review**.
