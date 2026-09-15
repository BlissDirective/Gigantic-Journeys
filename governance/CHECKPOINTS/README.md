# `governance/CHECKPOINTS/`

One report per milestone, `M<n>.md`, written by the Foreman on branch `checkpoint/M<n>` when all Bots have stopped feature work. The Coordinator answers with `REVIEW M<n>` (kit §5) and updates `PROGRESS.md` and `AUTHORIZATION_LOG.md`; the Owner replies `RESUME M<n+1>`.

Template (kit §6, exact):

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

Append each specialist's 5-line summary under a heading per Bot. The Coordinator's review is appended to the same file after merge as `## Coordinator REVIEW` with the six items from kit §5.
