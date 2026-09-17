# Luma AI — data terms on file

**Date collected:** 2026-09-17 · **Collected by:** Coordinator (from Luma's public Terms/Privacy/docs). **Source:** public terms only — **NOT yet vendor-confirmed** via `DATA_RETENTION_REQUEST_TEMPLATE.md`. Full analysis + quotes: `research/vendors/luma.md`. Ticket: M0-LEGAL-03.

Links: Terms https://lumalabs.ai/legal/terms-of-service · Enterprise Terms https://lumalabs.ai/legal/enterprise-terms-of-service · Privacy https://lumalabs.ai/legal/privacy-policy · API docs https://docs.lumalabs.ai/docs/api · deprecated captures client https://pypi.org/project/lumaapi/

- **Capability (precedes terms):** Luma appears to have **deprecated programmatic 3D reconstruction** (captures API deprecated; current API is generative video/image only; Genie sunset 2026-01-01). No supported server→server "scan → splat/mesh" path found. **Must confirm a reconstruction offering exists before terms even matter.**
- **Retention (input/output):** no written zero-retention; Enterprise retention discretionary/negotiated; standard ~30-day post-termination window.
- **Trains on customer data by default?** **YES, even on paid plans** (ToS licenses Input + Output to *"train … models,"* "perpetual and irrevocable" for Input reflected in Output).
- **Opt-out available?** **Only via Enterprise** ("No Train Guarantee"; customer = data controller).
- **Enabled for us?** No.
- **Programmatic deletion + receipt?** No documented deletion-confirmation; no per-asset programmatic delete (no reconstruction API). Account delete doesn't claw back already-licensed data.
- **Sub-processors / regions:** not published — confirm.
- **Security attestations:** not captured — request.
- **Ownership:** customer owns Output only under an active paid subscription; Luma may embed watermarks/provenance metadata.
- **Incident/breach notification:** not confirmed — request in DPA.

**Decision: NOT USABLE on default terms** (trains on our scans by default) **AND capability in question** (no supported reconstruction API found). If Luma is pursued: **Enterprise contract only** (No Train Guarantee + DPA, us = controller) **and** confirmed reconstruction offering. Otherwise **re-open the reconstruction-vendor decision** (Polycam, Scaniverse/Niantic, self-hosted 3DGS/COLMAP).

**Gate:** SECURITY_CHECKLIST §6.3 (before any real user scan, M1). This affects ADR-0002 / SPEC §3.10 — an architectural review the Owner should weigh (changing those is AUTH-gated).
