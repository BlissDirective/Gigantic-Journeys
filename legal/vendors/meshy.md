# Meshy — data terms on file

**Date collected:** 2026-09-17 · **Collected by:** Coordinator (from Meshy's public Terms/Privacy/docs). **Source:** public terms only — **NOT yet vendor-confirmed** via `DATA_RETENTION_REQUEST_TEMPLATE.md`. Full analysis + quotes: `research/vendors/meshy.md`. Ticket: M0-LEGAL-04.

Links: Terms https://www.meshy.ai/terms-of-use · Privacy https://www.meshy.ai/privacy-policy · Data/Training FAQ https://help.meshy.ai/en/articles/15724182-is-meshy-safe-and-private-data-and-training-faq · Asset retention https://docs.meshy.ai/en/api/asset-retention

- **Retention (input/output):** API-generated **assets auto-delete after max 3 days** (Enterprise can retain longer). **Gap:** docs cover *output*; whether the uploaded **source photo (input)** is purged immediately/on that schedule is **not stated — must confirm.** Deletion-on-request "up to 30 days."
- **Trains on customer data by default?** **YES** for non-Enterprise (ToS: *"Meshy may use Customer Inputs and Customer Outputs from non Enterprise Customers … to train, validate, test, or improve Services unless otherwise agreed to in the Order"*).
- **Opt-out available?** **Only via Enterprise** Order Form (contractual no-train). No self-serve opt-out.
- **Enabled for us?** No — the Owner's current account is not an Enterprise no-train agreement.
- **Programmatic deletion + receipt?** Yes for output: `DELETE /openapi/v1/image-to-3d/:id` (200 = confirmation). Source-photo deletion: unconfirmed.
- **Sub-processors / regions:** AWS (US) stated; full sub-processor list not published — confirm.
- **Security attestations:** ISO/IEC 27001:2022, SOC 2, GDPR claimed.
- **Biometric immediate-delete supported?** **Not contractually confirmed.** ToS also **prohibits uploading identifiable-person inputs** — needs a carve-out. This is the critical blocker.
- **Ownership:** paid = user owns output; **Free = CC BY 4.0 (unusable for a commercial app).**
- **Incident/breach notification:** not confirmed — request in DPA.

**Decision: USABLE WITH CONDITIONS — not usable on Free/Pro/standard terms for biometric face data.** Requires a negotiated **Enterprise Order Form + DPA** with: (1) written no-train clause (inputs + outputs), (2) immediate source-photo deletion with confirmation, (3) a PII/biometric carve-out overriding the identifiable-input ban, (4) a BIPA/CUBI/MHMDA biometric addendum, (5) a paid tier (not Free). Recognizability must pass our own 60% blind test (M2).

**Gate:** SECURITY_CHECKLIST §6.3 (before any face processing, M2). Owner/legal-team action: pursue the Enterprise agreement, or reconsider the head vendor.
