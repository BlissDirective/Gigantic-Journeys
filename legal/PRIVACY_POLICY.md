# Gigantic Journeys — Privacy Policy (DRAFT)

> **v1 scope note (AUTH #020, 2026-09-18):** v1 collects **no biometric data** — the avatar is a pre-made character, there is no face or body capture. **§3 (biometric handling) applies to the V2 custom-avatar feature only.** In v1 the sensitive user media is room/tabletop **scans** (processed on our own infrastructure); the rest of this policy applies as written.

**Status: DRAFT v0.1 · 2026-09-17 · NOT YET IN FORCE.** This is an engineering draft prepared by the Coordinator to operationalize `SPEC.md` §7 and `governance/SECURITY_CHECKLIST.md` §4–§6. **It is not legal advice.** Counsel must review and approve it before any real user data is processed (biometric consent goes live at M2; full sign-off is an M5 gate — `SECURITY_CHECKLIST §5.5`, SPEC §9.6). Bracketed `[…]` fields are placeholders the Owner fills.

Publisher: **SparkForge Labs** ([entity form + state to confirm — AUTH account track]). App: **Gigantic Journeys** (`com.sparkforgelabs.giganticjourneys`). Contact: **[privacy@giganticjourneys.com — mailbox to create]**. Effective date: **[on publish]**.

---

## 1. What this app does, in one paragraph

Gigantic Journeys turns a place you scan — a room or a tabletop build — into a tiny playable world, and turns a photo of you into a small 1:12 avatar that journeys through it. To do that, the app processes **photographs and video of your physical space** and, only after your explicit consent, **photographs of your face and body** to generate an avatar. This policy explains exactly what is collected, how long it is kept, who processes it, and how you delete it.

## 2. The data we process

This mirrors the authoritative table in `SPEC.md §7`. "Derived assets" means the reconstructed world/avatar the app builds from your capture; "source media" means the raw photos/video you captured.

| Data class | Collected when | Why | Retained until | How it is deleted |
|---|---|---|---|---|
| Raw scan video, poses, depth | you scan a space | to reconstruct the environment | derived assets exist; failed jobs ≤ 7 days | automatically; and by per-user delete-all |
| **Face and body photos (biometric)** | avatar creation, **after consent only** | to generate your avatar (a vendor job) | until the avatar is generated | **immediately after generation** — on device, in storage, and at the vendor; a deletion receipt (no media) is logged |
| Derived environment assets (splat, mesh, graph, spec, thumbnail) | reconstruction | so you can play and publish | while you keep it; published copies while published | per-user delete-all; unpublish removes from feeds immediately |
| Avatar assets (head mesh, textures, body parameters) | avatar creation | so your avatar persists | while your account exists | per-user delete-all |
| Consent records (policy version, timestamp, locale, text hash, stated retention) | at consent | legal proof of consent | as long as legally required, then destroyed | per the retention schedule |
| Telemetry events (frozen schema, pseudonymous id; **no GPS, no email, no media, no free text**) | during play | crash/quality/usage improvement | raw events per the retention schedule; aggregates kept | per-user delete-all |
| Correction events ("fix this label") | when you tap to correct | to improve the app, **training opt-in only** | derived data only | opt-out stops future use; delete-all removes |
| Ratings, reports, leaderboard times | community actions | the public leaderboard and moderation | while the environment/account exists | with the environment or the account |

We do **not** collect precise location. **GPS and EXIF/location metadata are stripped from every image and video on your device before upload, and stripped again on the server** (`SECURITY_CHECKLIST §4`).

## 3. Biometric data — special handling (Illinois BIPA, Texas CUBI, Washington MHMDA)

Your face and body photos are **biometric information**. Because of that:

- **Consent first.** No face or body photo leaves your device, and no avatar-generation job is created, until you have given **written, informed consent** in a separate, explicit step (not bundled into onboarding, terms, or the camera permission). See `legal/BIPA_CONSENT.md`.
- **A published retention & destruction schedule.** We keep a public schedule (`legal/RETENTION_SCHEDULE.md`) and destroy biometric source media on the timeline it states — here, **immediately after your avatar is generated**.
- **No sale, no profit, no disclosure.** We do not sell, lease, trade, or otherwise profit from your biometric data, and we do not disclose it except to the avatar-generation processor that creates your avatar, under contract, or as required by law.
- **Training is separate and off by default.** We never use your biometric data or derived avatar data to train models unless you turn on a **separate** training opt-in (§4), which concerns derived data only.
- **Withdrawal and deletion.** You can withdraw consent and delete everything from Settings at any time (§6).

The exact statutory requirements are mapped to app behavior in `legal/BIPA_CONSENT.md §5`. Counsel confirms scope and wording before M2.

## 4. Training opt-in (separate, default off)

Improving the app (for example, the surface classifier retrained post-launch, SPEC §M6) uses **only derived, de-identified data from users who explicitly opt in**, and **never** raw photos or video. The toggle is separate from consent and is **off by default**. Opting out stops future use; delete-all removes your prior contributions.

## 5. Who else processes your data (sub-processors)

We use a small set of vendors strictly to run the service. Each has a data-processing agreement and retention/deletion terms on file **before it touches user data** (`SECURITY_CHECKLIST §6.3`). A vendor that trains on customer data by default is not used without an opt-out in place.

| Processor | Purpose | Data it sees |
|---|---|---|
| **Luma** | scan → 3D reconstruction | raw scan video/poses/depth (not faces) |
| **[Meshy or Tripo — one, confirmed at M2]** | avatar head generation | face/body photos, transiently, deleted immediately after the job |
| **Supabase** | auth, database, storage | account, derived assets, consent records, telemetry |
| **Apple** | app distribution, IAP, TestFlight | account/purchase data per Apple's policy |

The current sub-processor list is maintained in `legal/vendors/`. We update it here before adding a processor.

## 6. Your rights and how to exercise them

- **Delete everything (one tap).** Settings → Delete my data removes every data class in this policy from your device, our storage, and our vendors, and completes within **30 days** (`SECURITY_CHECKLIST §5.4, §6`). Biometric source media is already deleted immediately after avatar generation.
- **Withdraw consent (one tap).** Stops all future biometric processing and deletes derived avatar data on request.
- **Access / correct / opt out of training** from Settings.
- Depending on where you live (e.g., Illinois, Texas, Washington, California, EEA/UK), you may have additional rights; contact **[privacy@giganticjourneys.com]** and we will honor applicable law. We do not discriminate against you for exercising a right.

## 7. Children

Gigantic Journeys is **13+**. We do not knowingly collect data from anyone under 13 and there is a **13+ age gate before consent** (`SECURITY_CHECKLIST §5.6`). No COPPA scope in v1 (SPEC §4).

## 8. Security

TLS in transit; storage buckets private by default with signed, short-lived URLs; row-level security on every database table; production keys held only in our build system, never on any workstation or agent. Full controls: `governance/SECURITY_CHECKLIST.md`.

## 9. Changes to this policy

We version this policy. A material change (especially to biometric handling) **re-prompts you for consent** before it applies to your biometric data (`SECURITY_CHECKLIST §5.5`). The version and date are shown at the top.

## 10. Contact

**[privacy@giganticjourneys.com]** — privacy requests and questions. **[Postal address — required by some app stores/laws; to add.]**

---

*Drafting notes for counsel (delete before publishing): confirm entity + governing state; confirm MHMDA applicability to identity-biometrics; confirm the biometric destruction timeline satisfies BIPA "≤ 3 years since last interaction" and CUBI "≤ 1 year after purpose"; confirm sub-processor disclosures; confirm required California/EEA disclosures if those users are in scope; set the postal contact.*
