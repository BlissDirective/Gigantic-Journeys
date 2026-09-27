# AUTH request — ADR-0001 addendum: Gaussian splat renderer package (M0-UNITY-02)

> **STATUS: AWAITING THE OWNER'S CONFIRMATION OF THIS TEXT.** Filed by gj-operator, 2026-09-27. The Operator was told the Owner approved "the M0-UNITY-02 design change" on 2026-09-27, but no written addendum proposal or Pending AUTH row existed in the repo to attach that approval to (searched `ADRs/`, `design/proposals/`, `governance/`, the ticket history, `PROGRESS.md`, and every file mentioning M0-UNITY-02 or "addendum"). A design-change approval must name the exact file and section it covers (`AUTHORIZATION_LOG.md`, "How to use this log"), and Bots never write the Decisions table, so **no AUTH number has been assigned and `ADRs/0001-engine-and-rendering.md` is unchanged.** Reply `APPROVED: ADR-0001 addendum (M0-UNITY-02)` (or with changes); the Coordinator logs it as the next free number (currently #035), pastes the addendum below into ADR-0001 § Addenda citing that number, and sets the ticket's `auth_required[0]` to approved.

```
AUTH REQUEST (next free #, currently #035)
Type: design-change (protected path: ADRs/0001-engine-and-rendering.md § Addenda)
What: Record the splat renderer package choice as ADR-0001 addendum 1 (text below).
Why: ADR-0001 defers the exact package, commit and license to M0-UNITY-02 "under its own AUTH";
     M0-UNITY-02 AT-4 needs the addendum and its APPROVED #n.
Cost: $0 (MIT open source)
Reversible: yes (swap the manifest pin; the sample and settings asset are renderer-neutral in shape)
Waiting on: Owner
```

**Blocks:** M0-UNITY-02 AT-4 (the ticket's other required criteria are met; it is in-review).

## Proposed addendum text (to paste under `## Addenda` in ADR-0001)

> **Addendum 1 (2026-09-27, APPROVED #___, ticket M0-UNITY-02): splat renderer package.**
> - **Package:** aras-p/UnityGaussianSplatting, UPM id `org.nesnausk.gaussian-splatting` (package.json version 1.1.1), added to `unity/Packages/manifest.json` as `https://github.com/aras-p/UnityGaussianSplatting.git?path=/package#2c6fed37da67a217367261fcfcd3316d34c73e76`, i.e. pinned to **commit `2c6fed37da67a217367261fcfcd3316d34c73e76`** (upstream `main`, 2025-10-17: v1.1.1 plus the Aug 2025 fixes for blending splats with the skybox and other objects). `packages-lock.json` records the same hash. Needs the built-in `com.unity.modules.vr` 1.0.0 (the renderer references `XRSettings`); its Burst, Collections and Mathematics dependencies resolve to the versions already locked.
> - **License:** MIT (© 2023 Aras Pranckevičius; `LICENSE.md` ships inside the package). Bundled third-party code is MIT as well: the GPU radix sort (DeviceRadixSort, Thomas Smith / b0nes164 GPUSorting) and the JSON parser (Alex Parker); every other source file is SPDX `MIT`. Compatible with a closed-source commercial app (SECURITY_CHECKLIST §7.3).
> - **Integration:** URP 17 render graph (Compatibility Mode off) through the package's `GaussianSplatURPFeature`, added to all three tier renderers by `ProjectSetup.EnsureSplatFeature`. LOD and culling knobs live in one ScriptableObject, `Assets/Settings/SplatRenderSettings.asset`, applied by `SplatRenderSettingsApplier`.
> - **Known limitation:** the package's global GPU radix sort (DeviceRadixSort, which needs wave intrinsics, so it runs only on Vulkan, Metal and D3D12) misbehaves on Apple Metal (upstream issue #226, open). It also has no LOD or streaming. On-device iOS correctness and 30/60 fps belong to M1-UNITY-01 (sort replacement: global bitonic, then tile-local or a native Metal plugin; `unity/docs/splat-render-integration.md`). If that work replaces the sort, the fork or patch is recorded as a further addendum.
> - **Fallback:** on low-end devices, or while the Metal sort is unresolved, environments render as **textured-mesh visuals from the collision mesh** (plan §8), per quality tier.
> - **Alternatives kept open:** scier/MetalSplatter (MIT, native Metal plugin) and rayanht/msplat (Apache-2.0, tile-local bitonic sort) are fallbacks for the iOS path, not v1 dependencies.
