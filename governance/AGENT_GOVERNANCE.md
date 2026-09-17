# Agent Governance

`governance/AGENT_GOVERNANCE.md` · v1.1 · 2026-09-17 · Status: **LOCKED except by AUTH REQUEST (design-change)** · Authorization: APPROVED #006, #007

The operating model for who does the work on Gigantic Journeys and how their actions are optimized for cost and reliability. It **supersedes the kit's eight-Bot team model** (`context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` §0, §2, §3) and returns to the plan's original Claude-subagent design (`context/DEVELOPMENT_PLAN.md` §2: Architect, Builder, Reviewer as separate contexts) with one consolidated Grok Bot for computer use. Companion documents: `agents/claude/SELF_GOVERNANCE.md` (Claude Code usage optimization), `agents/claude/COORDINATOR.md` and `agents/claude/BUILDER.md` (the two Claude roles), `agents/grok/roles/gj-operator.md` (the single Grok Bot prompt pack), `agents/grok/README.md` (repo rules for the Bot).

## 0. Why this model

Research and this project's own budget point the same way. Multiple agents running the same work in parallel burn far more tokens than one agent for the same result (Anthropic measured a multi-agent research system at roughly 15x the tokens of a single chat, with token volume explaining about 80% of the gain), and multi-agent systems are more fragile through context loss and conflicting decisions (Cognition). The Owner is on subscription seats (Claude Max, SuperGrok Plus), so the cost of extra agents shows up as quota exhaustion and throttling rather than a bill, but the waste is the same. The design principle is therefore: **one agent per surface, single-threaded writes, and each agent used only for what it alone does well.**

## 1. The agent roster

Cursor is retired from the automated loop (keep it as a personal editor if you like; it is not part of the pipeline).

| Agent | Surface | Does | Never |
|---|---|---|---|
| **Claude Code — Builder** | a Claude Code session | Writes all feature code and text: C#, TypeScript, Python, tests, docs, PR authoring, on `ticket/<id>` branches. Runs anything scriptable (CLI, API, `-batchmode`). **Self-reviews and merges its own PRs to `main` once CI is green** (AUTH #007). | Merges with red CI; skips self-review; does GUI-only work |
| **Claude Code — Coordinator / Secondary Reviewer** | this role, a separate Claude Code session | Governance, AUTH handling, PROGRESS, **periodic independent secondary review** (§5), checkpoint reviews; merges governance PRs. | Writes feature code; approves an AUTH; skips security-sensitive secondary reviews |
| **Grok Bot — Operator** (`gj-operator`) | one persistent Bot on the SuperGrok Plus cloud computer | Computer use (GUI with no API or CLI path) and long-running unattended operations, driven by one loaded skill hat per task. | Writes feature code; runs many copies of itself; holds production credentials |
| **Owner** | you | Authorizes spend, accounts, and design or plan changes; physical capture; final review at checkpoints. | — |

The kit's **Foreman** role is absorbed: with no multi-Bot team to coordinate, ticket assignment, the queue, standups, and checkpoint reports fall to the Coordinator (and VM/computer-use setup to the Operator). There is no separate Foreman Bot.

## 2. The routing rule (the money-saver)

For any task, route by **tool surface**, cheapest capable agent first:

1. **Can it be done with code, a CLI, an API, or Unity `-batchmode`?** → Claude Code **Builder**. This is the default and covers most work.
2. **Does it need a screen with no API or CLI path** (importing a scan into the Unity Editor visually, a vendor dashboard, a console step, visual QA screenshots), **or is it long-running and unattended** (babysitting the Luma reconstruction queue, watching a cost dashboard for hours)? → Grok Bot **Operator**.
3. **Is it governance, review, or merge?** → **Coordinator**.
4. **Is it spend, an account, physical capture, or a design or plan change?** → **Owner** (an AUTH REQUEST or an OWNER ticket).

The rule protects the Grok quota: **scriptable-first, GUI only as a last resort.** If a task could be done either way, it goes to the Builder. A ticket that hands work to the Operator states in one line why no scriptable path exists.

## 3. The consolidated Grok Bot Operator

One persistent Grok Bot, `gj-operator`, replaces the eight specialist Bots. It is an "AI teammate" on a cloud computer that works across websites, apps, files, and tools, and can be left running on long jobs.

- **Skill hats, not seats.** Per task the Operator loads the one relevant domain brief (`agents/grok/roles/gj-<domain>.md`) and its handbook (`projects/skills/<domain>/SKILLS.md`), does the work, and drops that context before the next task. The eight former role names (`gj-capture`, `gj-scenegraph`, `gj-gameplay`, `gj-avatar`, `gj-platform`, `gj-design`, `gj-qa-release`, `gj-data`) are now **skill domains**, not separate agents.
- **One hat at a time.** The Operator never carries all eight domains in context at once; that is the token waste consolidation exists to avoid.
- **Computer use and long-running ops only.** Anything buildable is the Builder's.
- **It still uses the repo like any contributor:** branches `ticket/<id>-<slug>`, PRs with the template for the artifacts it produces (QA screenshots, corpus manifests, reports), the AUTH and CHECKPOINT protocols, and the 2-hour sync cadence (`agents/grok/README.md`).

## 4. Concurrency policy

- **Single-threaded writes.** At most one agent writes to a given branch or file set at a time. Two agents never edit the same files concurrently.
- **Default one working agent.** Normal operation is the Builder working the queue in priority order, the Operator handling handed-off computer-use tasks, and the Coordinator reviewing. Sequential, not parallel.
- **Bounded bursts, by exception.** The Coordinator may authorize a capped parallel fan-out only for **isolated, read-only or write-isolated, high-value** work where wall-clock matters: a corpus reconstruction sweep, a one-time research pass. Every burst names its agent count cap and its isolation guarantee, and its writes still land single-threaded (one agent merges the results). This is the only sanctioned multi-agent pattern.
- **Never** parallelize to "go faster" on shared-state work; that is the fragile, token-heavy pattern this spec rejects.

## 5. Review, merge, and periodic secondary review (AUTH #007)

Per-PR separation of duties is relaxed for velocity: the Builder self-reviews and merges its own work rather than handing off to a second session for every merge. The compensating controls are the always-on automated gates and a periodic independent review.

- **Merge policy.** Any Claude Code role may merge its **own** reviewed work to `main` **once every required CI check is green** (secret-scan, repo hygiene, lint gate, governance, and the Unity and Android gates where they apply). A merge with red CI is a process violation. The Grok Operator does not self-merge; a Claude role merges its artifact PRs after a quick review.
- **Self-review is the first gate.** The Builder runs the §1 self-review in `agents/claude/SKILLS.md` on its own diff before merging: acceptance criteria met with evidence, SPEC conformance, an adversarial diff read, the REVIEW_RUBRIC blocking rows, and the security rows that apply.
- **Periodic secondary review is the second gate.** An independent reviewer (the Coordinator by default, or an Owner-designated reviewer) reviews at intervals, not per-PR: at least **weekly** (folded into the AUDIT) and at **every checkpoint**. It samples merged PRs since the last secondary review against `REVIEW_RUBRIC.md` and `SECURITY_CHECKLIST.md`, and covers **100% of security-sensitive merges** (auth, RLS, secrets, signed URLs, consent, payments, the movement/validator contract), which the Builder flags `secondary-review: required` at merge. Findings become fix tickets.
- **The Owner** remains the final reviewer at each checkpoint.
- **Residual risk, stated plainly.** A defect or unsafe change can reach `main` before a human or independent agent sees it; the automated security and lint gates plus 100% secondary review of security-sensitive merges are the mitigation, and the periodic review is expected to catch the rest quickly. This is the accepted cost of not switching sessions to merge (Owner decision, AUTH #007).

## 6. Credentials

- The Operator holds the **union of staging credentials** (staging Supabase, vendor sandboxes, the Bot GitHub machine-user PAT). This is the accepted simplification (Owner decision, 2026-09-16): a compromise or prompt-injection reaches everything the former eight roles could touch. The blast radius is bounded to **staging only**.
- **Production Supabase keys, Apple signing certificates and the App Store Connect API key, and payment credentials are CI-only and never reach any agent** (SECURITY_CHECKLIST §1.4). This line does not move.
- Where a hat needs only a subset (for example a vendor console), the Operator loads only that credential for the task where practical.
- The Builder holds no vendor or platform secrets; it works through the repo and CI.

## 7. Usage and token optimization

System-wide principles; the per-agent detail lives in `agents/claude/SELF_GOVERNANCE.md` (Claude) and `agents/grok/roles/gj-operator.md` (Grok).

- **Route to the cheapest capable surface** (§2). Most work is scriptable and belongs to the Builder, not the Operator.
- **One hat / one role doc per task.** Never load all domains or all role docs at once.
- **The repo is external memory.** Durable findings go to files (`PROGRESS.md`, reports), not long-lived chat context. "If it is not in the repo, it did not happen" is also a token rule.
- **Prompt-cache-friendly work.** Keep the stable context stable so the automatic prompt cache is reused; batch a session around one ticket.
- **Tool-call discipline.** Batch independent calls; prefer targeted search over broad scans; each Grok server-side tool call and each computer-use action is metered or quota-drawing, so avoid redundancy.
- **Single validated action over speculative ones.** One correct push beats three that fail CI.
- **Spend caps hold.** The $50/day agent-plus-API cap (kit §7) and vendor per-key caps remain; the pipeline halts at the cap.
- **Monitoring cadence.** The Coordinator reports usage posture in the weekly AUDIT and at each checkpoint: which surface consumed what, any throttling hit, and whether the routing rule was followed. A monthly review adjusts the model if a surface is over-consumed.

## 8. Owner-label to executing-agent mapping

Ticket `owner` names the **skill domain**; the executing agent follows the routing rule (§2). New tickets may use `claude-builder` or `gj-operator` directly.

| Ticket owner label (domain) | Typical executing agent |
|---|---|
| `gj-gameplay`, `gj-scenegraph`, `gj-platform`, `gj-avatar`, `gj-data` (services, Unity, API, schemas, ML) | Claude Code **Builder** (buildable), with the **Operator** for any GUI-only or long-running step |
| `gj-capture` | **Builder** for the pipeline and tools; **Operator** for in-Editor scan import and capture-dashboard work |
| `gj-design` | **Builder** for tokens and UI Toolkit code; **Operator** for producing mockups or visual verification that needs a GUI |
| `gj-qa-release` | **Operator** for visual QA, device runs, and store-console steps; **Builder** for test code and CI |
| `gj-foreman` (coordination, checkpoints, VM setup) | **Coordinator** for coordination and checkpoint reports; **Operator** for VM and computer-use setup |
| `coordinator` | **Coordinator** |
| `owner` | **Owner** |
| `claude-builder` | **Builder** |
| `gj-operator` | **Operator** |

The 61 existing tickets keep their domain labels; re-labeling to `claude-builder` / `gj-operator` happens as each is picked up, or in a bulk pass if the Owner asks.

## 9. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 1.0 | 2026-09-17 | Consolidated to Claude Code Builder + Coordinator and one Grok Bot Operator; Cursor retired from the loop; routing rule, concurrency policy, credential model, and usage-optimization principles set | AUTH #006 |
| 1.1 | 2026-09-17 | Builder may self-review and merge its own PRs to main on green CI; per-PR separation replaced by periodic independent secondary review (weekly, at checkpoints, and 100% of security-sensitive merges); merge policy and residual-risk note added | AUTH #007 |
