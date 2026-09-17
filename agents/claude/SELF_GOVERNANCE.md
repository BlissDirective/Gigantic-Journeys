# Claude Code — Self-Governance and Usage Optimization

`agents/claude/SELF_GOVERNANCE.md` · v1.0 · 2026-09-17 · Status: LOCKED except by AUTH (design-change) · Authorization: APPROVED #006

Rules every Claude Code session on this project follows, in **both** roles (Builder and Coordinator), to do the most useful work per token. Read at the start of every session alongside the role doc (`BUILDER.md` or `COORDINATOR.md`).

## 0. What "optimize usage" means on Claude Max

The Owner is on **Claude Max**, a subscription with rolling usage limits (short-window and weekly), not per-token billing. So the goal is not to minimize a dollar invoice; it is to **maximize useful work inside the limits** and avoid throttling that would stall the build. Two honest facts shape these rules:

- **Prompt caching is automatic.** Claude Code and the API cache stable prefixes on their own; there are no TTL knobs to set here. What a session controls is whether its behavior *keeps the cache warm* (stable context, reused prefixes) or *invalidates it* (churn, reordering, reloading). These rules bias toward the former.
- **The cheapest token is the one not spent.** Most waste is redundant reads, over-broad searches, oversized context, and speculative actions that fail and must be redone. Cutting those is the whole game.

Safety exception: never trade away correctness to save usage. Reviews, security audits, consent-gate and RLS checks, and the merge gate get the tokens they need. Under-reviewing to conserve quota is a self-governance violation, not a saving.

## 1. Context discipline

- **Load only what the task needs.** Read the ticket, then the specific files it names, not the whole tree. One role doc and one skill domain per ticket, never all of them.
- **Do not re-read what is already in context.** The harness tracks file state; after a successful `Edit`/`Write`, trust it, do not read the file back to "verify." Re-read only when something else could have changed the file.
- **Prefer `Read` with `offset`/`limit`** on large files; pull the section you need, not 2,000 lines.
- **Let context compaction happen.** Do not restate the whole plan each turn; the summary carries it. Do not paste large file contents into chat or commit messages.

## 2. Prompt-cache-friendly behavior

- **Keep the stable prefix stable.** The system prompt, `CLAUDE.md`, and the active role doc are the cached prefix; do not reorder or rewrite them mid-session.
- **Batch a session around one ticket** so its context (rules, SPEC section, role doc, the ticket) is loaded once and reused across the turns that finish it.
- **Avoid gratuitous context churn** (reloading files, switching tickets mid-flow); each switch cools the cache and re-pays for the new context.

## 3. Tool-call optimization

- **Batch independent calls in one turn.** Reads, greps, and globs with no dependency between them go in a single message so they run together (as this project's setup does throughout).
- **Search narrow, not wide.** `Grep`/`Glob` with a precise pattern and path beat reading directories. Use ripgrep semantics, not `cat`/`grep` loops in Bash.
- **One validated action over speculative ones.** For any push or CI-facing change, run the repo's fast checks first (`ruff`, `tickets/validate.py`, movement sync, YAML parse) and push once green. One clean push beats three that fail and must be redone.
- **Do not poll.** Wait on background tasks and PR events through the harness's notifications, never with `sleep` loops or repeated status calls.
- **Reuse results.** If a search or read already answered a question this session, use that answer; do not re-run it.

## 4. Delegation and subagents

- **Delegate broad, multi-file sweeps to a subagent** that returns the conclusion, not the file dumps, when a question means reading across many files. Keep the finding, discard the search context.
- **Do not fan out for a single-file lookup** you can do directly; a subagent carries its own context cost.
- **Cap parallel subagents.** Bounded bursts only, per `AGENT_GOVERNANCE.md` §4, and only for isolated work. Never spawn agents to "go faster" on shared state.

## 5. The repo as external memory

- **Write durable state to files, not long chat context:** `PROGRESS.md`, reports under `qa/` and `data/reports/`, ticket `history`. Re-read a small file when needed instead of holding everything in context all session.
- **One source of truth per fact.** Do not duplicate; link. Regenerate derived text (the `PROGRESS.md` ticket table) from the source (`tickets/validate.py --summary`) rather than hand-maintaining two copies.

## 6. Session hygiene

- **One ticket per session** where possible; finish it, update its JSON and `PROGRESS.md`, then start the next with fresh, minimal context.
- **Summarize before switching** if a switch is unavoidable, so the next context is small.
- **Close the loop, then stop.** End the turn when the task is done or blocked on the Owner; do not keep a session warm doing nothing.

## 7. Division of load between the two Claude roles

- **The Builder carries the token-heavy work** (reading code, writing code, running tests). It follows §1–§6 hardest.
- **The Coordinator stays lean:** it reads the ticket, the diff, the rubric rows that apply, and the AUTH log, then writes the review. It does not re-read the whole repo to review one PR.
- **If usage approaches a Max limit,** prioritize the merge-critical path (review and merge what is ready, keep CI green) over starting new Builder work; a green, mergeable state is the safe place to pause.

## 8. What justifies spending more

Spend the tokens without hesitation on: reviewing against every acceptance test and security row, reproducing a CI failure before fixing it, adversarially re-reading a diff before a push, a security audit, and anything touching consent, RLS, signed URLs, or secrets. The cost of a missed defect or a leaked secret dwarfs the tokens saved by cutting a corner here.

## 9. Change log

| Version | Date | Change | Authorization |
|---|---|---|---|
| 1.0 | 2026-09-17 | Initial self-governance and usage-optimization rules for Claude Code (Builder and Coordinator) on Claude Max | AUTH #006 |
