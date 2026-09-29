# M0-REPO-07: Dependabot CI-action bumps (triage and QA)

2026-09-29, gj-operator. The bumps were delivered as a direct commit to `main` (`87c38b1`, Operator precedent)
rather than by merging each Dependabot PR. GitHub closed the four superseded PRs automatically once `main`
contained the same versions.

## Triage
| PR | Bump | Decision | Why |
|---|---|---|---|
| #1 | actions/checkout 4 → 7 | **Applied** (`87c38b1`) | Node 24 runtime on GitHub-hosted runners; no removed inputs used (`lfs`, `fetch-depth` unchanged) |
| #2 | actions/setup-python 5 → 7 | **Applied** | No removed inputs used |
| #4 | actions/setup-dotnet 4 → 6 | **Applied** | Only `dotnet-version` is used |
| #5 | actions/cache 4 → 6 | **Applied** | `path`/`key`/`restore-keys` unchanged; the Unity Library cache restored in unity-tests and ios-build |
| #3 | game-ci/unity-builder 4 → 6 | **HELD** (PR left open, no comment posted) | v6 is a rewrite that downloads a CLI binary at run time inside the job holding the Unity licence and the Apple signing secrets. It can be verified only through a full ios-build, and that job can't be green end to end until the Owner supplies the Admin-role App Store Connect key. **Owner/Coordinator decision.** |

## CI on the bumped main (AT-2)
Two commits were checked:
- **`87c38b1`**, pushed in the batch `b1bd8dc..76b943b`.
- **`76b943b`**, the head of that batch.

| Workflow | Run | Result |
|---|---|---|
| lint (checkout v7, setup-python v7) | on 76b943b | green (309 tests) |
| governance, secret-scan | on 76b943b | green |
| supabase-local (checkout v7) | 36517116390 | green |
| unity-tests (checkout v7, cache v6, unity-test-runner v4) | 36517116518 | **green** (preflight, editmode + playmode, gate) |
| ios-build (checkout v7, cache v6, setup-dotnet v6, unity-builder v4) | 36517116408 | **Green through** the preflight, Linux Xcode export, macOS player build (Burst AOT) and unsigned xcodebuild. It **fails only at** "Export the .ipa (App Store distribution signing)" in *signed archive + TestFlight upload*: the known Owner item (Admin-role ASC key), unrelated to these bumps. |
| android-build | not run | This workflow runs on demand only (Android is deferred to v1.1). The same checkout and cache bumps are proven in unity-tests and ios-build. |

All workflow files YAML-parse (checked locally before the push).

## Still pinned at older majors (next Dependabot round, expected)
- `actions/upload-artifact@v4` (5 uses)
- `actions/download-artifact@v4` (2)
- `actions/setup-node@v4` (2)
- `gitleaks/gitleaks-action@v2` (1)

Dependabot opens these on its schedule; triage them the same way. upload/download-artifact must move together, because v4 and later artifacts aren't cross-compatible with other majors.

**Verdict:** AT-1 met (four applied on green CI, one held with a reason). AT-2 met (every workflow that runs on push parses and
passes up to the known TestFlight step). Status → **in-review**.
