# Capture → Render Quality v1 — designs + Brain-B builds

Goal: a user films a room for **≤4 minutes, handheld**, and it renders **flawlessly** as an
interactive environment inside the ~150 MB / 30 fps iPhone budget. This proposal designs the
highest-leverage improvements synthesised from the external video→3D survey
(`external-synthesis-builds.md`, PDF `GiganticJourneys-Video-to-3D-Synthesis`) and records the
**deterministic Brain-B cores built now** plus the **Operator (GPU / Unity / model) wiring** each
needs.

**Clean-IP posture (unchanged):** every item below is built from a **published method** or a
**permissively-licensed** project (Apache/MIT/BSD). No non-commercial code, weights, or model
outputs enter the shipping path. The feed-forward model weights (MapAnything-apache, VGGT
commercial) and any monocular-depth weights go through counsel/AUTH before shipping. Learned
models train on owned / licensed / synthetic data only.

**Split convention.** "Built now" = a deterministic, GPU-free Python core + tests in
`services/reconstruction/` (the data contract the heavy stack mirrors). "Operator" = the
CUDA/nerfstudio training wiring, the iOS/Metal viewer, and the cloud model serving — tracked as
handoff items. This mirrors how GJ already ships Brain-B references ahead of the engine.

---

## Commercial-safe — priority order

### 1. gsplat anti-aliased + MCMC densification (quick win, pure config)
- **Concept.** gsplat (Apache-2.0, our backbone) already re-implements Mip-Splatting's opacity
  compensation (`rasterize_mode="antialiased"`, alias-free at any zoom) and an MCMC densification
  strategy (relocates dead Gaussians → fewer floaters at a fixed budget). Both are the two biggest
  quality killers for a short, uneven handheld pass.
- **Built now.** `ReconstructionConfig.rasterize_mode` / `densify_strategy` (+ validation);
  `render_quality.splatfacto_quality_args(config)` maps them to ns-train flags. Defaults preserve
  current behaviour. Tests: `test_render_quality.py`.
- **Operator.** Confirm the exact Splatfacto flag/value against the pinned nerfstudio version, pass
  the args in `ns_train_capped`, and A/B `antialiased`+`mcmc` vs `classic`+`default` on the corpus
  (PSNR + floater count), then flip the defaults.

### 2. DN-Splatter depth + normal regularisation + mesh (biggest quality lever)
- **Concept.** DN-Splatter (Apache-2.0, on gsplat) regularises the splat with ARKit/LiDAR sensor
  depth and a monocular prior, plus normal smoothness, and extracts a mesh — engineered for
  smartphone RGB-D. Fixes textureless-wall/floor failures and yields a cleaner collision mesh.
- **Built now.** `depth_normal.py`: `edge_aware_log_l1` (sensor depth, down-weighted at image
  edges), `pearson_depth_loss` (scale-invariant, for a mono prior), `normal_consistency`,
  `normal_tv`. Tests: `test_depth_normal.py` (aligned → lower loss; scale-invariance proven).
- **Operator.** Mirror these losses on the rendered depth/normals in Splatfacto training; route
  DN-Splatter's mesh export into the existing Open3D collision step. Verify the licence of any
  monocular-normal helper weights before shipping them.

### 3. Monocular depth prior alignment (Depth Anything V2 Small)
- **Concept.** A relative mono-depth map becomes a usable metric prior once scale/shift-aligned to
  ARKit metric depth; it fills the regularisers where sensor depth is missing (far/low-texture).
  Depth Anything V2 **Small** is Apache-2.0 and runs ~30 fps on-device (also powers capture
  guidance).
- **Built now.** `depth_prior.py`: `DepthPrior` port, `align_scale_shift` (least-squares),
  `apply_scale_shift`, `to_metric`, `MockDepthPrior`. Tests: `test_depth_prior.py` (recovers a
  known scale/shift; skips invalid pixels).
- **Operator.** Run the Depth Anything V2 **Small** (Apache) CoreML model on device / box, feed its
  output through `to_metric` into the Pearson loss (#2). (Base/Large/Giant weights are CC-BY-NC —
  do not ship.)

### 4. BAD-Gaussians in-exposure trajectory (handheld motion blur)
- **Concept.** Model the blur in a frame as the integral over the camera's trajectory *during its
  exposure*; render virtual sub-frame sharp views, average them, and bundle-adjust the trajectory
  — turning blur into supervision and refining ARKit poses. BAD-Gaussians is Apache-2.0.
- **Built now.** `exposure_trajectory.py`: SE3 interpolation (`slerp` + lerp), `sample_linear`,
  `sample_cubic_bspline` (4-knot), `exposure_weights`. Tests: `test_exposure_trajectory.py`
  (endpoints/midpoint exact, unit quats, deterministic).
- **Operator.** Render the sub-frame poses + average per the weights in the training loop; expose
  the trajectory knots as optimisable alongside the ARKit prior pose.

### 5. Splatfacto-W appearance embeddings (exposure / auto-WB drift)
- **Concept.** Give each training image a learned appearance embedding → a small colour transform,
  absorbing auto-exposure/white-balance drift across the sweep; novel views render canonically.
  Splatfacto-W is Apache-2.0, in Nerfstudio.
- **Built now.** `appearance.py`: `AffineColor`, `apply_affine_color`, `AppearanceModel`
  (per-image transform; unseen view → identity). Tests: `test_appearance.py`.
- **Operator.** Wire the per-image embedding + colour MLP in Splatfacto; apply the transform at
  training render, identity at delivery.

### 6. MapAnything feed-forward metric front-end (replace COLMAP+GLOMAP)
- **Concept.** A feed-forward transformer regresses dense **metric** point maps + poses in one
  pass, and can be **conditioned on our ARKit poses/intrinsics** to lock scale — robust on
  low-texture, low-parallax indoor footage where classic SfM fails. MapAnything ships an
  **Apache-2.0** weights variant (`facebook/map-anything-apache`). This is the learned successor to
  the ARKit-pose splat-init adapter already merged.
- **Built now.** `feedforward_frontend.py`: `FeedForwardReconstructor` port, `FeedForwardResult`,
  `MockFeedForward`, and `write_frontend_model` — the bridge that turns the model's metric output
  into the exact COLMAP model the trainer reads (reusing `arkit_poses`'s writer) and **gates seed
  points by confidence** (feed-forward analogue of the scene-graph confidence gate). Tests:
  `test_feedforward_frontend.py` (ARKit conditioning → metric; confidence filtering; bridge writes
  the model).
- **Operator.** Serve MapAnything-apache on the box/cloud GPU, feed ARKit poses + intrinsics as
  input, pipe its result through `write_frontend_model`, then train Splatfacto on it. A/B dense
  init + pose quality + latency vs COLMAP+GLOMAP. **Counsel:** confirm the apache checkpoint's
  training-data basis before shipping.

### 7. On-device delivery: SOG compression + .spz + MetalSplatter
- **Concept.** Self-Organizing Gaussians (PlayCanvas splat-transform, MIT) + `.spz` (Niantic, MIT)
  compress a dense room (~20–40×) to fit 150 MB; MetalSplatter (MIT) is a native-iOS renderer that
  already reads `.spz`.
- **Built now.** `delivery.py`: `plan_compression` / `estimate_bytes` — the GPU-free planner that
  picks the SH degree + codec factor to hit a byte target and reports whether it fits (else: cut the
  splat count). Tests: `test_delivery.py`.
- **Operator.** Add a `splat-transform` (MIT) SOG stage to the export path driven by the plan;
  evaluate a MetalSplatter-based viewer against the 150 MB / 30 fps budget.

---

## Safe with caveat (counsel / AUTH)

### 8. Metric3D v2 as an alternative DepthPrior (metric depth + normals in one net)
- BSD-2 code, DINOv2 (Apache) backbone; **released weights' terms unverified → counsel before
  shipping**. Plugs into the `DepthPrior` port (#3) with no new code; its canonical-camera trick
  aligns to known ARKit intrinsics, giving both a metric-depth and a normal prior for #2.

### 9. VGGT-1B-Commercial + VGGT-SLAM submaps / loop closure (full-video front-end)
- **Concept.** The alternative / robustness peer to MapAnything, and the way to keep a whole
  3–4-min video globally consistent at bounded GPU memory: windowed submaps + global alignment +
  loop closure (VGGT-SLAM is BSD-2; VGGT commercial checkpoint is a custom, application-gated
  licence → **counsel/AUTH**, excludes military).
- **Built now.** `submap.py`: `submap_windows` (overlapping coverage) + `loop_closure_candidates`
  (descriptor-similarity pairs, adjacency-skipping, best-first) — the GPU-free scheduling core. The
  reconstructor itself is another `FeedForwardReconstructor` implementation (#6 port). Tests:
  `test_submap.py`.
- **Operator.** Serve the VGGT commercial checkpoint; produce per-submap retrieval descriptors;
  run global alignment over the windows + candidates; feed the merged map through
  `write_frontend_model`.

---

## Not built (out of this pass) — remaining

- **FisherRF capture guidance** ("you missed this wall" + informative-frame selection). High value
  for keeping capture ≤4 min, but FisherRF is **non-commercial** (built on Inria 3DGS), so it needs
  a **clean-room reimplementation on gsplat** — a separate build, not authorised in this pass.
- All **Operator GPU/Unity/model-serving wiring** listed above (training-loop integration, the iOS
  Metal viewer, cloud model serving).
- **Counsel/AUTH** items: MapAnything-apache training data; VGGT commercial licence; Metric3D v2 /
  Depth Anything (non-Small) / any depth-normal weights.

## Suggested prototype order
1 (config A/B) → 2 (depth/normal, biggest lever) + 3 (depth prior) → 6 (MapAnything front-end spike)
→ 4 (deblur) + 5 (appearance) → 7 (delivery) → 9 (VGGT full-video) → 8 (Metric3D swap-in) →
FisherRF clean-room (separate authorisation).
