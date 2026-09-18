# `research/rnd/` — V2 custom-avatar R&D track (charter)

**Status: V2 research track · charted 2026-09-18 · AUTH #020 deferred custom avatars to V2 · not on the v1 critical path.** v1 ships pre-made characters (ADR-0006); this track builds the "become a recognizable version of yourself" feature for V2. It graduates into the product only when it clears the gates below. This is a charter, not an authorization to spend — compute and any capture program need their own AUTH when started.

## Goal
A **premier, identity-preserving 1:12 avatar** generated from a player's photos/video, riggable to the GJ humanoid skeleton, recognizable in a blind test, generated in under ~2 minutes, and — decisively — **processed on infrastructure we control** so biometric data never reaches a third party (the cleanest BIPA/CUBI/MHMDA posture, and the reason to own it rather than rent it).

## Data — the legitimate, higher-quality path
- **Synthetic-first (primary for a first shippable model).** Render 200k–1M labeled faces/bodies from **ICT-FaceKit (MIT)** and **FLAME-2023-Open (CC-BY geometry)** with domain randomization (identity, expression, lighting, skin, hair, glasses, camera). Perfect 3D labels, unlimited volume, **zero consent/licensing issues**. This is the data engine — pure engineering.
- **Post-launch opt-in real data.** Users who turn on the (separate, default-off) training toggle contribute derived, de-identified data over time, closing the synthetic→real domain gap legitimately.
- **Optional consented capture program (later).** Paid volunteers with explicit biometric + ML-training consent + model release; a real-data layer if needed.
- **NOT stock/scraped faces.** Most stock licenses forbid AI training, and the people never consented to biometric-model training — this is the Clearview/BIPA fact pattern and would make the model a liability, not an asset. Excluded.

## Licensing (the real constraint — audit every file)
- Commercial-clean **bases only**: ICT-FaceKit (MIT), FLAME-2023-Open (CC-BY). FLAME **textures/albedo**, DECA/EMOCA/MICA **weights**, BFM, SMPL/-X, PIFuHD/ECON, PanoHead/Next3D are **non-commercial** — do not ship them. Pretrained reconstruction weights carry their own non-commercial license even when the base is CC-BY, so we **train our own regressor**.
- Even the **identity metric** (ArcFace/InsightFace) is non-commercial — use a commercially-licensed or self-trained face recognizer to *measure* fidelity.
- Repos mislabel licenses (permissive top-level bundling non-commercial model files) — audit each embedded asset (see `research/vendors/avatar-selfhost.md`).

## Compute — local-first
- **Three buckets:** data generation (cheap, mostly one-time), training (the variable, experiment-count-driven cost), serving (per-avatar at runtime).
- **Local GPU is the efficient path** for a no-rush, privacy-first build: a single strong consumer card (RTX 4090/5090, ~$1.6–2k, or a used 3090) trains this small vision model and every future retrain for ~electricity, and keeps biometric data on a box we own. Cloud (H100 ~$2–3/hr) only when a big parallel sweep is worth it.
- **Rough synthetic-first estimate:** data-gen ~$0.5–3k; training ~$2–15k of cloud-equivalent (or ~one GPU + electricity locally); serving ~$0.001–0.02/avatar. **Build a first model for ~$3–20k, or ~one GPU + power locally.** NVIDIA/CUDA strongly preferred (a Mac is fine for rendering data, rough for training).
- **The real risk is the synthetic→real domain gap and identity fidelity, not the GPU bill** — de-risk with a cheap early fidelity spike (~$0.5–2k or a few local-GPU days) before committing.

## Phased roadmap (each phase gated)
- **Phase 0:** clean base + synthetic data engine + baseline regressor (photo→ICT/FLAME params + texture). Identity ≈ the linear basis.
- **Phase 1:** identity fidelity — opt-in real data, self-supervised photometric losses, a commercially-clean identity loss, neural texture/displacement beyond the linear basis, a stylized hair library.
- **Phase 2 (premier):** full body on a clean basis, multi-frame video fusion, in-the-wild robustness across the long tail.
- **Gate at every phase:** automated identity similarity **and** a human blind test; graduate into the product only when it **beats the vendor baseline on our metric** and clears on-device latency + the biometric-compliance gates (consent, retention schedule, on-prem processing).

## Relationship to v1
None on the critical path. v1 = pre-made characters (ADR-0006), zero biometric. This track runs in parallel when the Owner funds it, and its output rides on the *same* GJ rig and animation set — so shipping it in V2 does not change the game loop.
