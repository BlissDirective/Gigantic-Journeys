# ADR-0001: Engine and rendering: Unity 6, URP, a Gaussian splat renderer package

Date: 2026-09-15 · Status: Accepted (recorded from plan §1 and kit §3.1, §3.3) · Authorization: APPROVED #000 · Owner Bot: gj-gameplay (project), gj-capture (splat renderer)

## Context
One codebase for iOS and Android with photoreal Gaussian-splat environments, a 30 fps floor on a 2023 mid-tier Android, and a team of Bots that must drive the editor headlessly.

## Decision
Unity 6 (6000.x LTS, exact version pinned in `unity/ProjectSettings/ProjectVersion.txt`) with the Universal Render Pipeline, IL2CPP, Vulkan and Metal. Environments render through a Unity Gaussian splat renderer package (MIT or compatible license; aras-p UnityGaussianSplatting lineage is the candidate). The exact package, commit, and license are recorded as an addendum to this ADR by ticket M0-UNITY-02 under its own AUTH. Fallback on low-end devices: textured-mesh visuals from the collision mesh (plan §8).

## Alternatives considered
- Unreal: heavier mobile footprint, weaker headless Bot tooling. Godot: splat renderer and mobile toolchain less mature.
- Writing our own splat renderer: not in scope before M1 proves the product.

## Consequences
Unity Personal until revenue, then Pro (kit §7). CI runs `-batchmode` tests and builds through game-ci. Splat LOD and culling become the first performance workstream (plan §8).

## Follow-ups
M0-UNITY-01, M0-UNITY-02, M0-UNITY-03.

## Addenda

> **Addendum 1 (2026-09-27, APPROVED #035, ticket M0-UNITY-02): splat renderer package.**
> - **Package:** aras-p/UnityGaussianSplatting, UPM id `org.nesnausk.gaussian-splatting` (package.json version 1.1.1), added to `unity/Packages/manifest.json` as `https://github.com/aras-p/UnityGaussianSplatting.git?path=/package#2c6fed37da67a217367261fcfcd3316d34c73e76`, i.e. pinned to **commit `2c6fed37da67a217367261fcfcd3316d34c73e76`** (upstream `main`, 2025-10-17: v1.1.1 plus the Aug 2025 fixes for blending splats with the skybox and other objects). `packages-lock.json` records the same hash. Needs the built-in `com.unity.modules.vr` 1.0.0 (the renderer references `XRSettings`); its Burst, Collections and Mathematics dependencies resolve to the versions already locked.
> - **License:** MIT (© 2023 Aras Pranckevičius; `LICENSE.md` ships inside the package). Bundled third-party code is MIT as well: the GPU radix sort (DeviceRadixSort, Thomas Smith / b0nes164 GPUSorting) and the JSON parser (Alex Parker); every other source file is SPDX `MIT`. Compatible with a closed-source commercial app (SECURITY_CHECKLIST §7.3).
> - **Integration:** URP 17 render graph (Compatibility Mode off) through the package's `GaussianSplatURPFeature`, added to all three tier renderers by `ProjectSetup.EnsureSplatFeature`. LOD and culling knobs live in one ScriptableObject, `Assets/Settings/SplatRenderSettings.asset`, applied by `SplatRenderSettingsApplier`.
> - **Known limitation:** the package's global GPU radix sort (DeviceRadixSort, which needs wave intrinsics, so it runs only on Vulkan, Metal and D3D12) misbehaves on Apple Metal (upstream issue #226, open). It also has no LOD or streaming. On-device iOS correctness and 30/60 fps belong to M1-UNITY-01 (sort replacement: global bitonic, then tile-local or a native Metal plugin; `unity/docs/splat-render-integration.md`). If that work replaces the sort, the fork or patch is recorded as a further addendum.
> - **Fallback:** on low-end devices, or while the Metal sort is unresolved, environments render as **textured-mesh visuals from the collision mesh** (plan §8), per quality tier.
> - **Alternatives kept open:** scier/MetalSplatter (MIT, native Metal plugin) and rayanht/msplat (Apache-2.0, tile-local bitonic sort) are fallbacks for the iOS path, not v1 dependencies.
