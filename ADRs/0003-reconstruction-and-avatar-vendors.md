# ADR-0003: Reconstruction and avatar via third-party APIs; vendor-neutral package format

Date: 2026-09-15 · Status: **Superseded by ADR-0005** (2026-09-18, AUTH #018/#019) · Authorization: APPROVED #000 · Owner Bots: gj-capture (reconstruction), gj-avatar (head generation)

> **Superseded.** Luma (reconstruction) and Meshy/Tripo (avatar) were invalidated by vendor research (`research/vendors/`): Luma deprecated its reconstruction API and trains by default; Meshy's ToS bans identifiable-person photos. ADR-0005 records the replacement — self-hosted reconstruction (with a managed bridge) and Avatar SDK/MetaPerson on-prem. The vendor-neutral package format below still holds.

## Context
Scan-to-splat and image-to-3D heads are solved by vendors at a per-job cost inside the budget; building either in-house would consume the whole schedule.

## Decision
Reconstruction through the Luma API (Gaussian splat plus mesh). Avatar heads through an image-to-3D realistic mode from Meshy or Tripo; the vendor is fixed by an addendum at M2 after the M0 vendor-terms review (M0-LEGAL-04). The environment package format (splat, mesh, scene graph, environment spec, thumbnail) is vendor-neutral so a vendor can be swapped without changing the app. A self-hosted gsplat path is documented here as the fallback if price or terms change; it is not built in v1.

## Alternatives considered
- Self-hosted reconstruction from day one: higher fixed cost and ops before M1 validates the product.
- Polycam or Scaniverse APIs: evaluated as fallbacks; Luma chosen for splat plus mesh output in one job.

## Consequences
Vendor data-retention and training terms must be on file before any user data is sent (SECURITY_CHECKLIST §6.3). Per-job cost is tracked and capped ($50/day). Source media is deleted after derived assets exist.

## Follow-ups
M0-LEGAL-03, M0-LEGAL-04, M0-CAPT-01.
