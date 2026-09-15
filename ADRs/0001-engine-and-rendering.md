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
(Package choice: pending M0-UNITY-02.)
