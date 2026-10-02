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

## Pass 3 — exhaustive matching on the partial and weak clips (2026-10-02, gj-operator)

**Why.** On GLOMAP, registration followed continuity: each cut or jump between segments usually started a
separate component, and only the largest was trained. Sequential matching (with loop detection) compares
nearby frames, so it can miss a segment that revisits an area seen earlier. On ≤ 357 frames, **GPU
exhaustive matching** (every pair) takes only 19–60 s, so it was tried on the 9 clips that were partial,
multi-segment or weak. Everything else was unchanged: the same frames (`--skip-extract`), 4096 features,
GLOMAP, `scaled-10k-dense`, the 2M cap, A10G.

`modal run services/reconstruction/modal_app.py --corpus <9 clips> --skip-extract --corpus-matcher exhaustive --budget 8 --spent 0.04`

Before the run, the 9 canonical outputs were copied to `gj-corpus:/open-video-recon/_pre-pass3/<slug>/`
(`reconstruct_clip` overwrites in place). Each clip was then judged on held-out metrics and the render
pairs. Where pass 3 was worse, the 2026-09-28 run was restored and the pass-3 run was archived.

| Clip | Reg % (old → new) | PSNR | SSIM | LPIPS | Pass-3 $ | Decision |
|---|---|---|---|---|---|---|
| tabletop/lego-paranal-observatory | 64.4 → **100.0** | 35.6 → 29.3 | 0.973 → 0.944 | 0.034 → 0.065 | 0.39 | **keep**: all 3 shots joined. PSNR is lower because the held-out set now spans the whole model (17 views, was 11); the renders are sharp |
| rooms/medieval-great-hall-winchester | 55.4 → **85.7** | 24.5 → 24.9 | 0.814 → 0.842 | 0.327 → 0.278 | 0.39 | **keep** (better on every axis) |
| tabletop/fantasy-diorama-dock-platform | 67.9 → 67.9 | 22.2 → 22.8 | 0.779 → 0.787 | 0.179 → 0.172 | 0.29 | keep (slightly better) |
| rooms/mediterranean-country-home | 60.1 → 60.1 | 22.5 → 23.2 | 0.847 → 0.858 | 0.250 → 0.229 | 0.31 | keep (better) |
| tabletop/tudor-dollhouse | 25.5 → 25.5 | 26.2 → 26.6 | 0.887 → 0.894 | 0.183 → 0.173 | 0.36 | keep (slightly better) |
| rooms/office-warehouse-fpv | 21.2 → 20.3 | 19.5 → **23.4** | 0.809 → 0.819 | 0.258 → 0.272 | 0.24 | keep (weak → usable-partial) |
| rooms/art-museum-galleries-eric-carle | 39.5 → 39.5 | 29.3 → 25.4 | 0.928 → 0.886 | 0.156 → 0.262 | 0.37 | **restore** old (worse) |
| rooms/abandoned-farmhouse | 37.2 → 91.5 | 17.7 → 15.3 | 0.761 → 0.695 | 0.406 → 0.541 | 0.29 | **restore** old: the joined segments have wrong poses (half the renders are mush) |
| rooms/modern-church-fpv | 24.7 → 55.5 | 24.3 → 16.5 | 0.875 → 0.695 | 0.181 → 0.677 | 0.40 | **restore** old (wrong poses) |

**Findings**
- Exhaustive matching **fixes multi-shot tabletop and hall clips** where the shots overlap (lego 64 → 100 %,
  Winchester 55 → 86 %), and it nudges the rest up by 0.4–0.7 dB.
- It **over-links** where it shouldn't. On clips with repetitive texture or blur (the farmhouse's cluttered
  rooms, the FPV church), it accepts false matches between segments, and GLOMAP then fuses them into one
  model with wrong poses. Registration % alone would read those runs as better, so the verdict always needs
  the held-out LPIPS (≥ 0.5 = broken) and a look at the renders.
- **Recommended corpus default:** exhaustive matching for clips of ≤ ~400 frames, *gated* by a pose-sanity
  check. Reject the run, falling back to sequential, if held-out LPIPS rises by more than 0.1 or PSNR drops
  more than 3 dB while registration jumps. This is a Builder follow-up in `modal_app.py`; the defaults were
  not changed here.
- SfM cost rose with exhaustive matching (lego 143 → 378 s, Winchester → 372 s), mostly in GLOMAP's
  rotation averaging and bundle adjustment over the denser view graph, not in matching.

**Canonical corpus after pass 3** (15 clips; `services/reconstruction/corpus/open_video_recon_results.json`):
6 good (lego observatory, library, Eldon House, mosque, museum case, Winchester), 2 usable (Theed,
fantasy dock), 5 usable-partial (Eric Carle, Mediterranean, dollhouse, church, office), 1 weak
(farmhouse), 1 fail (penthouse). Summed in-container cost of the canonical runs: **$5.04** (each clip is
one A10G run at $0.23–0.63, median $0.29). Splats range from 170K to 780K, which is inside the 2M cap and
the ~1–2.5M iOS budget (M1-UNITY-01). Packages are 6.8–17.7 MB (SPZ + 100K-triangle collision OBJ), well
under 150 MB.

**Cost of pass 3.** In-container meter: **$3.04** for 9 clips ($0.24–0.40 each). Modal per-app report: $3.34.
Workspace October metered: $0.04 → **$6.83**, all covered by Starter credits, **$0 billed**. As on 09-28,
the workspace summary runs ahead of the per-app report, so the summary is used for cap tracking:
$6.83 of the $20 limit, $13.17 left. Runpod was not used ($48.57 balance, 0 pods).
