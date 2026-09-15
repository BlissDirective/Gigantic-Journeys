<!--
Gigantic Journeys pull request. Every section is required unless it says optional.
The Coordinator reviews against tickets/<ID>.json acceptance tests, SPEC.md,
governance/REVIEW_RUBRIC.md, and governance/SECURITY_CHECKLIST.md. PRs that skip
sections, lack evidence, or touch protected paths without an APPROVED #n are
rejected. Rules for Bots: agents/grok/README.md.
-->

## Ticket

- Ticket: `tickets/<ID>.json`
- Branch: `ticket/<ID>-<slug>` (or `setup/<role>-skills`, `auth/<nnn>-<slug>`, `checkpoint/M<n>`)
- Bot: `gj-<role>`

## What changed

<!-- 3 to 10 lines. What, where, why. Link the ADR if one is involved. -->

## Acceptance tests

<!-- One row per acceptance criterion in the ticket, in order, with its level. Required criteria
need evidence (CI job link, file path, or report path in this PR). Suggested criteria (tests, QA,
performance, device checks) list evidence if you have it, otherwise "not measured"; they never
block a merge (AUTH #003). -->

| AT | Level | How verified | Evidence |
|---|---|---|---|
| AT-1 | required |  |  |
| AT-2 | suggested |  |  |

## Visual evidence

<!-- Suggested for anything under unity/Assets/UI, unity/Assets/Gameplay, unity/Assets/Player,
unity/Assets/Capture, design/, or any screen. Screenshots (PNG in qa/evidence/<ID>/) or a clip
attached to this PR. Profiler screenshot on the reference Android device for gameplay and UI PRs
(Design Skills §4). Write "N/A" only for non-visual changes. -->

## Security considerations

- [ ] No secrets, tokens, keys, or `.env*` files in this diff or in any commit on this branch
- [ ] No raw photos, video, or scan media committed
- [ ] New tables or buckets have RLS enabled plus policies and tests (or N/A)
- [ ] New downloads use signed, short-lived URLs (or N/A)
- [ ] Face or biometric processing sits behind the consent gate (or N/A)
- [ ] Source media deletion path exists for any new media input (or N/A)
- [ ] New dependencies are exactly pinned and audited (or N/A)
- [ ] No PII, GPS, or EXIF in telemetry, logs, screenshots, or reports (or N/A)

Notes:

## Authorization

<!-- Required if this PR touches SPEC.md, ADRs/, data/schemas/, design/DESIGN_SYSTEM.md,
design/tokens/, the locked design docs, tickets/SCHEMA.json, config/movement.json, or the
milestone plan. Cite the Owner's reply exactly, e.g. "APPROVED #007". Otherwise write "None". -->

APPROVED #

## Performance

<!-- Suggested. Gameplay, UI, capture, avatar, and services PRs: the numbers that apply. Frame time p50 and
p99 on the reference device, animation CPU ms, motion DB size, scan time, avatar generation time,
package size, job cost per scan. Write "N/A" for docs-only changes. -->

## QA

- [ ] `gj-qa-release` visual pass requested (suggested for gameplay, UI, capture PRs)
- [ ] Pre-PR design checklist run (Design Skills §4) for UI and gameplay PRs (suggested)
- [ ] Ticket JSON updated: `status`, `branch`, `pr`, `history`
