# gj-foreman — Working Handbook

Remit: turn milestone plans into tickets, route each ticket to the right agent, keep work unblocked, run standups, and write checkpoint reports for Gigantic Journeys. Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3 step 2, §9).

> **Who wears this hat (AUTH #006, #027).** The 8-Bot team was consolidated into one Claude Code Builder, a Coordinator, and one Grok Operator (`governance/AGENT_GOVERNANCE.md` §1, §8). There is no separate Foreman Bot. Coordination and checkpoint reports go to the **Coordinator**. VM and computer-use setup go to the **Operator** (`gj-operator`). Tickets with `owner: gj-foreman` (M0-FORE-01..04, M1-FORE-01, M4-FORE-01) follow that split. Kit §2 is historical context for this role. Where it disagrees with AGENT_GOVERNANCE, AGENT_GOVERNANCE wins.

Research list: `projects/skills/foreman/RESOURCES.md`.

## 1. Rules this hat must follow (cite, don't paraphrase)

| Rule | Source |
|---|---|
| Session start: token check, pull, PROGRESS, tickets, SKILLS, auth-request issues | `agents/grok/README.md` §3 |
| Branch names, commit message form `<ticket-id>: <what>`, 2-hour push cadence | `agents/grok/README.md` §4 |
| PR template, evidence standard, outright-reject list | `agents/grok/README.md` §5, `.github/PULL_REQUEST_TEMPLATE.md` |
| AUTH REQUEST format and triggers (spend, account, protected paths) | `agents/grok/README.md` §6, `.github/scripts/auth_gate.py` |
| CHECKPOINT template | `agents/grok/README.md` §7, `governance/CHECKPOINTS/README.md` |
| Standups, BLOCKER and DEFECT issues | `agents/grok/README.md` §8 |
| Review rows A–H; B rows block | `governance/REVIEW_RUBRIC.md` |
| Secret hygiene, least privilege, milestone security gates | `governance/SECURITY_CHECKLIST.md` §1, §8, §12 |
| Routing rule, concurrency, merge policy, credentials | `governance/AGENT_GOVERNANCE.md` §2, §4, §5, §6 |
| Ticket lifecycle and status flow | `tickets/README.md`, `tickets/SCHEMA.json` |
| What v1 is; testing is never a merge gate | `SPEC.md` §8, §11 (AUTH #003) |

The Foreman does not own movement or UI. When a ticket touches them, the assignee must run Movement Bible §10 (the `movement.json` contract, mirrored in `config/movement.json`) and Design Skills §4 (the pre-PR design checklist). The Foreman confirms that the PR shows this.

## 2. Decomposing a milestone into tickets

1. **Start from the exit test.** SPEC §8 states one exit test per milestone. Each P0 ticket must be on the path to that test. The M0 exit test is M0-UNITY-04: a ticket goes from creation to a merged PR with a QA screenshot and no human typing.
2. **One ticket = one reviewable change.** Keep it under about 800 changed lines (REVIEW_RUBRIC B5). Give it one owner domain and one branch. Deliverables are repo paths. If a ticket needs two domains, split it and link them with `depends_on`.
3. **Acceptance tests are the contract.** Each AT is testable, names its evidence (a CI job, file path or report), and carries a `level`. Deliverables, security, governance and automated CI are `required`. Tests, QA, performance and device checks are `suggested` (SPEC §11). Only the Coordinator edits ATs (`tickets/README.md`); an author never edits their own (REVIEW_RUBRIC B4).
4. **Mark `scope_out` explicitly.** Anything deferred goes to `BACKLOG.md`, not into the ticket.
5. **Flag AUTH needs up front.** Spend, accounts, `SPEC.md`, `ADRs/`, `data/schemas/`, `design/DESIGN_SYSTEM.md`, `design/tokens/`, the locked design docs, `config/movement(.schema).json`, `tickets/SCHEMA.json`, `governance/AGENT_GOVERNANCE.md` and `agents/claude/SELF_GOVERNANCE.md` are protected (`auth_gate.py`). Put the need in `auth_required` so the ticket does not stall mid-PR.
6. **Validate** with `python tickets/validate.py` before pushing. `--summary` prints the counts table for PROGRESS.md.

## 3. Assigning by role (routing rule)

Route by tool surface, cheapest capable agent first (AGENT_GOVERNANCE §2):

1. Can it be done with code, a CLI, an API or Unity `-batchmode`? → **Builder**. This is the default.
2. Does it need a screen with no API, or is it long-running and unattended? → **Operator**. Examples: Editor visual import, vendor dashboards, visual QA screenshots, watching the reconstruction queue. The ticket states in one line why no scriptable path exists.
3. Governance, review or merge? → **Coordinator**.
4. Spend, an account, physical capture, or a design or plan change? → **Owner**, via an AUTH REQUEST or an `owner` ticket.

The `owner` label names the skill domain. AGENT_GOVERNANCE §8 maps each domain to its executing agent. The Operator wears one hat at a time (§3).

## 4. Detecting blockers

Check these signals every session:

- **Status `blocked`** must have `blocked_by` (validate.py enforces this). Today M1-PLAT-01 is waiting on Apple/Google OAuth plus a Supabase access token, and M1-RES-01 is waiting on a monthly Tier 2 compute AUTH (SPEC §5).
- **Stalled `in-progress`.** Watch for no commits on the ticket branch for 8 hours of active time (`agents/grok/README.md` §8). Check with `gh run list` and `git log origin/<branch>`.
- **Pending AUTH.** Open `auth-request` issues and the AUTHORIZATION_LOG "next free" number.
- **Red or skipped CI on main.** Use `gh run list -R BlissDirective/Gigantic-Journeys`. Unity jobs skip unless `UNITY_CI_ENABLED=true` and the Unity secrets exist (`unity-tests.yml`, `ios-build.yml` preflight). A skip is not green evidence for Unity work.
- **Owner-only dependencies.** Corpus capture (M0-OWNER-01), accounts, and the machine-user PAT (M0-REPO-04) cannot be worked around. File them as BLOCKER issues and move to other work.

Clear a blocker by routing it (§3). If it can't be cleared in 8 hours, open a BLOCKER issue with the template. Escalate to the Owner only for AUTH and true blockers.

## 5. Running standups

Post a 5-line standup every 4 hours of active operation to the Owner's channel (`agents/grok/README.md` §8). The channel is whatever the Owner names; kit §2 suggested `#gj-standup`, which is TBD until the Owner confirms it.

```
Done: <ticket ids + commit/PR links>
In progress: <ticket id — agent — next step>
Blocked: <ticket id — blocked_by — who clears it>
AUTH pending: <#n — one line> | none
Next: <the next 1–3 tickets in priority order>
```

Rules: use evidence links, not adjectives. Keep it to five lines. Repeat nothing from the last standup unless its state changed.

## 6. Writing checkpoint reports

- At milestone end all feature work halts. Collect a 5-line summary per active domain: done, evidence, open PRs, risks, recommendation (`agents/grok/README.md` §7).
- Write `governance/CHECKPOINTS/M<n>.md` in the exact template from `governance/CHECKPOINTS/README.md`, on branch `checkpoint/M<n>` (tickets M0-FORE-04, M1-FORE-01, M4-FORE-01). The M0 readiness review in `governance/checkpoints/M0.md` shows the level of evidence expected.
- **Security notes** list the SECURITY_CHECKLIST §12 rows due at this checkpoint (M0: 1.1–1.6, 8.1, 8.2) with their state.
- **Spend** is measured against approved caps: the $50/day agent+API cap (kit §7, SECURITY_CHECKLIST §8.5) and per-AUTH caps such as the #031 $100 reconstruction spike. Figures come from the spike report and the vendor dashboards, never from estimates.
- End with "Awaiting: Coordinator REVIEW, then Owner RESUME." Feature work resumes only after `RESUME M<n+1>`.

## 7. Operating the repo (validated flow)

```
set -a; . ./.env.local; set +a; export GH_TOKEN="$GITHUB_TOKEN"   # never echo it
git fetch origin && git worktree add <dir> -b <branch> origin/main
ruff check . && ruff format --check . && python tickets/validate.py && python .github/scripts/check_movement_sync.py
python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]"
git pull --rebase && gh run list -L 10    # push only when no Unity workflow is running (unity-license concurrency)
```

- Main is protected. It has seven required checks and blocks force-pushes; admins are exempt (M0-REPO-02, `qa/vm-setup/repo-settings.md`). Never force-push.
- Update PROGRESS.md and the ticket `history` with every change you land.

## 8. Mistakes to avoid

- Adding a `*requirements*.txt` with heavy or GPU deps. CI pip-installs it and `pip-audit --strict` fails. Keep heavy deps in a Dockerfile (see `services/reconstruction/`).
- Editing a protected path without `APPROVED #n`. The `auth-gate` job fails, and the Coordinator must reject it (REVIEW_RUBRIC B2).
- Letting a Unity job retry a bad password. Repeated failed sign-ins locked the Unity account on 2026-09-24 (PROGRESS Blockers, M0-REPO-03). Keep the `unity-license` concurrency group, and stop after one 401.
- Treating a Unity "skipped" preflight as a pass.
- Running two agents on the same files (AGENT_GOVERNANCE §4). Another worker's paths are off-limits for the session.
- Parallelizing to go faster on shared state. Only the Coordinator authorizes bursts, and it names the cap and the isolation.
- Writing progress claims without evidence (SPEC §11: evidence, not a sentence).
- Pasting a token into a command line that gets echoed, or into logs (SECURITY_CHECKLIST §1).

## 9. Checklists

**Before opening or landing any change (pre-PR):**
- [ ] Ticket JSON updated (`status`, `branch`, `pr`, `history`, `updated`), and `validate.py` passes.
- [ ] Every required AT has concrete evidence (REVIEW_RUBRIC A1).
- [ ] No protected path is touched, or `APPROVED #n` is cited and logged (B2).
- [ ] No spend, account or vendor is added without AUTH (B3).
- [ ] Secret scan is clean, and no `.env*`, key or token appears in the diff, logs or screenshots (C1, SECURITY_CHECKLIST §1).
- [ ] ruff, format, validate, movement-sync and workflow YAML parse are all green locally.
- [ ] PROGRESS.md is updated on merge (REVIEW_RUBRIC §0 step 5).

**Before a checkpoint:** every ticket in the milestone is merged, done, or carries `blocked_by` and a BLOCKER issue. The §12 security rows are checked. Spend is summed against the caps. M0-FORE-03 confirms every handbook exists and has its required sections.

**Before filing an AUTH batch:** the number follows the last `AUTHORIZATION_LOG.md` row and any open request. Each request uses the exact six-line format. Cost is stated one-time and monthly. Reversibility is stated.

## 10. Pointers

`CLAUDE.md` · `SPEC.md` §8, §11 · `PROGRESS.md` · `BACKLOG.md` · `governance/{AGENT_GOVERNANCE,REVIEW_RUBRIC,SECURITY_CHECKLIST,AUTHORIZATION_LOG}.md` · `governance/CHECKPOINTS/` · `agents/grok/README.md` · `agents/grok/roles/gj-operator.md` · `agents/claude/{COORDINATOR,BUILDER,SKILLS}.md` · `.github/workflows/` · `tickets/validate.py` · `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` §2, §4, §6.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + a curated RESOURCES.md starter set. |
| 2026-09-26 | The Foreman hat is now split between the Coordinator (coordination, checkpoints) and the Operator (VM setup), per AUTH #006. Protected main has admins exempt and seven required checks (M0-REPO-02). The Unity lockout lesson is from M0-REPO-03. | gj-operator expanded RESOURCES.md to 106 link-checked entries and rewrote SKILLS.md around decomposition, routing, blockers, standups and checkpoints (M0-SKILL-01). |
