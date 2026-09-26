# M0-UNITY-01 — first Editor open (headless) — local evidence

- **Date:** 2026-09-25 (CDT), gj-operator (Grok Bot), Operator Linux box (Debian 13, x86_64).
- **Editor:** Unity `6000.0.28f1` (changeset `f336aca0cab5`) + iOS Build Support, installed with the Unity Hub CLI.
- **License:** existing machine-bound Unity Personal `.ulf` via the local Licensing Client ("Serial number assigned to: …UnityPersXXXX", "Pro License: NO"). No sign-in performed.
- **Mode:** every run `-batchmode -nographics`.

## What the first open did
1. Package Manager resolved `Packages/manifest.json` as pinned (URP 17.0.4, Input System 1.11.2, Animation Rigging 1.3.0, Test Framework 1.4.6, uGUI 2.0.0, modules) and wrote `Packages/packages-lock.json` (46 packages).
2. `-executeMethod GiganticJourneys.EditorTools.ProjectSetup.Run` (`unity/Assets/Editor/ProjectSetup.cs`, idempotent) applied: product/company name, bundle id `com.sparkforgelabs.giganticjourneys` (iOS + Android), iOS IL2CPP + Metal, Android IL2CPP/ARM64, Input System handler, URP pipeline + renderer assets per quality tier (`Assets/Settings/URP-{Low,Medium,High}`; tiers Low/Medium/High, iOS default High), URP as the default pipeline, `Assets/Scenes/SampleScene.unity` and `ProjectSettings/EditorBuildSettings.asset` listing it (enabled, GUID `a9f5306c8ce47e866ba3c5a57745e253`).

## Results
| Check | Result |
|---|---|
| Console errors, warm open (Library present) | **0 errors, 0 warnings** (logMessageReceived hook + Console `LogEntries` counts) |
| Console errors, cold open (Library deleted, as on CI) | **0 errors, 0 warnings** after domain load. The log has 18 first-import lines "Shader '…': fallback shader '…FallbackError' not found" (import ordering; they do not recur) |
| Environment-only log lines (not project issues) | `FMOD failed to initialize the output device` (no audio device on the headless box), `[Licensing::Module] Error: Access token is unavailable` (no Hub token handed to the Editor; the .ulf license still validates), `Curl error 42: Callback aborted` (request aborted on quit) |
| EditMode tests (`-runTests -testPlatform EditMode`) | **Passed 4/4** — `editmode-results.xml` |
| PlayMode tests (`-runTests -testPlatform PlayMode`) | **Passed 1/1** — `playmode-results.xml` |
| Local iOS Xcode export (`BuildPipeline.BuildPlayer`, target iOS, the CI export step's equivalent) | **Succeeded**, 0 errors, 1 warning (Burst cannot cross-compile for iOS on a Linux Editor, so Burst is off for Linux exports); `PRODUCT_BUNDLE_IDENTIFIER = com.sparkforgelabs.giganticjourneys` |
| `git status` after reopening (Linux and iOS active targets, and after test runs) | clean — no tracked-file churn; Library/Temp/Logs/UserSettings ignored |
| `csharpier check unity/Assets` (1.3.0) | clean |

Not done here (suggested evidence): an Editor GUI screenshot (the open was headless by design) and the QA-VM screenshot for AT-5.
