# Counsel brief — v1 custom avatars (biometric), on-device / no-vendor

**Engineering compliance brief for in-house counsel · 2026-10-02 · prepared by Builder/Coordinator (AUTH #027) · ticket M1-LEGAL-01.**
**This is an engineering summary to scope your review — it is *not* legal advice.** The authoritative drafts are the files in §8.

---

## 0. The ask (what your sign-off unblocks)
Custom avatars are now a **v1** feature (AUTH #044 / ADR-0007). A player may **pick a preset character** (the default) **or** opt in to create a **custom "idealized-me" avatar** from their own face. The custom path processes a face, so it is **biometric** and is a **hard ship gate**: the on-device biometric **runtime** (ticket M1-AVAT-02) and the **consent copy** ship **only after your sign-off** (`SECURITY_CHECKLIST` §5.5, AUTH #016) **and** a secondary security review (AUTH #007). Nothing biometric ships before then.

We ask you to review — for the **on-device / no-vendor** design below — the consent experience, retention/deletion, minors handling, and App Store privacy labels, and to answer the questions in §6 so the consent wording can be frozen (`consent_text_hash = consent-v1`).

## 1. What changed since the earlier plan (read this first)
Legal drafts you may have seen were written for a **V2, vendor-based** design: photos uploaded to a third-party avatar generator (Meshy/Tripo) and "deleted at the provider." **That design is retired.** The v1 design is materially narrower:

- **On-device only.** Face processing happens entirely on the device (ARKit/Vision).
- **No vendor, no upload.** No face/body image or video is ever transmitted or stored server-side. There is **no third-party processor** of biometric data.
- **No biometric identifier is retained — anywhere.** The capture and any landmarks are **discarded on-device immediately** after the avatar is fit. The only thing that persists is a **bounded, non-identifying cosmetic parameter set** ("`avatar_params`" — coarse morph weights plus skin-tone/hair enums), which is **not a biometric identifier** and cannot reconstruct the face.
- **Net:** we never hold a face template/embedding, and there is no disclosure-to-processor. This is lower-risk than the drafted framework.

> **Note on the drafts:** `legal/BIPA_CONSENT.md` still carries the old vendor-flow wording in §2–§3 and one §5 table row ("sent to" / "deleted at the provider"). Those passages are flagged for a **reframe to on-device/no-vendor** and are on the pre-sign-off worklist (§7). **Where that draft and this brief differ, this brief describes the actual v1 design.**

## 2. Exactly what is and isn't handled
- **Processed transiently, on-device:** camera frames / an optional short guided video of the user's face and body, and the face **landmarks** derived from them — **used only to fit the parameter set, then discarded on-device.**
- **Persisted:** only **`avatar_params`** — bounded cosmetic morph weights + enums (`data/schemas/avatar/avatar_params.schema.json`). On-device by default; server-side **only** if the user *separately* opts in to cloud-sync (params only, still non-biometric).
- **Never collected or stored (enforced by schema + tests):** no photo/video bytes, **no facial landmarks**, **no face embedding / recognition template / descriptor**, no raw biometric measurements. The schema is a closed object with an explicit forbidden-key guard.

## 3. The consent experience (drafted; your wording sign-off required)
- **Separate, explicit screen** — never bundled into onboarding, Terms, or the OS camera prompt; the OS camera permission is requested **after** consent.
- **Written release**, one plain sentence, affirmative tap only — no pre-checked boxes, no "by continuing you agree."
- **Default is "pick a preset"**, so the vast majority of users never trigger any biometric processing (data minimization by default).
- **Layered, purpose-specific, default-off opt-ins**, each writing an immutable consent record (`data/schemas/avatar/consent_record`): **(A)** on-device face processing (the BIPA release); **(B)** cloud-sync of params; **(C)** per-share upload of a **gameplay-view** clip/shot (highlight / summit / competition — rarely shows a face), into moderation (#026); **(D)** training (de-identified derived data only — never photos or the face).
- **Versioned** consent; any material wording change re-prompts and writes a new record.
- **One-tap withdrawal + delete** in Settings, completing within 30 days (photos were never persisted).
- **13+ age gate** precedes consent.

## 4. Retention & deletion
Face frames/landmarks are **destroyed on-device immediately after the avatar is fit** — never persisted, never transmitted. Consent records carry **no image and no raw biometric** (proof-of-consent only). Withdrawal/deletion removes the avatar params and stops processing; there is no server-side biometric to delete. Public schedule: `legal/RETENTION_SCHEDULE.md` (biometric section to be reframed on-device/no-vendor).

## 5. Statute surface (for your confirmation)
We believe these apply; please confirm scope and sufficiency:

- **BIPA (Illinois):** §15(a) retention/destruction schedule, §15(b) informed written release **before collection**, §15(c) no sale/profit, §15(d) no disclosure without consent, §15(e) standard of care.
- **CUBI (Texas):** §503.001 — consent before capture; destroy within a reasonable time (≤ 1 yr after purpose).
- **MHMDA (Washington):** consumer-health-data consent + withdrawal **if in scope**.
- **GDPR Art. 9** (if/when EU users): biometrics are special category → explicit consent.
- **Apple:** App Store UGC rules + **privacy labels** (on-device-only biometric input).

A requirement → app-behavior table is in `legal/BIPA_CONSENT.md` §5.

## 6. Specific questions for counsel
1. **On-device capture as "collection."** Does transient, **on-device** extraction of face geometry — immediately discarded, never transmitted — still constitute "collection/capture of a biometric identifier" under BIPA §15(b) / CUBI? (We assume **yes** and gate consent **before** capture regardless — please confirm that is sufficient.)
2. **Written-release wording.** Does the §2 one-sentence release satisfy BIPA §15(b) "written release" once **reframed** to on-device/no-vendor (no "sent to a provider")?
3. **No-disclosure posture.** With **no vendor/processor** and no transmission, is §15(d) disclosure consent simply **not triggered**? Any residual disclosure language to keep or drop?
4. **Retention schedule.** Is "destroyed on-device immediately after generation; only non-identifying params persist" adequate under §15(a) / CUBI, and must the **public** written schedule still enumerate biometric even though nothing biometric persists server-side?
5. **MHMDA scope.** Are we in scope, and if so is a **distinct MHMDA consent string** required?
6. **Minors.** The gate is **13+**. For ages 13–17, is parental consent required (BIPA or elsewhere), or should custom-avatar creation be **18+**?
7. **Non-US / geo variants.** Do we need a signed or geo-specific consent variant (GDPR explicit consent; other US state laws)?
8. **Privacy labels.** Confirm the correct Apple privacy-label treatment for on-device-only, non-persisted biometric input (we expect "data not collected").
9. **Sign-off to freeze.** With the above resolved, approve the final wording so we can freeze `consent_text_hash` as `consent-v1`.

## 7. Pre-sign-off worklist (engineering; gated by your answers)
Before the runtime ships, the Builder will finalize (and you re-review): **reframe** `legal/BIPA_CONSENT.md` §2/§3/§5 vendor language → on-device/no-vendor; align the biometric sections of `legal/RETENTION_SCHEDULE.md`, `legal/PRIVACY_POLICY.md`, `legal/DELETION_FLOW.md`, `legal/APP_STORE_UGC_COMPLIANCE.md`; produce the Apple privacy-label matrix. Building now and **not** gated on you: the non-biometric data contracts (done) and the preset-roster path (M1-AVAT-01).

## 8. References
- `governance/AUTHORIZATION_LOG.md` — AUTH #044 (+ 2026-10-02 addendum) · AUTH #016 (in-house legal) · AUTH #007 (secondary review)
- `ADRs/0007-v1-custom-avatars-parametric-on-device.md`
- `design/proposals/custom-avatars-v1.md`
- `governance/SECURITY_CHECKLIST.md` §5 / §6
- `legal/BIPA_CONSENT.md` (draft; vendor passages pending reframe)
- `data/schemas/avatar/` — `avatar_params`, `consent_record`, `validate_avatar.py`, tests
- Tickets: M1-AVAT-01..05, **M1-LEGAL-01**

---

*Not legal advice. Prepared to scope counsel's review under the AUTH #044 binding condition (`SECURITY_CHECKLIST` §5.5, AUTH #016) plus secondary security review (AUTH #007). This brief contains no secrets, no user biometric data, and no personal data.*
