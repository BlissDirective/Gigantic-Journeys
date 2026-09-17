# Review Rubric

`governance/REVIEW_RUBRIC.md` · v1.0 · 2026-09-15 · Applied by the Coordinator to every PR before merge. Bots read it before opening a PR; a PR that would fail a blocking row should not be opened.

## 0. How a review runs

1. Read the ticket (`tickets/<id>.json`). The acceptance tests are the contract.
2. Read the PR against the template: every section present, every acceptance-test row carries evidence.
3. Walk sections A–H below. Rows marked **B** block: any failure means *changes requested* (or *reject*, §9). Rows marked *A* are advisory: noted in the review and tracked as debt.
4. Write the verdict with reasons tied to acceptance-criterion ids, rubric rows, and checklist rows (§10 template). This rubric is applied by the **Builder at self-review before merging** and by the **secondary reviewer at intervals** (AUTH #007). Merge when every B row passes and CI is green. Tests, QA passes, performance measurements, and device checks are suggestions (SPEC §11, AUTH #003): reviewed when evidence is offered, noted as advisory when absent, never a reason to withhold a merge.
5. On merge: update the ticket (`status`, `history`), `PROGRESS.md`, and, if an AUTH was consumed, `governance/AUTHORIZATION_LOG.md`.

Verdicts: **merge** · **changes requested** (fixable within the ticket) · **reject** (wrong ticket, scope creep, unauthorized protected-path change, secret in history, or a resubmission that ignores earlier findings).

Acceptance criteria carry a `level`: `required` (deliverables, security, governance, automated CI checks) or `suggested` (tests, QA, performance, device evidence, coverage). Only required-level criteria can block.

## A. Correctness against acceptance tests

| # | Check | |
|---|---|---|
| A1 | Every required-level acceptance criterion has a row in the PR with concrete evidence: CI job, file path, or report path in this PR. Suggested-level criteria list evidence when available or "not measured". | B |
| A2 | Whatever automated checks and tests the PR includes run in CI and pass; a test exercises the stated condition rather than a tautology. | B |
| A3 | Suggested-level criteria (manual QA, device measurements, blind tests) are reviewed when evidence is offered; missing evidence is noted, never blocking. | A |
| A4 | Nothing outside the ticket's scope changed; drive-by changes are split out or sent to `BACKLOG.md`. | B |
| A5 | The change matches `SPEC.md`. Behavior not in SPEC is either a non-goal (reject) or needs a design-change AUTH. | B |
| A6 | Behavior is deterministic where SPEC demands it (validator, route generation, ranking): same input, same output (a test proving it is suggested). | B |

## B. Governance

| # | Check | |
|---|---|---|
| B1 | Branch is `ticket/<id>-<slug>` (or an allowed exception); the PR references the ticket; the ticket JSON is updated (`status`, `branch`, `pr`, `history`). | B |
| B2 | If the PR touches `SPEC.md`, `ADRs/`, `data/schemas/`, `design/DESIGN_SYSTEM.md`, the locked design docs, `design/tokens/`, `tickets/SCHEMA.json`, `config/movement.json`, or the milestone plan: the PR body cites `APPROVED #n`, that number is APPROVED in `AUTHORIZATION_LOG.md`, and the change matches what was approved. Otherwise **reject**. | B |
| B3 | No spend, account creation, or paid service enters through the change (an SDK that needs a card, a new vendor, a new runner) without an `APPROVED #n`. Otherwise **reject**. | B |
| B4 | The author did not edit the ticket's acceptance tests. | B |
| B5 | Commits arrive within the sync cadence (at most 2 h of active work between pushes) and the PR is reviewable in size (about 800 changed lines or fewer unless generated). | A |

## C. Security (details in `SECURITY_CHECKLIST.md`)

| # | Check | |
|---|---|---|
| C1 | Secret scan green on every commit of the branch; no `.env*` (other than `.env.example`), key, certificate, or token in the diff, history, screenshots, logs, or fixtures. Otherwise **reject** and rotate. | B |
| C2 | OWASP Mobile Top 10 (2024) walked for app changes: M1 credential usage, M2 supply chain, M3 auth/authz, M4 input/output validation, M5 communication, M6 privacy controls, M7 binary protections, M8 misconfiguration, M9 data storage, M10 cryptography. Each applicable item has a one-line note in the PR. | B |
| C3 | Supabase: every new or changed table has RLS enabled and policies in the same migration (owner-only, published-read, service-role-only; a test per policy is suggested); no service-role usage from the client; storage buckets private by default; `check_rls.py` green. | B |
| C4 | Environment packages, media, and avatars are served only through signed URLs with a short TTL; no public bucket unless an ADR names it (thumbnails at most). | B |
| C5 | Any path that receives images or video strips GPS/EXIF on device and verifies server-side (fixture tests suggested). | B |
| C6 | Face or body processing is unreachable without a recorded consent; a test proving that no consent means the request is refused before any upload is suggested. | B |
| C7 | Any new media input has a deletion path (device, storage, vendor) with a test or a logged receipt. | B |
| C8 | Dependencies: exact pins (`==`, lockfiles, Unity `packages-lock.json`, actions by tag), `npm audit` and `pip-audit` clean at high and above, each new dependency justified in one line with a compatible license. | B |
| C9 | Least privilege: no new credential broader than the task; Bots never gain production keys; CI secrets appear only in the jobs that need them. | B |
| C10 | Logs, telemetry, and reports carry no PII, GPS, raw media references, or user content. | B |

## D. Performance targets (`SPEC.md` §6; advisory under AUTH #003)

| # | Check | |
|---|---|---|
| D1 | Gameplay, UI, capture, and avatar PRs state their expected effect on the SPEC §6 targets; a measurement from one of the Owner's iPhones (debug overlay report or Profiler) is welcome when available. | A |
| D2 | Animation + IK + warping ≤ 4 ms/frame; motion DB ≤ 60 MB; ≤ 2 IK chains beyond feet; the motion-db report is updated when clips change. | A |
| D3 | The capture flow keeps active scan under 90 s and avatar generation under 2 min in the Owner's runs. | A |
| D4 | Services: per-scan cost and wall-clock reported for any pipeline change; no step exceeds its ticket's budget; the daily-cap logic is untouched or improved. | B |
| D5 | No full-screen blur in play; the HUD is one overlay pass within the top 8 %. | B |
| D6 | Package size and download path measured for any change to the environment package. | A |

## E. Code quality

| # | Check | |
|---|---|---|
| E1 | Layer boundaries hold: the five movement assemblies reference only downward (Bible §2); services expose a CLI or function entry point with typed I/O; no cross-service imports. | B |
| E2 | Movement and camera constants live only in `config/movement.json`; no magic numbers in C# or Python. | B |
| E3 | Inngest steps are idempotent and retry-safe; vendor calls have timeouts and classified errors. | B |
| E4 | Errors are handled at the boundary with user-facing copy in the voice guide, never swallowed; logs are structured. | B |
| E5 | Naming, structure, and formatting pass the linters; no dead code, commented-out blocks, or TODOs without a ticket id. | A |
| E6 | Public functions and non-obvious decisions carry a short comment or docstring; the README is updated for any new tool or entry point. | A |

## F. Test coverage

| # | Check | |
|---|---|---|
| F1 | New logic comes with unit tests (suggested); validators, ranking, schema checks, and metadata stripping benefit most from property or fixture tests covering edge cases (empty graph, unreachable summit, spam pattern, GPS in several container formats). | A |
| F2 | Coverage does not drop for the touched package (report welcome for services; EditMode/PlayMode results for Unity). | A |
| F3 | Tests are deterministic and hermetic: no network, no vendor calls, no real media; fixtures are synthetic and small. | B |
| F4 | A skipped or disabled test carries a reason; deleting tests to get green is noted as debt. | A |

## G. UI and design adherence

Before the design system is locked, Design Skills §3 rules and the §4 pre-PR checklist apply as written. After `DESIGN_SYSTEM.md` is locked (decisions 1–10):

| # | Check | |
|---|---|---|
| G1 | Only tokens from `design/tokens/` are used for color, type, spacing, radius, and motion; no literal values in USS/UXML. | B |
| G2 | Contrast on the three test scans: text ≥ 4.5:1, icons ≥ 3:1, with the scrim strategy applied (verification screenshots and a deuteranopia check are suggested). | B |
| G3 | Every glass surface has a flat fallback and every animation a Reduce Motion equivalent (testing with Reduce Transparency and Increase Contrast is suggested). | B |
| G4 | Touch targets ≥ 44 pt / 48 dp; play controls ≥ 56; safe-zone insets respected; one primary action per screen. | B |
| G5 | No text-only instructions in capture, create, or play; waits over 1 s show progress, over 10 s determinate progress with content. | B |
| G6 | Non-photo elements use only the locked element language (decision 1); nothing new enters the play viewport without an ADR. | B |
| G7 | Copy follows the voice guide (decision 2): short, warm, verbs first, no jargon. | A |
| G8 | The signature transition and avatar presentation match decisions 3 and 4. | B |

## H. Documentation and traceability

| # | Check | |
|---|---|---|
| H1 | Architecture or vendor choices are in an ADR (with AUTH) and the PR links it. | B |
| H2 | Field measurements, clip names, and contradictions go under the locked docs' Field notes headings, never into the body. | A |
| H3 | Ticket `history` updated; `PROGRESS.md` left to the Coordinator. | A |

## 9. Severity scale for findings

- **Critical**: secret exposure, RLS missing on user data, consent bypass, unauthorized protected-path change. Reject; fix within 24 h; rotate if applicable.
- **High**: required-criterion failure, spend or cap breach, missing signed URLs, unpinned dependency with a known vulnerability. Changes requested.
- **Medium**: advisory-row failures that accumulate as debt. Merge allowed with a debt ticket.
- **Low**: style and wording. Noted.

## 10. Review comment template

```
Verdict: merge | changes requested | reject
Ticket: <id> — AT-1 pass (evidence) · AT-2 fail (why) · …
Rubric: <failed rows, one line each>
Security: <checklist rows with findings and severity>
Performance: <numbers versus budget>
Design: <deviations with rule numbers>
Governance: <AUTH references verified or missing>
Next: <what unblocks merge>
```
