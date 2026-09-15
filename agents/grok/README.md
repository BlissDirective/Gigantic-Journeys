# Working with this repository: rules for Grok Bots

`agents/grok/README.md` · v1.1 · 2026-09-15 · Every Bot reads this at every session start. The Foreman enforces it; the Coordinator rejects PRs that break it.

## 0. Platform and testing policy (AUTH #003)

- v1 ships on the iOS App Store only. Android stays a compiling build target, not a release target; no Android-specific work.
- No minimum device model: build for the best graphics and capabilities on the newest iPhones, with automatic quality tiers for older ones.
- Tests, QA passes, performance measurements, and device checks are suggestions that never block a merge; the Owner tests on real iPhones throughout. The merge gates are the automated CI checks and the security rules. Acceptance criteria carry `required` or `suggested` levels (`SPEC.md` §11).

## 1. Who is who

- **Owner** (BlissDirective): authorizes spend, accounts, and changes to `SPEC.md`, ADRs, data schemas, the design system, and the milestone plan. Does physical capture. Replies `APPROVED #n` or `DENIED #n`.
- **Coordinator** (Claude Code): reviews every PR on GitHub against the ticket's acceptance tests, `SPEC.md`, `governance/REVIEW_RUBRIC.md`, and `governance/SECURITY_CHECKLIST.md`. The only one who merges to `main`. Keeps `PROGRESS.md` and `governance/AUTHORIZATION_LOG.md`.
- **Foreman** (`gj-foreman`): assigns tickets, runs standups, unblocks, batches AUTH REQUESTs, writes checkpoint reports.
- **Specialists** (`gj-capture`, `gj-scenegraph`, `gj-gameplay`, `gj-avatar`, `gj-platform`, `gj-design`, `gj-qa-release`, `gj-data`): the work. Prompt packs in `agents/grok/roles/`: when the Owner creates a Bot, the whole fenced block in that file is the Bot's instructions (the kit prompt plus the Coordinator preamble).

## 2. Two repositories, one rule about secrets

- VM repo: `~/projects/gigantic-journeys/` on the Bot computer, cloned from GitHub. `.env.local` holds every key and never leaves the VM (gitignored; CI fails any tracked `.env*` except `.env.example`).
- GitHub repo: `github.com/BlissDirective/Gigantic-Journeys`. Everything except secrets syncs here. The Coordinator sees only this. Work that is not on GitHub does not exist.
- Never paste a secret into chat, a commit, a ticket, an issue, a PR, a screenshot, a log, or a report. If you did, say so immediately: it gets rotated (SECURITY_CHECKLIST §1.5).
- Bots authenticate to GitHub as the machine user, never as the Owner (AUTH #002, approved 2026-09-15). The Owner personally issues the machine user's token and hands it to the team; see §3 step 0.

## 3. Session start (every specialist, every session)

0. **GitHub access first.** Check that `GITHUB_TOKEN` in `~/projects/gigantic-journeys/.env.local` is a real token (not `PLACEHOLDER`) and that `git ls-remote https://github.com/BlissDirective/Gigantic-Journeys` succeeds with it. If either fails, stop and ask the Owner (specialists through the Foreman): *"Owner, I need the GitHub PAT for the Bot machine user before I can begin work. Please share it through the Bot credential store; I will write it to .env.local and never paste it anywhere else."* No ticket starts, and no other credential is ever used, until the token is in place. The Foreman asks for it as its very first message.
1. `git fetch` and pull your branch; read `PROGRESS.md` and your tickets in `tickets/`.
2. Re-read `projects/skills/<role>/SKILLS.md`. Design and gameplay Bots also re-read Design Skills §3–5 and the Movement Bible sections they touch.
3. Check the `auth-request` issues for `APPROVED` or `DENIED` on anything you wait on.
4. Work the highest-priority unblocked ticket assigned to you. Push at least every 2 hours. Open the PR with the template.
5. Before ending: push, update the ticket JSON (`status`, `branch`, `history`), append learnings to `SKILLS.md`.

## 4. Branches, commits, cadence

- One branch per ticket: `ticket/<id>-<slug>`, for example `ticket/M0-UNITY-04-debug-overlay`. Exceptions: `setup/<role>-skills` (your research handbook), `auth/<nnn>-<slug>` (log rows for an AUTH batch), `checkpoint/M<n>` (the Foreman's checkpoint report).
- Never push to `main`. Never force-push a shared branch. Never rewrite history on someone else's branch.
- Commit messages: `<ticket-id>: <what changed>`, imperative, one logical change per commit.
- **Sync cadence: push at least every 2 hours of active work**, unfinished or not. Open the PR as a draft early.
- One ticket per branch per PR. Found something else? New ticket via the Foreman, or a line in `BACKLOG.md`.
- Before every push: `pre-commit run --all-files`, `python tickets/validate.py`, and the checks CI runs for your language (`ruff check . && ruff format --check .`; `npm run lint && npm test`; Unity `-batchmode -runTests`).

## 5. Pull requests

- Use `.github/PULL_REQUEST_TEMPLATE.md` in full: ticket, what changed, acceptance-test table with evidence, visual evidence, security considerations, authorization, performance, QA.
- Evidence is an artifact in the PR or CI: a test name, a CI job link, a PNG under `qa/evidence/<ticket>/`, a report under `qa/reports/` or `data/reports/`. A sentence is not evidence.
- Gameplay, UI, and capture PRs: a `gj-qa-release` visual pass and a performance readout from one of the Owner's iPhones are welcome when available; they are suggestions, not gates (AUTH #003).
- A PR is rejected outright when it: contains a secret or `.env*` file; touches a protected path without `APPROVED #n` (the CI `auth-gate` fails it first); adds spend or an account; edits its own acceptance tests; ignores a previous review; contains raw media.
- Address every review comment or reply why not, then re-request review. Do not open a second PR for the same ticket.
- Changes to a path another Bot owns need that Bot's review first (`reviewers` in the ticket).

## 6. AUTH REQUEST (the only hard rule)

Stop and request authorization before any of: (1) spending money or adding a paid service, including free tiers that require a card; (2) creating any account; (3) changing anything in `SPEC.md`, any ADR, `data/schemas/`, `design/DESIGN_SYSTEM.md`, `design/tokens/`, the locked design docs, `config/movement.json` (Bible §10), `tickets/SCHEMA.json`, or the milestone plan.

How: open a GitHub issue with the **AUTH REQUEST** template (label `auth-request`), numbered after the last entry in `governance/AUTHORIZATION_LOG.md` and any open request. Specialists route through the Foreman; the Foreman may batch several issues. Post the same block in the Owner's channel. The format is exact:

```
AUTH REQUEST #<n>
Type: spend | account | design-change
What: <one line>
Why: <one line>
Cost: <one-time / monthly>
Reversible: yes | no
Waiting on: Owner
```

The Owner replies `APPROVED #<n>` or `DENIED #<n> — <reason>` on the issue. Nothing else unblocks it. The PR that uses the approval cites `APPROVED #<n>` in its Authorization section; the Coordinator logs the decision. While waiting, work another ticket and record the wait in the ticket's `blocked_by`.

Allowed without AUTH: appending under the `Field notes` heading of the Movement Bible, the Design Skills, or DESIGN_SYSTEM.md (measured values, clip names, contradictions). Anything else in those files is a design change.

## 7. CHECKPOINT

At the end of every milestone all Bots stop feature work. Each specialist hands the Foreman a 5-line summary (done, evidence, open PRs, risks, recommendation). The Foreman opens branch `checkpoint/M<n>` adding `governance/CHECKPOINTS/M<n>.md`:

```
# CHECKPOINT M<n> — <date>
Exit test: <pass/fail> — <evidence links>
Merged tickets: <list>
Open PRs awaiting Coordinator: <list>
Design decisions made this milestone (all with AUTH #): <list>
Security notes: <list>
UI screens changed (with screenshots): <list>
Spend this milestone vs budget: <numbers>
Blockers and risks: <list>
Recommendation for M<n+1>: <3 lines>
Awaiting: Coordinator REVIEW, then Owner RESUME.
```

The Coordinator runs `REVIEW M<n>`; the Owner replies `RESUME M<n+1>`. Only then does feature work resume.

## 8. Standups, blockers, defects

- The Foreman posts a 5-line standup every 4 hours to the Owner's channel: done, in progress, blocked, AUTH pending, next. Tickets stalled 8 hours are reassigned.
- A blocker the Foreman cannot clear becomes a **BLOCKER** issue (template). Owner actions (scans, devices, accounts) are `OWNER` tickets.
- QA defects are **DEFECT** issues linked to the ticket and PR.

## 9. Your research handbook (first task)

Before any ticket: research the top 100 resources for your role (kit §3), save `projects/skills/<role>/RESOURCES.md` (annotated) and `projects/skills/<role>/SKILLS.md` (patterns, mistakes, pre-PR checklists), commit on `setup/<role>-skills`, open the PR (ticket `M0-SKILL-nn`). Keep `SKILLS.md` current; it is reviewed at every checkpoint.

## 10. What the Coordinator checks (so you can check first)

Required-level acceptance criteria with evidence → `SPEC.md` conformance → REVIEW_RUBRIC rows A–H → SECURITY_CHECKLIST rows → CI green (secret-scan, lint, governance, unity-tests) → suggested-level evidence when offered → AUTH references. If any would fail, fix it before opening the PR.
