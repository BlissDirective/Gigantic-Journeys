# Vendor research — Luma AI (scan → 3D reconstruction)

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Luma is the reconstruction provider assumed in ADR-0002 / SPEC §3.10. This pass surfaces **two blocking findings** that warrant re-opening that assumption. Well-sourced (URLs inline); items flagged "confirm directly" are not settled. Not legal advice; terms record in `legal/vendors/luma.md`. **Changing ADR-0002 or SPEC is AUTH-gated — this is input for the Owner, not a change.**

## Fit verdict: CONDITIONAL → likely NO on current public evidence — re-open the reconstruction-vendor decision

### Blocking finding 1 — capability gap (the bigger one)
Luma appears to have **deprecated its programmatic 3D-reconstruction pipeline** and pivoted entirely to generative video/image. The artifact we need (Gaussian splat + mesh from a real scan) seems obtainable today only through the **manual consumer iOS app**, not a server API.
- The old captures API client `lumaapi` (PyPI) is explicitly deprecated — *"WARNING: We are no longer actively supporting this capture API…"* (last release v0.0.5, 2024-09-18).
- The **current** Luma API is **generative only** (Ray3.2 video, UNI-1.1 image) — no reconstruction endpoints.
- Luma's own `llm-info` page lists only Luma App (generative), Luma API (Ray/UNI), Enterprise — **no "3D," "capture," "splat," "NeRF," "mesh."** Genie (text→3D) was sunset 2026-01-01.
- The consumer iOS app still produces splats/meshes (`.ply` splat + GLB/OBJ/USDZ), but that's **manual**, not an automated pipeline.

**Implication:** the M1 "upload → Luma reconstruction → splat + collision mesh" step (M1-CAPT-02, ADR-0002) has no supported server-to-server path as researched. Either confirm a reconstruction offering still exists for us, or evaluate alternatives (**Polycam, Scaniverse/Niantic, self-hosted 3D Gaussian Splatting / COLMAP**).

### Blocking finding 2 — trains on user data by default, even on paid plans
Standard ToS (updated 2026-05-14) licenses Input **and** Output to Luma to *"create, test, improve, train, or otherwise develop the … models,"* and the license is *"perpetual and irrevocable"* for Input reflected in Output/Usage/Aggregated Data. Privacy Policy (2026-04-20): they use uploaded images/videos to *"Train, develop, and improve the … models."*
- **No-train only via Enterprise:** Enterprise Terms carry a *"No Train Guarantee"* and make the **customer the data controller** (Luma the processor). This is the only configuration that meets our gate (SECURITY_CHECKLIST §6.3).
- **Retention:** no written zero-retention; Enterprise retention is discretionary/negotiated. Standard ~30-day post-termination window.
- **Deletion:** account delete stops future use but *"does not affect any licenses you have granted"* (already-incorporated data not clawed back). **No documented deletion-confirmation/receipt; no programmatic per-asset delete** (there is no reconstruction API). Must confirm.
- **Ownership:** customer owns Output only if produced under an active paid subscription; Luma reserves the right to embed watermarks/provenance metadata.

## Unity suitability (if a reconstruction path is confirmed)
- Meshes (glTF/GLB, OBJ, USDZ) import to Unity 6 natively.
- A **Gaussian splat is not natively rendered by Unity 6** — needs a dedicated splat-renderer package (already anticipated: M0-UNITY-02).

## API, pricing (snapshot, observed 2026-09-17)
- Public API is **generative only**, credit-based (plans Plus/Pro/Ultra/Enterprise). **No reconstruction API / no published reconstruction price.**
- Third-party trackers (not verified on canonical /pricing): Plus ~$30/mo (10k credits), Pro ~$90 (40k), Ultra ~$300 (150k); credits don't roll over; failed generations still charge. **Confirm at lumalabs.ai/pricing** — and note this is generative-media pricing, not reconstruction.

## Questions to confirm directly with Luma (before relying on it — blocking)
1. **Do you still offer room/space 3D reconstruction (splat/mesh) at all in 2026 — via API or a supported workflow — or is 3D Capture being sunset like Genie?**
2. If yes: is there a **server/programmatic API**, turnaround, formats, SLA?
3. **Enterprise "No Train Guarantee" in writing** for reconstruction + a **DPA** (us = controller, Luma = processor).
4. **Zero/short retention + documented deletion with receipt** (ideally per-asset, on-demand); actual max-retention numbers.
5. **Sub-processors and storage regions** for private-home scan media.
6. **Commercial-use rights** for reconstructions shipped in an iOS game; are watermarks/provenance embedded?
7. Written **reconstruction pricing**.

## Sources (observed 2026-09-17)
- Terms — https://lumalabs.ai/legal/terms-of-service · Enterprise Terms — https://lumalabs.ai/legal/enterprise-terms-of-service · Privacy — https://lumalabs.ai/legal/privacy-policy
- API docs (generative) — https://docs.lumalabs.ai/docs/api · product overview — https://lumalabs.ai/llm-info
- Deprecated captures client — https://pypi.org/project/lumaapi/
