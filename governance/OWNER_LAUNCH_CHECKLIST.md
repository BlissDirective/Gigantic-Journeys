# Owner Launch Checklist

`governance/OWNER_LAUNCH_CHECKLIST.md` · v1.0 · 2026-09-17 · Maintained by the Coordinator, actioned by the Owner. Every task here is **Owner-level**: something only you can do (accounts, spend and AUTH approvals, credentials, physical capture, devices, repo settings, legal sign-off, testers, store submission, marketing, business). The agents do everything else. Order is roughly chronological; cross-cutting tracks run throughout. Check items off as you go; the Coordinator updates status at each checkpoint.

Legend: ☐ to do · ▶ in progress · ✅ done. AUTH numbers reference `governance/AUTHORIZATION_LOG.md`.

## 0. Immediate — before `START M0`

- ☐ **Create the Bot GitHub machine user + fine-grained PAT** (AUTH #002, approved), scoped to this repo (Contents RW, Pull requests RW, Issues RW, Metadata R; ≤90-day expiry). Store in the Bot credential store and `.env.local`. Ticket M0-REPO-04.
- ☐ **Configure branch protection + native secret scanning on `main`** (M0-REPO-02, revised by AUTH #007): require a PR and green required checks, no force-push, no deletion, push protection on; per-PR Code Owner review is NOT required; the Builder's identity can merge on green CI.
- ☐ **Add the App Store Connect API key to CI secrets** (M0-REPO-05): `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64`; repository variable `APPLE_TEAM_ID`. Create the App Store Connect app record for `com.sparkforgelabs.giganticjourneys` (this reserves the name) with an internal TestFlight group on automatic distribution.
- ☐ **Create the one Grok Bot** (`gj-operator`) by pasting `agents/grok/roles/gj-operator.md`; hand it the PAT when it asks.
- ☐ **Start the Claude Code Builder session** (separate from this Coordinator session) so it can work the queue and merge on green CI.
- ☐ **Approve the M0 AUTH batch** (#008 onward): Unity account and plan, Luma API, Meshy and/or Tripo, Supabase (staging + production), Vercel, Inngest, `giganticjourneys.com` + `.app`, USPTO TESS search, attorney engagement.
- ☐ **Buy Motion Warping: Climb & Interact** ($19.99, AUTH #001) on the Unity account.
- ☐ **Register the domains** `giganticjourneys.com` and `.app`.
- ☐ **Scan the day-one corpus** (M0-OWNER-01): 10 rooms + 5 tabletop builds with your phone camera; hand off through the corpus intake path; no faces, documents, or addresses; GPS off.
- ☐ **Film the movement reference captures** (Movement Bible §7): the 8 Rokoko Vision reaction takes (~40 min) and the Move.ai hero clips (flag plant, running jump, hard landing, roll).
- ☐ **List the iPhones you own** (model + year) so the Coordinator sets the quality-tier reference points (newest + oldest).
- ☐ **Decide on an iPhone Duo dev device** for verifying the three Duo features: buy one (AUTH spend, $1,999+) or accept adaptive design until one is available.
- ☐ **Issue `START M0`.**

## 1. M0 — Harness

- ☐ **Add Unity license secrets to CI** (M0-REPO-03) once the Unity account exists: `UNITY_LICENSE` or `UNITY_EMAIL`/`UNITY_PASSWORD`/`UNITY_SERIAL`.
- ☐ **Send vendor data-retention questions** to Luma and Meshy/Tripo (drafts prepared by the capture/avatar domains); collect answers for `legal/vendors/`.
- ☐ **Engage the attorney** to begin reviewing the M0 legal drafts (consent, retention, deletion). Final sign-off is a later gate (M5).
- ☐ **Answer AUTHs** as they arrive; keep the queue unblocked.
- ☐ **Clear the M0 checkpoint:** run `REVIEW M0`, confirm the exit test (a ticket to merged PR with QA evidence and no human typing), then `RESUME M1`.

## 2. M1 — Scan to playable (the validation milestone)

- ☐ **Have the reference iPhone(s) in hand** for the motion-matching spike (M1-MOVE-01) and the performance targets.
- ☐ **Get Luma's retention/terms on file** before any real user scan is sent (SECURITY_CHECKLIST §6.3).
- ☐ **Scan 10 fresh rooms** (not in the training corpus) for the exit test (M1-QA-01).
- ☐ **Approve the Tier 2 monthly compute AUTH** if you want the research track running this month (M1-RES-01), or defer it.
- ☐ **Clear the M1 checkpoint — the big go/no-go:** 8 of 10 fresh scans reach a summit with at least two valid routes, no manual fixes. Under 6/10, approve the re-plan AUTH. Confirm the motion-matching-vs-blend-trees decision. Then `RESUME M2`.

## 3. M2 — Avatar

- ☐ **Confirm the head-generation vendor** (Meshy or Tripo) from the M0 comparison; approve that account AUTH; an ADR records it.
- ☐ **Attorney sign-off on the BIPA consent copy** before any face processing goes live (SECURITY_CHECKLIST §5.5).
- ☐ **Recruit ~20 test users** for the avatar blind test and record their consent.
- ☐ **Provide your own face + full-body captures** and coordinate testers' captures (physical).
- ☐ **Clear the M2 checkpoint:** avatars recognizable in a blind test at 60%+, generated under 2 minutes, all on the shared rig; source photos provably deleted. Then `RESUME M3`.

## 4. M3 — Game loop, tabletop, and Duo

- ☐ **Scan tabletop builds** (Lego and similar) for the tabletop mode (physical).
- ☐ **Verify the three Duo features** on a Duo device if you acquired one (stand-mode layout, unfold transition, rear-camera capture); otherwise review the adaptive design. Go/no-go per feature at this checkpoint.
- ☐ **Play-test:** you and three testers each explore five environments.
- ☐ **Clear the M3 checkpoint:** everyone wants a sixth; Tier 1 holds 30 fps on your older iPhone; Duo features decided. Then `RESUME M4`.

## 5. M4 — Sharing, moderation, leaderboards

- ☐ **Recruit ~50 testers** to publish environments.
- ☐ **Operate the moderation queue** as the escalation point; the exit test is zero moderation misses in your review.
- ☐ **Confirm the ranking survives a deliberate rate-spam test.**
- ☐ **Decide repository public vs private** before broader user data flows (currently public; revisit here).
- ☐ **Tier 2 decision point:** on the R1–R5 evidence, decide whether Tier 2 physics enters v1.1, V2, or is shelved.
- ☐ **Clear the M4 checkpoint;** then `RESUME M5`.

## 6. M5 — Store readiness, IAP, and launch

- ☐ **Attorney final sign-off:** privacy policy, BIPA consent, retention schedule, deletion flow.
- ☐ **Configure the two IAP SKUs** in App Store Connect (cosmetic outfit pack, realism+ materials) with prices; set the free-tier caps and the lifted-cap values (a pricing AUTH).
- ☐ **Choose and set up the IAP provider** (RevenueCat or Unity IAP; ADR at M5) and complete App Store Connect **banking and tax** so IAP can earn.
- ☐ **Complete App Store privacy labels** accurate to the frozen telemetry schema; confirm the 13+ age gate.
- ☐ **Verify the data-deletion flow end to end** on staging (SECURITY_CHECKLIST §6.4).
- ☐ **Grow the TestFlight cohort to 100** and reach a 99%+ crash-free rate.
- ☐ **Provide store assets:** screenshots with the diorama as the hero shot, the preview video (real room → unfold/shrink → play → publish → friend plays), description, keywords, localized for the top 5 markets.
- ☐ **Submit the App Store featuring nomination** citing iPhone Duo adoption (M5-DUO-01).
- ☐ **Give explicit approval to submit** to the App Store (the M5 exit test requires your explicit go). Then submit.

## 7. M6 — Learning loops (post-launch)

- ☐ **Approve the first surface-classifier retrain** on opt-in derived data, about four weeks post-launch, with before/after metrics on the held-out corpus.
- ☐ **Review the weekly data reports** and approve validator/generator update PRs on the standing cadence.
- ☐ **Handle moderation escalations** and App Store review responses; watch the crash dashboard.

## 8. Cross-cutting — Legal and compliance (green before M5)

- ☐ Attorney engaged (spend AUTH). ☐ BIPA / Texas CUBI / Washington MHMDA consent signed off before M2 face processing. ☐ Vendor DPAs on file (Luma, Meshy/Tripo, Supabase). ☐ Privacy policy and retention schedule published. ☐ USPTO TESS search done (M0) and a trademark filing decision made for "Gigantic Journeys" in classes 9 and 41 (spend). ☐ 13+ age gate, no COPPA scope. ☐ Confirm the SparkForge Labs business entity for developer accounts, DPAs, trademark, and IAP banking.

## 9. Cross-cutting — Marketing and launch

- ☐ Build-in-public Day N updates from week 1. ☐ Social handles and hashtags (#GiganticJourneys, #GJrun). ☐ Landing page on `giganticjourneys.com`. ☐ Launch video (diorama hero + Duo unfold). ☐ App Store featuring nomination. ☐ TestFlight public beta seeded in Duo communities if M3 is on schedule. ☐ Press and influencer outreach for launch.

## 10. Ongoing Owner rituals

- ☐ **Answer AUTH REQUESTs promptly** — the only hard blocker for the agents.
- ☐ **Clear each milestone checkpoint** (`REVIEW M<n>` → your `RESUME M<n+1>`); you are the final reviewer.
- ☐ **Monthly budget and usage review** (AGENT_GOVERNANCE §7): spend vs the $750–1,300/month range, and per-surface usage on Max and SuperGrok Plus.
- ☐ **Rotate the Bot PAT each milestone** (≤90-day expiry; SECURITY_CHECKLIST §8.1).
- ☐ **Arrange the periodic secondary review** (AUTH #007): the Coordinator does it weekly and at checkpoints; you decide if you want an additional independent reviewer beyond that.

## Definition of launch done (SPEC §9)

A new user on iPhone scans a room or a Lego build in under 90 s, creates a recognizable 1:12 avatar in under 2 minutes behind an explicit consent step, reaches a summit and completes two routes with no manual fixes, publishes it, and a friend plays from a link within five minutes; the app holds its quality targets on your iPhones and 99%+ crash-free across the cohort; every compliance gate is green; and the App Store has approved the app.
