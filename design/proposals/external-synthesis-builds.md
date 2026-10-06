# External-Repo Synthesis → GJ Builds (Operator Handoff Log)

Running log of GJ builds derived from analysing external repositories. We extract only
**open-source *information*** — published methods and ideas — and implement them
**clean-room** as GJ-owned code. We never vendor an external project's source, weights,
or model outputs when its licence is restrictive; the idea is free, the artifacts are
not.

**Clean-IP posture (applies to every entry below):**
- Built from the **published paper / open knowledge**, not the repo's code or weights.
- **No external code, trained weights, or model outputs** enter the shipping path or any
  training set.
- Open-to-read ≠ patent-free: a freedom-to-operate / patent check stays with counsel
  (AUTH #044 lane) before anything derived ships.
- Training any learned model uses **owned / licensed / CC0 / synthetic** data only (same
  posture as the audio sourcing).

| Source repo | Licence | What we took | Builds |
|---|---|---|---|
| [facebookresearch/fast3r](https://github.com/facebookresearch/fast3r) (CVPR 2025) | FAIR **Noncommercial** Research License → artifacts discarded | Open-knowledge *ideas* only | #1 splat-init, #2 train-short/test-long, #3 confidence gating |
| [nerfstudio/gsplat](https://github.com/nerfstudio-project/gsplat) + DN-Splatter / BAD-Gaussians / Splatfacto-W | Apache-2.0 | antialiased+MCMC, depth+normal, deblur, appearance (code + method) | batch 2 #1–#5 |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) (apache weights) | Apache-2.0 | feed-forward metric front-end, ARKit-conditioned | batch 2 #6 |
| Depth Anything V2 Small / Metric3D v2 | Apache / BSD (weights verify) | monocular depth + normal prior | batch 2 #3, #8 |
| PlayCanvas splat-transform / Niantic SPZ / MetalSplatter | MIT | SOG compression + native iOS render | batch 2 #7 |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) + VGGT-SLAM | VGGT commercial (gated) / BSD-2 | full-video submaps + loop closure | batch 2 #9 |

---

## Source: Fast3R (CVPR 2025) — open-knowledge extractions

Fast3R's code/weights are FAIR-NC and are **not used**. We kept three published ideas,
most of which are field-wide prior art (DUSt3R lineage, feed-forward→splat init,
confidence maps). All three builds are Brain-B (deterministic Python, stdlib-only,
tested, no GPU to import).

### Build 1 — ARKit-pose → COLMAP model (splat-init without SfM) ✅ built

**Idea (Tier A, license-free):** hand the splat trainer camera poses + a seed cloud
directly, instead of recovering them with the slow/brittle COLMAP SIFT + GLOMAP
global-mapper stage. On iOS we already have a *better-than-feed-forward* pose source:
**ARKit tracks metric poses during the scan**, so the splat lands at true scale (fixing
the up-to-scale ambiguity the DUSt3R/Fast3R family has), and it's pure on-device-origin
data — fitting a real USER scan that may never leave our infra (ADR-0005 / AUTH #030).

**Files:**
- `services/reconstruction/reconstruction/arkit_poses.py` — `ArkitSfM` (satisfies the
  `sfm.SfM` port), the ARKit→COLMAP coordinate conversion (metric; ARKit/OpenGL →
  COLMAP/OpenCV axis flip), and a COLMAP **text** model writer
  (`cameras.txt` / `images.txt` / `points3D.txt`) the nerfstudio `colmap` dataparser reads.
- Wired into `select_sfm("arkit")` and `ReconstructionConfig(sfm="arkit")`.
- Tests: `services/reconstruction/tests/test_arkit_poses.py` (9) — metric round-trip,
  axis flip, model writing, bundle loading, selector/config.

**Operator wiring (gj-platform / gj-gameplay):**
1. iOS capture (M1-CAPT) exports `arkit_poses.json` **beside the `images/` dir** in the
   bundle. Schema: `{"frames":[{"name","intrinsics":{fx,fy,cx,cy,width,height},
   "cam_to_world":[16 floats, row-major]}], "points":[{"xyz":[x,y,z],"rgb":[r,g,b]}]}`.
   ARKit's `camera.transform` is column-major `simd_float4x4` — **transpose to row-major**
   on export. Seed `points` are optional (ARKit feature points or depth-derived).
2. Run reconstruct with `ReconstructionConfig(sfm="arkit")` → no SIFT/GLOMAP; Splatfacto
   inits from the ARKit poses + seed cloud.
3. **A/B on the corpus:** `arkit` vs `colmap` for SfM-stage latency and final PSNR, to
   quantify the saved global-mapping time. Record in `qa/`.

### Build 2 — Train-short / test-long positional indices ✅ built (reference)

**Idea (Tier B, clean-room from the paper):** a many-view reconstructor must handle a
variable, often large, frame count while training on only a handful of views. Fast3R's
"positional embedding interpolation" = **randomised positional indices** (training's few
views draw indices from the whole pool, covering it) + **index interpolation at
inference** (M views spread across the trained range, fractional when M exceeds the pool,
so it never extrapolates).

**Files:**
- `services/reconstruction/reconstruction/positional_index.py` — `PositionalIndexScheme`
  (`sample_training_indices`, `inference_indices`, `embedding`, `training_coverage`).
- Tests: `services/reconstruction/tests/test_positional_index.py` (9) — coverage → 1.0
  from short batches, no extrapolation past the pool at 1000+ views, determinism.

**Operator wiring:** this is the index/embedding math for a **future GJ-owned learned
reconstructor** — not in the live pipeline. It's **data-gated**: the learned net is a
later build that needs owned/licensed/synthetic training data (see posture above). ML/
Operator consumes `PositionalIndexScheme` when that model is built.

### Build 3 — Confidence → scene_graph gating ✅ built

**Idea (Tier A, license-free):** geometry the reconstruction/vision pass is unsure of
must not become playable surface. A surface whose confidence is below a floor is demoted
to class `void` + material `unknown`, so traversal never routes the miniature onto
hallucinated geometry. Both values are already in the **frozen** `scene_graph.json` enums
(AUTH #037) — **no schema change**.

**Files:**
- `services/scenegraph/scenegraph/confidence.py` — `gate_surface` / `GateResult`.
- `SceneConfig.confidence_floor` (default **0.0 = disabled**); wired into
  `build_scene_graph` (gate applied before measurement, so a gated surface carries no
  walkable measurements or material; its true low confidence is still reported).
- Tests: `services/scenegraph/tests/test_confidence.py` (8) — passthrough at floor 0,
  demotion below floor, mixed scene keeps trusted surfaces + validates the frozen schema.

**Operator wiring (gj-gameplay / vision pass):** the self-hosted vision pass returns a
per-surface `VisionLabel.confidence`; set `SceneConfig.confidence_floor` to the chosen
trust threshold. Feed reconstruction/pointmap confidence through so weak regions gate to
`void` automatically. Default stays 0.0 until the vision pass emits calibrated confidence.

---

## Consolidated operator action items

- [ ] **Capture (M1-CAPT):** export `arkit_poses.json` (row-major `cam_to_world` +
      intrinsics, optional seed points) in the bundle.
- [ ] **Reconstruct (gj-platform):** add an `sfm="arkit"` path in the Modal runner and
      A/B it against `colmap` on the corpus; record latency/PSNR in `qa/`.
- [ ] **Vision pass (gj-gameplay):** emit per-surface confidence and set a
      `confidence_floor`; verify weak geometry gates to `void`.
- [ ] **Learned reconstructor (ML, later):** data-source first (owned/licensed/synthetic),
      then use `PositionalIndexScheme`; counsel FTO check before any derived model ships.

_These are candidates and references, not shipping commitments. Each remains subject to
the clean-IP posture above._

---

## Source batch 2 — video&rarr;3D capture & render quality (2026-10-06)

Synthesised from the external video&rarr;3D survey (PDF `GiganticJourneys-Video-to-3D-Synthesis`);
full design in `design/proposals/capture-render-quality-v1.md`. Every item is built from a
permissively-licensed project or a published method &mdash; no non-commercial code, weights, or
outputs ship. Each entry is a **deterministic Brain-B core + tests built now**; the GPU-training /
iOS-Metal / model-serving half is the **Operator** wiring noted with it.

**Commercial-safe (built now, priority order):**
1. **gsplat anti-aliased + MCMC** &mdash; `ReconstructionConfig.rasterize_mode`/`densify_strategy` +
   `render_quality.splatfacto_quality_args`. _Operator:_ pass the flags in `ns_train_capped`, A/B on
   the corpus, flip defaults.
2. **DN-Splatter depth+normal + mesh** &mdash; `depth_normal.py` (edge-aware log-L1, Pearson,
   normal consistency/TV). _Operator:_ mirror on rendered depth/normals; mesh &rarr; Open3D collision.
3. **Mono-depth prior alignment** &mdash; `depth_prior.py` (`DepthPrior` port, scale/shift align to
   ARKit metric). _Operator:_ run Depth Anything V2 **Small** (Apache) &rarr; Pearson loss.
4. **BAD-Gaussians in-exposure trajectory** &mdash; `exposure_trajectory.py` (SE3 slerp/lerp, linear +
   cubic B-spline, weights). _Operator:_ render+average sub-frames, bundle-adjust the trajectory.
5. **Splatfacto-W appearance** &mdash; `appearance.py` (per-image affine colour; novel view &rarr;
   identity). _Operator:_ wire the embedding + colour MLP in Splatfacto.
6. **MapAnything feed-forward front-end** &mdash; `feedforward_frontend.py` (`FeedForwardReconstructor`
   port + `write_frontend_model` bridge to the COLMAP init, ARKit-conditioned, confidence-gated seed).
   _Operator:_ serve `facebook/map-anything-apache` (Apache), A/B vs COLMAP+GLOMAP. _Counsel:_
   apache-weights training-data basis.
7. **Delivery compression planner** &mdash; `delivery.py` (`plan_compression` to hit the 150 MB budget).
   _Operator:_ add a splat-transform SOG stage (MIT) + a MetalSplatter (MIT) viewer.

**Safe with caveat (built now; counsel before shipping the model/weights):**
8. **Metric3D v2** &mdash; plugs into the `DepthPrior` port (no new code); _counsel:_ its weights' terms.
9. **VGGT + VGGT-SLAM** &mdash; `submap.py` (windowing + loop-closure candidates) is the GPU-free
   scheduling core; VGGT is another `FeedForwardReconstructor`. _Counsel/AUTH:_ VGGT commercial licence.

**Clean-room (non-commercial origin, reimplemented on GJ's stack):**
10. **FisherRF capture guidance** &mdash; `capture_guidance.py`: coverage-uncertainty information-gain
    for next-best-view ("you missed this wall") coaching + informative-frame selection to keep the
    capture under 4 minutes. No FisherRF / Inria code, weights, or outputs. _Operator:_ compute
    per-view visible-cell sets from scene geometry; optionally refine the uncertainty with the
    renderer's Fisher diagonal.

Tests: ~44 new (reconstruction suite 247 passing); ruff + governance validators green; no protected
path touched. Licence adoptions logged as **AUTH #049** (permissive stack) + **#050** (caveated
commercial models); the Brain-B cores + FisherRF are open-knowledge / permissive.

**Remaining (not built this pass):** all Operator GPU / Unity / model-serving wiring above
(training-loop integration, iOS Metal viewer, cloud model serving). FisherRF capture-guidance is now
**built clean-room** (`capture_guidance.py`). Licence checks are resolved by AUTH #049/#050 — the
non-commercial-weights boundary and the VGGT / Metric3D counsel conditions are recorded there.

_These are candidates and references, not shipping commitments. Each remains subject to the
clean-IP posture above._
