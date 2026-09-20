# App Store UGC compliance — Apple Guideline 1.2 (DRAFT requirement + mapping)

**Status: DRAFT v0.1 · 2026-09-20 · Coordinator.** The requirement and evidence map for Apple App Review **Guideline 1.2 (Safety — User-Generated Content)**, a **launch gate** for Gigantic Journeys (AUTH #026, `SECURITY_CHECKLIST §10.5`, SPEC §3.7). **Not legal advice;** the Owner's in-house legal team owns the final ToS/EULA wording and the contact-info/DMCA registrations. This file is the single place App Review, the legal team, and the Builder can see *what 1.2 requires* and *where each piece lives*.

## Why this is a hard gate
Any app hosting user-generated content that Apple can review is held to Guideline 1.2. Missing any pillar is a common, avoidable rejection. GJ is UGC by definition (players publish scanned environments to a ranked global feed), so all four pillars must be live and demonstrable at submission.

## The four pillars → how GJ satisfies each
| # | Apple 1.2 requires | GJ implementation | Where | Ticket |
|---|---|---|---|---|
| 1 | **A method to filter objectionable content** before it is published | Automated vision-moderation pass on every publish; cleared → public, flagged → held "Under review" for human review (auto-clear + human-on-report) | SPEC §3.7; `SECURITY_CHECKLIST §10.5` | M4-DATA-03 |
| 2 | **A mechanism to report** content + a **timely response** | One-tap in-app report (every environment and user) with a reason sheet; human queue (gj-data → Owner); **act within 24 hours** to remove content and eject violators | ToS §5; decision 8d | M4-DATA-03, M4-GAME-01 |
| 3 | **The ability to block abusive users** | In-app block: a blocked user's content is hidden and they cannot interact with yours | ToS §5; SPEC §3.7 | M4-DATA-03 |
| 4 | **Published developer contact information** | Contact info published **in-app (Settings → About/Legal)**, on the **App Store product page (support URL)**, and on the **website** | ToS §11 (below) | M4-GAME-01 (in-app), M5 store setup |

Apple also expects the **EULA to state zero tolerance for objectionable content or abusive users** — ToS §4 (zero-tolerance clause) + §5.

## Pillar 4 in detail — the published-contact-info requirement
This is the piece most often missed. It must be **published and reachable**, not just present in the ToS text. Concretely:

**What must be published (and kept current):**
- Publisher / legal entity name + registered address — *[in-house legal to confirm the entity]*.
- **General support** contact: `support@giganticjourneys.com` + a support URL `https://giganticjourneys.com/support`.
- **Abuse / content-concern / takedown** contact: `abuse@giganticjourneys.com`.
- **Legal / privacy** contact: `legal@giganticjourneys.com`.
- **DMCA designated agent**: `dmca@giganticjourneys.com` + a registered agent name/address.

**Where it must appear (three surfaces):**
1. **In-app** — Settings → About / Legal shows the entity, support, abuse, and legal contacts and links the ToS + Privacy Policy (build task, M4-GAME-01).
2. **App Store product page** — Apple requires a **Support URL** (and a Marketing URL is recommended); the privacy-policy URL is already required (M5 store setup).
3. **Website** — `giganticjourneys.com` publishes the same contacts + the ToS and Privacy Policy at stable URLs (domains registered under AUTH #014).

**Mailboxes/pages to create (owner action):** the four role mailboxes above on the `giganticjourneys.com` domain (AUTH #014 registered the domain and role addresses), plus the `/support`, `/terms`, and `/privacy` web pages. None of these use a personal email address.

## EULA acceptance & DMCA
- **Acceptance gate:** users accept the ToS/EULA at account creation, and **publishing requires an explicit agreement to the community rules** (ToS §0, §4; build task M4-GAME-01).
- **DMCA:** register the designated agent with the U.S. Copyright Office; implement the §512 notice/counter-notice flow and a repeat-infringer policy (ToS §5A) — *in-house legal action*.

## Open items for the in-house legal team
1. Confirm the **legal entity** name, registered address, and **governing law/venue**; fill the ToS placeholders.
2. Approve the **zero-tolerance** clause (ToS §4) and the **24-hour action** commitment (ToS §5) as sufficient for Guideline 1.2.
3. Create the **role mailboxes** and the **web pages** (support/terms/privacy); confirm the App Store **Support URL**.
4. **Register the DMCA agent** and confirm the takedown/counter-notice process (and any non-US equivalents, e.g. EU DSA notice-and-action, if targeting the EU).
5. Reconcile with **Apple's Licensed Application EULA** minimum terms (including the acknowledgment that Apple is not responsible for UGC).

## Evidence at submission (what App Review will see)
- The four pillars demonstrable in a build: filter (content under review), report (one-tap + reason sheet), block (block a user), contact (Settings → About/Legal + product-page support URL).
- The ToS/EULA in-app and at a public URL with the zero-tolerance + 24-hour + contact terms.
- The M4 exit (M4-QA-01): 50 published environments through publish → moderation → browse → rate → report with **zero moderation misses** in the Owner's review.

## References
SPEC §3.7 · `governance/SECURITY_CHECKLIST.md §10.2/§10.4/§10.5` · AUTH #026 · `legal/TERMS_OF_SERVICE.md` · `legal/PRIVACY_POLICY.md` · tickets M4-DATA-03, M4-GAME-01, M4-QA-01.
