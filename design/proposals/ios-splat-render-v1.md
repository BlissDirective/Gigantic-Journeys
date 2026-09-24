# iOS Gaussian-Splat Render — Plan (v1)

`design/proposals/ios-splat-render-v1.md` · 2026-09-24 · Builder plan for **M1-UNITY-01**. Feeds M1-CAPT-03 AT-2 and the ADR-0005 addendum. Evidence base: `research/vendors/reconstruction-cost-and-trainer-analysis.md` (Part 3).

## Why this is its own ticket (the #1 program risk)

Reconstruction (gsplat) is the de-risked half of the backend. **Displaying** the splat is the unsolved half: as of Sept 2026 there is **no public demonstration of correctly depth-sorted Gaussian splats at 30 fps on a physical iPhone inside Unity.** This risk is **orthogonal to the trainer** — every trainer just emits a `.ply`/`.spz`/`.sog`; the failure lives in Unity's per-frame Metal depth sort. So it is separated from M0-UNITY-02 (the general renderer package) and driven render-first (Owner decision, 2026-09-24).

## The problem: per-frame depth sort on Metal

Gaussian splatting must re-sort every splat back-to-front by depth **each frame** for correct alpha blending. The de-facto Unity renderer, **aras-p/UnityGaussianSplatting (MIT)**, uses an AMD-FidelityFX-derived **GPU radix sort** that is fast on desktop but **glitches on Apple Metal** (issue #226, open Mar 2026; correct output only with sorting disabled = visually wrong). It also has **no LOD/streaming** (self-described "toy visualization").

Native proof that splats *do* run on iPhone:
- **scier/MetalSplatter (MIT)** — native Swift/Metal, iPhone/iPad/macOS/visionOS; reads PLY/SPZ.
- **rayanht/msplat (Apache-2.0)** — **tile-local bitonic sort** (each 16×16 tile sorts ≤2048 gaussians in threadgroup memory), ~350 fps on M4 Max. This is the sort technique that sidesteps the Metal radix-sort bug.

## Options

| # | Approach | Effort | Risk | Notes |
|---|---|---|---|---|
| A | **Fix aras-p's sort** — replace the global radix sort with a **tile-local bitonic sort** (msplat approach) inside the Unity compute path | Medium | Medium | Stays in Unity/URP; MIT base; reuses aras-p's rasterizer. Preferred first attempt. |
| B | **Native Metal plugin** — wrap MetalSplatter (MIT) as a Unity native rendering plugin, bypassing Unity's compute sort on iOS | High | Medium-low | Highest-confidence correctness (native proof exists); more integration work (plugin bridge, lifecycle, render-target handoff). Fallback if A stalls. |
| C | **Constrain the content** — narrow sort keys (32→16-bit) + hard splat budget so the existing sort behaves | Low | High | Not a standalone fix (the radix sort still glitches on Metal); a multiplier on A/B, not a substitute. |

## Recommended path

1. **Baseline (desktop):** integrate **aras-p (MIT)** in Unity 6 URP via `GaussianSplatURPFeature` (render graph; Compatibility Mode off). Confirm a corpus splat renders correctly in the Editor. Establishes the pipeline end-to-end.
2. **iOS correctness (the crux):** attempt **Option A** (tile-local bitonic sort) on a physical iPhone. If correctness or perf stalls, switch to **Option B** (MetalSplatter native plugin). Ship whichever gives correct depth ordering first.
3. **Perf + size (Option C as multiplier):** hold the room to **~1–2.5M splats** (gsplat MCMC budget), ship **SOG (~20×)** or **.spz (~10×)**, target **≤150 MB** and **≥30 fps**. Author **LOD / chunked streaming** ourselves (aras-p has none) for larger or multi-room scenes.

## Acceptance (see M1-UNITY-01)
- Correct, non-glitching, depth-ordered splats on a **physical iPhone** in Unity 6 URP (the gate for "solved").
- Recorded splat count / package MB / fps against the ≤150 MB & 30 fps targets (measurements are suggested evidence, SPEC §11).
- Splats delivered only via **signed URLs** (SECURITY_CHECKLIST §3.1).

## Dependencies & licensing
- Depends on M0-UNITY-01 (Unity scaffold), M0-UNITY-02 (renderer package), M1-CAPT-03 (produces the splat). Needs the first Editor open + `UNITY_LICENSE`, a Mac (Xcode), and a physical iPhone.
- All render components are MIT/Apache-2.0 (aras-p MIT, MetalSplatter MIT, msplat Apache-2.0, spz MIT).
