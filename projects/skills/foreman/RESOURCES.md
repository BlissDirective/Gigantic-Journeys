# gj-foreman — Resources (curated foundation)

Curated, verified starter set for orchestration / CI / mobile release ops. Expand to the full annotated top-100 in a live research pass (each session adds what it learns). All entries are real, canonical references.

## Autonomous multi-agent & agentic coding
- Anthropic — "Building effective agents" (anthropic.com/engineering) — agent design patterns; when orchestration helps vs hurts.
- Anthropic — Claude Code docs (code.claude.com/docs) — the harness this project runs on.
- "SWE-bench" (swebench.com) — benchmark for autonomous code changes; calibrates what agents can/can't do.
- ReAct (Yao et al., 2022, arXiv 2210.03629) — reason+act loop underlying tool-use agents.

## CI/CD & release engineering
- GitHub Actions docs (docs.github.com/actions) — workflows, concurrency, secrets, OIDC.
- game-ci (game.ci) — Unity in CI: license activation, `-batchmode` builds, test runners.
- Semantic Versioning (semver.org); Keep a Changelog (keepachangelog.com).
- "Trunk-Based Development" (trunkbaseddevelopment.com) — green-main discipline.

## Mobile game production & Unity release management
- Apple — App Store Connect / TestFlight docs (developer.apple.com/app-store-connect).
- Apple — App Review Guidelines (developer.apple.com/app-store/review/guidelines) — esp. §1.2 UGC, §5 privacy.
- Unity — Mobile optimization best practices (docs.unity3d.com; Unity Learn).
- Unity — IL2CPP + build pipeline docs (docs.unity3d.com).

## Repo-internal (read these first)
- `CLAUDE.md`, `governance/AGENT_GOVERNANCE.md`, `agents/claude/*.md`, `governance/REVIEW_RUBRIC.md`, `governance/SECURITY_CHECKLIST.md`, `.github/workflows/*`.
