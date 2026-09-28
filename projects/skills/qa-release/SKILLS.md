# gj-qa-release — Working Handbook

Remit: test harnesses (Unity EditMode/PlayMode, the scripted editor smoke task, milestone exit harnesses), the visual QA procedure and evidence standard, on-device measurement across the iPhone tier matrix, crash analytics and triage, and App Store release operations: TestFlight, submission, and store policy (kit §3 role block; `agents/grok/roles/gj-qa-release.md`). Re-read this file at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** writes test code, harness scripts and workflow changes. The **Operator** does computer-use and long-running ops: running the smoke task on the Linux box, dispatching and watching CI, collecting evidence, App Store Connect and TestFlight chores through the ops account (`AGENT_GOVERNANCE.md` §2). Owned path: `qa/` (README, `scripts/`, `reports/`, `evidence/`, `vm-setup/`).

**The policy that shapes everything here (SPEC §11, AUTH #003):** every test, QA pass, device measurement and coverage figure is a **suggestion, never a merge gate**. The merge gates are the automated CI checks (secret scan, repo hygiene, lint, governance, and the `unity tests gate` required check) plus the security rules in SECURITY_CHECKLIST. QA's job is evidence and confidence: raise real defects loudly, never block a merge on a measurement.

Research list: `projects/skills/qa-release/RESOURCES.md` (134 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template with evidence, sync cadence | `agents/grok/README.md` §3–§5; REVIEW_RUBRIC B1, B5 |
| Tests and device checks are suggestions; CI + security are the only gates | `agents/grok/README.md` §0; SPEC §11; REVIEW_RUBRIC A3 |
| Required criteria have concrete evidence rows; suggested ones are reviewed when offered | REVIEW_RUBRIC A1–A3 |
| Tests deterministic and hermetic: no network, no vendor calls, no real media | REVIEW_RUBRIC F1, F3; SECURITY_CHECKLIST §6.5 |
| Skipped tests carry a reason; deleting tests to get green is debt | REVIEW_RUBRIC F4 |
| Perf evidence states the expected effect on SPEC §6 targets | REVIEW_RUBRIC D1, D2; SPEC §6 |
| No full-screen blur in play; HUD one overlay pass | REVIEW_RUBRIC D5; Design Skills rules 21, 27 (§3.8, §3.12) |
| Visual PRs get the Design Skills §4 checklist and a `gj-qa-release` visual pass | Design Skills §4; REVIEW_RUBRIC G1–G8 |
| Secrets never in reports, logs, screenshots or evidence | SECURITY_CHECKLIST §1.3; REVIEW_RUBRIC C1, C10 |
| Bots never handle raw user photos/video; corpus is Owner-supplied | SECURITY_CHECKLIST §6.5 |
| Separate ops account for TestFlight/Play with no production secrets | SECURITY_CHECKLIST §8.4 (M5 gate) |
| Release flags: debug endpoints, verbose logging, test modes off; symbols stripped; debug overlay compiled out | SECURITY_CHECKLIST §9.7, §9.8 (M3 gate) |
| Full OWASP Mobile Top 10 walk before release | SECURITY_CHECKLIST §9.1–§9.10 (M5 gate) |
| Rate-spam and leaderboard plausibility tests are merge gates | SECURITY_CHECKLIST §10.2, §10.3; M4-QA-01 AT-3 |
| Incidents: contain, record in `governance/INCIDENTS.md`, notify the Owner | SECURITY_CHECKLIST §11 |
| Motion measurements: Bible spike pass/fail and the motion-db report | Movement Bible §2, §12 step 5 (`qa/motion-db-report.md`), §13 |
| Field measurements go under the locked docs' Field notes, never the body | REVIEW_RUBRIC H2 |
| No new vendor, paid tier or runner without `APPROVED #n` | REVIEW_RUBRIC B3; `agents/grok/README.md` §6 |

## 2. EditMode / PlayMode test patterns

- **What exists** (M0-UNITY-01, done):
  - `unity/Assets/GiganticJourneys/Tests/EditMode/`: `GiganticJourneys.EditMode.Tests.asmdef`, `ProjectSettingsSmokeTests.cs`, `IosBurstSettingsTests.cs`.
  - `unity/Assets/GiganticJourneys/Tests/PlayMode/`: `GiganticJourneys.PlayMode.Tests.asmdef`, `RuntimeSmokeTests.cs`.
  - Test Framework 1.4.6 is pinned in `Packages/manifest.json`.
  - The last recorded run: unity-tests 36250099866, EditMode 6/6 and PlayMode 1/1 (M3-UNITY-01 history).
- **EditMode for logic, PlayMode for frames.** Put pure logic (movement.json parsing, validators, token/contrast maths, schema checks) in EditMode: it's fast and needs no player loop. Use PlayMode `[UnityTest]` coroutines only when behaviour depends on frames, physics or the scene. Keep the pyramid wide at the bottom.
- **Determinism:** fix seeds, step physics explicitly where possible, and avoid wall-clock waits (`WaitForSeconds` in a test is a smell). Use `LogAssert` so an unexpected console error fails the test. Validators and route generation must be same-input-same-output (REVIEW_RUBRIC A6).
- **Fixtures:** small synthetic assets only (F3). No corpus splats in tests until a synthetic sample exists (M0-UNITY-02 brings the sample splat).
- **Layering:** test assemblies reference runtime assemblies downward only (REVIEW_RUBRIC E1; Bible §2).
- **Movement constants** come from `config/movement.json`. Test against the file, never a copied literal (REVIEW_RUBRIC E2; the `movement.json single source of truth` check).
- **Perf tests:** the Performance Testing package (`Measure.Frames`) gives repeatable numbers, but editor/runner numbers are **not** device numbers. Label them as such.
- **Flaky tests:** quarantine with `[Ignore("reason + ticket")]`, file a defect, and never delete (F4).

## 3. Headless editor scripting

- **Smoke task** (M0-QA-01, in-progress): `qa/scripts/editor_smoke.py` runs the pinned editor in `-batchmode` (under `xvfb-run` when there's no DISPLAY) with `-executeMethod GiganticJourneys.EditorTools.QA.EditorSmoke.Run` (`unity/Assets/Editor/QA/EditorSmoke.cs`).
  - It opens the project, imports the sample splat, opens the sample scene, renders the camera offscreen to `qa/evidence/M0-QA-01/01-editor-smoke.png` and writes `qa/reports/M0-editor-smoke.md`.
  - Latest report (2026-09-26 08:46 CDT): PASS on 2 runs with identical results. The **import sample splat** step is **pending M0-UNITY-02**. Close M0-QA-01 after that lands.
- **Pinned editor:** `unity/ProjectSettings/ProjectVersion.txt`, 6000.0.84f1 (78ab6fc243d5). The harness compares the installed editor to the pin and checks the iOS module (AT-1). Install with the Unity Hub CLI.
- **Logs:** the raw editor log is **never committed**, because it can carry licensing details. `editor_smoke.py` keeps only `[GJ-SMOKE]` and error lines, after redaction (emails, serials, token/licence lines, home path). Keep that redaction list current whenever you add log capture.
- **Known environment-only noise** on the headless box (not project issues): FMOD output-device failure, `[Licensing::Module]` token messages, Curl error 42 on quit, dbus/AT-SPI (`ENV_NOISE` in the script).
- **Exit codes:** editor scripts call `EditorApplication.Exit(code)`, and the harness treats non-zero, timeouts, compile errors and exceptions as FAIL.
- **Batchmode has no Game view:** capture through `Camera.Render` into a RenderTexture, as the smoke task does.
- **CI side:** `unity-tests.yml` (game-ci/unity-test-runner@v4, `testMode: all`, `-nographics`) runs only on push to main and `workflow_dispatch`.
  - Every run is a Unity sign-in, and Unity locks the account after 7 failed sign-ins in a row, so keep runs few.
  - All Unity workflows share the `unity-license` concurrency group.
  - Preflight skips green unless the project exists, `UNITY_CI_ENABLED` is `true`, and `UNITY_EMAIL` + `UNITY_PASSWORD` exist (M0-REPO-03, done).
  - **Never dispatch a Unity workflow while another is running, and don't push to main during one.**

## 4. Visual QA evidence standard

- **Procedure:** `qa/VISUAL_QA.md` **doesn't exist yet**. It's M0-QA-02 (open), which must define:
  - per-PR-type checklists (gameplay, UI, capture);
  - evidence naming `qa/evidence/<ticket>/<nn>-<what>.png`, ≤ 2 MB each;
  - clips ≤ 30 s, attached to the PR and never committed;
  - the reference-device Profiler screenshot;
  - the Design Skills §4 items QA re-checks;
  - the DEFECT issue flow with severities S1–S4.
  - The first live use is M0-UNITY-04 (the debug overlay, open).
  - Severity definitions are **TBD (M0-QA-02)**. Don't invent them in reports before that ticket lands.
- **Until then, follow the parts already written down** in `qa/README.md` (evidence PNGs ≤ 2 MB, clips attached not committed) and M0-QA-02 AT-1.
- **Every evidence set has a privacy line** (M0-QA-02 AT-3; M0-QA-01 AT-4): no faces, addresses, documents or screens with personal data. The smoke report automates this line (no captured imagery imported).
- **A good report has:** ticket id, build/commit hash, device + iOS version (or host + graphics device for editor runs), steps, expected vs actual, numbers with units, and links to evidence files and CI runs. `qa/reports/M0-editor-smoke.md` and `qa/reports/M0-UNITY-01/README.md` are the house style.
- **Design re-checks** (Design Skills §4; REVIEW_RUBRIC G2–G5, D5): contrast on the three test scans, glass/flat and Reduce Motion variants, targets ≥ 44 pt (play ≥ 56), safe zones, progress on waits, HUD in the top 8 %, deuteranopia check.
- **Compress** PNGs (Pillow) to stay under 2 MB, and strip metadata from any screenshot before committing.

## 5. Device matrix

- **Policy** (SPEC §6, §11.2): no minimum iPhone model. The newest iPhones get best-possible quality with a 60 fps target (up to 120 Hz ProMotion). Older iPhones get automatic quality tiering toward 30 fps. The Owner tests on real iPhones, and "reference Android device" wording in older docs means "measured on the Owner's iPhones" (§11.4).
- **Matrix shape:** newest (current Pro), one mid (a model a few years old), oldest-supported (the lowest model running the iOS version the Unity 6 build requires).
  - **Exact models: TBD.** They're whatever the Owner has on hand, recorded per report (SPEC §10 glossary: "the Owner's newest and oldest iPhones are the informal reference points").
  - **Minimum iOS: TBD.** It's fixed by the shipped Unity 6 build's requirement (Unity system requirements page; RESOURCES §E).
- **Quality tiers:** URP assets `Assets/Settings/URP-{Low,Medium,High}`, iOS default High (`qa/reports/M0-UNITY-01/README.md`). Verify the tier actually switches on device.
- **What to record** per device run: model identifier, iOS version, build hash, tier, avg and p99 frame time, thermal state over time, memory peak, splat count.
  - SPEC §6 targets: 30/60 fps; animation+IK+warping ≤ 4 ms; motion DB ≤ 60 MB; package ≤ 150 MB; crash-free ≥ 99 %.
  - Bible §13 spike: ≥ 30 fps p99, animation ≤ 4 ms, DB ≤ 60 MB, hands within 0.05 A on 20/20 edges.
  - These are targets and never gates.
- **#1 risk to watch:** Metal depth-sort glitches in the splat renderer (aras-p issue #226; M1-UNITY-01 AT-2). Look for popping and flicker when the camera moves, and use a GPU frame capture to confirm.
- **Burst:** the macOS player lane builds with iOS Burst AOT ENABLED; the Linux export lane turns it off for that build only (`IosBurstBuildHook.cs`; M3-UNITY-01). Perf and TestFlight builds come from the macOS lane. Burst off-vs-on device fps is suggested evidence still pending (M3-UNITY-01 AT-3).
- **Android** stays a compiling target (`android-build.yml`, on demand, debug-signed). No Android device QA in v1 (AUTH #003).

## 6. Store submission checklists

- **Build lane** (`.github/workflows/ios-build.yml`):
  - The Linux export + unsigned `xcodebuild` runs on push to main when `unity/**`, `config/movement.json` or the workflow change.
  - The macOS player lane (dispatch `lane=macos`) is the perf/TestFlight lane.
  - The TestFlight job (when the repo variable `TESTFLIGHT_ENABLED` is `true`) does a signed archive with cloud-managed signing via the App Store Connect API key, then uploads through fastlane pilot.
  - Internal testers with automatic distribution get every build. The build number is the workflow run number.
  - Secrets `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8_BASE64` and the variable `APPLE_TEAM_ID` are CI-only (M0-REPO-05, done: app record and internal TestFlight group created).
  - **gj-qa-release verifies the lane on its first real TestFlight run (M1) and records findings in `qa/`.** No such record exists yet.
- **TestFlight ops:** use the separate ops account with no production secrets (§8.4). Fill in what-to-test notes per build. External groups trigger Beta App Review. Watch the tester feedback and crash logs. Builds expire, so keep a current one in the cohort.
- **Pre-submission (M5)** — SPEC §9 and SECURITY_CHECKLIST §12 M5 row:
  - [ ] Every SPEC §9 definition-of-done item has evidence linked from `governance/checkpoints/M5.md`.
  - [ ] Privacy nutrition labels match the real data flows, including the crash SDK (§9.6; SPEC §9 item 6). The privacy manifest is present for the app and each SDK.
  - [ ] In-app account deletion works end to end (§6.4; Apple requirement).
  - [ ] 13+ age gate (§5.6); age-rating questionnaire consistent with UGC.
  - [ ] UGC per Apple 1.2: vision-pass auto-clear, one-tap report, human queue, block, published developer contact (§10.5, AUTH #026).
  - [ ] IAP: the two SKUs (SPEC §3.8), restore, Family Sharing, tested with StoreKit config and sandbox.
  - [ ] Release flags off, symbols stripped, debug overlay compiled out (§9.7, §9.8); full §9.1–§9.10 walk.
  - [ ] Export-compliance answer set.
  - [ ] Screenshots with the diorama hero (REQ). The preview video and top-5 localization are OPT (`governance/OWNER_LAUNCH_CHECKLIST.md`). No V2 features shown (AUTH #020).
  - [ ] Crash-free ≥ 99 % across the TestFlight cohort, judged by the Owner (SPEC §9 item 5).
  - [ ] Phased release planned so crash-free can be watched before 100 %.
- **Play Console** is v1.1 material only (AUTH #003). Resources are in RESOURCES §D for later.
- **Featuring + Duo launch video:** M5-DUO-01 (gj-qa-release).

## 7. Crash triage

- **Tool:** AUTH #017 approved a free-tier crash-reporting account (Sentry or Crashlytics). `research/vendors/crash-reporting.md` recommends Sentry (free Developer tier, `sendDefaultPii = false`, Release Health crash-free metric), supplemented by Xcode Organizer/MetricKit, with Crashlytics as fallback.
  - That file says it's **research, not a locked decision**: the choice is confirmed when the Builder wires it in. **No crash SDK is in the project yet** (no ticket found).
  - The free tier's event cap is the watch item. Upgrading is a spend AUTH.
- **Privacy:** crash payloads carry no PII, GPS, raw media refs or user content (C10; §10.1). Keep PII collection off and server-side scrubbing on. Pseudonymous IDs only (SPEC §7).
- **Symbolication:** release builds strip symbols (§9.7), so upload dSYMs/IL2CPP symbols from CI. Verify on the first TestFlight build that a forced test crash symbolicates to C# and native frames.
- **Loop:**
  1. New issue.
  2. Group or fingerprint check.
  3. Reproduce on the matrix device with the build hash.
  4. Classify severity per M0-QA-02's S1–S4 (TBD).
  5. File a DEFECT with the evidence.
  6. Link the fix PR.
  7. Verify on the next TestFlight build.
  8. Close.
- **Also check what SDKs miss:** jetsam memory kills and watchdog terminations don't always appear as crashes in SDKs. Check Organizer/MetricKit for older iPhones.
- **Security incidents** (a leaked key in a log, PII in a payload) are SECURITY_CHECKLIST §11 incidents, not ordinary defects.

## 8. Mistakes to avoid

- Treating a QA or perf fail as a merge blocker, or letting a real defect ship silently. Escalate it instead.
- Committing raw editor logs, clips or unredacted output. Evidence over 2 MB. Screenshots with faces, addresses or personal data.
- Putting a secret, project ref, Apple team detail or `.p8` anywhere in `qa/`. CI secrets stay in CI (§1.3, C9).
- Dispatching Unity workflows back-to-back or in parallel. Sign-in failures lock the Unity account after 7.
- Reporting editor or runner fps as device fps. Testing only on the newest iPhone.
- Tests that hit the network, a vendor or real media (F3). Deleting a flaky test instead of quarantining it.
- Using production credentials for TestFlight or App Store ops. Only the ops account (§8.4).
- Inventing severity levels, device models or thresholds that aren't decided. Mark them TBD with the ticket.

## 9. Checklists

**Pre-PR (QA / harness):**
- [ ] Ticket JSON updated (status, branch, pr, history). Required criteria have evidence rows; suggested ones say what was offered (A1–A3, B1).
- [ ] Tests deterministic and hermetic; skips carry reasons (F3, F4).
- [ ] Evidence named `qa/evidence/<ticket>/<nn>-<what>.png`, ≤ 2 MB, privacy line present; clips attached, not committed.
- [ ] Reports carry build hash, device/host and numbers with units; no secrets or PII (C1, C10).
- [ ] No Unity workflow running when pushing; no extra Unity dispatches.
- [ ] Repo checks green: `ruff check .`, `ruff format --check .`, `python tickets/validate.py`, `python .github/scripts/check_movement_sync.py`, workflow YAML parses.

**Per TestFlight build:** macOS lane green · build number = run number noted · symbols uploaded · what-to-test notes · forced-crash symbolication verified (first build) · device pass on the matrix · findings in `qa/reports/`.

**Release (M5):** section 6's pre-submission list · §12 M5 row green · Owner approval recorded.

## 10. Pointers

`qa/README.md`, `qa/scripts/editor_smoke.py`, `qa/reports/` (M0-editor-smoke.md, M0-UNITY-01/, M1-PLAT-01.md), `qa/vm-setup/repo-settings.md` · `unity/Assets/GiganticJourneys/Tests/`, `unity/Assets/Editor/QA/EditorSmoke.cs`, `unity/Assets/Editor/Build/IosBurstBuildHook.cs` · `.github/workflows/unity-tests.yml`, `ios-build.yml`, `android-build.yml` · `research/vendors/crash-reporting.md` · `governance/OWNER_LAUNCH_CHECKLIST.md` · SPEC §6, §9, §11 · SECURITY_CHECKLIST §1.3, §6.5, §8.4, §9, §10.2–§10.3, §11, §12 · Movement Bible §2, §12, §13 · Design Skills §4 · tickets M0-QA-01, M0-QA-02, M0-UNITY-01, M0-UNITY-02, M0-UNITY-04, M0-REPO-03, M0-REPO-05, M1-QA-01, M1-UNITY-01, M3-UNITY-01, M4-QA-01, M5-DUO-01.

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | The smoke task passes twice, with the splat import pending M0-UNITY-02. `qa/VISUAL_QA.md` and the S1–S4 definitions don't exist yet (M0-QA-02). unity-tests runs only on main/dispatch because of Unity sign-in lockout. The macOS lane is the perf/TestFlight lane (Burst on). No crash SDK is wired yet; AUTH #017 covers a free tier and the research recommends Sentry. The first real TestFlight run is still to be verified and recorded. | gj-operator expanded RESOURCES.md to 134 link-checked entries and rewrote SKILLS.md around the AT-2 topics (M0-SKILL-08). |
