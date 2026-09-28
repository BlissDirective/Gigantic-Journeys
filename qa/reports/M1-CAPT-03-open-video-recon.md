# M1-CAPT-03 / M1-PIPE-01 — open-video corpus reconstruction (15 clips)

**2026-09-28 · Operator (gj-operator), Owner-approved run.** All 15 active clips of the open-license stand-in corpus (M0-OWNER-01 revision 2, `gj-corpus:/open-video/{rooms,tabletop}/<slug>/`) were reconstructed on Modal with the self-hosted pipeline. Nothing left project infrastructure: frames were decoded inside Modal, and every output stays in the private `gj-corpus` volume under `/open-video-recon/<slug>/`. `_superseded/` was not touched. Machine-readable results: `services/reconstruction/corpus/open_video_recon_results.json`.

## What ran

`modal run services/reconstruction/modal_app.py --corpus all` (the new corpus mode):

1. **Frames (CPU, `extract_clip_frames`).** ffmpeg decodes only each clip's `recommended_segments` (clip time), at 3× the planned rate. The rate is ≤2 fps, with at most 300 frames per clip (400 for clips over 240 s; the 659 s dollhouse got 0.54 fps). Frames are scaled to 1600 px on the long side. The sharpest candidate of every window of 3 (variance of the Laplacian) is kept, and a window is dropped if its best frame is below 0.3× the clip median. This stage cost about $0.003–0.008 per clip.
2. **Reconstruct (A10G, `reconstruct_clip`).** SfM uses COLMAP 4.1.1: GPU SIFT capped at 4096 features, sequential matching with loop detection, then the **GLOMAP** global mapper. Training is Splatfacto `scaled-10k-dense` (10k iterations, the benchmark profile) with the 2M splat cap, then SPZ compression and the cleaned, decimated collision mesh. Quality is scored on held-out views (every 8th registered frame). Each clip's GPU time is hard-capped at 30 min, and a pre-flight projection stops the whole job before any GPU work if it would cross $18.

**Why not the room-benchmark SfM defaults (incremental mapper + exhaustive matching, 8192 features)?** The pilot (`tabletop/lego-paranal-observatory`, 196 frames at 3 fps) never finished the incremental mapper: each global bundle adjustment took 2+ min, the steps were degenerate (CHOLMOD "not positive definite"), and I stopped it after 25 min. An SfM-only bench on the same frames registered 196/196 with GLOMAP, but took 873 s, because dense video frames produce long tracks (mean track length 22, about 5.7K observations per image). Dropping to 2 fps and 4096 features cut SfM to 143 s. The incremental mapper remains the default for photo sets.

## Results

Metrics: registration % = registered / extracted frames (largest model only). PSNR / SSIM / LPIPS are on held-out registered frames, so they measure the reconstructed part only. Wall = the GPU function's wall time. Cost = GPU + CPU + memory at Modal list prices (A10G $1.10/h, $0.0473 per core-hour, $0.008 per GiB-hour), plus frame extraction.

| Clip | Frames | Reg % | PSNR / SSIM / LPIPS | Wall (min) | Cost ($) | Verdict |
|---|---|---|---|---|---|---|
| tabletop/lego-paranal-observatory | 132 | 64.4 | 35.6 / 0.973 / 0.034 | 9.2 | 0.25 | good |
| rooms/public-library-reading-room | 43 | 100.0 | 34.1 / 0.970 / 0.031 | 10.0 | 0.27 | good (short pan) |
| rooms/historic-house-eldon-house | 291 | 85.6 | 25.3 / 0.834 / 0.270 | 23.2 | 0.63 | good |
| rooms/mosque-prayer-hall-umayyad | 206 | 100.0 | 24.7 / 0.844 / 0.144 | 16.6 | 0.45 | good |
| tabletop/model-village-museum-case | 207 | 100.0 | 24.6 / 0.838 / 0.237 | 10.0 | 0.28 | good |
| rooms/medieval-great-hall-winchester | 175 | 55.4 | 24.5 / 0.814 / 0.327 | 11.9 | 0.32 | usable |
| tabletop/lego-theed-diorama | 237 | 96.6 | 21.7 / 0.819 / 0.262 | 15.9 | 0.43 | usable |
| tabletop/fantasy-diorama-dock-platform | 84 | 67.9 | 22.2 / 0.779 / 0.179 | 10.2 | 0.28 | usable |
| rooms/art-museum-galleries-eric-carle | 281 | 39.5 | 29.3 / 0.928 / 0.156 | 9.4 | 0.26 | usable, partial |
| rooms/mediterranean-country-home | 148 | 60.1 | 22.5 / 0.847 / 0.250 | 9.5 | 0.26 | usable, partial |
| tabletop/tudor-dollhouse | 357 | 25.5 | 26.2 / 0.887 / 0.183 | 12.0 | 0.33 | usable, partial |
| rooms/modern-church-fpv | 227 | 24.7 | 24.3 / 0.875 / 0.181 | 8.4 | 0.23 | usable, partial |
| rooms/abandoned-farmhouse | 129 | 37.2 | 17.7 / 0.761 / 0.406 | 9.8 | 0.27 | weak |
| rooms/office-warehouse-fpv | 222 | 21.2 | 19.5 / 0.809 / 0.258 | 8.7 | 0.24 | weak (4 fps retry kept) |
| rooms/penthouse-apartment-fpv | 212 | 88.7 | 14.4 / 0.733 / 0.646 | 8.8 | 0.24 | **fail**: wrong poses |

All 15 pipeline runs completed and produced an SPZ, a PLY, a collision OBJ, a sparse model and renders. 14 are usable to some degree. **Penthouse failed:** its poses are wrong with both GLOMAP and an incremental-COLMAP retry (PSNR 14.1), and the render is mush. Two retries were tried: 4 fps frames for office-warehouse (PSNR 17.8 → 19.5, kept) and for modern-church (PSNR 24.3 → 20.4, not kept). Superseded runs are kept in `gj-corpus:/open-video-recon/_pass1/` and `_pass2/`.

## Cost

- Canonical 15 clips (measured in-container): **$4.73**, averaging $0.32 per clip. No clip was projected over $2; the dearest was Eldon House at $0.63 (SfM 14 min).
- Whole job by Modal billing, including the stopped pilot, the SfM bench and the retries: **$7.62** in the per-app report for today. Workspace metered spend for September went from $7.00 to $17.48 (Δ $10.48; the gap to the per-app report looks like reporting lag). Everything is covered by credits and billed $0. **The workspace is now at about $17.5 of the ~$20 monthly spend limit, so further Modal GPU work this month needs the Owner to raise the limit.** The limit was not changed.

## Observations

- **Reconstruct well:** slow, steady, textured walkthroughs and orbits with no cuts: the museum case, the mosque hall, Eldon House, the Lego observatory and the library. On GLOMAP, registration tracks continuity: each hard cut or jump between segments usually starts a separate component, and only the largest component is trained.
- **Partial:** long tours of many rooms (dollhouse, Eric Carle galleries) at the frame cap register one connected stretch. Multi-segment clips (farmhouse with 5 segments, Winchester with 3) join only where the segments overlap.
- **Poor:** fast FPV drone flights (office-warehouse, church, penthouse) have motion blur, large parallax per frame and low-texture white or glass surfaces. Penthouse failed outright. More frames did not reliably help.
- **SfM on video:** density, not frame count, drives SfM time. 2 fps and 4096 features were enough; GLOMAP handled video far better than the incremental mapper (which won on the Mip-NeRF photo set).
- Training time was about 6–8 min per clip regardless of frame count, so SfM is the cost variable (0.4–14 min).

## Artifacts

- Per clip on Modal: `gj-corpus:/open-video-recon/<slug>/` contains `<slug>.spz`, `splat.ply`, `collision.obj`, `sparse/` (COLMAP model), `renders/` (2 held-out ground truth | render pairs), `preview.jpg`, `run.json` (timings, frames, registration, metrics, GPU, cost), `frames/` and `frames.json`.
- Preview JPEGs and a contact sheet were downloaded to the Operator box for the Owner. They are not committed: they are renders of third-party CC-BY footage, and the evidence standard is PNG-only.

Privacy: the inputs are public, openly licensed videos (attribution in `services/reconstruction/corpus/OPEN_VIDEO_ATTRIBUTION.md`). No user scans and no personal data were used. Media and outputs stay in the private Modal volume; nothing large is committed to git.
