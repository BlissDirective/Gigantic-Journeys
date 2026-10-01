# Custom avatars in v1 — parametric, privacy-first

**Proposal · 2026-10-01 · Builder/Coordinator (AUTH #027) · requests AUTH #044**
Supersedes the **avatar half of AUTH #020 / ADR-0006** (which deferred custom likeness avatars to V2).
**Security-sensitive (biometric)** → 100 % secondary review (AUTH #007) **and** in-house counsel sign-off
before the feature ships (SECURITY_CHECKLIST §5.5, AUTH #016). This proposal specs the design and builds
the **non-biometric data contracts**; the on-device biometric runtime is gj-gameplay/Operator (iOS) and
**gated on the legal review**.

Owner direction (this session): move custom avatars into v1 as **parametric variations of one base body**;
if a user declines custom, they pick a selectable character; **(1)** target "idealized me" (semi-similar
hair/skin/face-shape/signature features, need not be fully recognizable); **(2)** face restricted to
on-device, in-game highlight/summit/competition captures are from the gameplay view (rarely show the
face), and any upload of shots/video is **100 % opt-in**; **(3)** spec + build now.

---

## 0. The decision
- **v1 avatar = one base rig + a parameter set.** Every character — the 8 selectable presets (#024) and a
  user's custom avatar — is the **same thing**: a bounded, non-identifying **parameter set** ("genome") on
  the shared GJ humanoid rig (1 A, foot/hand IK markers, tool sockets). Preset = a curated parameter set;
  custom = a parameter set fit on-device from the user's face. **Identical representation → conformant by
  construction → all movement works unchanged.**
- **Custom is fully optional and fully opt-in.** Default path is "pick a character." Custom is a separate,
  explicit, consented flow.
- **Everything is layered opt-in** (§4): nothing biometric happens without consent; nothing leaves the
  device without a *separate, purpose-specific* opt-in.

## 1. The Owner's two legal questions — answered
**Q1: Does opt-in for custom avatar help compliance?** **Yes — it is the cornerstone.** BIPA §15(b) and
CUBI require *informed written consent/release before collection*; GDPR Art. 9 treats biometrics as special
category needing explicit consent. A separate, explicit, unbundled opt-in (our SECURITY_CHECKLIST §5.2) is
exactly what these require. Default-off + "pick a preset instead" means the vast majority of users never
trigger biometric processing at all — the strongest possible posture (data minimization by default).

**Q2: Does a *second* opt-in for any online submission / data collection help?** **Yes — strongly.**
Layered, *purpose-specific* consent (a distinct opt-in for custom-avatar creation, then again for cloud
sync, then again per share-type: highlight / summit / competition) is the gold standard for **purpose
limitation + data minimization** (GDPR Art. 5; BIPA intent; Apple's data-use rules). It makes the default
"**nothing leaves your device**," and each outward step an affirmative, revocable choice. Combined with your
point that **gameplay-view captures rarely show the avatar's face**, even shared content carries little to
no biometric signal.

**The honest caveat.** Opt-in is *necessary but not sufficient*. The full package still needs: versioned
informed-consent copy that re-prompts on change (§5.5), a **public biometric retention/destruction
schedule** (BIPA §15(a)), one-tap withdrawal + deletion (§5.4), a **13+ age gate** (§5.6, already a v1
requirement) and minors handling, no sale/transfer (§5.3/§15(c)), and accurate **Apple App Store privacy
labels** + UGC compliance. All of this is **drafted already** in `legal/` for V2 — this proposal activates
and *strengthens* it for v1, and it ships only after in-house counsel signs off.

**Why our design is *stronger* than the framework we drafted.** The existing `legal/BIPA_CONSENT.md`
assumed photos are uploaded to a **vendor** (Meshy/Tripo) and deleted "at the provider." Our design has
**no vendor and no upload**: the face is processed **only on-device** (ARKit/Vision landmarks → coarse
params), the photo/video is **discarded on-device and never transmitted or stored server-side**, and only a
**non-identifying parameter set** persists. We never hold a biometric identifier at all — a materially
lower-risk posture than the V2 plan.

## 2. Avatar representation — the parameter set (the "genome")
One schema (`data/schemas/avatar/avatar_params`) used by presets and custom alike, on `gj-humanoid-1A`:
- **body** (height/build morph weights, bounded), **face** (a handful of coarse shape morph weights —
  *not* landmarks, *not* a face template), **skin_tone** (bounded/enumerated), **hair** (style enum +
  colour), **features** (glasses / facial-hair / etc. enums), **cosmetic** (outfit SKU + material tier —
  the AUTH #024 IAP SKUs), **provenance** (`preset` + preset_id, or `custom_on_device`).
- **Forbidden by schema** (`additionalProperties:false` + an explicit no-list): any photo/video bytes,
  facial landmarks, a face embedding/recognition template, or raw measurements that could re-identify.
  **The parameter set is cosmetic, bounded, and non-identifying — it is not biometric data.**
- Because it's a reshape/reskin of the one base rig, a custom avatar **passes rig-conformance by
  construction** (no per-avatar retarget / verb-clip gate; #024) and every clip + the #043 fluidity pack +
  motion matching work on it with zero changes.

## 3. The custom pipeline (on-device, no vendor)
1. **13+ age gate** (§5.6) → **"Create your avatar" intro** → **separate biometric consent screen** (§5.2;
   `legal/BIPA_CONSENT.md`) → **then** the OS camera permission.
2. On-device capture → **ARKit/Vision face landmarks** (+ optional short guided video) → **fit** the coarse
   `avatar_params` (an "idealized me": approximate face shape, skin tone, hair, signature features).
3. **Discard** all media + landmarks immediately on-device. **Persist only `avatar_params`** (on-device by
   default; server-side only with the separate cloud-sync opt-in, §4). Nothing is uploaded to any vendor —
   there is no vendor.
Target fidelity: **semi-similar / idealized**, not exact — which is cheaper, more robust to a bad selfie,
avoids the uncanny valley, and matches the 1:12 stylized world.

## 4. Privacy architecture — the layered opt-in
Each layer is a **separate, explicit, default-off** consent with its own immutable **consent record**
(`data/schemas/avatar/consent_record`: `purpose`, `granted`, `policy_version`, `consent_text_hash`,
`timestamp`, `locale`, `app_version`). No action in a layer is permitted without a matching `granted` record.

| Layer | Purpose | Default | What it gates |
|---|---|---|---|
| **A** | `custom_avatar_biometric` | off → pick a preset | on-device face processing to fit `avatar_params` (BIPA release) |
| **B** | `avatar_cloud_sync` | off (on-device only) | storing the **parameter set** server-side (cross-device; non-biometric) |
| **C** | `share_highlight` / `share_summit` / `share_competition` | off | uploading a **rendered gameplay clip/shot** (ties to M4 publish + moderation, #026) |
| **D** | `training` | off | de-identified derived data only — never photos, never the face |

Default state: **everything on-device, nothing shared.** Withdrawal is one tap (§5.4) and deletes the
avatar + stops processing; since no photo was ever stored, there's nothing server-side to delete beyond the
params. Shared clips are **gameplay-view** (rarely any face), per-share opted-in, and moderated (#026).

## 5. Compliance mapping (activate + strengthen SECURITY_CHECKLIST §5/§6)
- **§5.1** → strengthen: "face/body bytes **never leave the device** (no vendor, no upload); only the
  non-identifying `avatar_params` persists." A consent record exists **before** any capture.
- **§5.2** separate explicit consent screen (not bundled) — as drafted.
- **§5.3** training opt-in default off (layer D).
- **§5.4** one-tap withdrawal + delete within 30 days.
- **§5.5** versioned consent copy, re-prompt on change — **counsel reviews before the v1 feature ships**
  (the gate moves earlier than M5, because the feature is now v1).
- **§5.6** 13+ age gate (already v1) + minors handling for counsel.
- **§6.2** → **N/A-by-design**: no vendor and no server-side photo ever; media is discarded on-device.
- Apple: UGC compliance (`legal/APP_STORE_UGC_COMPLIANCE.md`, #026 moderation) + accurate **privacy
  labels** reflecting on-device-only biometric use.

## 6. Integration (why this is cheap for us)
- **Rig-conformant by construction** (§2) → motion matching, IK, tool sockets, the #043 fluidity/realism
  pack, and the whole clip DB work on any avatar unchanged.
- The **roster (8 presets, #024)** becomes 8 curated `avatar_params` on the same base — no separate asset
  path.
- No new runtime cost beyond a reskin/reshape of the base mesh; stays inside the mobile budget and quality
  tiers (AUTH #003).

## 7. What I build now vs. who builds the rest
- **Builder, now (deterministic, non-biometric, testable here):** the `avatar_params` + `consent_record`
  **schemas + validator + tests + fixtures**, and the on-device-pipeline **CONTRACT** doc. These define and
  enforce the data-minimizing privacy architecture; no face is processed in Python.
- **gj-gameplay / Operator (iOS, Unity C#/Swift):** the on-device capture + landmark fit + params
  application on the base rig; the consent/opt-in UX; render + per-share upload.
- **In-house counsel (AUTH #016):** sign off the biometric consent copy + retention + minors + privacy
  labels **before the feature ships**. This is a hard gate — the runtime does not ship without it.

## 8. Governed edits required (under AUTH #044)
- **SECURITY_CHECKLIST §5/§6** — activate for v1 with the strengthened on-device-only controls + the
  counsel-before-ship gate. (M-plan rows updated: biometric gate is a v1 item, not V2.)
- **ADR-0007** — custom avatars in v1 as parametric on-device variations; supersedes ADR-0006 (avatar half).
- **SPEC** §1/§2/§3.2/§3.9/§4/§7/§8/§9 — avatar section: preset **or** custom-parametric; on-device
  biometric; data classes + deletion.
- **DESIGN_SYSTEM decision 4** — character selection = pick-a-character **or** create-custom flow.
- **legal/** — `BIPA_CONSENT.md` reframed to **on-device/no-vendor** (even simpler release: "your photos
  never leave your device"), `RETENTION_SCHEDULE`, `PRIVACY_POLICY`, `APP_STORE_UGC_COMPLIANCE`,
  `DELETION_FLOW`. Drafted by the Builder; **counsel-gated** before ship.

## 9. Tickets (M1, area AVAT)
- **M1-AVAT-01** (gj-gameplay) — parameter-set avatar model + roster presets on the shared rig + in-app selection.
- **M1-AVAT-02** (gj-gameplay/Operator) — on-device custom pipeline: capture → landmark fit → `avatar_params` → discard media (iOS).
- **M1-AVAT-03** (gj-gameplay) — layered consent/opt-in UX + consent records (A/B/C/D).
- **M1-AVAT-04** (gj-gameplay) — per-share upload opt-in + gameplay-view capture, into the M4 publish/moderation path (#026).
- **M1-AVAT-05** (claude-builder) — the Brain-B data contracts (this proposal builds it): schemas + validator + tests + CONTRACT.
- **M1-LEGAL-01** (owner/counsel) — reinstated for v1: counsel review of the biometric consent/retention/labels before ship.

## 10. Risks
- **BIPA is litigious** (statutory damages, private right of action). Mitigation: on-device-only + no
  template stored + explicit versioned consent + retention schedule + the counsel gate. **Do not ship the
  runtime before counsel sign-off.**
- **Minors / App Store** — 13+ gate + minors handling + accurate privacy labels (counsel + review).
- **Scope** — the *data contracts* are cheap and land now; the iOS runtime is real work (Operator) and must
  not destabilize the v1 critical path. Custom is optional, so presets ship regardless.
- **Determinism** — `avatar_params` must stay within the rig's conformance envelope so motion never breaks;
  the validator enforces the bounds.

## 11. AUTH request — #044
Requesting `APPROVED #044` for **custom avatars in v1 as parametric, on-device, opt-in variations**, with:
(1) the data contracts + tickets in §7/§9 (buildable now, no biometric processing); (2) the governed edits
in §8 under this AUTH; (3) an explicit **condition**: the on-device biometric runtime (M1-AVAT-02) and the
consent copy ship **only after in-house counsel sign-off** (SECURITY_CHECKLIST §5.5) and secondary security
review (AUTH #007). Supersedes the avatar half of #020 / ADR-0006. Type: design-change + milestone-plan
(SECURITY_CHECKLIST, ADRs, SPEC, DESIGN_SYSTEM, legal, data/schemas). Cost: **$0** (on-device; no vendor).
Reversible: yes (custom is optional; presets are the default path).
