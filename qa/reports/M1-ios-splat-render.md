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
  has one and it is not in the build list. M1-GAME-01 puts the golden scene in the build. Then check the log
  line `[GJ-SPLAT-SORT] engaged on Metal`.
- **AT-3:** sustained fps at about 1–2.5M splats, plus package MB, using the M0-UNITY-04 debug overlay
  (fps p50/p99, Save report). The bitonic sort is O(n log² n): if it misses 30 fps at budget, first raise
  `sortEveryNthFrame` to 2–3 on Medium (Low already uses 2; it is a per-tier knob), then escalate to Tier C per the runbook.

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
