# gj-capture — Resources (curated foundation)

Curated, verified starter set for mobile capture + Gaussian-splat reconstruction. Expand to the full annotated top-100 in a live pass. All entries real/canonical.

## Gaussian splatting (core)
- Kerbl et al., "3D Gaussian Splatting for Real-Time Radiance Field Rendering" (SIGGRAPH 2023) — the foundational method. ⚠ INRIA reference **code is non-commercial** (paper is fine to study).
- gsplat — github.com/nerfstudio-project/gsplat (Apache-2.0) — our trainer library; JMLR paper (jmlr.org).
- Nerfstudio / Splatfacto — docs.nerf.studio — end-to-end training pipeline.
- Brush — github.com/ArthurBrussee/brush (Apache-2.0) — Rust/wgpu trainer (secondary adapter).

## SfM & mesh
- COLMAP — colmap.github.io (BSD) — feature/match + incremental SfM.
- GLOMAP — github.com/colmap/glomap (BSD) — global SfM, ~3.5× faster ("Global SfM Revisited", arXiv 2407.20219).
- Open3D — open3d.org (MIT) — point cloud + mesh (Poisson/TSDF).

## Compression / mobile delivery
- Niantic spz — github.com/nianticlabs/spz (MIT) — ~10× compact splat container.
- PlayCanvas SOGS + splat-transform — github.com/playcanvas/splat-transform (MIT) — ~20× compression, format conversion.
- Mobile-GS (xiaobiaodu.github.io/mobile-gs-project) — distillation for phone-class rendering.

## Capture UX & AR
- Apple — ARKit docs (developer.apple.com/documentation/arkit) — poses, depth, scene reconstruction.
- Google — ARCore docs (developers.google.com/ar).
- Polycam / Scaniverse / Luma — study their in-app capture guidance UX (product apps).

## Reference internal
- `research/vendors/reconstruction-cost-and-trainer-analysis.md`, `reconstruction-selfhost.md`, `reconstruction-alternatives.md`; `services/reconstruction/`.
