# AUTH request — Custom avatars in v1 (parametric, on-device, opt-in) (#044)

> **STATUS: APPROVED #044 — Owner instruction, 2026-10-01** ("Let's move custom avatars to v1, as
> parametric variations … spec and build all of this now"). **Security-sensitive (biometric).** Full
> design: `design/proposals/custom-avatars-v1.md`.

```
AUTH REQUEST (#044)
Type: design-change + milestone plan (protected paths: governance/SECURITY_CHECKLIST.md §5/§6,
      ADRs/ (new ADR-0007), SPEC.md, design/DESIGN_SYSTEM.md, legal/, data/schemas/avatar/)
What: Move custom-likeness avatars from V2 into v1 as parametric variations of ONE base rig.
      Preset OR custom; custom is fit ON-DEVICE (ARKit/Vision landmarks -> coarse non-identifying
      params); the photo/video is discarded on-device, never uploaded, no vendor; only avatar_params
      persists. Layered, default-off, purpose-specific opt-in (custom biometric / cloud-sync /
      per-share upload / training). Supersedes the avatar half of #020 / ADR-0006.
Why:  Owner wants a custom avatar in v1 with a strong privacy posture; on-device + coarse params +
      layered opt-in is materially lower-risk than the drafted vendor-based V2 plan, and parametric
      keeps it rig-conformant by construction (movement works unchanged).
Cost: $0 (on-device; no vendor, no new spend).
Reversible: yes (custom is optional; the preset roster is the default path).
BINDING CONDITIONS (security-sensitive, biometric):
  - 100% secondary security review (AUTH #007).
  - The on-device biometric runtime (M1-AVAT-02) + the consent copy SHIP ONLY AFTER in-house counsel
    sign-off (SECURITY_CHECKLIST §5.5, AUTH #016). Building the data contracts + drafting the legal
    copy now is permitted; shipping the biometric runtime without counsel sign-off is not.
Waiting on: in-house counsel review (before ship); Operator/gj-gameplay for the iOS runtime.
```

## Buildable now (no biometric processing; no protected-path risk)
- `data/schemas/avatar/avatar_params.schema.json` — the parameter-set "genome" on `gj-humanoid-1A`:
  bounded/enumerated cosmetic params (body/face-shape morph weights, skin tone, hair, features,
  cosmetic SKU, provenance). `additionalProperties:false` + an explicit no-list that **forbids** any
  photo/video, facial landmarks, face embedding/template, or re-identifying measurement. Non-biometric
  by construction.
- `data/schemas/avatar/consent_record.schema.json` — the layered per-purpose consent record
  (`purpose` enum A–D, `granted`, `policy_version`, `consent_text_hash`, `timestamp`, `locale`,
  `app_version`); no image, no raw biometric.
- A stdlib validator + tests + valid/invalid fixtures; an on-device-pipeline CONTRACT.
- Tickets M1-AVAT-01..05 + reinstated M1-LEGAL-01 (counsel review).

## Governed edits under #044 (Builder drafts; counsel-gated where noted)
1. `SECURITY_CHECKLIST.md` §5/§6: activate for v1, strengthen §5.1 to on-device-only / no-vendor, mark
   §6.2 N/A-by-design, move the counsel gate (§5.5) to **before the v1 feature ships**; update the
   M-plan rows (biometric is a v1 gate now).
2. `ADRs/0007-*.md`: custom avatars in v1 as parametric on-device variations (supersedes ADR-0006 avatar half).
3. `SPEC.md` avatar sections + `design/DESIGN_SYSTEM.md` decision 4 (pick-a-character OR create-custom).
4. `legal/`: reframe `BIPA_CONSENT.md` to on-device/no-vendor ("your photos never leave your device"),
   update `RETENTION_SCHEDULE`, `PRIVACY_POLICY`, `APP_STORE_UGC_COMPLIANCE`, `DELETION_FLOW`. **Counsel
   signs off the wording before ship.**

## On ship (the hard gate)
The biometric runtime does not ship until: counsel has signed off the consent/retention/labels; the
secondary security review has passed; the 13+ age gate + minors handling are in place; and the App
Store privacy labels reflect on-device-only biometric use.
