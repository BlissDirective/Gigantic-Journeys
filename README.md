# Gigantic Journeys

A mobile game (Unity 6; v1 ships on the iOS App Store, Android later) in which a near-photorealistic 1:12 avatar of the player journeys through the real environments they capture: indoor rooms and tabletop builds in v1. The environment is the content; the avatar is the piece; traversal is the product. No synthetic game objects in v1.

Owner: BlissDirective (SparkForge Labs). Software: a Claude Code Builder writes it, the Coordinator reviews and merges. Computer use and long-running ops: one Grok Bot Operator. Model: `governance/AGENT_GOVERNANCE.md`.

## Start here

| Need | File |
|---|---|
| What v1 is, non-goals, budgets, definition of done | `SPEC.md` |
| Where things stand | `PROGRESS.md` |
| How the avatar moves (locked) | `design/MOVEMENT_BIBLE.md` |
| How it looks and feels (locked) | `design/Gigantic-Journey-Design-Skills.md`, `design/DESIGN_SYSTEM.md` |
| The plan and process (authoritative) | `context/GIGANTIC_JOURNEYS_PROMPT_KIT.md` |
| Rules for Bots: branches, PRs, AUTH REQUEST, CHECKPOINT | `agents/grok/README.md` |
| How PRs are judged | `governance/REVIEW_RUBRIC.md`, `governance/SECURITY_CHECKLIST.md` |
| What the Owner has authorized | `governance/AUTHORIZATION_LOG.md` |
| The agent operating model and usage rules | `governance/AGENT_GOVERNANCE.md`, `agents/claude/SELF_GOVERNANCE.md` |
| Everything the Owner must do through launch | `governance/OWNER_LAUNCH_CHECKLIST.md` |
| Work items | `tickets/` (schema, validator, one JSON per ticket) |
| Architecture decisions | `ADRs/` |
| Movement constants (single source of truth) | `config/movement.json` |

## Hard rules

1. The Builder self-reviews and merges its own code on green CI; the Coordinator does periodic independent secondary review (AUTH #007). No merge on red CI.
2. Every PR is reviewed against its ticket's acceptance tests, `SPEC.md`, the rubric, and the security checklist.
3. Spend, accounts, and changes to `SPEC.md`, ADRs, data schemas, the design system, or the milestone plan need the Owner's `APPROVED #n` (`AUTH REQUEST` first).
4. No secrets in the repo. CI fails any PR with keys, tokens, or a committed `.env*` file.

## CI

`secret-scan` (gitleaks, repo hygiene) · `lint` (ruff, npm, CSharpier, audits) · `governance` (ticket validation, movement.json sync, AUTH gate on protected paths) · `unity-tests` (skips until the Unity project and license secrets exist) · `android-build` (on demand only; keeps the Android target compiling for v1.1) · `ios-build` (Unity export on Linux, unsigned archive on GitHub's free macOS runner; skips until the Unity project and license exist).
