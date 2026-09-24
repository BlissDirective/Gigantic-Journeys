# gj-foreman — Working Handbook

Remit: orchestration, CI/release ops, and production hygiene for Gigantic Journeys. Re-read at every session start; update when you learn something. Authored by the Builder 2026-09-24 as the working foundation (RESOURCES.md is the curated reference set).

> Agent-model note (AUTH #006/#027): the 8-Bot team consolidated to **one Claude Builder + one Grok Operator** wearing skill hats; Cursor retired. "Foreman" work is now shared between the Builder (code, CI) and the Operator (long-running ops). This handbook is the reference for that hat.

## Principles
- **Green main, always.** No merge on red CI (SECURITY_CHECKLIST §8.2). The lint gate (`ruff`, exact pins, `pytest`; per-package TS; CSharpier) is the merge gate, not tests-as-suggestions (SPEC §11 / AUTH #003).
- **Single-threaded writes with bounded bursts** (AGENT_GOVERNANCE). Rebase/merge `origin/main` before pushing; never force-push a shared branch.
- **Everything the Owner approved is in `governance/AUTHORIZATION_LOG.md`.** Protected paths need `APPROVED #n`. Spend/accounts/schema/design-lock changes are Owner-only.
- **Secrets never touch git** (SECURITY_CHECKLIST §1). CI secrets are write-only; the VM `.env.local` is staging-only.

## Workflow
1. Read first (CLAUDE.md list): SPEC, PROGRESS, AUTHORIZATION_LOG, REVIEW_RUBRIC, SECURITY_CHECKLIST, open PRs/auth-requests.
2. Validate before any push: `ruff check . && ruff format --check . && python tickets/validate.py && python .github/scripts/check_movement_sync.py` + YAML parse of workflows.
3. Update `PROGRESS.md` on every merge/AUTH/checkpoint; `python tickets/validate.py --summary` regenerates the ticket counts.
4. On divergent `main`: `git fetch origin main` → `git merge origin/main` into the work branch → re-validate → fast-forward `main` → push. No force-push.

## CI / release (iOS-only v1, AUTH #003)
- Language jobs run only when files of that kind exist (lint.yml `detect`), so the gate is green on a bare scaffold and strict once code lands.
- Unity/iOS/Android build workflows **skip without `UNITY_LICENSE`**; don't let a Unity job lock out the Unity account (respect the concurrency/guard added on main).
- App Store Connect API key, Apple certs/profiles, Unity license live **only** in CI secrets the Owner adds; CI deletes its working copy each run (SECURITY_CHECKLIST §1.4).

## Pitfalls
- Adding a `*requirements*.txt` with heavy/GPU deps → CI pip-installs it on a CPU runner and `pip-audit --strict` fails. Keep heavy deps in a Dockerfile; keep requirements stdlib-only unless CI-installable.
- Editing a protected path without `APPROVED #n` → `auth-gate` fails / Coordinator rejects.
- Forgetting the attribution footer on GitHub comments; forgetting to update PROGRESS on merge.

## Checklists
- **Pre-merge:** CI green · reviewed vs ticket ATs + rubric + security checklist · protected paths cite AUTH · PROGRESS updated · no secrets.
- **Release:** version bump · signing secrets present in CI · privacy labels accurate · crash reporting wired (M0-SKILL-08 / gj-qa-release).

## Pointers
`CLAUDE.md` · `governance/AGENT_GOVERNANCE.md` · `agents/claude/{BUILDER,COORDINATOR,SELF_GOVERNANCE}.md` · `.github/workflows/` · `tickets/validate.py`.
