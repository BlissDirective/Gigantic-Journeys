# M0 AUTH batch — accounts, spend, name protection

**Drafted by the Coordinator · 2026-09-17 · satisfies ticket M0-FORE-02 (the M0 AUTH batch).** These are **ready to approve**. Reply in chat or on the matching GitHub issue with `APPROVED #NNN` (or `DENIED #NNN — reason`) per line; the Coordinator moves each to the Decisions table in `governance/AUTHORIZATION_LOG.md` and unblocks its tickets. You can approve some and hold others.

Costs are **estimates** confirmed at account creation; all spend stays under the **$50/day** agent+API cap and the **$750–1,300/month** steady-state range (kit §7). Credentials rule: the Bot holds **staging** creds only; **production keys, signing, and payment credentials are CI-only** (`SECURITY_CHECKLIST §1.4`).

## Summary

| # | Type | What | Cost (est.) | Reversible | Blocks |
|---|---|---|---|---|---|
| #008 | account | Unity account + **Personal** plan | $0 (Pro at revenue) | yes | build/CI, M0-REPO-03 |
| #009 | account + spend | Luma reconstruction API | usage-based, ~$/scan | yes | capture pipeline, M0-LEGAL-03 |
| #010 | account + spend | Meshy **and** Tripo trial accounts (M2 comparison) | free/trial tiers | yes | avatar, M0-LEGAL-04 |
| #011 | account | Supabase (staging + production) | $0 now; ~$25/mo/project later | yes | backend, all data work |
| #012 | account | Vercel (API hosting) | $0 (Hobby); Pro later | yes | API |
| #013 | account | Inngest (durable workflows) | $0 (free tier) | yes | scan→package pipeline |
| #014 | spend | Domains `giganticjourneys.com` + `.app` | ~$25–55/yr | yes | privacy-policy URL, landing |
| #015 | spend | USPTO TESS search (+ filing decision) | $0 search; filing deferred | yes | name protection |
| #016 | spend | Attorney engagement (consent + privacy review) | ~$[1–4k] est., confirm on quote | n/a | M2 face processing, M5 gate |
| #017 | account | Crash reporting (Sentry or Firebase) | $0 (free tier) | yes | M5 crash-free tracking |

---

## The requests

```
AUTH REQUEST #008
Type: account
What: Create a Unity account and use the free Unity Personal plan for v1.
Why: Required to build the Unity 6 app and to add Unity license secrets to CI (M0-REPO-03).
Cost: $0 one-time; Unity Pro (~$2,200/yr/seat) deferred until revenue exists (SECURITY_CHECKLIST notes; AUTH log standing limits).
Reversible: yes
Waiting on: Owner
```
**Blocks:** M0-REPO-03, all Unity build/CI work.

```
AUTH REQUEST #009
Type: account + spend
What: Create a Luma account and enable its reconstruction API for scan → 3D.
Why: Core capture pipeline (ADR-0002); needed for M1. Retention/training terms must be on file first (M0-LEGAL-03, SECURITY_CHECKLIST §6.3).
Cost: usage-based per scan (est.); held under the $50/day cap; no real user scan until terms are on file.
Reversible: yes
Waiting on: Owner
```
**Blocks:** M0-LEGAL-03, M1 capture/reconstruction tickets.

```
AUTH REQUEST #010
Type: account + spend
What: Create Meshy AND Tripo trial accounts for the M2 head-generation comparison.
Why: M0-LEGAL-04 compares both and recommends one for M2; the other is dropped. Biometric terms (immediate-delete) must be on file before any face processing.
Cost: free/trial tiers for the comparison; the chosen vendor's paid plan is a later line if needed.
Reversible: yes
Waiting on: Owner
```
**Blocks:** M0-LEGAL-04, M2 avatar generation.

```
AUTH REQUEST #011
Type: account
What: Create Supabase projects for staging and production (auth, Postgres+RLS, storage, edge functions).
Why: The backend for all user data (ADR-0002). Production service key is CI-only; the Bot gets staging only (SECURITY_CHECKLIST §1.4, §8.3).
Cost: $0 on the free tier now; ~$25/month/project (Pro) when limits require, an incremental line.
Reversible: yes
Waiting on: Owner
```
**Blocks:** all backend/data/RLS tickets from M1.

```
AUTH REQUEST #012
Type: account
What: Create a Vercel account to host the API.
Why: API layer in front of Supabase/Inngest (ADR-0002).
Cost: $0 (Hobby) for development; Pro (~$20/mo) only if production needs it.
Reversible: yes
Waiting on: Owner
```
**Blocks:** API tickets. *(Optional if the architecture consolidates on Supabase edge functions — Builder confirms in an ADR.)*

```
AUTH REQUEST #013
Type: account
What: Create an Inngest account for durable scan→reconstruct→graph→journey→package workflows.
Why: Durable orchestration (ADR-0002).
Cost: $0 (free tier) at v1 volume.
Reversible: yes
Waiting on: Owner
```
**Blocks:** pipeline/workflow tickets. *(Optional if Supabase scheduled functions cover it — Builder confirms in an ADR.)*

```
AUTH REQUEST #014
Type: spend
What: Register giganticjourneys.com and giganticjourneys.app.
Why: A hosted privacy-policy URL (App Store requires one), the landing page, and email addresses (privacy@, support@, abuse@).
Cost: ~$25–55/year total (.app requires HTTPS; both via a standard registrar).
Reversible: yes (renewable annually)
Waiting on: Owner
```
**Blocks:** privacy-policy hosting, `legal/` contact addresses, landing page.

```
AUTH REQUEST #015
Type: spend
What: Run the free USPTO TESS search for "Gigantic Journeys" (classes 9 and 41) and record a filing recommendation.
Why: Name protection — confirm the name is clear before building brand around it (kit §9).
Cost: $0 for the search. An actual trademark filing (~$250–350/class) is a SEPARATE later spend AUTH, deferred until there is traction.
Reversible: yes
Waiting on: Owner
```
**Blocks:** name-protection decision; safe to build under the name.

```
AUTH REQUEST #016
Type: spend
What: Engage counsel to review the biometric consent copy, privacy policy, retention schedule, and ToS drafted in legal/.
Why: Biometric processing (BIPA/CUBI/MHMDA) is the project's largest legal exposure; sign-off gates M2 face processing and is an M5 gate (SECURITY_CHECKLIST §5.5). Drafts in legal/ reduce billable time.
Cost: ~$[1,000–4,000] estimate for a scoped review; confirm on the attorney's quote before proceeding.
Reversible: n/a (professional services)
Waiting on: Owner
```
**Blocks:** M2 consent go-live sign-off, M5 legal gate.

```
AUTH REQUEST #017
Type: account
What: Create a crash-reporting account (Sentry or Firebase Crashlytics) on the free tier.
Why: Track the 99%+ crash-free target from M3 onward and post-launch (SPEC §6, §9.5).
Cost: $0 (free tier).
Reversible: yes
Waiting on: Owner
```
**Blocks:** crash-free measurement (M3, M5).

---

## Not in this batch

- **App Store Connect app record** (reserve `com.sparkforgelabs.giganticjourneys`): an Owner action under the **already-held** Apple Developer account — no AUTH needed (no spend, no new account). It's on the launch checklist (§0).
- **Trademark filing** (classes 9 & 41): deferred; file as a separate spend AUTH once there's traction (see #015).
- **iPhone Duo dev device** ($1,999–3,199): optional; file only if you choose on-device Duo verification (checklist §0, §M3).
- **Tier 2 GPU compute** ($400–1,000/mo): a separate monthly line, approved month by month (SPEC §5); first requested at M1 if you run the research track.

## After approval
The Coordinator logs each approved item to the Decisions table, updates `PROGRESS.md`, and unblocks the named tickets. Account creation itself is **Bot-prep** (an agent drives signup; you accept ToS/payment and move any production key into CI) — see the delegability tags in `OWNER_LAUNCH_CHECKLIST.md`.
