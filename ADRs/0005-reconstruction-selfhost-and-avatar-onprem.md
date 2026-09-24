# ADR-0005: Reconstruction self-host (with a managed bridge); avatar via Avatar SDK/MetaPerson on-prem

Date: 2026-09-18 · Status: Accepted; **avatar half superseded by ADR-0006** · Authorization: APPROVED #018 (reconstruction), #019 (avatar), #030 (self-host prioritized; bridge conditional) · Supersedes: ADR-0003 · Owner: claude-builder (pipeline), coordinator (governance)

> **Addenda (2026-09-18):** (1) The **avatar decision here (Avatar SDK/MetaPerson on-prem, #019) is superseded by ADR-0006** — v1 uses a curated roster of pre-made characters with no biometric processing; Avatar SDK is deferred to the V2 custom-avatar track. (2) The **reconstruction managed bridge is selected: KIRI, corpus-only** (splat+mesh matches the self-host target; it only ever processes the consented corpus, never real user homes; real user scans wait for the self-host pipeline). The reconstruction decision otherwise stands.
>
> **(3) 2026-09-24 (AUTH #030):** self-host is the **committed, prioritized** v1 reconstruction path — the **M1-CAPT-03 spike stands up as soon as possible**. This **supersedes (2)'s pre-selection of KIRI**: a managed bridge (KIRI or Autodesk APS) is now **conditional**, used only when a **written no-train + DPA + data-residency** commitment is on file *before any use*, and only ever on the consented corpus — never real user scans. Absent that commitment there is **no bridge** and self-host is the sole reconstruction backend. **Luma remains rejected** (deprecated to generative video/image; default terms train on inputs; no-train is Enterprise-only) — not usable under our security/legal bar.

## Context
ADR-0003 chose Luma for reconstruction and Meshy/Tripo for avatar heads, both as third-party APIs, with a self-hosted gsplat path documented only as a fallback. Vendor research (2026-09-17, `research/vendors/`) invalidated both premises:
- **Luma** has deprecated its programmatic reconstruction API (pivoted to generative video/image) and, on default terms, trains on customer inputs even on paid plans (no-train is Enterprise-only). It is no longer a usable reconstruction backend.
- **Meshy**'s ToS prohibits uploading identifiable-person photos and trains on non-Enterprise inputs by default — a hard blocker for biometric face data without a negotiated Enterprise carve-out.

Both problems share a root cause: vendor lock-in/deprecation and vendors training on our users' biometric/home data. The Owner decided (this session) to move data processing onto infrastructure we control.

## Decision
**Reconstruction (APPROVED #018):** the target backend is a **self-hosted Gaussian-splat pipeline** — COLMAP/GLOMAP (poses, seeded by ARKit) → **gsplat/Splatfacto or Brush** (splat training) → Open3D (collision mesh) → prune/compress → CDN → Unity 6 URP splat renderer. All components are **Apache/BSD/MIT** (the non-commercial INRIA 3DGS/SuGaR code is explicitly excluded). The path is validated by a de-risking **spike** (M1-CAPT-03) before commitment. In parallel, a **managed API bridge** may be used for early M1 validation: **Autodesk APS Reality Capture** (has a DPA + explicit delete; mesh-only) or **KIRI Engine** (splat+mesh) **only under a written no-train + DPA + data-residency commitment**. Luma is dropped.

**Avatar (APPROVED #019):** head generation moves to **Avatar SDK / MetaPerson (itSeez3D)** on the **Enterprise "Local Compute" (on-prem)** plan, so a user's biometric face photos are processed on infrastructure we control and never enter a vendor training cloud. Its EULA already contemplates consented identifiable-person photos, and it ships native Unity + iOS SDKs with recognizability as an explicit design goal. **Self-hosting the avatar pipeline is deferred to V2** (the high-quality models — FLAME textures, DECA/EMOCA/MICA, BFM, SMPL/-X — are non-commercially licensed, so a from-scratch build would trade a vendor-ToS problem for an IP-license one plus an ML-quality risk).

The environment-package format stays **vendor-neutral** (splat, mesh, scene graph, environment spec, thumbnail), so the reconstruction bridge/self-host and the avatar vendor can change without touching the app.

## Alternatives considered
- **Keep Luma / a pure-API reconstruction backend:** Luma's reconstruction API is deprecated; other pure-API options either don't expose a server reconstruction endpoint (Polycam, Niantic) or have weak data terms (KIRI) or are mesh-only (Autodesk). A managed bridge is retained only as an interim, terms-gated option.
- **Self-host avatars now:** not viable for v1 on licensing + ML-quality grounds (see `research/vendors/avatar-selfhost.md`); revisit in V2 on a commercially-clean basis (FLAME-2023-Open / ICT-FaceKit + a self-trained regressor).
- **Stay with Meshy under an Enterprise carve-out:** possible but higher-friction (its ToS bans person-photos by default); Avatar SDK's on-prem path gives the same data-control posture with a vendor already built for consented person-photos.

## Consequences
- **Privacy/compliance upside (the main driver):** biometric face data (Avatar SDK on-prem) and private-home scan imagery (self-host reconstruction) stay on our infrastructure — the cleanest posture for BIPA §15/CUBI/MHMDA, and it removes the vendor-training vector. Vendor DPAs are still required for any managed bridge, and BIPA's core duties (written consent, published retention schedule, no-sale, security) still apply (SECURITY_CHECKLIST §5, §6).
- **New risk — iOS-in-Unity splat rendering:** on-device splat rendering is immature (~200–500K splats @30 fps on iPhone; Metal radix-sort is the pain point). The pipeline must aggressively prune/compress splats and/or ship the mesh for gameplay/collision to hit the ≤150 MB package and fps budget. This is the item most likely to bite; the spike targets it first.
- **New ops burden:** self-host reconstruction adds a GPU worker (job queue, autoscaling, cost caps, quality-gating, monitoring) — a fit for the Grok Operator's long-running-ops role and the Builder's pipeline code. Cost is ~<$1/scan on rented GPUs, within the $50/day cap.
- **Cost shape changes** from per-scan vendor fees to GPU rental (reconstruction) + an Enterprise/on-prem plan (avatar, pricing TBD — confirm).
- **Reversal:** the vendor-neutral package format means we can fall back to a managed reconstruction bridge or a different avatar vendor without app changes.

## Follow-ups
- **M1-CAPT-03** (new): self-host reconstruction spike + managed-bridge stand-up for M1 validation.
- **M1-CAPT-02**: retarget from "Luma reconstruction" to the self-host pipeline / bridge.
- **M0-LEGAL-04**: retarget the head-vendor terms dossier to Avatar SDK/MetaPerson (on-prem + DPA); Meshy dropped.
- **M0-LEGAL-03**: Luma dropped as reconstruction vendor; collect terms for the chosen managed bridge (Autodesk APS / KIRI) if used.
- Send the vendor questionnaire (`legal/vendors/DATA_RETENTION_REQUEST_TEMPLATE.md`) to Avatar SDK and any reconstruction bridge before real user data flows.
