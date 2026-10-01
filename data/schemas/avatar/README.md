# `data/schemas/avatar/` — v1 custom-avatar data contracts (AUTH #044)

The **non-biometric** data contracts behind the v1 custom-avatar feature (`design/proposals/custom-avatars-v1.md`).

- **`avatar_params.schema.json`** — the cosmetic parameter set ("genome") on the shared GJ humanoid rig
  (`gj-humanoid-1A`). Preset and custom avatars use it identically, so any avatar is **rig-conformant by
  construction** and the movement stack (motion matching, #043, IK, tool sockets) works unchanged. It is
  bounded + enumerated and **carries no biometric data** — no photo/video, no landmarks, no face
  embedding/template, no re-identifying measurement.
- **`consent_record.schema.json`** — one immutable, **per-purpose** opt-in/withdrawal record for the layered
  consent (custom biometric / cloud-sync / per-share upload / training). Proof of consent; no image, no raw
  biometric (`legal/BIPA_CONSENT.md` §4).
- **`validate_avatar.py`** — reference validator (`validate(doc, kind)`) + the `forbidden_keys` privacy guard;
  the on-device C# runtime mirrors these checks.

## Privacy model (SECURITY_CHECKLIST §5/§6; AUTH #044)
A custom avatar is fit from the user's face **on-device** (ARKit/Vision landmarks → coarse params); the
photo/video is **discarded on-device and never uploaded** (no vendor). Only `avatar_params` persists —
on-device by default, server-side only under the separate `avatar_cloud_sync` opt-in. No action in a consent
purpose is permitted without a matching `granted:true` `consent_record`.

**The biometric runtime ships only after in-house counsel sign-off** (SECURITY_CHECKLIST §5.5, AUTH #016).

## Versions
| Schema | Version | By | Status |
|---|---|---|---|
| `avatar_params.schema.json` | **1.0.0** | AUTH #044 (2026-10-01) | v1 contract; additive changes bump the minor version |
| `consent_record.schema.json` | **1.0.0** | AUTH #044 (2026-10-01) | v1 contract; additive changes bump the minor version |

Change rule: same as `data/schemas/README.md` — any change needs an `APPROVED #n` (design-change); additive →
minor bump, removing/tightening → major bump; ship fixtures + keep `tests/test_avatar_schemas.py` green.
