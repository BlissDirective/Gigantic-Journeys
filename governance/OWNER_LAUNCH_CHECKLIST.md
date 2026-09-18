# Owner Launch Checklist

`governance/OWNER_LAUNCH_CHECKLIST.md` · v1.4 · 2026-09-18 · Maintained by the Coordinator, actioned by the Owner. Every task here is **Owner-level**: something only you can do, or must authorize and sign off. The agents do everything else. **Part 1** is the sequenced path (roughly chronological); **Part 2** is the cross-cutting tracks that run throughout. Check items off as you go; the Coordinator updates status at each checkpoint.

Legend: ☐ to do · ▶ in progress · ✅ done. AUTH numbers reference `governance/AUTHORIZATION_LOG.md`; ticket IDs reference `tickets/`.

Each task carries a **[priority · delegability]** tag.

**Priority** — what launch actually needs:
- **REQ** — a hard gate: Apple won't approve without it, the law requires it, or the core loop does not function.
- **REC** — not a gate anyone checks, but risky to skip *for this app specifically* (biometrics, photos of homes, minors, a public UGC leaderboard).
- **OPT** — growth, polish, or process convenience; defer, scale down, or cut for v1.

**Delegability** — how much you can offload:
- **Bot** — an agent can do it end-to-end once you authorize it: research, drafting, routine emails, staging config with no payment or secret, automated tests, monitoring, free-tier signups. *(Prefer the Claude Code Builder where a script or API exists; reserve the Grok Bot for true no-API GUI and long-running watches — `AGENT_GOVERNANCE §2`.)*
- **Bot-prep** — an agent does the bulk, but you must finish the act that carries weight: accept ToS, pay, enter/attest, sign, or move a secret into CI.
- **Owner** — you (or another human) only: physical capture; legal identity, signature, or payment as principal; reserved approval/decision authority; Apple-account access; secret/credential custody; GitHub repo admin (the Bot's PAT deliberately lacks Administration/Secrets/Actions — AUTH #002); or handling real user biometric/home media (`SECURITY_CHECKLIST §6.5, §10.4`).

Where a line bundles tiers, each sub-part carries its own tag.

## ⚠ v1 game-plan update (2026-09-18 — supersedes items below; SPEC v1.3 is authoritative)

Two Owner decisions change several items in this checklist:
- **v1 avatar = pre-made character roster, NO biometric** (ADR-0006 / AUTH #020). This **removes from v1**: the head-generation vendor (Meshy/Tripo/Avatar SDK), the biometric consent step + BIPA/CUBI/MHMDA sign-off, face/body captures, the avatar blind test, and the avatar-vendor DPA. Those items below are **V2, not v1**. M2 is now "Character & rig." Custom avatars → `research/rnd/`.
- **Reconstruction = self-host + KIRI corpus-only bridge** (ADR-0005 / AUTH #018). **Luma is dropped** — ignore Luma account/terms lines below. Home-scan data stays on our own infra.

The 13+ age gate, GPS/EXIF stripping, the privacy policy (room scans), moderation, IAP, and the rest stay as written.

## Minimum viable launch path (the REQ spine)

The smallest chain that legally and functionally ships. Everything not on it is REC (do if you can) or OPT (defer):

1. **Apple Developer account (held) + App Store Connect app record.**
2. **A coding surface** (the Claude Code Builder) and **Unity (Personal)** to build the app.
3. **Core services:** Supabase (production); one scan-reconstruction vendor (Luma); one head-generation vendor (Meshy **or** Tripo — not both).
4. **The core loop works:** scan → recognizable 1:12 avatar (behind an explicit consent step) → summit + two routes with no manual fixes → publish → a friend plays from a link. (This is the real content of M1 + M2 + M3.)
5. **Compliance gates:** biometric consent step; privacy policy at a public URL; App Store privacy nutrition labels; in-app account deletion (verified); 13+ age gate; GPS/EXIF stripping on uploads; UGC moderation + report + block.
6. **At least one test iPhone**, your own corpus scans, and **App Store screenshots**.
7. **Submit and respond to App Store review.**

One paid item is *not* on the REQ spine but I'd still not skip it: **a focused legal consult on the biometric consent copy + privacy policy** (BIPA/CUBI/MHMDA exposure). It's REC, but it's the highest-ROI risk reduction on the whole list.

**Read the delegability column together with this spine:** nearly every REQ line is **Owner** — physical capture, decisions, legal/identity acts, and real user data. Delegation offloads setup, configuration, research, drafting, and monitoring; it does **not** shorten the core. The biggest scope-cut levers remain: **launch free**, **volunteers not hires and single digits not dozens** of testers, **one head vendor**, and **adaptive Duo, no device purchase**.

# Part 1 — The sequenced path

## 0. Now — before you say `START M0`

- ☐ **[OPT · Owner]** **Create the Bot GitHub machine user + fine-grained PAT** (AUTH #002), scoped to this repo. Store in the Bot credential store and `.env.local`. Ticket M0-REPO-04. *(Bootstrap credential — can't use the Bot to create the Bot's own identity; only needed if you run the Grok Bot pipeline.)*
- ☐ **[REC · Owner]** **Set branch protection + native secret scanning on `main`** (M0-REPO-02, revised by AUTH #007). *(Needs repo Administration, which the Bot's PAT lacks by design; secret scanning is free and worth keeping.)*
- ☐ **[REQ · Owner]** **Create the App Store Connect app record** for `com.sparkforgelabs.giganticjourneys` (reserves the name) with an internal TestFlight group. **[REC · Owner]** **Add the ASC API key to CI secrets** (`ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`) + `APPLE_TEAM_ID` (M0-REPO-05). *(Apple-account access + CI secret custody.)*
- ☐ **[REQ · Owner]** **Start the coding surface** (the Claude Code Builder session). **[OPT · Owner]** **Create the Grok Bot** (`gj-operator`) and hand it the PAT. *(Bootstrap.)*
- ☐ **[REQ · Owner]** **Approve the essential accounts** in the M0 batch (#008 on): Supabase, one head vendor, Luma, Unity. **[OPT · Owner]** the rest: Vercel, Inngest, the two domains, USPTO search, the second head vendor. *(Approval authority; the account creation itself is Bot-prep — see the Accounts track.)*
- ☐ **[REC · Bot-prep]** **Buy Motion Warping: Climb & Interact** ($19.99, AUTH #001). **[OPT · Bot-prep]** **Register the domains** `giganticjourneys.com` + `.app`. *(An agent can drive the purchase flow; you authorize the payment.)*
- ☐ **[REQ · Owner]** **Scan the day-one corpus** (M0-OWNER-01): 10 rooms + 5 tabletop builds; no faces/documents/addresses; GPS off. **[REC · Owner]** **Film the movement reference captures** (Bible §7). *(Physical capture — no agent has a camera.)*
- ☐ **[REQ · Owner]** **List the iPhones you own** for the quality tiers. **[OPT · Owner]** **Decide on an iPhone Duo dev device.** Then **[REQ · Owner] issue `START M0`.**

## 1. M0 — Harness

- ☐ **[REC · Owner]** **Add Unity license secrets to CI** (M0-REPO-03). *(CI secret custody.)*
- ☐ **[REC · Bot]** **Send the vendor data-retention questions** to Luma and the head vendor; collect answers for `legal/vendors/`. *(Agent drafts and sends; you're cc'd.)*
- ☐ **[REC · Bot-prep]** **Engage the attorney** to review the consent, retention, and deletion drafts. *(An agent can shortlist counsel and prepare the brief; you sign and pay.)*
- ☐ **[REQ · Owner]** **Answer AUTHs** as they arrive; keep the queue unblocked.
- ☐ **[REQ · Owner]** **Clear the M0 checkpoint:** `REVIEW M0`, confirm the exit test, then `RESUME M1`.

## 2. M1 — Scan to playable (the validation milestone)

- ☐ **[REQ · Owner]** **Have the reference iPhone(s) in hand** for the motion-matching spike (M1-MOVE-01) and performance targets.
- ☐ **[REC · Bot]** **Get Luma's retention/terms on file** before any real user scan (SECURITY_CHECKLIST §6.3). *(Agent can retrieve and file the terms.)*
- ☐ **[REQ · Owner]** **Scan 10 fresh rooms** (not in the training corpus) for the exit test (M1-QA-01).
- ☐ **[OPT · Owner]** **Approve or defer the monthly Tier 2 compute** (M1-RES-01).
- ☐ **[REQ · Owner]** **Clear the M1 checkpoint — the big go/no-go:** 8 of 10 fresh scans reach a summit with two routes, no manual fixes; confirm the animation-stack decision. Then `RESUME M2`. *(Existential; the 8/10 bar is your call.)*

## 3. M2 — Character & rig

- ☐ **[REQ · Bot-prep]** **Author/source the character roster** (~6–12 rigged, semi-photoreal 1:12 characters) and retarget the shared movement set (M2-AVAT-01). *(Art + integration — licensed, commissioned, or generated-once art; no user faces. Agents build the pipeline; you approve the look.)*
- ☐ **[OPT · Owner]** **Recruit a few play-testers** for character + movement feel. *(No biometric, no consent — just fun.)*
- ☐ **[REQ · Owner]** **Clear the M2 checkpoint:** the roster rigs and retargets cleanly, every character moves identically well, and the cosmetic IAP previews on the chosen character. Then `RESUME M3`.

*(v1 has no face capture, no biometric consent, no avatar vendor — AUTH #020. Custom likeness avatars are the V2 R&D track, `research/rnd/`.)*

## 4. M3 — Game loop, tabletop, and Duo

- ☐ **[REQ · Owner]** **Scan tabletop builds** (Lego and similar) — physical. *(Trim: OPT if you scope v1 to rooms-only.)*
- ☐ **[OPT · Owner]** **Verify the three Duo features** on a device, or review the adaptive design. Go/no-go per feature.
- ☐ **[REC · Owner]** **Play-test five environments** with you + three testers.
- ☐ **[REC · Owner]** **Clear the M3 checkpoint:** everyone wants a sixth; Tier 1 holds 30 fps on your older iPhone; Duo decided. Then `RESUME M4`.

## 5. M4 — Sharing, moderation, leaderboards

- ☐ **[REC · Owner]** **Recruit testers to publish environments.** *(Trim: a handful + seeded content is enough — not 50.)*
- ☐ **[REQ · Owner]** **The moderation queue + report + block** must exist and be operated as the escalation point (Apple UGC Guideline 1.2). *(Agents build it; you are the human escalation and Bots get no raw media.)*
- ☐ **[REC · Bot]** **Confirm the ranking resists a deliberate rate-spam test.** *(Automatable test the Builder can run.)*
- ☐ **[OPT · Owner]** **Decide repository public vs private** before broader user-data flows.
- ☐ **[OPT · Owner]** **Tier 2 decision:** v1.1, V2, or shelve.
- ☐ **[REQ · Owner]** **Clear the M4 checkpoint;** then `RESUME M5`.

## 6. M5 — Store readiness, IAP, and launch

- ☐ **[REC · Owner]** **Attorney final sign-off:** privacy policy, BIPA consent, retention schedule, deletion flow.
- ☐ **[OPT · Bot-prep]** **Configure the two IAP SKUs**, prices, and free-tier caps (a pricing AUTH). *(You decide prices; an agent enters them. Cut entirely if you launch free.)*
- ☐ **[OPT · Owner]** **Choose + set up the IAP provider** (RevenueCat or Unity IAP; ADR at M5) and complete App Store Connect **banking + tax**. *(Banking/tax are legal-identity acts.)*
- ☐ **[REQ · Bot-prep]** **Complete App Store privacy labels** accurate to the telemetry schema; **confirm the 13+ age gate.** *(An agent drafts the labels and builds the gate; you review and attest.)*
- ☐ **[REQ · Bot]** **Verify the data-deletion flow end to end** on staging (SECURITY_CHECKLIST §6.4). *(Automatable E2E test.)*
- ☐ **[REC · Owner]** **Grow the TestFlight cohort and reach a high crash-free rate.** *(Trim: "100 at 99%" is self-imposed; 10 testers + no known crashes is compliant. Real people + Apple-account admin.)*
- ☐ **[REQ · Bot-prep]** **Provide App Store screenshots** (diorama hero). **[OPT · Bot-prep]** **the preview video** + top-5-market localization. *(An agent can capture and upload drafts; you approve, and provide gameplay footage for the video.)*
- ☐ **[OPT · Bot-prep]** **Submit the App Store featuring nomination** citing Duo adoption (M5-DUO-01).
- ☐ **[REQ · Owner]** **Give explicit approval to submit,** then submit and respond to App Store review. *(Legal attestation.)*

## 7. M6 — Learning loops (post-launch)

- ☐ **[OPT · Owner]** **Approve the first surface-classifier retrain** (~4 weeks out) with before/after metrics. *(Agents run it after your approval.)*
- ☐ **[REC · Owner]** **Review the weekly data reports** and approve validator/generator update PRs. *(Agents generate the reports; you approve.)*
- ☐ **[REQ · Owner]** **Handle moderation escalations, crashes, and App Store review responses.** *(Agents can draft responses and triage crashes; moderation of real media and Apple replies are yours.)*

# Part 2 — Cross-cutting tracks

These run throughout the build, not at a single milestone.

## Accounts and credentials

- ☐ **[REQ · Owner]** **Apple Developer Program** (held) and the **App Store Connect app record**. *(Apple-account access.)*
- ☐ **[REQ · Bot-prep]** **Unity** account and plan. *(Personal is free; Pro only becomes mandatory at revenue. Agent drives signup; you accept ToS + payment.)*
- ☐ **[REQ · Bot-prep]** **Luma** and **one of Meshy / Tripo** (pick one).
- ☐ **[REQ · Bot-prep]** **Supabase.** *(Agent creates the project; you move the production key into CI — never onto the Bot.)*
- ☐ **[OPT · Bot-prep]** **Vercel** and **Inngest.** *(Architecture-dependent; Supabase edge functions + scheduled jobs may cover these.)*
- ☐ **[OPT · Bot-prep]** **Domains** `giganticjourneys.com` + `.app`. *(A hosted privacy-policy URL can be free; a purchased domain is marketing.)*
- ☐ **[OPT · Bot-prep]** **RevenueCat or Unity IAP.** *(Only if IAP ships at launch.)*
- ☐ **[REC · Bot]** A **crash-reporting** account. *(Free tier, no card — Sentry / Firebase / Xcode Organizer.)*
- ☐ **[OPT · Owner]** The **GitHub machine user.** *(Bootstrap credential for the Bot pipeline.)*
- ☐ **[OPT · Owner]** **App Store payment banking + tax** forms. *(Only if earning at launch.)*
- ☐ **[OPT · Owner]** The **SparkForge Labs business entity + EIN.** *(Ship as an individual if you like; an LLC is REC for biometric liability, not a gate.)*
- ☐ **[OPT · Bot-prep]** A **USPTO account** for the trademark.
- ☐ **[REC · Owner]** **Rotate the Bot PAT each milestone** (≤90-day expiry; SECURITY_CHECKLIST §8.1). *(Secret custody.)*
- ☐ **[REQ · Owner]** **Keep production Supabase keys, Apple signing, and payment credentials CI-only** (SECURITY_CHECKLIST §1.4); no agent holds them.

## Legal, privacy, and compliance (green before M5)

- ☐ **[REC · Bot-prep]** **Engage the attorney** (spend AUTH). *(Agent shortlists + briefs; you sign and pay. Highest-ROI risk reduction on the list.)*
- ☐ **[REQ · Owner]** **The BIPA / Texas CUBI / Washington MHMDA consent step** before any M2 face processing. *(Agents draft the copy and build the gate; the legal responsibility is yours.)*
- ☐ **[REQ · Bot-prep]** **Publish the privacy policy** (at a public URL) before M5; **[REC · Bot-prep]** the retention schedule. *(Agent drafts + hosts; you approve the legal content.)*
- ☐ **[REQ · Bot]** **Verify the deletion flow** (in-app account deletion). *(Automatable E2E test.)*
- ☐ **[REC · Bot-prep]** **Vendor DPAs on file** (Luma, head vendor, Supabase). *(Agent requests + files; you sign.)*
- ☐ **[REQ · Bot-prep]** **13+ age gate, no COPPA scope.** *(Agent builds it; you confirm.)*
- ☐ **[REC · Bot-prep]** **Terms of Service + EULA.** *(Agent drafts; Apple's standard EULA is available; you adopt.)*
- ☐ **[OPT · Bot-prep]** **USPTO TESS search** (free, prudent) and a **trademark filing decision** for classes 9 and 41. *(Agent runs the search; you decide on filing, defer until traction.)*
- ☐ **[REQ · Bot-prep]** **App Store privacy labels** accurate to the frozen telemetry schema. *(Agent drafts; you attest.)*
- ☐ **[OPT · Owner]** **Confirm the SparkForge Labs business entity** for accounts, DPAs, trademark, and IAP banking.

## Testers and QA

- ☐ **[REQ · Owner]** **You test on your iPhones every milestone** as the final reviewer of each exit test.
- ☐ **[REC · Owner]** **Recruit and consent volunteers** for the avatar blind test (M2) and publishing/moderation stress (M4). *(Trim: single digits of free volunteers cover M2–M4; only the final beta wants a larger cohort. "Recruit" always means volunteers, never hires.)*
- ☐ **[REQ · Owner]** **Operate the moderation queue** from M4 as the escalation point.
- ☐ **[REQ · Owner]** **Clear each milestone exit test** as the final reviewer.
- Note: all tests, QA passes, and device measurements are **suggestions, never merge gates** (AUTH #003); the merge gates are the automated CI checks and the security rules.

## Monetization and finance

*(This entire track is OPT for launch — defer it and ship free.)*

- ☐ **[OPT · Bot-prep]** **Two cosmetic IAP SKUs** with prices; the **free-tier caps + lifted-cap values** (a pricing AUTH).
- ☐ **[OPT · Bot-prep]** **IAP provider** (RevenueCat or Unity IAP; ADR at M5).
- ☐ **[OPT · Owner]** **App Store banking + tax.**
- ☐ **[REC · Owner]** **Fund the running cost.** *(The $750–1,300/month figure is the maximal plan; trimmed, real burn is far lower. Daily cap $50 agent+API.)*
- ☐ **[OPT · Owner]** **Approve the Tier 2 compute line monthly** if running ($400–1,000/month).
- ☐ **[OPT · Bot-prep]** **Set regional pricing.**

## Marketing and go-to-market

*(This entire track is OPT for launch — none of it gates App Store approval. The one overlap, App Store screenshots, is REQ and lives under M5.)*

- ☐ **[OPT · Bot-prep]** **Build-in-public Day N updates** from week 1. *(Agent drafts; you post in your voice.)*
- ☐ **[OPT · Bot-prep]** **Social handles + hashtags** (#GiganticJourneys, #GJrun).
- ☐ **[OPT · Bot]** **Landing page** on `giganticjourneys.com`. *(Builder builds + deploys; you approve copy.)*
- ☐ **[OPT · Bot-prep]** **Launch video** (diorama hero + Duo unfold). *(Agent edits; you supply gameplay footage + direction.)*
- ☐ **[OPT · Bot-prep]** **Press + influencer list and outreach.**
- ☐ **[OPT · Bot-prep]** **App Store featuring nomination.**
- ☐ **[OPT · Owner]** **TestFlight public beta** seeded in Duo communities if M3 is on schedule.
- ☐ **[OPT · Bot-prep]** **Launch-day plan + ASO** (keywords, screenshots).

## Devices and capture

- ☐ **[REQ · Owner]** **At least one test iPhone.** *(Your full iPhone matrix — oldest sets the quality floor — is REC.)*
- ☐ **[OPT · Owner]** **The iPhone Duo device decision** (buy vs adaptive design).
- ☐ **[OPT · Bot-prep]** A **paid iOS device farm**, only if solo testing becomes a bottleneck. *(Agent can set up a cloud farm; you authorize the spend.)*
- ☐ **[REQ · Owner]** **The physical corpus scans** (Part 1). **[REC · Owner]** the reference mocap captures and more corpus as tuning and M6 need it.

## Ongoing Owner rituals

- ☐ **[REQ · Owner]** **Answer AUTH REQUESTs promptly** — the only hard blocker for the agents.
- ☐ **[REQ · Owner]** **Clear each milestone checkpoint** (`REVIEW M<n>` → your `RESUME M<n+1>`).
- ☐ **[REC · Bot-prep]** **Monthly budget + usage review** (AGENT_GOVERNANCE §7). *(Agent compiles the numbers; you review.)*
- ☐ **[REC · Owner]** **Rotate the Bot PAT each milestone** (if the PAT exists).
- ☐ **[OPT · Owner]** **Decide whether you want an additional independent reviewer** beyond the Coordinator's weekly and checkpoint secondary reviews.

## Definition of launch done (SPEC §9)

A new user on iPhone scans a room or a Lego build in under 90 s, creates a recognizable 1:12 avatar in under 2 minutes behind an explicit consent step, reaches a summit and completes two routes with no manual fixes, publishes it, and a friend plays from a link within five minutes; the app holds its quality targets on your iPhones and 99%+ crash-free across the cohort; every compliance gate is green; and the App Store has approved the app.

Note: this definition blends the **REQ** compliance and submission gates with **product-quality** targets (recognizable avatar, scan success rate, crash-free rate) that make the app *good* rather than merely *shippable*. The compliance gates and a functioning core loop are non-negotiable; the specific quality thresholds are yours to set.
