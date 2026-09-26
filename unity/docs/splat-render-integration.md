# iOS Splat-Render Integration — Runbook (M1-UNITY-01)

`unity/docs/splat-render-integration.md` · 2026-09-26 · Implementation runbook for the render-first spike. Companion to the plan `design/proposals/ios-splat-render-v1.md` and the spike report `research/vendors/reconstruction-spike-report.md` (§1). Executed by gj-operator (Unity Editor + macOS + a physical iPhone); Builder owns the code.

> **Goal:** get a reconstructed Gaussian splat rendering **correctly depth-sorted at 30 fps on a physical iPhone** in Unity 6 URP. Input: the smoke-test `smoke.spz` from the Modal run (M1-CAPT-03). The #1 program risk is the **per-frame Metal depth sort**, not rasterization.

## What you need
- Unity 6 — the pinned editor in `unity/ProjectSettings/ProjectVersion.txt` (currently `6000.0.84f1`), project at `unity/`.
- A `.spz` (or `.ply`) splat — start with the M1-CAPT-03 `smoke.spz`.
- The iOS build path already wired: `.github/workflows/ios-build.yml` (Linux export → macOS archive → TestFlight). Install on the iPhone via the internal TestFlight group.
- Licenses (all clean): aras-p/UnityGaussianSplatting **MIT**, Niantic spz **MIT**, rayanht/msplat **Apache-2.0**, scier/MetalSplatter **MIT**. Record any package add in SECURITY_CHECKLIST §7.4 terms (version + license).

---

## Step 1 — Add the renderer package
Add aras-p/UnityGaussianSplatting to `unity/Packages/manifest.json`, **pinned** (confirm the exact package id and a release tag against the repo before committing; do not float on a branch — §7.1):

```json
"org.nesnausk.gaussian-splatting": "https://github.com/aras-p/UnityGaussianSplatting.git?path=/package#v1.1.1"
```

Then commit the updated `packages-lock.json`. If the Editor cannot resolve the git dependency in CI, vendor the `/package` folder under `unity/Packages/` instead and pin by commit SHA.

## Step 2 — URP wiring (Unity 6 render graph)
1. Render graph **Compatibility Mode OFF** (Project Settings → Graphics → Render Graph). aras-p's URP path requires it off on Unity 6.
2. Add the **`GaussianSplatURPFeature`** renderer feature to the URP renderer asset(s) created by `ProjectSetup.cs` — at minimum `Assets/Settings/URP-High-Renderer.asset` (the iOS default tier); add to Low/Medium too if you want splats in every tier.
3. Confirm graphics APIs = Metal (already asserted by `ProjectSettingsSmokeTests.IosUsesMetalOnlyAndIl2Cpp`).

## Step 3 — Bring a splat into the scene
1. Convert the splat to a `GaussianSplatAsset`: **Tools → Gaussian Splats → Create GaussianSplatAsset**, input `smoke.spz`, choose a compressed position/SH format for mobile (start "Very Low"/"Low" to stay small).
2. In the boot scene (`ProjectIdentity.BootScenePath`), add a GameObject with a **`GaussianSplatRenderer`** component; assign the asset. Frame it with the main camera.
3. **Cap the splat count to ~1–2.5M** for iPhone (re-export the asset at a budget, or use gsplat MCMC `--max-num-splats` upstream). This is the single biggest fps lever besides the sort.

## Step 4 — First device build = establish the baseline (expect the glitch)
Build to the iPhone via TestFlight (flip `TESTFLIGHT_ENABLED=true` once M0-UNITY-01 is merged — it is). Expect aras-p's **global GPU radix sort to glitch on Metal** (issue #226): splats render but depth ordering flickers/never settles. Confirm the **workaround baseline**: temporarily disable sorting (aras-p exposes a sort toggle / you can no-op the sort dispatch) → it should render *stably but visually wrong* on the iPhone (this matches the community reports and proves rasterization works; the sort is the only blocker). Record both in the spike report §1.

---

## Step 5 — The sort fix (ladder; stop at the first tier that hits 30 fps correctly)

Restating the constraint honestly: aras-p uses **one global sort of all splats by view depth per frame**, then draws instanced quads. Its radix sort (AMD FidelityFX-derived) misbehaves on Metal. The msplat "**tile-local bitonic sort**" (~350 fps on M4 Max) is fast because it is part of a **tile-based rasterizer** — each 16×16 tile sorts only its own ≤2048 splats in threadgroup memory. That tile architecture is **not** how aras-p works, so a true tile-local sort is a renderer rewrite, not a drop-in. Climb this ladder:

### Tier A — budget + measure (hours)
Hold the splat budget (~1–1.5M to start), keep aras-p as-is, and measure raster fps on device with sorting disabled (correctness wrong, but it tells you the rasterizer's ceiling). If even this can't clear ~30 fps at your budget, lower the budget / SH order before touching the sort.

### Tier B — swap the global sort for a Metal-safe **global bitonic sort** (the recommended first real fix)
This keeps aras-p's architecture and only replaces the *sort stage*: same input (a per-splat depth **key** + the splat **index**), same output (indices ordered back-to-front). A **Batcher bitonic sort** uses only simple compare-and-swap over global memory — no large-threadgroup radix reduction — so Metal handles it correctly. It's O(n·log²n) (slower than radix at big n), which is exactly why the splat budget matters; at ~1–2M it is usually fine for 30 fps.

Reference compute kernel (`Assets/GiganticJourneys/Runtime/Render/BitonicSort.compute`):

```hlsl
#pragma kernel BitonicSort
// x = sortable depth key (see FloatToSortableUint), y = splat index (payload).
RWStructuredBuffer<uint2> _Data;
uint _Count; // padded to a power of two
uint _K;     // outer stage size (2,4,8,...,Count)
uint _J;     // inner stride (K/2 ... 1)

[numthreads(256, 1, 1)]
void BitonicSort(uint3 id : SV_DispatchThreadID)
{
    uint i = id.x;
    if (i >= _Count) return;
    uint l = i ^ _J;
    if (l > i)
    {
        bool ascending = ((i & _K) == 0);
        uint2 a = _Data[i];
        uint2 b = _Data[l];
        if ((a.x > b.x) == ascending) { _Data[i] = b; _Data[l] = a; }
    }
}
```

Order-preserving float→uint for the key (so a uint sort == a float sort), and the dispatch loop:

```csharp
// key so that ASCENDING uint order == BACK-TO-FRONT draw order.
// Pack far-first: use (view-space distance) directly, or negate near-first depth.
static uint FloatToSortableUint(float f)
{
    uint u = math.asuint(f);
    uint mask = (u >> 31) != 0u ? 0xFFFFFFFFu : 0x80000000u;
    return u ^ mask;
}

// n must be padded to a power of two; fill padding with key=0xFFFFFFFF (sinks to the end).
void SortDispatch(ComputeShader cs, int kernel, ComputeBuffer data, uint n)
{
    int groups = (int)((n + 255) / 256);
    for (uint k = 2; k <= n; k <<= 1)
        for (uint j = k >> 1; j > 0; j >>= 1)
        {
            cs.SetInt("_Count", (int)n);
            cs.SetInt("_K", (int)k);
            cs.SetInt("_J", (int)j);
            cs.SetBuffer(kernel, "_Data", data);
            cs.Dispatch(kernel, groups, 1, 1);
        }
}
```

**Hook point in aras-p:** it computes per-splat view depth into a key buffer and calls its `GpuSorting` (radix) to produce the sorted index buffer each frame (see the sort dispatch in `GaussianSplatRenderSystem` / `GaussianSplatRenderer`). Replace that single radix call with `SortDispatch(...)` over the same `{key,index}` buffer (padded to a power of two). Confirm the exact buffer names/field against the pinned package source. Nothing else in aras-p changes.

Validate on device: depth ordering is now **stable and correct**; record fps @ splat count.

### Tier C — tile-local bitonic / native Metal plugin (only if B can't hit 30 fps)
If the global bitonic is too slow at the needed splat count, go tile-based. Two routes, both large:
- **Port msplat's approach:** a binning pass assigns splats to screen tiles, then one dispatch per tile sorts its ≤N splats in `groupshared` memory with a bitonic network, then per-tile blend. This is a rasterizer rewrite — treat it as adopting msplat, not editing aras-p.
- **Native Metal plugin:** wrap **MetalSplatter (MIT)** as a Unity native rendering plugin and hand it the splat + camera; it already renders correctly on iPhone. More integration plumbing (plugin bridge, render-target handoff) but the highest-confidence correctness.

Groupshared bitonic sketch (per-tile, for the port):

```hlsl
groupshared uint2 gTile[2048]; // one tile's splats: (key, index)
// load overlapping splats -> gTile; GroupMemoryBarrierWithGroupSync();
// bitonic network over gTile (k: 2..cap, j: k/2..1) with SV_GroupThreadID; sync each pass;
// then blend gTile front-to-back for this tile.
```

Decision rule: try A→B first; escalate to C only with device numbers showing B misses 30 fps at an acceptable splat budget. Log the decision in the spike report §5 (feeds an ADR-0005 addendum if it firms up).

---

## Testing on the phone — TestFlight (no Mac, no Xcode)
You test entirely through Apple's free **TestFlight** app on your iPhone — no Mac, no cable, nothing on a computer:
1. Install **TestFlight** from the App Store; sign in with the Apple ID that is an internal tester on the **Gigantic Journeys Internal** group (you're the Account Holder — add your Apple ID under App Store Connect → the app → TestFlight → Internal Testing if it isn't already).
2. With `TESTFLIGHT_ENABLED=true`, each CI run uploads the build via `fastlane pilot`; after Apple processing (usually minutes for internal testers — no beta review), it appears in TestFlight. Tap **Install/Update**, open **Gigantic Journeys**, and it runs like a normal app.
3. Loop: push → CI builds on the macOS runner → TestFlight → your phone, over the air.

Build two small things into the render test scene so the check is measurable **without a Mac** (Instruments/Xcode would need one; these don't):
- an **on-screen fps HUD** (debug only, behind `GJ_DEBUG`) showing fps + splat count;
- a **touch-drag orbit camera** so you can move around the splat and confirm depth ordering from multiple angles (the #226 glitch is angle-dependent).

## On-device test procedure (record in the spike report §1)
1. Build via `ios-build.yml` (TestFlight lane) → install from TestFlight on the iPhone.
2. Record: **correct depth-sorted splats? Y/N** (the gate for "solved"), **fps @ splat count**, **package MB** (≤150 target), device model + iOS version, and a short video.
3. Compare Tier A (unsorted, baseline) vs the chosen fix. Note thermal throttling over a 2–3 min run.

## Later (not the spike): signed-URL loading + security
For the spike a bundled `GaussianSplatAsset` is fine. In production the splat is delivered by a **signed URL, ≤15 min TTL, after an authz check** (SECURITY_CHECKLIST §3.1) and streamed into a runtime-created asset — never a direct storage URL, never committed media (§6.1). Track that under M1-UNITY-01 AT-5.

## Files this runbook implies (Builder to add once the Editor confirms the aras-p hook)
- `unity/Packages/manifest.json` + `packages-lock.json` — the pinned package.
- `unity/Assets/Settings/URP-*-Renderer.asset` — the URP feature added.
- `unity/Assets/GiganticJourneys/Runtime/Render/BitonicSort.compute` + a small C# dispatcher + the aras-p sort-stage swap (Tier B).
- Boot scene + `GaussianSplatAsset` for `smoke.spz` (do not commit large real media; the smoke asset is public-dataset-derived).
- `Assets/GiganticJourneys/Runtime/Debug/FpsHud.cs` (a `GJ_DEBUG` fps + splat-count HUD) and a touch-orbit camera on the splat test scene, so the on-device check is measurable without a Mac.
