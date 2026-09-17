# Vendor research — Meshy (head/avatar generation)

**Decision-support · observed 2026-09-17 · Coordinator research pass.** Meshy is the Owner-selected head vendor (AUTH #010; Owner holds an account). This dossier confirms technical fit and — critically — the data terms that gate biometric use. All quotes are verbatim from Meshy pages (URLs inline); anything uncertain is flagged "confirm with Meshy." Not legal advice; the terms record is `legal/vendors/meshy.md`.

## Fit verdict: CONDITIONAL

**Technically good; the default (Free/Pro) legal terms are a hard blocker for biometric face photos.** Meshy is usable for our face data **only under a negotiated Enterprise Order Form + DPA** with a no-train clause, immediate source-photo deletion, and a PII carve-out. Recognizability of a photo-derived head is **unverified** and must pass our own 60% blind test (M2).

### Two showstoppers on standard terms
1. **Trains on non-Enterprise inputs by default, no self-serve opt-out.** ToS §"Training on User Content": *"Meshy may use Customer Inputs and Customer Outputs from non Enterprise Customers … to train, validate, test, or improve Services unless otherwise agreed to in the Order."* Marketing pages say the opposite ("we will NOT … use it for any training purpose without your consent"), but accepting the ToS *is* that consent — not a contractual no-train guarantee. Only **Enterprise** is contractually no-train: *"[Enterprise] data will not be used for AI training."*
2. **ToS bans uploading identifiable-person photos — exactly our use.** *"You … will not include any personally identifiable information about yourself or any third party in your Customer Input … [or] any other data that could identify a specific person."* A face photo identifies a person, so our core use likely breaches standard ToS without a custom carve-out.

Plus: **Free-tier output is CC BY 4.0** (Meshy owns it, attribution required) — unusable for a closed-source commercial app. A **paid/Enterprise tier is mandatory**.

## 1. Capability fit — GOOD (technically)
- **Products:** Image-to-3D (1 photo, or 2–8 multi-view), the Realistic Character Generator (rigged full-body human from a front photo), AI texturing (Meshy 7).
- **Time:** ~1–2 min standard (Ultra +~1 min) — **meets <2 min** with Ultra off.
- **Output/Unity:** API `target_formats` = glb, fbx, obj, usdz, stl, 3mf (+ blend); PBR maps (metallic/roughness/normal); poly control 100–15,000 via Smart Topology. **GLB/FBX + PBR import cleanly into Unity 6.**
- **Recognizability — UNVERIFIED.** Meshy publishes no face-identity/likeness metric; markets characters/figurines, not verified likeness. **Our 60% blind test (M2) is the gate.**

## 2. Data terms — MAJOR CONCERNS (see `legal/vendors/meshy.md`)
- **Training:** on by default for non-Enterprise (quote above); no-train only via Enterprise Order Form.
- **PII ban:** standard ToS forbids identifiable-person inputs → needs an Enterprise carve-out + biometric DPA.
- **Deletion — partial, with a critical gap.** API delete exists: `DELETE /openapi/v1/image-to-3d/:id` (200 OK on success = confirmation; 409 while in progress). API-generated **assets auto-delete after max 3 days** (Enterprise can retain longer). **Gap:** docs cover generated *output*; they do **not** explicitly say the uploaded **source photo (input)** is purged immediately or on that schedule — for biometric data this must be confirmed and contractually required (immediate delete after the job, per SECURITY_CHECKLIST §6.2). Deletion-on-request otherwise "up to 30 days."
- **Ownership:** paid tiers = user owns output (grants Meshy a service license); **Free = CC BY 4.0** (unusable for us).
- **Security:** AWS (US); ISO/IEC 27001:2022, SOC 2, GDPR compliance claimed.

## 3. API, pricing, limits
- **REST API:** yes; pay-as-you-go **credits** (separate from subscription).
- **Credit costs (Meshy 7):** Image-to-3D 20 (no texture) / 30 (+texture) / 35 (8K), +5 Ultra; Smart Topology 5/15/20; texture 10–15; rig 5; failed generations not charged.
- **Monthly credit allotments:** Free 100 (CC BY 4.0), Pro 1,000, Premium 3,000, Ultra 8,000; Studio (seat-based) and Enterprise (custom) exist.
- **Exact USD prices: NOT reliably captured** (pricing page renders dynamically) — do not quote a dollar figure without confirming on the live page / with sales.
- **Rate limits:** ~20 RPS paid (100 Enterprise); concurrent tasks Pro 10 → Ultra 100.

## Questions to confirm directly with Meshy (biometric go/no-go — resolve before sending any real face photo)
1. **Source-photo deletion:** does task-delete / the 3-day purge delete the **uploaded input image immediately**, or only the mesh? Can we contractually require immediate source-photo deletion on completion, with confirmation?
2. **Written no-train clause** in an Enterprise Order Form overriding the standard training clause (inputs *and* outputs).
3. **PII/biometric carve-out** overriding the ToS ban on identifiable inputs, plus a **DPA and a BIPA/CUBI/MHMDA biometric addendum** (consent, retention/destruction, no sale/sharing).
4. **Retention config** for inputs/logs/thumbnails/embeddings (fixed short window; is the 3-day API-asset max contractually binding?).
5. **Sub-processors & region** (full list; guaranteed US-only for our data).
6. **Current USD pricing** (Pro/Premium/Ultra/Studio/Enterprise; API volume pricing).
7. **Recognizability:** run our own 60% blind test on photo-to-3D-head output before committing.

## Sources (observed 2026-09-17)
- Terms of Use — https://www.meshy.ai/terms-of-use · Privacy — https://www.meshy.ai/privacy-policy
- Data & Training FAQ — https://help.meshy.ai/en/articles/15724182-is-meshy-safe-and-private-data-and-training-faq
- Asset retention — https://docs.meshy.ai/en/api/asset-retention · https://help.meshy.ai/en/articles/15643844-how-long-does-meshy-keep-api-generated-assets
- Image-to-3D — https://www.meshy.ai/features/image-to-3d · https://docs.meshy.ai/en/api/image-to-3d · Realistic Character Generator — https://www.meshy.ai/3d-tools/realistic-character-generator
- API pricing — https://docs.meshy.ai/en/api/pricing · Pricing — https://www.meshy.ai/pricing · Rate limits — https://docs.meshy.ai/en/api/rate-limits
