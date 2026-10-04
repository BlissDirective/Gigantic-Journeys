# M1-UNITY-01 — iOS Metal splat render path (the #1 risk) — build notes

2026-10-02, gj-operator. Runbook: `unity/docs/splat-render-integration.md` (Tier B). Ticket stays
**in-progress**: everything that can be built and checked on the Linux box and in CI is done; the gate
(AT-2, correct ordering on a physical iPhone) and the fps numbers (AT-3) need the device.

## What was built (Tier B: Metal-safe global sort, package unmodified)
- `unity/Assets/GiganticJourneys/Splats/Sorting/Resources/GJ/MetalSafeSplatSort.compute`:
  wave-free bitonic sort, flip/disperse form (every compare is ascending, so a non-power-of-two count works
  by treating indices `>= _Count` as +inf; no padding buffer). Kernels: `CSCalcKeys` (fresh key = sortable
  view-space z, value = splat index, every sorted frame, so a bad frame can't poison the next),
  `CSLocalSort` / `CSLocalDisperse` (512 elements per 256-thread group in threadgroup memory),
  `CSFlip` / `CSDisperse` (global strides). Only compare-and-swap, `groupshared` and group barriers: no
  wave/SIMD intrinsics and no cross-group forward-progress assumptions, which is what breaks the package's
  radix sort on Apple GPUs (aras-p/UnityGaussianSplatting#226). 256 threads and 4 KB groupshared per group are
  within every Metal iOS GPU's limits.
- `BitonicSortNetwork.cs`: the dispatch schedule plus a CPU mirror of every kernel (the reference).
- `MetalSafeSplatSorter.cs`: records the schedule into a `CommandBuffer`.
- `MetalSafeSplatSort.cs` (component, `[RequireComponent(GaussianSplatRenderer)]`): mode **Auto** (Metal
  only) / ForceOn / Off. When engaged it parks the package sort (`m_SortNthFrame = int.MaxValue`; the package
  sorts once at frame 0, then never) and, in `RenderPipelineManager.beginCameraRendering` (before the URP
  `GaussianSplatURPFeature` pass), writes keys into the package's own sort buffers
  (`m_GpuSortDistances`/`m_GpuSortKeys`) and sorts them. Same key, same matrix (`worldToCamera` with row 2
  negated × localToWorld) and same ascending order as the package, so the draw order is what the radix sort
  would give if it worked. It adopts the tier's `sortEveryNthFrame` from `SplatRenderSettingsApplier`.
  The package fields are reached by reflection against the pinned commit; a test fails CI if they move.
- `SplatRenderSettingsApplier` adds the component automatically in play mode, so every tiered splat gets
  it. It does nothing off Metal (Vulkan/D3D keep the package sort).

## Evidence (box: Unity 6000.0.84f1, xvfb + `-force-vulkan -force-device-index 0`)
`M1-UNITY-01/sort-tests-vulkan.xml`: **25/25 passed** (`MetalSafeSplatSortTests`):
- CPU network: 14 counts from 0 to 70 001, including 511/512/513/1025/4097; duplicates and extremes;
  elements past the count untouched. Each result is checked as an ascending, key-preserving permutation.
- **GPU**: the real compute shader on a Vulkan device sorts n = 1, 513, 4097, 70 001 and matches the CPU
  reference bit-for-bit. In CI (`-nographics`, no compute) that test reports Ignored; the CPU tests,
  the shader-kernel presence test and the package-binding guard run.
- Schedule: 1M splats = 11 merge stages (11 flip + 55 global disperse + 11 local disperse + 1 local sort =
  78 dispatches), every group count is ≤ 65 535.
- iOS compile: the shader compiles for Metal in the ios-build Unity player build (CI).

## Needs a physical iPhone (Owner / gj-qa-release, via the internal-debug TestFlight build)
- **AT-2 (gate):** splats render correctly depth-sorted from every angle (the #226 glitch is angle-dependent),
  with no flicker. The device check needs a splat in a build scene: today only `Assets/Capture/Samples/SplatSample.unity`
  has one and it is not in the build list. **Now testable:** the internal-debug SplatRoom scene (below). Then check the log
  line `[GJ-SPLAT-SORT] engaged on Metal`, or the on-screen label reading "Tier B".
- **AT-3:** sustained fps at about 1–2.5M splats, plus package MB, using the M0-UNITY-04 debug overlay
  (fps p50/p99, Save report). The bitonic sort is O(n log² n): if it misses 30 fps at budget, first raise
  `sortEveryNthFrame` to 2–3 on Medium (Low already uses 2; it is a per-tier knob), then escalate to Tier C per the runbook.

## Device-test splat room (2026-10-03): AT-2/AT-3 on the iPhone
Build **48** (internal-debug, run 37137079024, uploaded 2026-10-03 12:01 PM CT) adds a debug-only scene,
`Assets/Scenes/DeviceTest/SplatRoom.unity`, where the movement character walks through one real reconstructed
corpus room.
- **Room:** Winchester Great Hall (`medieval-great-hall-winchester`, corpus pass 3, 86% registered), **780,004 splats**.
  Source: "King Arthur's Round Table and Winchester Castle Walk Through [4K]" by [4K] Free Download Stock Videos,
  CC BY 3.0, modified (reconstructed). The credit is shown on screen in the scene. The pass-3 `.spz` uses a newer
  SPZ layout that the pinned aras-p importer can't read, so the asset was converted from the run's `splat.ply` at the
  package's "Medium" quality (pos/scale Norm11, color Norm8x4, SH Norm6): 36 MB raw, 30.4 MB packed.
- **Placement:** scale 8 (miniature: the hall is about 11.4 × 6.2 m around the 1 m capsule) and z = −8 to undo the
  nerfstudio frame's mirror. Box renders from the training-camera poses match the source video frames.
  Spawn is at the entrance half, facing the Round Table end. There is an invisible floor plus four walls
  (x ±2.9, z ±5.4); the reconstruction has no collision mesh.
- **Label and report:** the scene shows name · splat count · sort tier · credit. The overlay's Save report gains
  `splat_room`, `splat_loaded`, `splat_count`, `sort_tier`, `sort_every_nth_frame`, `sorts_issued` and
  `sort_dispatches_per_sort`. `sort_ms` reads "not instrumented (GPU)" because the sort runs inside the
  camera's command buffer, so there's no cheap CPU-side timing (fps/frame-time percentiles cover it).
- **Reaching it:** release builds still boot MovementTest and contain neither the scene nor the splat. In the
  internal-debug flavor, the overlay (three-finger tap) gets a scene-switcher row under Save report with one
  button per other build scene, so tap **SplatRoom**. The `GiganticJourneys.DeviceTest` assembly compiles only
  in the editor, development or `GJ_DEBUG` builds.
- **Known reconstruction limits (not sort bugs):** the entrance end (facing −z) is thin and murky. About 80
  frames of the doors segment were mis-registered in the pass-3 join. Low near-floor views show blobby floaters.
  Judge ordering and popping while facing the Round Table and the columns.

### Asset handling (public repo)
`secret-scan.yml` repo-hygiene rejects tracked `.ply/.splat/.spz/.ksplat` ("privacy and size"), and
corpus media is not kept in git. Committing the converted Unity `.asset/.bytes` would sidestep that rule, not follow
it, so **no splat data is committed**. Instead:
- The converted package (deterministic tar.gz, 30,354,343 bytes, sha256 `2bba3810…1618cf`) lives in the
  **private** staging bucket `environments` at `_devtest/medieval-great-hall-winchester/splat-room-unity.tar.gz`.
  A public fetch is refused.
- Right before dispatch, gj-operator mints a ≤15-min signed URL on the box and passes it as the
  `ios-build.yml` input `splat_url`. CI reads it from the event file, masks it, downloads it, verifies size and
  SHA-256 against `unity/Assets/GiganticJourneys/DeviceTest/splat-room.json`, and unpacks only that room's
  asset files into a gitignored `Resources` folder. No Supabase key or Modal token is in CI (SECURITY_CHECKLIST
  §2.3), and no new secret was added.
- `check-device-test` verifies the exported Xcode player data: the scene and splat are present only in
  internal-debug (and the splat only when a URL was given), never in release.
- Re-running the debug build with the splat needs a fresh URL. An internal-debug dispatch without `splat_url` still
  builds; the scene then says "splat not in this build".

Guards: EditMode `SplatRoomTests` (descriptor, scene wiring, build-list exclusion, debug-only assembly, gitignore,
local-asset match, switcher, report hook), PlayMode `SplatRoom_SpawnsCharacterOnFloor_AndReportsTheRoom` (passes with
and without the asset, and on Vulkan with it), and pytest `test_ios_debug_flavor.py` (fetch/verify/unpack,
add-scene, export check). Box render: Vulkan follow view, 93.5% of pixels covered by splats.

## Device check of build 48 and the v2 room (2026-10-03)
**Owner's result on the iPhone 14 (build 48):** it renders and Tier B is engaged (the label says "Tier B"). It ran at **20–23 fps**
(p99 frame time 43–48 ms; one portrait shot showed 40 fps), so it fails AT-3 against 60. The view was blurry, with
large floaters and needle-like overexposed splats near the floor, and the orange capsule turned partly or fully
black among the splats. He asked to be able to change the view angle independently of movement.

**Fixes (commits bd469b4, 3d07bae), first shipped in internal-debug TestFlight build **50** (run 37167356135):**
- **Black character, root cause:** the package composite (`Hidden/Gaussian Splatting/Composite`) returns
  `col.rgb / col.a`. Where every splat is behind an opaque object (the capsule), the splat buffer is (0,0,0,0), so
  the result is 0/0 = NaN. On Metal (half precision) that NaN survives the `SrcAlpha` blend and writes black. The box
  (Vulkan) doesn't show it. That's why the black area follows the capsule outline exactly and why splats in front of it
  (alpha > 0) "fix" parts of it. The GJ shader `Splats/Shaders/GJSplatCompositeSafe.shader` discards pixels with
  alpha < 1/255 (a NaN-safe test) and clamps the un-premultiplied colour, which also stops faint fringes from blowing
  out to white. The package stays unmodified: `GaussianSplatRenderer.m_ShaderComposite` points at it
  (`SampleSplat.AssignRendererResources`). Lighting wasn't the cause: the scene has a sun and trilight ambient.
- **Splat cleanup (offline):** `services/reconstruction/tools/prune_splat_ply.py` (rules in `splat_ops.DisplayPrune`,
  pytest-pinned) on the pass-3 `splat.ply`: 780,004 → **400,000**. Removed: alpha < 0.1 (138,764), largest axis above
  the 98.5th percentile (9,619), needles with anisotropy > 20 and largest axis above the 80th percentile (14,269),
  outside the robust 0.5–99.5% box (7,636), and isolated splats with < 12 in their 3×3×3 cell neighbourhood on a 160³
  grid (19,610). Then the 400,000 most opaque were kept. The training cap's `importance()` favours big splats, which
  are exactly what this removes, so it isn't used here. A dark floor 0.25 m below the walk plane and a warm dark
  background fill the gaps that the old floor floaters used to cover.
- **Performance profile** (descriptor fields, applied by the loader on top of the High tier the iPhone runs):
  - Render scale **0.7** in players. It scales the URP target, so the splat pass's fill rate and overdraw drop about 2×,
    and it is restored when the scene unloads.
  - **SH order 1**: cheaper view data, less view-dependent sparkle.
  - **Tier B sort at most every 2nd frame, and only after 3 cm / 1.5° of camera motion** (`MetalSafeSplatSort.resortMoveMeters` /
    `resortAngleDeg`; a still camera keeps a valid order, so standing still costs no sort).
  - **MSAA and HDR off on the room camera.** The splat pass is an unsafe render-graph pass, so a 4× MSAA HDR target is
    stored and reloaded around it every frame.
  - Together with the halved splat count, these target the sort (about 2.4× fewer elements, sorted only when moving)
    and the fill rate (0.49× pixels, no MSAA, fewer large splats). New report lines: `render_scale`, `sh_order`,
    `sorts_skipped_still`, `resort_threshold`, `camera_msaa_hdr`.
- **Orbit camera:** see the build note in `ios-lane.md`. Drag on the right or empty part of the screen to orbit, pinch to
  zoom.
- **Box check:** `/workspace/splat-check-v2.png` on the box (not committed; it's a render of CC BY corpus content),
  before (780K) vs after (400K) from the device-aspect follow view at the spawn, mid-hall facing the side wall, and the
  overview. The Round Table end now reads clearly from the spawn, and the floor streaks are gone. Holes remain where
  the capture is thin (side walls, entrance end).
- **Package:** `environments/_devtest/medieval-great-hall-winchester/splat-room-unity-v2-400k.tar.gz`
  (private bucket, 15,675,479 bytes, sha256 `64b182c8…bfabc`, pinned in `splat-room.json`). Same handling as v1:
  operator-minted ≤15 min signed URL, no key in CI.

## Device check of build 50 and the v3 room (2026-10-04)
- **Build 50 on the Owner's iPhone 14** (evidence `qa/evidence/M1-UNITY-01/`): AT-2 PASS (Tier B order correct, no
  popping while orbiting), AT-3 fps p50 60.0 / avg 57.8, frame p99 33.4 ms, 400K splats, render 0.70. The capsule now
  shades normally. Still smeared near the floor, columns and entrance, with white blobs and dark shapes where the video
  never looked; the Round Table end is sharp.
- **Sort cadence:** the report said `sort_every_nth_frame: 1`. `SplatRenderSettingsApplier.OnEnable` re-applied the High
  tier's cadence after the Metal-safe sort parked the package sort. Fixed in `05eda83` (applier overrides for SH order
  and cadence). The report now splits frame times into `frame_ms_after_sort`, `frame_ms_after_label` and
  `frame_ms_other`, so the next device report shows whether the p99 spikes are sort frames. The sort is not spread
  across frames yet. If the split points at sort frames, that is the next step.
- **Retrain (Modal L40S, `modal_app.py::retrain`, frames and COLMAP model reused):**

  | run | recipe | splats | held-out PSNR / SSIM / LPIPS | cost |
  |---|---|---|---|---|
  | v1 (pass 3) | splatfacto 10k | 780,004 | 24.93 / 0.842 / 0.278 | - |
  | `quality-30k` | 30k, antialiased rasterize, bilateral grid (per-image exposure/colour), scale regularisation | 828,710 | 23.70 / 0.832 / **0.253** | $0.60 |
  | `quality-30k-camopt` | same + SO3xR3 pose refinement | 732,623 | 17.76 / 0.643 / 0.406 | $0.68 |

  The bilateral grid is applied only during training. Eval frames get the base colours, so PSNR is penalised for the exposure
  differences the grid absorbs, and LPIPS (structure) is the fairer number. The camopt run's held-out poses are not refined,
  so its eval views are visibly offset; rejected. nerfstudio 1.1.5 splatfacto has no depth/normal loss without depth data,
  and opacity resets are on by default; no extra floater term was added.
- **Box comparison** (`/workspace/splat-v3-compare.png` on the box, not committed: renders of CC BY corpus content).
  v2 = v1 pruned to 400K. v3 = `quality-30k` pruned 828,710 -> 400,000 (`tools/prune_splat_ply.py`, defaults). Same three
  `SplatRoomScene.Screenshot` views plus held-out eval view 6 (source | v1 | v3). v3 is sharper (Round Table, columns,
  windows, floor texture; Laplacian variance 0.0039 -> 0.0072 in the follow view), has fewer large white floor blobs in
  the overview (blown-out pixels 7.0% -> 6.3%) and loses the big white floater in eval view 6. Remaining: speckled floor
  fragments and dark gaps beside the left column. The mid-hall side view is outside the captured zone and is bad in both
  (the new camera limits keep the player out of it). **Shipped v3.**
- **Package:** `environments/_devtest/medieval-great-hall-winchester/splat-room-unity-v3-400k.tar.gz` (private bucket,
  15,067,234 bytes, sha256 `c9969c40…897e3c`, pinned in `splat-room.json`).
- **Camera and play-area limits (`3517ff8`):** `services/reconstruction/tools/room_limits.py` maps the COLMAP training
  cameras into the splat's frame (the nerfstudio dataparser transform; points land on the splat with a median 1 mm NN
  distance). It counts how many camera frustums see each floor cell and writes the limits into `splat-room.json`.
  - Walk area: x -2.26..2.39, z -3.86..0.79 m (largest rectangle seen by >= 8 cameras).
  - Spawn: (-0.05, 0.02, -3.03), yaw 4.4°.
  - Camera box: walk area + 1 m, y 0.25..4.46.
  - Orbit pitch: -10..22.6°.
  - Zoom: 0.6..1.3x.
  - View yaw: 4.4° ± 45°. The 20 cameras that see the walk area all look +z, with pitch -17..21°.
  - Occluder walls on the thin-coverage sides: x = -3.36 and x = 3.49, each 4.96 m high and 7.05 m long, drawn with
    the floor material.
  - `FollowCamera` pulls the eye back into the camera box and sphere-casts (r 0.15 m) against walls/occluders.
- **Not fixed by training:** regions the video never saw. Research spike `M1-PIPE-02` (generative repair agent) covers
  them.

## Free-look camera mode (2026-10-04, after build 54)
- **Owner feedback on build 54:** in SplatRoom he can't turn the camera fully, the way he can in the sample scene; he
  wants every direction and angle. He also still sees a fair amount of blur and fragmented shapes and lights.
- **Per-room `cameraMode`** in `splat-room.json`:
  - `"coverage"` (the default) keeps the training-camera limits from `room_limits.py`.
  - `"free"` gives full 360° yaw plus the `freeOrbit` pitch and zoom range.
  - Both modes keep the walk area, the camera box (x/z and top), the occluder walls and camera collision.
  - The coverage values stay in the file, so a room can switch back.
- **Winchester now uses `"free"`:** yaw 360°, eye elevation -60..80°, zoom 0.5–2.5×.
- **Camera fixes that came with it:**
  - The eye never drops under the ground beneath the character (`EyeAboveGroundM` 0.02 m). The 0.15 m collision
    sphere is bigger than the miniature character's half height, so the sphere cast alone started inside the floor.
  - The camera box now bounds x/z and the top even when the look-at point sits below the box floor. For the 0.15 m
    character it always did sit below, so the box had not been clamping in the room.
- **Trade-off:** free look shows what the capture never saw. M1-PIPE-02 phase 1 (`weak_regions.py`) finds 83% of the
  occupied cells within 4 m of the camera box weak (median 2.7 training views), against 2% in the walk area. The
  blur and fragments the Owner reports sit there. Phase 2 is the repair route; the coverage mode is the fallback.

## AT-4 — LOD / chunked streaming (specification)
aras-p has neither LOD nor streaming. The plan uses its 256-splat chunks (`m_GpuChunks`, already used for
quantization bounds):
1. **Cells.** The reconstruction service cuts each room splat into spatial cells (about 2 m cubes, Morton-ordered)
   and writes one asset per cell per LOD: L0 is full, L1 keeps the 25% most opaque×large splats (MCMC
   importance), L2 keeps 6%. L1/L2 SH order is 0. Each cell has a manifest entry with bounds, splat count per LOD and byte size.
2. **Selection** (per frame, CPU, by `SplatRenderSettingsApplier`'s culling tick): frustum-cull cells, then pick
   a LOD by projected size (screen-space radius of the cell bounds vs 0.25 / 0.08 of the screen height). A
   **global splat budget** (the tier's `maxSplats`) is filled nearest-first, and further cells drop a LOD
   until the budget holds. ±10% hysteresis stops LOD thrash.
3. **Streaming.** Cells load asynchronously through signed URLs (AT-5) into a per-cell `GaussianSplatRenderer`.
   An LRU cache sized to 1.5× the tier budget evicts the farthest cells. A cell that hasn't loaded yet draws its L2 (prefetched with the
   manifest), so nothing pops to empty.
4. **Sorting across cells.** Each cell renderer sorts itself (Metal-safe sort per cell, smaller n = faster),
   and the package draws renderers far-to-near by object depth (`GatherSplatsForCamera`). Cells are convex
   and don't overlap, so per-cell sorting plus far-to-near cell order is correct apart from splats that straddle a cell
   border. The service assigns each splat to exactly one cell by its centre, which is acceptable at 2 m.
5. **Budget numbers:** High has a 2.5M on-screen budget, Medium 1.5M, Low 1.0M (`SplatRenderSettings.asset`). Package ≤150 MB holds
   because only L2 of every cell is bundled; L0/L1 stream.

## AT-5 — signed URLs (open)
The spike uses bundled assets. The runtime-created asset loaded from a ≤15 min signed URL after an authz check
(SECURITY_CHECKLIST §3.1) is not built yet. It needs the Supabase signed-URL endpoint, which is the other
worker's lane, and lands with the streaming loader above.
