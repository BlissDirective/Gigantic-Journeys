# M0-UNITY-01 addendum: Editor upgrade 6000.0.28f1 → 6000.0.84f1 (security)

- **Date:** 2026-09-26 (CDT), gj-operator (Grok Bot), Operator Linux box. Owner-approved upgrade.
- **Why:** Unity's release API labels `6000.0.28f1` **"Security Alert"**: [sept-2025-01](https://unity.com/security/sept-2025-01), CVE-2025-59489 (CWE-426 untrusted search path, CVSS 8.4). Every 6000.0 release before **`6000.0.58f2`** is affected.
- **Chosen:** **`6000.0.84f1`**, changeset **`78ab6fc243d5`**, stream LTS, released 2026-09-16. It is the newest 6000.0 release in `services.api.unity.com/unity/editor/release/v1/releases?version=6000.0` and carries **no label**. (6000.0.47f1–58f1 carry the sept-2025-01 "Security Alert"; 6000.0.58f2–66f1 carry a later "Warning" label; 66f2 onward carry none.) 84f1 is above the 58f2 fix, so it is patched.
- **Install:** `unityhub --headless install --version 6000.0.84f1 --changeset 78ab6fc243d5 --module ios` → Editor + iOS Build Support at `~/Unity/Hub/Editor/6000.0.84f1`. Android Build Support is not installed locally: `android-build.yml` runs only on demand and builds in game-ci's `unityci/editor:ubuntu-6000.0.84f1-android-3` image, not on this box. The matching `-ios-3` / `-android-3` / `-base-3` images exist on Docker Hub.
- **License:** the existing machine-bound Personal `.ulf` (no sign-in, no password used).
- **CI pin:** the game-ci workflows have no `unityVersion` input, so they read `ProjectVersion.txt` (auto) and need no workflow edit.

## What the upgrade changed (committed)
| File | Change |
|---|---|
| `ProjectSettings/ProjectVersion.txt` | `6000.0.84f1 (78ab6fc243d5)` |
| `Packages/manifest.json` + `packages-lock.json` | The Package Manager raised packages below the Editor's minimums: Input System 1.11.2 → **1.20.0**, Animation Rigging 1.3.0 → **1.4.1**, Test Framework 1.4.6 → **1.6.0**, Visual Studio 2.0.22 → **2.0.27**; URP stays **17.0.4** (core/shadergraph deps 17.0.3 → 17.0.4), Burst 1.8.18 → 1.8.30, Collections 2.5.1 → 2.6.8, and others |
| `Assets/UniversalRenderPipelineGlobalSettings.asset`, `Assets/Settings/URP-{Low,Medium,High}.asset`, `ProjectSettings/ProjectSettings.asset`, `ProjectSettings/ShaderGraphSettings.asset` | Re-serialized by the new URP/Editor: new default fields only (new URP resource blocks, reflection-probe prefilter flags, new Player fields). No behaviour change intended |

## Results
| Check | Result |
|---|---|
| Normal open (existing Library), `-batchmode -nographics` | exit 0; Console **0 errors, 0 warnings** (`LogEntries` counts) |
| Clean CI-like open (fresh copy of `unity/` with no Library/Temp/Logs/UserSettings) | exit 0, 44 s; Console **0 errors, 0 warnings**; no "fallback shader" import noise; no files changed by the open |
| `ProjectSetup.Run` re-applied twice | second run makes no changes (idempotent on 6000.0.84f1) |
| EditMode tests | **Passed 4/4**: `upgrade-6000.0.84f1/editmode-results.xml` |
| PlayMode tests | **Passed 1/1**: `upgrade-6000.0.84f1/playmode-results.xml` |
| Environment-only log lines | ALSA/FMOD (no audio device), `[Licensing::Module] Access token is unavailable` (no Hub token handed to the Editor; the .ulf validates), same as on 28f1 |

## CI on the upgrade
| Workflow | Run | Commit | Result |
|---|---|---|---|
| ios-build | [36241881048](https://github.com/BlissDirective/Gigantic-Journeys/actions/runs/36241881048) | `b567e36` (push) | **success**: Unity iOS export + unsigned xcodebuild |
| unity-tests | [36245697459](https://github.com/BlissDirective/Gigantic-Journeys/actions/runs/36245697459) | `95a3b99` (workflow_dispatch on main; contains `b567e36`) | **success**: EditMode 4/4, PlayMode 1/1 |
| unity-tests | [36241881067](https://github.com/BlissDirective/Gigantic-Journeys/actions/runs/36241881067) (attempt 2) | `b567e36` (push, re-run) | **success**: EditMode 4/4, PlayMode 1/1 |

Attempt 1 of 36241881067 was cancelled when later pushes took the `unity-license` concurrency slot; both green runs had no Unity login 401s. Also recorded in the M0-UNITY-01 ticket history.
