# Gigantic Journeys: Privacy Policy (DRAFT)

**Status: DRAFT v0.2 · 2026-09-29 · NOT YET IN FORCE.** This is an engineering draft, not legal advice. The Owner's in-house
legal team reviews it before M5 (AUTH #016; SPEC §9.6). Bracketed `[…]` fields are placeholders for the Owner or counsel.

**v0.2 changes (from v0.1, 2026-09-17):** rewritten for the v1 scope under AUTH #020 / ADR-0006.
- v1 has **no face or body capture and no biometric processing**; characters are pre-made.
- The data table now follows [`RETENTION_SCHEDULE.md`](RETENTION_SCHEDULE.md) v0.2, and deletion links [`DELETION_FLOW.md`](DELETION_FLOW.md).
- Telemetry is described from the frozen schema v1.0.0 and the proposed App Store privacy label (`data/schemas/README.md`).
- Processors are updated: reconstruction runs on our own infrastructure (ADR-0005). Luma was dropped, and the avatar vendor is V2 only.
- Publishing and moderation (SPEC §3.7, AUTH #026) and people in frame (AUTH #025) are added.

The v0.1 biometric text moves to the V2 appendix and to [`BIPA_CONSENT.md`](BIPA_CONSENT.md).

Publisher: **SparkForge Labs** ([entity form and state to confirm]). App: **Gigantic Journeys** (`com.sparkforgelabs.giganticjourneys`).
Contact: **[privacy@giganticjourneys.com, mailbox to create]**. Effective date: **[on publish]**.

---

## 1. What this app does

Gigantic Journeys turns a place you capture (a room or a tabletop build) into a small playable world that a pre-made
character climbs through. To do that, we process **video of your physical space**. We **don't** collect photos of your face or
body, and we don't process biometric data. This policy explains what we collect, why, how long we keep it, who processes
it, and how you delete it.

## 2. The data we process

This table follows our published [retention schedule](RETENTION_SCHEDULE.md).
- **Source media** means the video and motion data you capture.
- **Derived assets** means the 3D environment we build from it.

| Data | When | Why | How long | How it is deleted |
|---|---|---|---|---|
| **Capture video and motion data** (camera poses, depth, gravity; no location) | You capture a place | To rebuild it in 3D | Until your environment is built, **at most 24 hours** after upload; failed builds **at most 7 days** | Automatically, and by Delete my data |
| **Your environments** (3D model, collision shape, route data, thumbnail) | After a capture is rebuilt | So you can play and, if you choose, publish | While you keep them. Published copies stay while published. | Delete an environment (immediate) or Delete my data. Unpublishing removes it from browse immediately. |
| **Character choice and purchases** | You pick a character or buy a cosmetic | So your choices persist and purchases can be restored | While your account exists | Delete my data. Apple keeps its own purchase records. |
| **Account** (a sign-in identifier from Sign in with Apple or Google; a relay email only if you share one) | You create an account | To keep your environments and purchases yours | While your account exists | Delete my data (we also revoke the Apple sign-in token) |
| **Gameplay and quality events** (a pseudonymous id; play, capture, route, rating and correction events; performance numbers. **No location, no email, no photos or video, no free text.**) | While you use the app | To fix crashes, improve capture quality and tune journeys | Raw events **[N days; proposal 90]**; totals without your id are kept | Delete my data removes your raw events and rotates your id |
| **Corrections** ("fix this label") | You correct a label | To improve the app. Used for training **only if you opt in** (§5). | Derived data only | Opt out stops future use; Delete my data removes them |
| **Ratings, reports and leaderboard times** | You rate, report or finish a timed route | Rankings, leaderboards and moderation | While the environment exists | With the environment, or your own rows with Delete my data |
| **Consent and terms records** (policy version, time, locale, a hash of the text you accepted) | You accept the terms or this policy | Proof of what you agreed to | **[period set by counsel]** | Destroyed when that period ends. Kept after Delete my data, without any content, as legal proof. |

**Location:** we don't collect precise location. GPS and other location metadata are **removed on your phone before
upload and checked again on our servers**; an upload that still carries location is rejected.

**People in your capture:** the app coaches you to capture spaces, not people. It doesn't detect or recognise faces. Your
captures are processed only on our own infrastructure. Anything you choose to **publish** also passes our moderation check
(§4) before anyone else can see it.

## 3. How we build your environment

Your capture is uploaded over an encrypted connection to private storage. It is rebuilt on **computers we control**
(rented cloud computers that keep nothing after the job; see §6), and the source video is deleted as soon as the build
succeeds. No third-party reconstruction service processes your captures. A separate test corpus, made of open-licence
and consented videos, is used to develop the app and is never mixed with your data.

## 4. Publishing, browsing and moderation

Environments are **private unless you publish them**. When you publish one:
- **Location data is stripped again.**
- **An automated check** looks at the published environment and its thumbnail. Environments waiting for it show "Under
  review" and only you can play them.
- **Anyone can report** an environment. A person reviews reports and appeals, seeing only the published thumbnail and
  environment, never your source video.
- **Other players see** your environment, a display name or id **[until profiles exist, an id]**, play counts, ratings and
  route times. You can unpublish at any time.
- **You can block players**, and we act on abusive content (see the [Terms of Service](TERMS_OF_SERVICE.md)).

## 5. Training opt-in (separate, off by default)

With your permission, we may use **derived, de-identified data** (such as your label corrections) to improve the app's
understanding of surfaces. We **never** train on your raw video. The switch is separate from everything else and **off by
default**. Turning it off stops future use; Delete my data removes past contributions.

## 6. Who processes your data for us

Each processor works under a data-processing agreement with retention and deletion terms on file **before it touches your
data**. We don't use vendors that train on customer data by default.

| Processor | Purpose | What it handles |
|---|---|---|
| **Supabase** | Accounts, database, private file storage | Account, environments, consent records, gameplay events, ratings, reports |
| **Modal** (rented GPU compute) | Runs our reconstruction software | Your capture, **only for the duration of the job**; nothing is kept afterwards |
| **Inngest** | Coordinates background jobs | Job ids and status; no media |
| **Apple** | App distribution, in-app purchases, Sign in with Apple | Purchase and sign-in data under Apple's policy |
| **Google** (if you use Google sign-in) | Sign-in | Sign-in data under Google's policy |
| **[Moderation vision check provider, if external; confirm in M4]** | The automated check on published environments | The published thumbnail and environment only |

We list any change in [`legal/vendors/`](vendors/) and update this table before adding a processor.

## 7. Your choices and rights

- **Delete my data (one tap, in Settings).** This deletes your account, environments, captures, gameplay events,
  corrections and your own ratings, reports and times, including copies at our processors. It finishes **within 30 days**,
  and backups expire within **[the backup window]**. The steps are in [`DELETION_FLOW.md`](DELETION_FLOW.md).
- **Delete one environment or unpublish it** at any time.
- **Training opt-in:** on or off in Settings (§5).
- Depending on where you live (for example California, the EEA or the UK) you may have more rights, such as access or
  correction. Contact **[privacy@giganticjourneys.com]** and we will honour the law that applies. We won't treat you
  differently for using a privacy right.

**App Store privacy details (proposed; see `data/schemas/README.md`):**
- **Identifiers:** User ID (pseudonymous).
- **Usage Data:** Product Interaction.
- **Diagnostics:** performance data.

All are linked to your account and none are used for tracking. **Not collected:** location, contact info, contacts, photos or videos, device ID.

## 8. Children

Gigantic Journeys is for players **13 and older**. An age check runs before an account is created. We don't knowingly
collect data from anyone under 13, and we delete it if we learn we have.

## 9. Security

- Data is encrypted in transit.
- Storage is private by default, and files are shared only through links that expire within 15 minutes.
- Every database table is protected by row-level security.
- Production keys live only in our build system.

The full list of controls is in `governance/SECURITY_CHECKLIST.md`.

## 10. Changes to this policy

This policy is versioned. We tell you in the app before a material change applies, and the version and date appear at the top.

## 11. Contact

**[privacy@giganticjourneys.com]** for privacy requests and questions. **[Postal address, required by some app stores and laws; to add.]**

---

## Appendix: V2 custom avatars (not part of v1)

A later version may offer a custom avatar made from photos of you. If it ships:
- Face and body photos become **biometric data**, processed only after a separate, written consent (`BIPA_CONSENT.md`).
- They are deleted immediately after the avatar is generated, on the device, in storage and at the vendor.
- They are never sold and never used for training.

This policy will be updated, and you will be asked for consent, before any such feature processes your data.

---

*Drafting notes for counsel (delete before publishing):*
- *Confirm the entity and the governing state.*
- *Set the raw-telemetry TTL, the consent-record period and the backup window (RETENTION_SCHEDULE §4).*
- *Confirm that the 24 h / 7 d raw-media promise is publishable.*
- *Confirm the California (CCPA/CPRA "sale/share": none) and EEA/UK disclosures, including the legal bases and international transfers (Modal and Supabase regions).*
- *Confirm the moderation-provider disclosure once M4 picks one.*
- *Confirm whether display names or ids are shown on leaderboards (M4-DATA-01).*
- *Set the postal contact.*
