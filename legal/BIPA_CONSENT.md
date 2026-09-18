# Biometric Consent — copy, flow, and record (DRAFT)

> **V2 ARTIFACT (AUTH #020 / ADR-0006, 2026-09-18).** v1 ships pre-made characters and processes **no biometric data**, so this consent flow is **not used in v1**. It is retained as the starting point for the **V2 custom-avatar** feature. Ticket M0-LEGAL-01 is cancelled for v1.

**Status: DRAFT v0.1 · 2026-09-17 · satisfies ticket M0-LEGAL-01 (draft).** Engineering draft of the exact consent experience and the consent record, operationalizing `governance/SECURITY_CHECKLIST.md §5` and `SPEC.md §3.9, §7`. **Not legal advice.** Counsel signs off the wording before it goes live at M2 (`SECURITY_CHECKLIST §5.5`). Owner/vendor placeholders in `[…]`.

The rule this enforces (`SECURITY_CHECKLIST §5.1`): **no face or body photo bytes leave the device, and no vendor job is created, until a consent record exists.**

---

## 1. Where consent sits in the flow

```
13+ age gate  →  "Create your avatar" intro  →  ┌─────────────────────────┐
(§5.6)                                          │  BIOMETRIC CONSENT STEP  │  ← separate, explicit, its own screen
                                                │  (this document)         │
                                                └─────────────────────────┘
                                                        │  consent recorded
                                                        ▼
                                       camera → capture → (on-device) → upload → vendor avatar job
```

Consent is **its own screen**, never bundled into onboarding, the Terms, or the OS camera-permission prompt (`§5.2`). The OS camera permission is requested **after** consent, separately.

## 2. The consent screen (primary copy)

**Headline:** Create your avatar from your photo

**The one plain sentence (the consent statement):**

> I agree that Gigantic Journeys can use photos of my face and body to generate my avatar, and I understand my photos are deleted right after the avatar is made.

**Primary button:** `I agree — continue`
**Secondary:** `Learn more` (opens the sheet in §3) · `Not now` (returns, no data collected)

Microcopy under the button:

> You're in control: you can withdraw consent and delete everything anytime in Settings. We never sell your biometric data. We don't use it to train anything unless you separately turn that on.

The **`I agree` button is the only thing that records consent.** No pre-checked boxes; no "by continuing you agree."

## 3. The "Learn more" sheet (secondary copy)

**What we collect.** Photos of your face and body that you capture in the next step.

**Why.** To generate your 1:12 avatar. The photos are sent to our avatar-generation provider (**[Meshy / Tripo — the one confirmed at M2]**) solely to create your avatar.

**How long we keep them.** Your face/body photos are **deleted immediately after your avatar is generated** — on your device, in our storage, and at the provider. We keep a deletion receipt (job id and timestamp) that contains **no image**.

**What we never do.** We never sell, trade, or profit from your biometric data. We never disclose it except to the provider that makes your avatar, under contract, or as the law requires.

**Training is separate.** We do **not** use your biometric or avatar data to improve our models unless you turn on the separate "Help improve Gigantic Journeys" toggle (off by default), which uses derived, de-identified data only — never your photos.

**Your rights.** Withdraw consent and delete everything in one tap in Settings; deletion completes within 30 days (biometric photos are already gone right after generation). Questions: **[privacy@giganticjourneys.com]**.

**The legal part.** Your face/body data is "biometric" under laws including the Illinois Biometric Information Privacy Act (BIPA), the Texas Capture or Use of Biometric Identifier Act (CUBI), and, where applicable, the Washington My Health My Data Act (MHMDA). This screen is your written release under those laws. Full detail: our Privacy Policy `[link]`.

## 4. The consent record (stored server-side; `§5.1`)

On `I agree`, write one immutable record **before** any capture:

```json
{
  "user_id": "<auth uid>",
  "policy_version": "consent-v1",
  "consent_text_hash": "<sha256 of the exact statement shown in §2>",
  "timestamp": "<UTC ISO-8601>",
  "locale": "<e.g. en-US>",
  "stated_retention": "deleted immediately after avatar generation; receipt retained without media",
  "app_version": "<build>",
  "granted": true
}
```

Rules:
- The hash is of the **exact** on-screen statement, so we can always prove what the user saw.
- A new `policy_version` (any material wording change) **re-prompts** and writes a new record (`§5.5`).
- Withdrawal writes a `granted:false` record with its own timestamp and triggers deletion (§6).
- The record carries **no image and no raw biometric** — it is proof of consent, not biometric data.

## 5. Statute → app-behavior mapping (for counsel to confirm)

| Requirement | Source | How the app satisfies it |
|---|---|---|
| Written, informed consent (release) before collection | BIPA §15(b); CUBI §503.001(b) | §2 consent screen + §4 record, gated before any capture/upload |
| Public written retention & destruction schedule | BIPA §15(a) | `legal/RETENTION_SCHEDULE.md`, linked from the policy |
| Destroy when purpose met / within statutory limit | BIPA §15(a) (≤ 3 yrs since last interaction); CUBI (≤ 1 yr after purpose) | photos destroyed **immediately after generation** — well inside both |
| No sale / profit | BIPA §15(c); CUBI | §3 statement + `SECURITY_CHECKLIST` (no biometric monetization) |
| No disclosure without consent | BIPA §15(d) | only the avatar processor, under DPA; disclosed in §3 and the policy |
| Reasonable standard of care / storage | BIPA §15(e) | `SECURITY_CHECKLIST` (encryption, signed URLs, RLS, CI-only keys) |
| Consumer-health-data consent + withdrawal (if in scope) | WA MHMDA | separate consent screen + one-tap withdrawal; counsel confirms MHMDA scope |
| Separate consent for any secondary/training use | BIPA intent; general | training opt-in is a separate, default-off toggle (§3, Privacy Policy §4) |

## 6. Withdrawal and deletion copy (Settings)

**Toggle/section:** Biometric data & avatar

> **Withdraw consent & delete avatar.** This deletes your avatar and stops all future biometric processing. Your original photos were already deleted right after your avatar was made. Completes within 30 days.
> `Withdraw & delete`

Withdrawal: writes the `granted:false` record, deletes avatar assets, and — because source photos are already gone — logs completion. Full account delete-all is the broader flow in `RETENTION_SCHEDULE.md`.

---

*Drafting notes for counsel (delete before shipping): confirm the one-sentence release satisfies BIPA §15(b) "written release"; confirm MHMDA applicability and, if in scope, whether a distinct MHMDA consent string is needed; confirm minors handling given the 13+ gate; confirm whether a signed/geo-specific variant is needed for non-US users; approve the final wording so the `consent_text_hash` can be frozen as `consent-v1`.*
