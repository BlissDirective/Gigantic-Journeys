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
Build **(pending)** (internal-debug, run (pending)) adds a debug-only scene,
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
