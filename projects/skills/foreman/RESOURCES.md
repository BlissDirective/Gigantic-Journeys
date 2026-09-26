# gj-foreman — Resources

The annotated research list for the foreman hat (orchestration, CI/release ops, production hygiene). Research focus is from kit §2: autonomous multi-agent software teams, agentic coding harnesses, mobile game production pipelines, and Unity mobile release management. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26: HTTP 200 plus a page-title match, and arXiv titles were checked against the abstract page. Vendors listed here are references only. Adopting any of them is a separate AUTH (`agents/grok/README.md` §6). Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first, before any external source: `CLAUDE.md`, `SPEC.md`, `governance/AGENT_GOVERNANCE.md`, `governance/REVIEW_RUBRIC.md`, `governance/SECURITY_CHECKLIST.md`, `agents/grok/README.md`, `tickets/README.md`, `.github/workflows/*`.

## A. Autonomous multi-agent teams and agent design

1. **Building effective agents (Anthropic)** — <https://www.anthropic.com/engineering/building-effective-agents> · *doc* — Workflow-vs-agent patterns; the reason GJ routes most work to one Builder rather than a swarm (AGENT_GOVERNANCE §2).
2. **How we built our multi-agent research system (Anthropic)** — <https://www.anthropic.com/engineering/multi-agent-research-system> · *postmortem* — Orchestrator-worker costs and failure modes; backs the "bounded bursts only" rule (AGENT_GOVERNANCE §4).
3. **Effective context engineering for AI agents (Anthropic)** — <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents> · *doc* — Context as a budget; supports one-hat-at-a-time loading and the repo-as-memory rule.
4. **Writing effective tools for agents (Anthropic)** — <https://www.anthropic.com/engineering/writing-tools-for-agents> · *doc* — Tool design that reduces wasted calls; applies to our validate/sync scripts as agent-facing tools.
5. **Effective harnesses for long-running agents (Anthropic)** — <https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents> · *doc* — Progress files and incremental commits for multi-session agents; mirrors PROGRESS.md + ticket history.
6. **Claude Code best practices for agentic coding (Anthropic)** — <https://www.anthropic.com/engineering/claude-code-best-practices> · *doc* — Plan-then-act, CLAUDE.md memory, verification loops used by the Builder.
7. **Anthropic Cookbook — agent patterns** — <https://github.com/anthropics/anthropic-cookbook> · *repo* — Reference implementations of orchestrator-worker and evaluator-optimizer loops.
8. **OpenAI — A practical guide to building agents** — <https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf> · *vendor guide* — Single-agent-first guidance and guardrails; a second vendor view on when to split agents.
9. **OpenAI Agents SDK docs** — <https://openai.github.io/openai-agents-python/> · *doc* — Handoffs and guardrails as primitives; vocabulary for describing our Builder/Operator hand-offs.
10. **Cognition — Don't build multi-agents** — <https://cognition.ai/blog/dont-build-multi-agents> · *postmortem* — Shared-context failures of parallel agents; the core argument for single-threaded writes.
11. **LangGraph multi-agent concepts** — <https://docs.langchain.com/oss/python/langchain/multi-agent> · *doc* — Supervisor and network topologies; helps reason about Coordinator/Builder/Operator as a supervisor graph.
12. **Microsoft AutoGen** — <https://github.com/microsoft/autogen> · *repo* — Conversational multi-agent framework; useful contrast to our ticket-file protocol.
13. **CrewAI docs** — <https://docs.crewai.com/> · *doc* — Role/task/crew abstraction close to the retired 8-Bot model; shows why role seats became skill hats.
14. **MetaGPT: Meta Programming for a Multi-Agent Collaborative Framework** — <https://arxiv.org/abs/2308.00352> · *paper* — SOP-driven software team of agents; our ticket JSON + acceptance tests are the SOP equivalent.
15. **ChatDev: Communicative Agents for Software Development** — <https://arxiv.org/abs/2307.07924> · *paper* — Waterfall-style agent company; evidence that structured phases reduce agent drift.
16. **AgentVerse: Facilitating Multi-Agent Collaboration** — <https://arxiv.org/abs/2308.10848> · *paper* — Dynamic team composition; informs when (rarely) a burst of agents pays off.
17. **Why Do Multi-Agent LLM Systems Fail?** — <https://arxiv.org/abs/2503.13657> · *paper* — Taxonomy of multi-agent failures (spec, misalignment, verification); a checklist for Foreman reviews.
18. **The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling** — <https://arxiv.org/abs/2404.11584> · *paper* — Survey of single vs multi-agent architectures; background for AGENT_GOVERNANCE §0.
19. **Generative Agents: Interactive Simulacra of Human Behavior** — <https://arxiv.org/abs/2304.03442> · *paper* — Memory/reflection loop; the SKILLS.md session log is a lightweight reflection store.
20. **Reflexion: Language Agents with Verbal Reinforcement Learning** — <https://arxiv.org/abs/2303.11366> · *paper* — Self-critique between attempts; basis for "append learnings to SKILLS.md" each session.
21. **ReAct: Synergizing Reasoning and Acting in Language Models** — <https://arxiv.org/abs/2210.03629> · *paper* — The reason-act loop behind every tool-using agent on the team.
22. **Toolformer: Language Models Can Teach Themselves to Use Tools** — <https://arxiv.org/abs/2302.04761> · *paper* — Why tool-call discipline matters: tools are cheap only when chosen deliberately.
23. **Voyager: An Open-Ended Embodied Agent with Large Language Models** — <https://arxiv.org/abs/2305.16291> · *paper* — Skill library that grows over time; the pattern behind projects/skills/<role>/.
24. **Model Context Protocol specification** — <https://modelcontextprotocol.io/> · *doc* — Standard for agent tool servers; how the Operator reaches GitHub and other services.

## B. Agentic coding harnesses and evaluation

25. **Claude Code documentation** — <https://docs.anthropic.com/en/docs/claude-code/overview> · *doc* — The Builder's harness: memory files, hooks, permissions, headless mode.
26. **Claude Code GitHub Actions** — <https://docs.anthropic.com/en/docs/claude-code/github-actions> · *doc* — Running the Builder from CI; relevant if the loop-proving ticket (M0-UNITY-04) is automated.
27. **SWE-bench** — <https://www.swebench.com/> · *doc* — Benchmark for autonomous repo changes; calibrates what an unattended agent can finish.
28. **SWE-bench: Can Language Models Resolve Real-World GitHub Issues?** — <https://arxiv.org/abs/2310.06770> · *paper* — The paper behind the benchmark; shows why tests-as-contract make tickets agent-solvable.
29. **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering** — <https://arxiv.org/abs/2405.15793> · *paper* — Agent-computer interface design; guides how ticket files and scripts should read to an agent.
30. **SWE-agent repository** — <https://github.com/SWE-agent/SWE-agent> · *repo* — Working reference harness; useful when designing Operator scripts.
31. **OpenHands (formerly OpenDevin)** — <https://github.com/All-Hands-AI/OpenHands> · *repo* — Open agent platform with sandboxed execution; comparison point for the Operator's box.
32. **OpenHands: An Open Platform for AI Software Developers as Generalist Agents** — <https://arxiv.org/abs/2407.16741> · *paper* — Architecture and evaluation of a generalist coding agent.
33. **Agentless: Demystifying LLM-based Software Engineering Agents** — <https://arxiv.org/abs/2407.01489> · *paper* — Simple localize-repair-validate pipelines rival complex agents; favors scriptable-first routing.
34. **Aider** — <https://aider.chat/> · *doc* — Git-native pair-programming agent; commit-per-change discipline similar to ours.
35. **OpenAI Codex CLI** — <https://github.com/openai/codex> · *repo* — Another terminal coding harness; compare sandbox and approval models.
36. **Terminal-Bench** — <https://www.tbench.ai/> · *doc* — Benchmark for agents working in terminals; relevant to Operator shell workflows.
37. **tau-bench: A Benchmark for Tool-Agent-User Interaction** — <https://arxiv.org/abs/2406.12045> · *paper* — Measures reliability across repeated runs; a reminder that one green run is not proof.
38. **AgentBench: Evaluating LLMs as Agents** — <https://arxiv.org/abs/2308.03688> · *paper* — Multi-environment agent evaluation; frames what to measure in weekly AUDITs.
39. **OWASP Top 10 for LLM Applications** — <https://owasp.org/www-project-top-10-for-large-language-model-applications/> · *doc* — Prompt injection and excessive agency risks; backs SECURITY_CHECKLIST §8 least privilege.
40. **Simon Willison — prompt injection series** — <https://simonwillison.net/series/prompt-injection/> · *doc* — Why agents holding staging credentials must treat fetched content as data.

## C. Repo governance, CI/CD and trunk discipline

41. **GitHub Actions documentation** — <https://docs.github.com/en/actions> · *doc* — Workflows, triggers, concurrency; all six GJ workflows live in .github/workflows/.
42. **GitHub Actions — control concurrency** — <https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs> · *doc* — The unity-license concurrency group that keeps one Unity sign-in at a time.
43. **GitHub Actions — security hardening** — <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions> · *doc* — Pinning actions, least-privilege GITHUB_TOKEN; SECURITY_CHECKLIST §7.1 and §8.
44. **About protected branches** — <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches> · *doc* — Required status checks and admin exemption; the M0-REPO-02 configuration.
45. **About rulesets** — <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets> · *doc* — Newer alternative to branch protection if main's policy is revisited.
46. **GitHub secret scanning and push protection** — <https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning> · *doc* — Native scanning enabled under SECURITY_CHECKLIST §1.6.
47. **Managing fine-grained personal access tokens** — <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens> · *doc* — Scope and expiry rules for the machine-user PAT (AUTH #002, SECURITY_CHECKLIST §8.1).
48. **GitHub CLI manual** — <https://cli.github.com/manual/> · *doc* — gh run list/watch used to confirm green CI before and after each push.
49. **Dependabot version updates** — <https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates> · *doc* — The weekly bump PRs triaged in M0-REPO-07.
50. **Gitleaks** — <https://github.com/gitleaks/gitleaks> · *repo* — The secret scanner in secret-scan.yml.
51. **pre-commit** — <https://pre-commit.com/> · *doc* — Local hooks named in agents/grok/README.md §4 before every push.
52. **Ruff** — <https://docs.astral.sh/ruff/> · *doc* — The Python lint/format gate in the pre-push validation.
53. **Trunk-Based Development** — <https://trunkbaseddevelopment.com/> · *doc* — Short-lived branches and a green trunk; the discipline behind "green main, always".
54. **Continuous Integration (Martin Fowler)** — <https://martinfowler.com/articles/continuousIntegration.html> · *doc* — Classic definition of CI; why the validate scripts run before every push.
55. **Conventional Commits** — <https://www.conventionalcommits.org/en/v1.0.0/> · *doc* — Structured commit messages; GJ uses the simpler `<ticket-id>: <what changed>` form.
56. **Semantic Versioning 2.0.0** — <https://semver.org/> · *doc* — Versioning for packages, schemas and the app build.
57. **Keep a Changelog** — <https://keepachangelog.com/en/1.1.0/> · *doc* — Changelog format; matches the change-log tables in SPEC and governance docs.
58. **Google SRE Book — Postmortem Culture** — <https://sre.google/sre-book/postmortem-culture/> · *doc* — Blameless incident write-ups for governance/INCIDENTS.md (SECURITY_CHECKLIST §11).
59. **Google SRE Book — Eliminating Toil** — <https://sre.google/sre-book/eliminating-toil/> · *doc* — Why recurring manual ops should become scripts handed to the Builder.
60. **DORA — capabilities and metrics** — <https://dora.dev/> · *doc* — Deployment frequency, lead time, change-fail rate; candidate metrics for checkpoint reports.
61. **Accelerate State of DevOps report** — <https://cloud.google.com/devops/state-of-devops> · *doc* — Evidence base for small batches and trunk-based work.
62. **Architecture Decision Records (adr.github.io)** — <https://adr.github.io/> · *doc* — ADR practice behind ADRs/ and the ADR template.
63. **Documenting Architecture Decisions (Michael Nygard)** — <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions> · *doc* — The original ADR format our template follows.

## D. Planning, decomposition, standups and checkpoints

64. **Scrum Guide** — <https://scrumguides.org/scrum-guide.html> · *doc* — Daily-scrum and increment definitions; the 5-line standup is a compressed daily scrum.
65. **Atlassian — standups** — <https://www.atlassian.com/agile/scrum/standups> · *doc* — Standup anti-patterns (status theatre); keep the GJ standup to done/in progress/blocked/AUTH/next.
66. **Atlassian — user stories and acceptance criteria** — <https://www.atlassian.com/agile/project-management/user-stories> · *doc* — Writing testable acceptance criteria like the ticket `acceptance_tests` array.
67. **INVEST in Good Stories (Bill Wake)** — <https://xp123.com/invest-in-good-stories-and-smart-tasks/> · *doc* — Independent, small, testable tickets; a decomposition check for new tickets.
68. **Shape Up (Basecamp)** — <https://basecamp.com/shapeup> · *doc* — Appetite-bounded work and hill charts; useful for scoping spikes like M1-CAPT-03.
69. **Kanban Guide** — <https://kanbanguides.org/> · *doc* — WIP limits and flow; matches the default one-working-agent policy.
70. **Theory of Constraints — The Goal summary (Lean Enterprise Institute)** — <https://www.lean.org/lexicon-terms/theory-of-constraints/> · *doc* — Find the one constraint (often an Owner action) and route work around it.
71. **Microsoft Engineering Fundamentals Playbook** — <https://microsoft.github.io/code-with-engineering-playbook/> · *doc* — Checklists for definition of done, code review and standups.
72. **Google Engineering Practices — code review** — <https://google.github.io/eng-practices/review/> · *doc* — Reviewer and author guides; complements REVIEW_RUBRIC.md.
73. **The Pragmatic Engineer — project management in tech** — <https://blog.pragmaticengineer.com/project-management-at-big-tech/> · *doc* — How large tech runs projects with lightweight process; calibration for GJ's overhead.
74. **Performing a Project Premortem (Gary Klein, HBR)** — <https://hbr.org/2007/09/performing-a-project-premortem> · *doc* — Pre-mortem technique for the "Blockers and risks" section of each checkpoint.

## E. Mobile game production pipelines and postmortems

75. **Game Developer — Production section** — <https://www.gamedeveloper.com/production> · *postmortem* — Production articles and postmortems; mine for scope and schedule lessons.
76. **GDC Vault** — <https://gdcvault.com/> · *talk* — Production and design talks cited by the Movement Bible and Design Skills.
77. **When quality comes before making money: Developing Monument Valley (Game Developer)** — <https://www.gamedeveloper.com/design/when-quality-comes-before-making-money-developing-i-monument-valley-i-> · *postmortem* — Eight-person Unity team shipping a polished premium iOS title; scope discipline for a small team.
78. **Supercell — About us** — <https://supercell.com/en/about-us/> · *doc* — Small autonomous cells and killing projects early; supports the M1 stop-and-replan rule (SPEC §8).
79. **Unity Game Production resources (Unity Learn)** — <https://learn.unity.com/> · *doc* — Official learning paths; the team's baseline for Unity workflows.
80. **Unity — Project organization best practices** — <https://unity.com/how-to/organizing-your-project> · *vendor guide* — Folder and naming conventions for unity/Assets.
81. **Unity — version control and Unity Version Control guidance** — <https://unity.com/how-to/version-control-systems> · *vendor guide* — Git + LFS considerations for a Unity repo.
82. **Git LFS** — <https://git-lfs.com/> · *doc* — Large binary handling if art assets enter the repo (none raw by policy).
83. **Unity Build Automation docs** — <https://docs.unity.com/ugs/manual/devops/manual/build-automation> · *doc* — Managed alternative to game-ci; context for why GJ chose Actions.
84. **Monument Valley — cost and reward of a hit iOS game (TechCrunch)** — <https://techcrunch.com/2015/01/15/monument-valley-team-reveals-the-cost-and-reward-of-making-a-hit-ios-game/> · *postmortem* — Real team-size, schedule and completion-rate numbers from a shipped iOS game; calibrates milestone expectations.
85. **Coherence of design docs — "The Anatomy of a Design Document" (Game Developer)** — <https://www.gamedeveloper.com/design/the-anatomy-of-a-design-document-part-1-documentation-guidelines-for-the-game-concept-and-proposal> · *doc* — Why SPEC.md stays the single authority above the Bible and design docs.

## F. Unity mobile build and release management

86. **game-ci documentation** — <https://game.ci/docs/> · *doc* — Unity activation, builder and test-runner actions used by unity-tests.yml and ios-build.yml.
87. **game-ci — GitHub activation** — <https://game.ci/docs/github/activation> · *doc* — Personal-license activation with email/password; the M0-REPO-03 lesson on 401 lockouts.
88. **game-ci unity-builder action** — <https://github.com/game-ci/unity-builder> · *repo* — The builder action; read its changelog before bumping versions.
89. **game-ci unity-test-runner action** — <https://github.com/game-ci/unity-test-runner> · *repo* — EditMode/PlayMode runner used in unity-tests.yml.
90. **Unity Manual — command line arguments** — <https://docs.unity3d.com/Manual/EditorCommandLineArguments.html> · *doc* — -batchmode/-executeMethod flags behind headless builds (routing rule step 1).
91. **Unity Manual — Building for iOS** — <https://docs.unity3d.com/Manual/iphone-BuildProcess.html> · *doc* — The Xcode export stage of ios-build.yml.
92. **Unity Manual — IL2CPP** — <https://docs.unity3d.com/Manual/IL2CPP.html> · *doc* — Required for iOS; affects build time and SECURITY_CHECKLIST §9.7.
93. **Unity Burst User Guide** — <https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/index.html> · *doc* — Burst AOT settings resolved in M3-UNITY-01.
94. **Unity Test Framework manual** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/index.html> · *doc* — EditMode/PlayMode test structure checked by unity-tests.
95. **Unity — Mobile optimization guide (e-book)** — <https://unity.com/resources/mobile-xr-web-game-performance-optimization-unity-6> · *vendor guide* — Performance playbook for SPEC §6 targets.
96. **Unity Manual — Profiler** — <https://docs.unity3d.com/Manual/Profiler.html> · *doc* — Evidence source for performance readouts (advisory under AUTH #003).
97. **fastlane docs** — <https://docs.fastlane.tools/> · *doc* — Automation behind the TestFlight lane (M0-REPO-06).
98. **fastlane pilot (upload_to_testflight)** — <https://docs.fastlane.tools/actions/upload_to_testflight/> · *doc* — The exact action the ios-build TestFlight stage calls.
99. **App Store Connect API** — <https://developer.apple.com/documentation/appstoreconnectapi> · *doc* — The CI-only API key used for uploads (M0-REPO-05).
100. **TestFlight overview (Apple)** — <https://developer.apple.com/testflight/> · *doc* — Internal vs external testing and build expiry for the M5 cohort.
101. **App Store Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> · *doc* — Esp. 1.2 UGC and 5.1 privacy; launch gates referenced by SPEC §3.7 and §3.9.
102. **Xcode — distributing your app (Apple)** — <https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases> · *doc* — Archive/export steps the macOS lane automates.
103. **Apple — cloud-managed certificates** — <https://developer.apple.com/help/account/certificates/cloud-managed-certificates/> · *doc* — Cloud signing used by the TestFlight lane instead of stored certs.
104. **GitHub-hosted runners (macOS images)** — <https://github.com/actions/runner-images> · *repo* — Xcode versions on macos-14/15 runners; check before bumping the iOS lane.
105. **Firebase Crashlytics for Unity** — <https://firebase.google.com/docs/crashlytics/get-started?platform=unity> · *vendor guide* — One crash-reporting option weighed in research/vendors/crash-reporting.md.
106. **Sentry for Unity** — <https://docs.sentry.io/platforms/unity/> · *vendor guide* — The other crash-reporting candidate in research/vendors/crash-reporting.md.
