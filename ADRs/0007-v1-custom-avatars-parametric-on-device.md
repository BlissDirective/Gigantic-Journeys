# ADR-0007: Custom avatars in v1 — parametric, on-device, opt-in

Date: 2026-10-01 · Status: Accepted · Authorization: APPROVED #044 · Supersedes: the avatar decision in ADR-0006 (and the avatar half of #020) · Owner: coordinator (governance), gj-gameplay (avatar system), claude-builder (data contracts)

## Context
ADR-0006 (AUTH #020) deferred custom-likeness avatars to V2 and shipped v1 with a curated pre-made roster, to remove biometric / vendor / App-Store risk and focus on the hero features. The Owner has since chosen to bring custom avatars into v1 with a privacy-first design that removes the risks that drove the deferral: a stylized "idealized-me" target (not photoreal), a parametric representation on the one shared rig, and on-device-only face processing with no vendor and layered opt-in. The movement work since (AUTH #043, motion matching) assumes one shared rig, which this design preserves. Full design: `design/proposals/custom-avatars-v1.md`.

## Decision
**v1 avatar = one base rig (`gj-humanoid-1A`) + a non-identifying parameter set.** A player picks a **preset** (the curated roster, #024) **or** creates a **custom** avatar fit **on-device** from their face (ARKit/Vision landmarks → coarse `avatar_params`, an "idealized me").

- **On-device only, no vendor.** The photo/video is discarded on-device and never uploaded; only `avatar_params` persists (on-device by default; server-side only under a separate `avatar_cloud_sync` opt-in). We never hold a biometric identifier server-side.
- **Layered, default-off, purpose-specific opt-in:** (A) custom biometric, (B) cloud-sync (params only), (C) per-share upload of rendered gameplay media — highlight / summit / competition (→ M4 moderation, #026), (D) training. Nothing leaves the device without the matching opt-in.
- **Parametric → rig-conformant by construction.** Preset and custom share the same `avatar_params` on the one rig, so motion matching, the #043 fluidity pack, IK and tool sockets work unchanged; the roster is 8 curated parameter sets.
- **Target fidelity: semi-recognizable / idealized**, not photoreal — cheaper, robust to a poor selfie, no uncanny valley, coherent with the 1:12 world.

## Alternatives considered
- **Keep custom in V2 (ADR-0006):** lowest risk, but the on-device / parametric design removes most of what drove the deferral, and the Owner wants the feature in v1.
- **Photoreal custom likeness / vendor (ADR-0005 / #019):** dense reconstruction, per-avatar rig-conformance, uncanny valley, biometric templates, App-Store scrutiny — rejected; the stylized on-device path is materially lower-risk and integrates for free.

## Consequences
- **Biometric is a v1 gate again (SECURITY_CHECKLIST §5/§6), strengthened to on-device-only** — a lower-risk posture than the drafted vendor-based V2 gate. The **on-device runtime + consent copy ship only after in-house counsel sign-off** (§5.5) and secondary security review (AUTH #007).
- **Data contracts:** `data/schemas/avatar/avatar_params` + `consent_record` (non-biometric; AUTH #044), rig-conformant by construction.
- **Legal:** `legal/BIPA_CONSENT.md` etc. move from V2 artifacts to active v1 copy, reframed to on-device / no-vendor; counsel re-reviews.
- **Reversal:** custom is optional; if it slips, the preset roster is the default path and ships regardless.

## Follow-ups
- SECURITY_CHECKLIST §5/§6 activated for v1 (AUTH #044); SPEC §1/§3.2/§7/§8/§9 + DESIGN_SYSTEM decision 4 reconcile; `legal/` reframe (counsel-gated).
- Tickets M1-AVAT-01..05 (roster+rig, on-device pipeline, consent UX, per-share opt-in, data contracts) + M1-LEGAL-01 (counsel review, reinstated for v1). M2-AVAT-01 superseded.
- Data contracts built: `data/schemas/avatar/` (AUTH #044).
