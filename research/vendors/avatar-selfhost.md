# Avatar — build/self-host feasibility

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Can we run our own photo → 3D avatar-head pipeline instead of a vendor (Meshy)? Sourced; not legal/IP advice.

## Verdict: technically FEASIBLE-WITH-SIGNIFICANT-EFFORT, but NOT ADVISABLE FOR v1 — a V2 investment

Latency (<2 min) is easy; the blockers are **licensing** (the mainstream research stack is non-commercial) and **recognizability quality** (texture + hair), neither of which AI coding agents can de-risk. Owner's question — "could we build a custom version?" — **answer: yes technically, but not cheaply, quickly, or for v1. The blocker is licensing + ML quality, not latency.**

## Licensing reality — the main blocker (CRITICAL)
A pipeline is only as commercial-friendly as its most-restrictive link. Almost every high-quality building block is research/non-commercial:

| Component | License | Commercial? |
|---|---|---|
| FLAME 2017/19/20/2023 | Academic/non-commercial | ❌ (commercial via MPI `ps-license@tue.mpg.de`) |
| **FLAME 2023 Open** | CC-BY-4.0 | ✅ geometry basis only |
| FLAME texture/albedo | CC-BY-**NC**-SA | ❌ |
| **ICT-FaceKit** (base) | MIT | ✅ (hi-res = separate paid license) |
| Basel Face Model (BFM) | Academic | ❌ (~€10k/yr or €40k perpetual) |
| DECA / EMOCA | Non-commercial | ❌ |
| MICA | Non-commercial (+ArcFace NC) | ❌ |
| HRN / Deep3DFaceRecon | BFM-encumbered | ❌ |
| PanoHead / Next3D | NVIDIA proprietary (EG3D) | ❌ |
| SMPL / SMPL-X / STAR | Non-commercial | ❌ (commercial via **Meshcapade**) |
| PIFuHD | CC-BY-NC | ❌ |
| ECON | Non-commercial (+SMPL-X) | ❌ |

**The trap:** pretrained reconstruction weights carry their *own* non-commercial license **even when the underlying 3DMM is CC-BY** — so FLAME 2023 Open being free does NOT make DECA/EMOCA/MICA usable. To ship commercially you must **retrain your own regressor** against FLAME-2023-Open / ICT-FaceKit on commercially-cleared, consented data. "Apache/MIT" avatar repos routinely bundle non-commercial FLAME/SMPL assets under a permissive top-level license (documented live in aigc3d/LAM issue #111) — **audit every embedded model file, don't trust the top-level license.**

## Most viable approach (if pursued) — parametric mesh, not splat
- **Geometry:** a riggable 3DMM — only **FLAME 2023 Open (CC-BY)** or **ICT-FaceKit (MIT)** are clean; both give blendshapes + LBS that export to Unity as a rigged skinned mesh and map to ARKit blendshapes.
- **Reconstruction (photo→params):** a feed-forward DECA/MICA-style regressor — **but you must train your own** (licensing).
- **Texture:** your own UV completion / de-lighting (FLAME's albedo is NC).
- **Body:** parametric shape sliders (SMPL-X-style) for a 1:12 figure — **not** PIFuHD/ECON (NC, slow, un-rigged).
- **Hair:** a stylized hairstyle library with auto-selection (3DMMs don't model hair; per-strand is unsolved).
- Note: modern one-shot avatars (GAGAvatar, LAM, SEGA) output **Gaussian splats** — don't drop into Unity as rigged meshes, and are mostly FLAME-encumbered.

## Quality & latency
- **Latency:** <2 min easily met (feed-forward regressors run sub-second).
- **Recognizability is the hard part:** identity is carried more by **texture (skin tone, albedo) and hairstyle** than mesh shape; only the frontal face is seen (sides/back need completion). A stylized 1:12 figure forgives photorealism but not gross identity errors (wrong skin tone/proportions/no matching hair fail the 60% blind test). Hitting 60%+ with a self-trained texture+hair stack is the primary quality risk vs a mature vendor.

## Effort & risk (solo dev + agents)
Multi-month. You own: a GPU inference service, **training a custom regressor** (ML research risk + sourcing consented commercial face-training data — itself a compliance problem), texture completion, a hairstyle system, auto-rig + ARKit mapping, Unity import, and biometric-handling infra. Agents accelerate glue/plumbing but **cannot de-risk the ML quality bar or the licensing** — the two things that decide success.

## Compliance upside (real, with a caveat)
On-prem processing means the **biometric image/faceprint never leaves infra we control** — no vendor DPA, no vendor-training, no cross-border transfer, fully enforceable deletion. Cleanest posture for BIPA §15(a)/CUBI/MHMDA and it removes the Meshy-ToS problem. **Caveats:** (a) self-hosting does not remove BIPA's core duties (written consent §15(b), public retention schedule, no-sale, security still apply); (b) shipping on **non-commercially-licensed models is itself a legal risk** — you'd trade a vendor-ToS problem for an IP-license problem unless you use the clean basis or pay for licenses.

## Recommendation: v1 vs later
- **v1:** do NOT build from scratch. Either (a) use a vendor offering **on-prem/EU processing or a strong DPA + no-training guarantee** (keeps most privacy upside without the ML/licensing lift), or (b) **license the building blocks commercially** (Meshcapade for SMPL/-X; MPI for FLAME/DECA/ECON) and integrate.
- **Later (V2):** revisit a self-hosted build on **FLAME-2023-Open or ICT-FaceKit + a self-trained regressor + own texture/hair** — the only from-scratch path that's simultaneously commercially licensable and privacy-clean, as a deliberate funded project, not a v1 feature.

## Sources (observed 2026-09-17)
- FLAME license — https://flame.is.tue.mpg.de/modellicense.html · SMPL-X — https://smpl-x.is.tue.mpg.de/modellicense.html · SMPL commercial (Meshcapade) — https://meshcapade.com/smpl/
- DECA — https://github.com/yfeng95/DECA · EMOCA license — https://github.com/radekd91/emoca/blob/release/EMOCA_v2/LICENSE · MICA — https://github.com/Zielon/MICA
- ICT-FaceKit (MIT) — https://github.com/USC-ICT/ICT-FaceKit · Basel BFM — https://faces.dmi.unibas.ch/bfm/bfm2019.html
- PanoHead (NVIDIA) — https://github.com/SizheAn/PanoHead · PIFuHD (CC-BY-NC) — https://github.com/facebookresearch/pifuhd/blob/main/LICENSE · ECON — https://github.com/YuliangXiu/ECON/blob/master/LICENSE
- License-contamination example — https://github.com/aigc3d/LAM/issues/111
