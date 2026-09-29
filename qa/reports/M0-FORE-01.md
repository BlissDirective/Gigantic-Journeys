# M0-FORE-01 — VM repo bootstrap and secret-hygiene proof

2026-09-29, gj-operator (overnight worker, acting for gj-foreman). Output is redacted: no secret values,
private hostnames or account emails. The checks ran read-only against the main clone
(`~/projects/gigantic-journeys`) and in a worktree off `origin/main`.

## AT-1 clone and `.env.local` ignored

```
$ git remote get-url origin              # credentials stripped
https://github.com/BlissDirective/Gigantic-Journeys.git
$ git check-ignore -v .env.local
.gitignore:6:.env.*	.env.local
$ git ls-files | grep -c '^\.env'
1
$ git ls-files | grep '^\.env'
.env.example
```

PASS, with one note. `.env.local` exists but no longer holds **PLACEHOLDER** values. Since 2026-09-26 it
carries the staging credentials the Owner supplied (M1-PLAT-01, SECURITY_CHECKLIST §8.3: staging only).
The AT's placeholder wording predates that and is superseded. What matters is that the file stays ignored,
which is proven above; values were not printed.

## AT-2 pre-commit

`pre-commit run --all-files` (pre-commit 4.6.2 in a throwaway venv, `PRE_COMMIT_HOME` in `/tmp`):

```
Detect hardcoded secrets (gitleaks v8.30.1)......Passed
check for added large files......................Passed
detect private key...............................Passed
check json / check yaml / merge conflicts........Passed
fix end of files.................................Passed
trim trailing whitespace.........................Passed
ruff / ruff format...............................Passed
refuse to commit .env files......................Skipped (no files to check)
refuse to commit raw media or scan files.........Skipped (no files to check)
protected path touched — needs APPROVED AUTH.....Passed
```

**Defect found and fixed.** The first run was red. `end-of-file-fixer` and `trailing-whitespace` rewrote
153 files: Unity-serialized assets (`.meta`, `.asset`, `.unity`, `.mat`, ProjectSettings), Unity
test-result XML under `qa/reports/`, and the machine-written `services/reconstruction/corpus/open_video_corpus.json`.
Unity rewrites those bytes on every save, so the hook would churn them on every commit. The fix is to
exclude `unity/`, `qa/reports/*.xml` and `services/reconstruction/corpus/*.json` from the two whitespace
fixers (`.pre-commit-config.yaml`). CSharpier still governs C# under `unity/`. All the changes from that
first run were reverted, and the second run is green with no files touched.

**Not done: `pre-commit install`.** This box is one machine shared by several agents, and every worktree
shares the main clone's `.git/hooks`. Installing the hook would change commit behaviour for every other
agent mid-flight, so it is left for the Owner or Coordinator to decide.

## AT-3 tool versions

| Tool | Version | Requirement |
|---|---|---|
| Unity | 6000.0.84f1 (`~/Unity/Hub/Editor/6000.0.84f1`) | matches `ProjectVersion.txt` |
| Python | 3.13.5 | ≥ 3.11: PASS |
| Node | **20.19.2** | ≥ 22: **FAIL** (CI uses Node 22 via setup-node) |
| git | 2.47.3 | — |
| Supabase CLI | 2.118.0 via `npx supabase@2.118.0` (no global install; Docker is not available to this user) | recorded |
| pre-commit | 4.6.2 (venv) | — |
| CSharpier | 1.3.0 (matches CI) | — |
| Go | present (`/usr/bin/go`; builds the gitleaks hook) | — |

Node gap: upgrading the system Node needs root. A user-level Node 22 (nvm or a tarball) would change
`PATH` for every agent on the shared box. Owner or Coordinator decision.

## AT-4 no secrets
This report and the commit contain no secret value, private hostname or account email. secret-scan
(gitleaks) runs on the commit.

Verdict: **PASS WITH GAPS.** AT-1 PASS (placeholder wording superseded), AT-2 PASS after the exclude fix
(hook install held), AT-3 FAIL on Node 20 < 22, AT-4 PASS. Decisions needed: install the pre-commit hook in
the shared clone? Upgrade Node to 22 on the box?
