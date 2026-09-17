# Reconstruction — build/self-host feasibility

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Can we run our own scan → Gaussian-splat/mesh pipeline instead of a vendor API? Sourced; not legal/IP advice (a brief IP check before commercial launch is prudent).

## Verdict: FEASIBLE-WITH-EFFORT (and legally clean) for a solo dev + AI agents

A mature, **commercially-licensed** self-host stack exists. Licensing is **not** the blocker (avoid INRIA; use the Apache/BSD reimplementations). The real cost is **ops/reliability** and the **immature iOS-in-Unity splat render path** — not the reconstruction itself. Compute is cheap (**<$1/scan**), and **≤10-min p50 is achievable** with ARKit-seeded poses.

**Biggest strategic upside:** user home imagery **stays on infrastructure we control** (a genuine BIPA/privacy win) and there is **zero vendor-deprecation risk** — the exact Luma failure mode this avoids.

## Recommended stack (all commercially licensed)
```
ARKit capture (video/photos + intrinsics + poses + depth)
  → COLMAP/GLOMAP triangulation SEEDED by ARKit poses   [BSD]
  → gsplat / Splatfacto (Nerfstudio) OR Brush            [Apache-2.0]
  → export .ply/.spz + prune/compress to mobile budget
  → collision mesh via Open3D Poisson/TSDF on depth      [MIT]
  → CDN → Unity 6 URP loader (aras-p renderer, MIT viewer)
```
- **Primary:** COLMAP + Nerfstudio/gsplat on rented NVIDIA GPUs (best-documented automated path).
- **Alternative to prototype:** **Brush** (Apache-2.0, Rust/wgpu) — single portable binary, "as fast as gsplat," fewer moving parts; a hedge against CUDA/driver ops pain.
- **ARKit poses are the key lever for ≤10 min:** known intrinsics/poses skip COLMAP's slow exhaustive matching (Nerfstudio ingests `transforms.json` and can skip COLMAP). Caveat: raw ARKit poses drift on larger rooms → budget a light global refinement (GLOMAP).

## Licensing (the critical question) — clean if we avoid INRIA
| Component | License | Commercial closed-source? |
|---|---|---|
| **INRIA 3DGS** + its CUDA rasterizer, **SuGaR** | Non-commercial research | **NO — BLOCKER, avoid entirely** |
| **gsplat / Splatfacto / Nerfstudio** | Apache-2.0 (clean-room) | **YES** |
| **Brush** (wgpu) | Apache-2.0 | **YES** |
| **COLMAP / GLOMAP** | BSD-3 | **YES** |
| **Open3D** (mesh) | MIT | **YES** |
| Unity **aras-p** splat renderer | MIT (viewer) | **YES** (train with gsplat/Brush, not INRIA) |

INRIA license blocker verbatim: *"THE USER CANNOT USE, EXPLOIT OR DISTRIBUTE THE SOFTWARE FOR COMMERCIAL PURPOSES WITHOUT PRIOR AND EXPLICIT CONSENT OF LICENSORS."* Train with **gsplat/Brush** and derive the collision mesh with **Open3D/2DGS**, never SuGaR. Residual caveat: this covers the *code/weights* license (the Apache stack avoids it); no clear public 3DGS *method* patent grant/restriction found — a brief IP check pre-launch is prudent.

## Cost & performance — comfortably in budget
- **GPU rental (2026):** H100 ≈ $1.49–3.00/hr; A100 80GB ≈ $0.67–1.49/hr (RunPod / community tiers).
- **Train time:** gsplat 7K iters ~3.4 min / 30K ~19.4 min on hard *outdoor* scenes; an **indoor room/tabletop at capped resolution + ~7–15K iters + ARKit-seeded poses on an H100 → ≤10 min p50 realistically**; FastGS-class tricks reach ~100 s if needed.
- **Cost/scan:** ~10 GPU-min ⇒ **~$0.25–0.75/scan** (well under $1). p99 latency + reliability is the concern, not p50 or cost.
- **Quality:** strong on textured indoor/tabletop; weak on reflective/transparent/textureless/thin structures. ARKit depth prior + 2DGS mesh regularizers help. Expect scan-to-scan variance.

## Effort & risk (solo dev + agents)
- **Scope:** ARKit capture (client) → signed upload → job queue + GPU autoscaling → containerized worker (COLMAP + gsplat/Brush + Open3D) → export/prune/compress → CDN → Unity loader + quality gate.
- **Estimate:** happy-path MVP ~2–4 weeks; production-reliable (retries, timeouts, cost caps, quality gating on bad scans, monitoring, cold-start) ~2–4 months part-time, plus ongoing maintenance.
- **Top risks:** (1) p99 robustness (bad captures, pose drift, non-convergence → need auto-detect + fallback); (2) GPU ops burden on a solo team; (3) quality variance vs a tuned vendor; (4) patching.

## Mobile rendering (Unity 6 / iPhone) — the weakest link, but feasible
- Licensing/format fine: aras-p **UnityGaussianSplatting** is MIT, supports Unity 6 + URP (Render Graph Compatibility Mode off), reads `.ply`.
- **iOS is the risk:** its readme says iOS "definitely don't work" out of the box — the compute-shader **radix sort needs Metal wave/subgroup ops**. Community reports get it running on Metal at a **~200–500K-splat / 30 fps budget**; native **MetalSplatter** (MIT) proves Metal renders splats well outside Unity.
- **Implication:** the server must **aggressively prune/compress** Gaussians (target a few hundred K, `.spz`/compressed `.ply`) to meet both the **≤150 MB package** and mobile fps — a hard requirement. Budget real engineering (or a native-plugin/MetalSplatter fallback) for the Metal sort. **This render maturity, not reconstruction or licensing, is the item most likely to bite.**

## Recommendation
Feasible and legally clean with **COLMAP/GLOMAP + gsplat/Splatfacto (or Brush) + Open3D**. Reserve the risk budget for **iOS-in-Unity rendering** and **production reliability/quality-gating**. **De-risk with a 1–2 week spike:** capture a real room → Brush/gsplat train → prune → render on a physical iPhone in Unity 6 URP, before committing.

## Sources (observed 2026-09-17)
- INRIA 3DGS license — https://github.com/graphdeco-inria/gaussian-splatting/blob/main/LICENSE.md · SuGaR — https://github.com/Anttwo/SuGaR
- gsplat — https://github.com/nerfstudio-project/gsplat/blob/main/LICENSE · Nerfstudio — https://github.com/nerfstudio-project/nerfstudio · custom data — https://docs.nerf.studio/quickstart/custom_dataset.html
- Brush — https://github.com/ArthurBrussee/brush · COLMAP — https://colmap.github.io/ · GLOMAP — https://github.com/colmap/glomap
- aras-p UnityGaussianSplatting — https://github.com/aras-p/UnityGaussianSplatting · MetalSplatter — https://github.com/scier/MetalSplatter · iOS Metal sort issue — https://discussions.unity.com/t/3d-gaussian-splat-viewer-on-ios-compute-sorting-problems-on-metal/1713103
- GPU pricing — https://www.runpod.io/pricing · gsplat paper — https://arxiv.org/pdf/2409.06765
