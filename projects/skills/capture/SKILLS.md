# gj-capture — Working Handbook

Remit: room/tabletop capture UX + the reconstruction backend (scan → Gaussian splat + collision mesh). Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- Backend is **self-host, committed + prioritized** (ADR-0005 / AUTH #030); a managed bridge is conditional (written no-train + DPA + residency) and expected N/A. Luma rejected.
- Pipeline code: `services/reconstruction/` (M1-CAPT-03) — COLMAP/GLOMAP → gsplat (MCMC, fixed budget) → `.spz`/`.sog` (splat-transform) → Open3D mesh. gsplat-first, pluggable (Brush second). See `research/vendors/reconstruction-cost-and-trainer-analysis.md`.
- Capture UX + coaching = SPEC §3.1 (AUTH #025): readiness predictor + multi-pass "add a pass"; people handled by coaching + publish-time moderation (no on-device face detection).

## Principles
- **Coverage, overlap/parallax, sharpness, even light, tracking continuity** are the five capture-quality axes — gate before upload; coach the user to fix, don't just reject.
- **Strip location metadata on device** before upload (EXIF/XMP/QuickTime atoms), verify + strip again server-side (SECURITY_CHECKLIST §4).
- **Raw media never enters git**; delete raw scan media once derived assets exist (SECURITY_CHECKLIST §6.1). Corpus is Owner-supplied + consented (§6.5).
- Reconstruction is **one-time per environment, amortized over downloads** — optimize delivery (zero-egress CDN) more than per-scan compute.

## Techniques
- Room walkthrough vs tabletop orbital coaching scripts; enforce loop closure and overlap.
- Splat budget via gsplat **MCMC** (`--max-num-splats`); compress to `.spz` (~10×) / `.sog` (~20×); target ≤150 MB, ~1–2.5M splats for iPhone.
- GLOMAP over COLMAP for throughput (~3.5× faster global SfM); SfM is CPU-bound — don't waste GPU on it at scale.

## Pitfalls
- Low-texture walls / reflective surfaces break SfM — coach for texture/coverage; log failures with the readiness score + coverage map (M1-CAPT-02 AT-5).
- Over-optimizing reconstruction cost while bleeding on CloudFront egress — use R2/B2 (zero egress).
- Assuming iOS render "just works" — the Metal splat sort is the #1 risk (M1-UNITY-01), separate from capture/reconstruction.

## Checklist (pre-upload)
Coverage ✓ · overlap/parallax ✓ · blur ✓ · light ✓ · tracking continuity ✓ · location metadata stripped ✓ · size within upload limits ✓.

## Pointers
`services/reconstruction/` · `research/vendors/reconstruction-*.md` · `design/proposals/{capture-ux-coaching-v1,ios-splat-render-v1}.md` · `ADRs/0005-*` · SPEC §3.1 · SECURITY_CHECKLIST §4/§6.
