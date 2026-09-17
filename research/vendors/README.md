# `research/vendors/`

Vendor research (Coordinator research pass, 2026-09-17). Decision-support, not decisions — all facts carry an observation date and sources; re-verify pricing/terms at build time. Vendor **data terms on file** live in `legal/vendors/`; this tree holds the capability/pricing/fit analysis.

| Report | For | Headline |
|---|---|---|
| `meshy.md` | head vendor (AUTH #010), M0-LEGAL-04 | **CONDITIONAL** — good tech fit, but standard terms train on inputs + ban identifiable-person photos → **Enterprise + DPA required** for biometric use |
| `luma.md` | reconstruction (ADR-0002), M0-LEGAL-03 | **⚠ RE-OPEN** — programmatic reconstruction API appears **deprecated**, and default terms train on scans even on paid plans (Enterprise-only no-train) |
| `iap-revenuecat-vs-unity.md` | M5 monetization ADR | **RevenueCat** primary (native entitlement, managed validation, free at our scale); **Unity IAP** fallback |
| `crash-reporting.md` | AUTH #017 | **Sentry** (free tier, privacy-first) + Apple Xcode Organizer/MetricKit supplement; Crashlytics fallback |

## Two findings that need Owner attention
1. **Meshy (head vendor):** usable for face data **only under a negotiated Enterprise agreement + DPA** (no-train clause, immediate source-photo deletion, PII/biometric carve-out; a paid tier — Free is CC BY 4.0). Recognizability unverified → own 60% blind test at M2.
2. **Luma (reconstruction):** current public evidence says Luma has **exited supported programmatic reconstruction** and trains on inputs by default. This challenges the ADR-0002 assumption. **Recommend re-opening the reconstruction-vendor decision** (Polycam, Scaniverse/Niantic, self-hosted 3D Gaussian Splatting / COLMAP) — and confirming directly with Luma before relying on it.

Both vendors' data terms are from **public pages only** and must be confirmed directly (send `legal/vendors/DATA_RETENTION_REQUEST_TEMPLATE.md`) before any real user data flows.
