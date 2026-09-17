# Owner Launch Checklist

`governance/OWNER_LAUNCH_CHECKLIST.md` · v1.2 · 2026-09-17 · Maintained by the Coordinator, actioned by the Owner. Every task here is **Owner-level**: something only you can do (accounts, spend and AUTH approvals, credentials, physical capture, devices, repo settings, legal sign-off, testers, store submission, marketing, business). The agents do everything else. **Part 1** is the sequenced path (roughly chronological); **Part 2** is the cross-cutting tracks that run throughout. Check items off as you go; the Coordinator updates status at each checkpoint.

Legend: ☐ to do · ▶ in progress · ✅ done. AUTH numbers reference `governance/AUTHORIZATION_LOG.md`; ticket IDs reference `tickets/`.

Priority tags (triage of what launch actually needs):
- **[REQ]** Required — a hard gate: Apple won't approve without it, the law requires it, or the core loop does not function.
- **[REC]** Recommended — not a gate anyone checks, but risky to skip *for this app specifically* (biometrics, photos of homes, minors, a public UGC leaderboard).
- **[OPT]** Optional — growth, polish, or process convenience; defer, scale down, or cut for v1.

Where a line bundles more than one tier, it carries the higher tag with a short "(trim: …)" note.

## Minimum viable launch path (the [REQ] spine)

The smallest chain that legally and functionally ships. Everything not on it is [REC] (do if you can) or [OPT] (defer):

1. **Apple Developer account (held) + App Store Connect app record.**
2. **A coding surface** (the Claude Code Builder) and **Unity (Personal)** to build the app.
3. **Core services:** Supabase (production); one scan-reconstruction vendor (Luma); one head-generation vendor (Meshy **or** Tripo — not both).
4. **The core loop works:** scan → recognizable 1:12 avatar (behind an explicit consent step) → summit + two routes with no manual fixes → publish → a friend plays from a link. (This is the real content of M1 + M2 + M3.)
5. **Compliance gates:** biometric consent step; privacy policy at a public URL; App Store privacy nutrition labels; in-app account deletion (verified); 13+ age gate; GPS/EXIF stripping on uploads; UGC moderation + report + block.
6. **At least one test iPhone**, your own corpus scans, and **App Store screenshots**.
7. **Submit and respond to App Store review.**

One paid item is *not* on the [REQ] spine but I'd still not skip it: **a focused legal consult on the biometric consent copy + privacy policy** (BIPA/CUBI/MHMDA exposure). It's [REC], but it's the highest-ROI risk reduction on the whole list.

The biggest scope-cut levers: **launch free** (deletes the entire monetization track), **volunteers not hires and single digits not dozens** of testers, **one head vendor**, and **adaptive Duo, no device purchase**.

# Part 1 — The sequenced path

## 0. Now — before you say `START M0`

- ☐ **[OPT]** **Create the Bot GitHub machine user + fine-grained PAT** (AUTH #002), scoped to this repo (Contents RW, Pull requests RW, Issues RW, Metadata R; ≤90-day expiry). Store in the Bot credential store and `.env.local`. Ticket M0-REPO-04. *(Only needed if you run the Grok Bot pipeline; skip if you drive computer-use steps yourself.)*
- ☐ **[REC]** **Set branch protection + native secret scanning on `main`** (M0-REPO-02, revised by AUTH #007): require a PR and green checks, no force-push, no deletion, push protection on; per-PR review not required; agents merge on green CI. *(Secret scanning is free and worth keeping regardless.)*
- ☐ **[REQ]** **Create the App Store Connect app record** for `com.sparkforgelabs.giganticjourneys` (this reserves the name) with an internal TestFlight group. **[REC]** **Add the ASC API key to CI secrets** (`ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`) + `APPLE_TEAM_ID` (M0-REPO-05). *(The record is required; the CI key just automates upload — you can archive/upload from Xcode instead.)*
- ☐ **[REQ]** **Start the coding surface** (the Claude Code Builder session) so the queue gets worked. **[OPT]** **Create the Grok Bot** (`gj-operator`) and hand it the PAT. *(The Bot is a convenience for computer-use steps, not an app requirement.)*
- ☐ **[REQ]** **Approve the essential accounts** in the M0 batch (#008 on): Supabase (production), one head vendor (Meshy **or** Tripo), Luma, Unity. **[OPT]** the rest of the batch: Vercel, Inngest, the two domains, USPTO search, the second head vendor. *(Trim to what the core loop needs; the Accounts track breaks this down.)*
- ☐ **[REC]** **Buy Motion Warping: Climb & Interact** ($19.99, AUTH #001). **[OPT]** **Register the domains** `giganticjourneys.com` + `.app`. *(The asset lifts traversal quality but the free Mixamo pipeline is a fallback; domains are marketing.)*
- ☐ **[REQ]** **Scan the day-one corpus** (M0-OWNER-01): 10 rooms + 5 tabletop builds; no faces/documents/addresses; GPS off. **[REC]** **Film the movement reference captures** (Bible §7): 8 Rokoko takes (~40 min) + the Move.ai hero clips. *(Corpus is needed to build and validate scan-to-playable; the mocap captures improve animation but have a free fallback.)*
- ☐ **[REQ]** **List the iPhones you own** (model + year) for the quality-tier reference points. **[OPT]** **Decide on an iPhone Duo dev device** ($1,999+) or accept adaptive design. Then **[REQ] issue `START M0`.**

## 1. M0 — Harness

- ☐ **[REC]** **Add Unity license secrets to CI** (M0-REPO-03): `UNITY_LICENSE` or `UNITY_EMAIL`/`UNITY_PASSWORD`/`UNITY_SERIAL`. *(Unity is required to build; the CI secret only enables automated CI builds.)*
- ☐ **[REC]** **Send vendor data-retention questions** to Luma and the head vendor; collect answers for `legal/vendors/`. *(Feeds accurate privacy labels and DPAs.)*
- ☐ **[REC]** **Engage the attorney** to start reviewing the consent, retention, and deletion drafts. *(The biometric consult; final sign-off is M5.)*
- ☐ **[REQ]** **Answer AUTHs** as they arrive; keep the queue unblocked.
- ☐ **[REQ]** **Clear the M0 checkpoint:** `REVIEW M0`, confirm the exit test, then `RESUME M1`.

## 2. M1 — Scan to playable (the validation milestone)

- ☐ **[REQ]** **Have the reference iPhone(s) in hand** for the motion-matching spike (M1-MOVE-01) and the performance targets.
- ☐ **[REC]** **Get Luma's retention/terms on file** before any real user scan (SECURITY_CHECKLIST §6.3). *(Becomes [REQ] once real users' scans flow.)*
- ☐ **[REQ]** **Scan 10 fresh rooms** (not in the training corpus) for the exit test (M1-QA-01). *(Your own scans; free.)*
- ☐ **[OPT]** **Approve or defer the monthly Tier 2 compute** (M1-RES-01). *(Research track; deferrable.)*
- ☐ **[REQ]** **Clear the M1 checkpoint — the big go/no-go:** 8 of 10 fresh scans reach a summit with two routes, no manual fixes; confirm the animation-stack decision. Under 6/10, approve the re-plan AUTH. Then `RESUME M2`. *(Existential: if this fails, there is no app. The 8/10 bar is your call.)*

## 3. M2 — Avatar

- ☐ **[REQ]** **Confirm the head-generation vendor** (Meshy or Tripo) and approve its account; an ADR records it.
- ☐ **[REQ]** **The biometric consent step** must gate all face processing. **[REC]** **Attorney sign-off on the consent copy** before it goes live (SECURITY_CHECKLIST §5.5). *(The consent gate is required by law + Apple; the attorney review is the recommended part.)*
- ☐ **[REC]** **Recruit test users for the avatar blind test** and record consent. *(Trim: 5–8 volunteers is enough — you can't blind-test your own face, but you don't need 20.)*
- ☐ **[REQ]** **Provide your own face + full-body captures** (physical).
- ☐ **[REQ]** **Clear the M2 checkpoint:** avatars recognizable in a blind test, generated under 2 minutes, on the shared rig; source photos provably deleted. Then `RESUME M3`. *(Recognizable avatar is the product hook; the 60% bar is your call.)*

## 4. M3 — Game loop, tabletop, and Duo

- ☐ **[REQ]** **Scan tabletop builds** (Lego and similar) for the tabletop mode (physical). *(Trim: [OPT] if you scope v1 to rooms-only; SPEC currently includes tabletop.)*
- ☐ **[OPT]** **Verify the three Duo features** on a device, or review the adaptive design. Go/no-go per feature. *(Duo is an opportunistic upside, not core.)*
- ☐ **[REC]** **Play-test five environments** with you + three testers.
- ☐ **[REC]** **Clear the M3 checkpoint:** everyone wants a sixth; Tier 1 holds 30 fps on your older iPhone; Duo decided. Then `RESUME M4`. *(Quality bars you set, not a hard gate.)*

## 5. M4 — Sharing, moderation, leaderboards

- ☐ **[REC]** **Recruit testers to publish environments.** *(Trim: a handful + seeded content is enough to stress moderation and ranking — not 50.)*
- ☐ **[REQ]** **The moderation queue + report + block** must exist and be operated as the escalation point (Apple UGC Guideline 1.2). *(The "zero misses" bar is the recommended validation of it.)*
- ☐ **[REC]** **Confirm the ranking resists a deliberate rate-spam test.** *(Leaderboard integrity; self-imposed gate.)*
- ☐ **[OPT]** **Decide repository public vs private** before broader user-data flows (currently public; revisit here).
- ☐ **[OPT]** **Tier 2 decision:** v1.1, V2, or shelve, on the R1–R5 evidence.
- ☐ **[REQ]** **Clear the M4 checkpoint;** then `RESUME M5`.

## 6. M5 — Store readiness, IAP, and launch

- ☐ **[REC]** **Attorney final sign-off:** privacy policy, BIPA consent, retention schedule, deletion flow. *(The policy and deletion themselves are [REQ]; the sign-off is the recommended assurance.)*
- ☐ **[OPT]** **Configure the two IAP SKUs**, prices, and free-tier caps (a pricing AUTH). *(Cut entirely if you launch free.)*
- ☐ **[OPT]** **Choose + set up the IAP provider** (RevenueCat or Unity IAP; ADR at M5) and complete App Store Connect **banking + tax**. *(Only needed if earning at launch.)*
- ☐ **[REQ]** **Complete App Store privacy labels** accurate to the frozen telemetry schema; **confirm the 13+ age gate.** *(Both hard gates: labels are required to submit; the age gate keeps you out of COPPA.)*
- ☐ **[REQ]** **Verify the data-deletion flow end to end** on staging (SECURITY_CHECKLIST §6.4). *(In-app account deletion is Apple-mandated.)*
- ☐ **[REC]** **Grow the TestFlight cohort and reach a high crash-free rate.** *(Trim: "100 at 99%" is a self-imposed bar; 10 testers + no known crashes on your devices is compliant.)*
- ☐ **[REQ]** **Provide App Store screenshots** (diorama as the hero shot). **[OPT]** **the preview video** and top-5-market localization. *(Screenshots are required to submit; the video is optional.)*
- ☐ **[OPT]** **Submit the App Store featuring nomination** citing Duo adoption (M5-DUO-01).
- ☐ **[REQ]** **Give explicit approval to submit,** then submit and respond to App Store review.

## 7. M6 — Learning loops (post-launch)

- ☐ **[OPT]** **Approve the first surface-classifier retrain** (~4 weeks out) with before/after metrics. *(Post-launch improvement.)*
- ☐ **[REC]** **Review the weekly data reports** and approve validator/generator update PRs.
- ☐ **[REQ]** **Handle moderation escalations, crashes, and App Store review responses.** *(Ongoing UGC-moderation and app-maintenance obligations.)*

# Part 2 — Cross-cutting tracks

These run throughout the build, not at a single milestone.

## Accounts and credentials

- ☐ **[REQ]** **Apple Developer Program** (held) and the **App Store Connect app record**.
- ☐ **[REQ]** **Unity** account and plan. *(Personal is free now; Pro only becomes mandatory once revenue exists.)*
- ☐ **[REQ]** **Luma** (scan reconstruction) and **one of Meshy / Tripo** (head generation — pick one).
- ☐ **[REQ]** **Supabase.** *(Production required; a separate staging project is [REC].)*
- ☐ **[OPT]** **Vercel** and **Inngest.** *(Architecture-dependent; Supabase edge functions + scheduled jobs may cover these.)*
- ☐ **[OPT]** **Domains** `giganticjourneys.com` + `.app`. *(You need a hosted privacy-policy URL, which can be free; a purchased domain is for marketing.)*
- ☐ **[OPT]** **RevenueCat or Unity IAP.** *(Only if IAP ships at launch.)*
- ☐ **[REC]** A **crash-reporting** account. *(Free tier — Sentry / Firebase / Xcode Organizer.)*
- ☐ **[OPT]** The **GitHub machine user.** *(Only for the Grok Bot pipeline.)*
- ☐ **[OPT]** **App Store payment banking + tax** forms. *(Only if earning at launch.)*
- ☐ **[OPT]** The **SparkForge Labs business entity + EIN.** *(You can ship as an individual; an LLC is [REC] for liability given biometrics, but not a launch gate.)*
- ☐ **[OPT]** A **USPTO account** for the trademark.
- ☐ **[REC]** **Rotate the Bot PAT each milestone** (≤90-day expiry; SECURITY_CHECKLIST §8.1). *(If the PAT exists.)*
- ☐ **[REQ]** **Keep production Supabase keys, Apple signing, and payment credentials CI-only** (SECURITY_CHECKLIST §1.4); no agent holds them.

## Legal, privacy, and compliance (green before M5)

- ☐ **[REC]** **Engage the attorney** (spend AUTH). *(The biometric consult — highest-ROI risk reduction on the list.)*
- ☐ **[REQ]** **The BIPA / Texas CUBI / Washington MHMDA consent step** before any M2 face processing. *(The mechanism is required by law + Apple; attorney sign-off of the wording is [REC].)*
- ☐ **[REQ]** **Publish the privacy policy** (at a public URL) before M5; **[REC]** the retention schedule.
- ☐ **[REQ]** **Verify the deletion flow** (in-app account deletion).
- ☐ **[REC]** **Vendor DPAs on file** (Luma, head vendor, Supabase).
- ☐ **[REQ]** **13+ age gate, no COPPA scope.**
- ☐ **[REC]** **Terms of Service + EULA.** *(Apple's standard EULA is available; a custom ToS is recommended for UGC.)*
- ☐ **[OPT]** **USPTO TESS search** (free, prudent) and a **trademark filing decision** for classes 9 and 41 (spend — defer filing until there's traction).
- ☐ **[REQ]** **App Store privacy labels** accurate to the frozen telemetry schema.
- ☐ **[OPT]** **Confirm the SparkForge Labs business entity** for accounts, DPAs, trademark, and IAP banking.

## Testers and QA

- ☐ **[REQ]** **You test on your iPhones every milestone** as the final reviewer of each exit test.
- ☐ **[REC]** **Recruit and consent volunteers** — the avatar blind test (M2) and publishing/moderation stress (M4) need people who aren't you. *(Trim: single digits of free volunteers cover M2–M4; only the final beta wants a larger cohort. "Recruit" always means volunteers, never hires.)*
- ☐ **[REQ]** **Operate the moderation queue** from M4 as the escalation point.
- ☐ **[REQ]** **Clear each milestone exit test** as the final reviewer.
- Note: all tests, QA passes, and device measurements are **suggestions, never merge gates** (AUTH #003); the merge gates are the automated CI checks and the security rules.

## Monetization and finance

*(This entire track is [OPT] for launch — defer it and ship free.)*

- ☐ **[OPT]** **Two cosmetic IAP SKUs** with prices; the **free-tier caps + lifted-cap values** (a pricing AUTH).
- ☐ **[OPT]** **IAP provider** (RevenueCat or Unity IAP; ADR at M5).
- ☐ **[OPT]** **App Store banking + tax.**
- ☐ **[REC]** **Fund the running cost.** *(The $750–1,300/month figure is the maximal plan; trimmed as above, real burn is far lower. Daily cap $50 agent+API, pipeline halts at the cap.)*
- ☐ **[OPT]** **Approve the Tier 2 compute line monthly** if running ($400–1,000/month).
- ☐ **[OPT]** **Set regional pricing.**

## Marketing and go-to-market

*(This entire track is [OPT] for launch — none of it gates App Store approval. The one overlap, App Store screenshots, is [REQ] and lives under M5.)*

- ☐ **[OPT]** **Build-in-public Day N updates** from week 1.
- ☐ **[OPT]** **Social handles + hashtags** (#GiganticJourneys, #GJrun).
- ☐ **[OPT]** **Landing page** on `giganticjourneys.com`.
- ☐ **[OPT]** **Launch video** (diorama hero + Duo unfold).
- ☐ **[OPT]** **Press + influencer list and outreach.**
- ☐ **[OPT]** **App Store featuring nomination.**
- ☐ **[OPT]** **TestFlight public beta** seeded in Duo communities if M3 is on schedule.
- ☐ **[OPT]** **Launch-day plan + ASO** (keywords, screenshots). *(Screenshots themselves are [REQ], under M5.)*

## Devices and capture

- ☐ **[REQ]** **At least one test iPhone.** *(Your full iPhone matrix — oldest sets the quality floor — is [REC].)*
- ☐ **[OPT]** **The iPhone Duo device decision** (buy vs adaptive design).
- ☐ **[OPT]** A **paid iOS device farm**, only if solo testing becomes a bottleneck.
- ☐ **[REQ]** **The physical corpus scans** (Part 1). **[REC]** the reference mocap captures and more corpus as tuning and M6 need it.

## Ongoing Owner rituals

- ☐ **[REQ]** **Answer AUTH REQUESTs promptly** — the only hard blocker for the agents.
- ☐ **[REQ]** **Clear each milestone checkpoint** (`REVIEW M<n>` → your `RESUME M<n+1>`); you are the final reviewer.
- ☐ **[REC]** **Monthly budget + usage review** (AGENT_GOVERNANCE §7).
- ☐ **[REC]** **Rotate the Bot PAT each milestone** (if the PAT exists).
- ☐ **[OPT]** **Decide whether you want an additional independent reviewer** beyond the Coordinator's weekly and checkpoint secondary reviews.

## Definition of launch done (SPEC §9)

A new user on iPhone scans a room or a Lego build in under 90 s, creates a recognizable 1:12 avatar in under 2 minutes behind an explicit consent step, reaches a summit and completes two routes with no manual fixes, publishes it, and a friend plays from a link within five minutes; the app holds its quality targets on your iPhones and 99%+ crash-free across the cohort; every compliance gate is green; and the App Store has approved the app.

Note: this definition blends the **[REQ]** compliance and submission gates with **product-quality** targets (recognizable avatar, scan success rate, crash-free rate) that make the app *good* rather than merely *shippable*. The compliance gates and a functioning core loop are non-negotiable; the specific quality thresholds are yours to set.
