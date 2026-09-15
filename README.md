# Gigantic Journeys

A mobile game (iOS and Android, Unity 6) in which a near-photorealistic 1:12 avatar of the player journeys through the real environments they capture: indoor rooms and tabletop builds in v1. The environment is the content; the avatar is the piece; traversal is the product. No synthetic game objects in v1.

Owner: BlissDirective (SparkForge Labs). Coordinator: Claude Code. Legwork: the Grok Bot team.

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
| Work items | `tickets/` (schema, validator, one JSON per ticket) |
| Architecture decisions | `ADRs/` |
| Movement constants (single source of truth) | `config/movement.json` |

## Hard rules

1. Only the Coordinator merges to `main`.
2. Every PR is reviewed against its ticket's acceptance tests, `SPEC.md`, the rubric, and the security checklist.
3. Spend, accounts, and changes to `SPEC.md`, ADRs, data schemas, the design system, or the milestone plan need the Owner's `APPROVED #n` (`AUTH REQUEST` first).
4. No secrets in the repo. CI fails any PR with keys, tokens, or a committed `.env*` file.

## CI

`secret-scan` (gitleaks, repo hygiene) · `lint` (ruff, npm, CSharpier, audits) · `governance` (ticket validation, movement.json sync, AUTH gate on protected paths) · `unity-tests` and `android-build` (skip until the Unity project and license secrets exist) · `ios-build` (stub until a Mac runner exists).
