# gj-qa-release — Resources

The annotated research list for the QA and release hat. Research focus is from the kit §3 role block: Unity test frameworks, mobile QA matrices, TestFlight and Play Console operations, App Store review guidelines, Play policy, and crash analytics. CI/build-signing and visual-evidence/defect process get their own groups because the repo's workflows (`unity-tests.yml`, `ios-build.yml`) and M0-QA-02 depend on them. Each entry gives a title, URL, type (doc / paper / talk / repo / postmortem / vendor guide) and why it matters for GJ.

Every URL was link-checked by gj-operator on 2026-09-26 (HTTP 200 plus a page-title check). Vendor links are references, not approvals. The crash-reporting account is covered by AUTH #017 (free tier only); any paid tier, new vendor or runner needs an AUTH (`agents/grok/README.md` §6; REVIEW_RUBRIC B3). v1 is iOS-only (AUTH #003), so the Google Play entries are for v1.1. Add new finds under the right group and note them in the SKILLS.md Session log.

Repo-internal reading comes first: `qa/README.md` and `qa/reports/`; `.github/workflows/unity-tests.yml`, `ios-build.yml`, `android-build.yml`; `research/vendors/crash-reporting.md`; SPEC §6, §9, §11; SECURITY_CHECKLIST §8.4, §9, §12; tickets M0-QA-01/02, M1-QA-01, M4-QA-01.

## A. Unity Test Framework, EditMode/PlayMode and headless editor scripting

1. **Unity Test Framework manual** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/index.html> · *doc* — The framework behind GiganticJourneys.EditMode.Tests and PlayMode.Tests (M0-UNITY-01 AT-4).
2. **UTF — Edit Mode vs Play Mode tests** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/edit-mode-vs-play-mode-tests.html> · *doc* — Which tests belong in which assembly; keeps the unity-tests job fast.
3. **UTF — Workflow: create a test assembly** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/workflow-create-test-assembly.html> · *doc* — asmdef setup the repo's two test assemblies follow.
4. **UTF — Running tests from the command line** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-command-line.html> · *doc* — -runTests, -testPlatform, -testResults flags used locally and by game-ci.
5. **UTF — UnityTest attribute** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-attribute-unitytest.html> · *doc* — Coroutine tests for frame-stepped gameplay behaviour in PlayMode.
6. **UTF — Setup and cleanup at build time** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-setup-and-cleanup.html> · *doc* — IPrebuildSetup/IPostBuildCleanup for scene fixtures in PlayMode player tests.
7. **UTF — Running tests programmatically (TestRunnerApi)** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-test-runner-api.html> · *doc* — Drive tests from editor scripts such as the QA smoke harness.
8. **UTF — Custom assertions** — <https://docs.unity3d.com/Packages/com.unity.test-framework@1.4/manual/reference-custom-assertion.html> · *doc* — Custom assertions and expected-log checks so console errors fail tests.
9. **NUnit documentation** — <https://docs.nunit.org/> · *doc* — The assertion and attribute model UTF is built on (TestCase, Values, constraints).
10. **NUnit — Constraint model** — <https://docs.nunit.org/articles/nunit/writing-tests/constraints/Constraints.html> · *doc* — Readable Assert.That constraints for movement/validator tests.
11. **Unity — Command line arguments** — <https://docs.unity3d.com/6000.0/Documentation/Manual/EditorCommandLineArguments.html> · *doc* — -batchmode, -nographics, -executeMethod, -logFile used by qa/scripts/editor_smoke.py.
12. **Unity Scripting API — EditorApplication.Exit** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/EditorApplication.Exit.html> · *doc* — Exit codes from editor scripts so the harness can detect pass/fail.
13. **Unity Scripting API — AssetDatabase.ImportAsset** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/AssetDatabase.ImportAsset.html> · *doc* — Scripted import of the sample splat (M0-QA-01 AT-2, pending M0-UNITY-02).
14. **Unity Scripting API — EditorSceneManager.OpenScene** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/SceneManagement.EditorSceneManager.OpenScene.html> · *doc* — Opening the sample scene in the smoke task.
15. **Unity Scripting API — Camera.Render** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Camera.Render.html> · *doc* — Offscreen camera render to a RenderTexture: how batchmode produces editor-smoke.png.
16. **Unity Scripting API — BuildPipeline.BuildPlayer** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/BuildPipeline.BuildPlayer.html> · *doc* — Scripted player builds (the iOS export lane and any QA build scripts).
17. **Unity Scripting API — IPreprocessBuildWithReport** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Build.IPreprocessBuildWithReport.html> · *doc* — Build hooks like IosBurstBuildHook.cs; also where release-flag checks can live (§9.8).
18. **Unity — Code coverage package** — <https://docs.unity3d.com/Packages/com.unity.testtools.codecoverage@1.2/manual/index.html> · *doc* — Optional coverage reports for EditMode/PlayMode (REVIEW_RUBRIC F2, suggested).
19. **Unity — Performance Testing package** — <https://docs.unity3d.com/Packages/com.unity.test-framework.performance@3.0/manual/index.html> · *doc* — Measure.Frames/Measure.Method for repeatable perf evidence (SPEC §6 targets, never gates).
20. **Unity — Assembly definitions** — <https://docs.unity3d.com/6000.0/Documentation/Manual/assembly-definition-files.html> · *doc* — Test assemblies referencing runtime layers downward only (REVIEW_RUBRIC E1).
21. **Unity — Unity Hub CLI** — <https://docs.unity3d.com/hub/manual/HubCLI.html> · *doc* — Headless install of the pinned editor + iOS module on the QA VM (M0-QA-01 AT-1).
22. **Unity — Log files** — <https://docs.unity3d.com/6000.0/Documentation/Manual/log-files.html> · *doc* — Where Editor/Player logs live; the raw Editor log is never committed (licensing details).
23. **Unity — How to run automated tests for your games with UTF** — <https://unity.com/how-to/unity-test-framework-video-game-development> · *doc* — Unity's own guide to structuring game tests with UTF.

## B. Unity CI with game-ci and iOS build and signing

24. **GameCI documentation** — <https://game.ci/docs/> · *doc* — The CI toolkit used by unity-tests, ios-build and android-build workflows.
25. **GameCI — Unity test runner (GitHub)** — <https://game.ci/docs/github/test-runner> · *doc* — Inputs of game-ci/unity-test-runner@v4 (testMode all, checkName, artifacts).
26. **GameCI — Unity builder (GitHub)** — <https://game.ci/docs/github/builder> · *doc* — game-ci/unity-builder used for the iOS export and Android debug APK.
27. **GameCI — Activation** — <https://game.ci/docs/github/activation> · *doc* — Why UNITY_EMAIL/UNITY_PASSWORD are needed on hosted runners (unity-tests.yml header).
28. **GameCI — Deployment to iOS** — <https://game.ci/docs/github/deployment/ios> · *doc* — The Unity → Xcode → fastlane → TestFlight lane the ios-build workflow implements.
29. **GameCI unity-test-runner repo** — <https://github.com/game-ci/unity-test-runner> · *repo* — Source and issues for the test action; check here when CI results look odd.
30. **GameCI unity-builder repo** — <https://github.com/game-ci/unity-builder> · *repo* — Source for the builder action and its customParameters.
31. **GitHub Actions — Using concurrency** — <https://docs.github.com/en/actions/using-jobs/using-concurrency> · *doc* — The unity-license concurrency group: one Unity sign-in at a time.
32. **GitHub Actions — Storing workflow data as artifacts** — <https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts> · *doc* — unity-test-results and ios-xcode-project artifacts QA pulls for evidence.
33. **GitHub Actions — Caching dependencies** — <https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows> · *doc* — The unity/Library cache key that keeps test runs fast.
34. **GitHub Actions — About GitHub-hosted runners** — <https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners> · *doc* — macos-14 runner images and why the public repo gets them unmetered.
35. **GitHub — About protected branches** — <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches> · *doc* — The 7 required checks on main (qa/vm-setup/repo-settings.md).
36. **fastlane docs** — <https://docs.fastlane.tools/> · *doc* — Automation toolchain behind the TestFlight upload.
37. **fastlane — pilot (upload_to_testflight)** — <https://docs.fastlane.tools/actions/upload_to_testflight/> · *doc* — The exact action ios-build.yml uses to push builds to TestFlight.
38. **fastlane — App Store Connect API** — <https://docs.fastlane.tools/app-store-connect-api/> · *doc* — Key-based auth (ASC_KEY_ID, ASC_ISSUER_ID, .p8) instead of an Apple ID session.
39. **fastlane — Continuous integration** — <https://docs.fastlane.tools/best-practices/continuous-integration/> · *doc* — Non-interactive CI patterns and keychain handling on runners.
40. **Apple — Creating API keys for App Store Connect API** — <https://developer.apple.com/documentation/appstoreconnectapi/creating-api-keys-for-app-store-connect-api> · *doc* — How the Owner issues the CI key (M0-REPO-05); least-privilege role choice (§8.4).
41. **Apple — xcodebuild man page (Technical Note TN2339)** — <https://developer.apple.com/library/archive/technotes/tn2339/_index.html> · *doc* — Command-line build/archive/export used by the unsigned compile check and signed archive.
42. **Apple — Distributing your app for beta testing and releases** — <https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases> · *doc* — Archive → export → upload flow behind the TestFlight lane.
43. **Apple — Automatic signing / cloud-managed certificates** — <https://developer.apple.com/help/account/certificates/cloud-managed-certificates> · *doc* — Cloud-managed signing used by the TestFlight job; no certificates in the repo.
44. **Unity — Building for iOS** — <https://docs.unity3d.com/6000.0/Documentation/Manual/iphone-BuildProcess.html> · *doc* — Unity iOS build process and the generated Xcode project QA inspects.
45. **Unity — iOS Player settings** — <https://docs.unity3d.com/6000.0/Documentation/Manual/class-PlayerSettingsiOS.html> · *doc* — Bundle id, target iOS version, IL2CPP/Metal settings QA verifies per build.
46. **Unity — Burst AOT settings** — <https://docs.unity3d.com/Packages/com.unity.burst@1.8/manual/building-aot-settings.html> · *doc* — Why the macOS lane asserts Burst ENABLED (M3-UNITY-01; IosBurstSettingsTests.cs).

## C. TestFlight and App Store Connect operations

47. **Apple — TestFlight overview** — <https://developer.apple.com/testflight/> · *doc* — Internal vs external testing; the cohort behind the 99 % crash-free target (SPEC §9).
48. **App Store Connect Help — TestFlight overview** — <https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview> · *doc* — Groups, build expiry and tester limits for beta ops.
49. **App Store Connect Help — Add internal testers** — <https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers> · *doc* — Internal testers with automatic distribution receive every build (ios-build.yml).
50. **App Store Connect Help — Invite external testers** — <https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers> · *doc* — External groups and public links; triggers Beta App Review.
51. **App Store Connect Help — Provide test information** — <https://developer.apple.com/help/app-store-connect/test-a-beta-version/provide-test-information> · *doc* — What-to-test notes, feedback email and beta review info per build.
52. **App Store Connect Help — View tester feedback** — <https://developer.apple.com/help/app-store-connect/test-a-beta-version/view-tester-feedback> · *doc* — Screenshot feedback and crash reports from TestFlight testers feed triage.
53. **App Store Connect Help — Upload builds** — <https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds> · *doc* — Upload paths and processing states QA watches after a CI run.
54. **App Store Connect Help — Export compliance overview** — <https://developer.apple.com/help/app-store-connect/manage-app-information/overview-of-export-compliance> · *doc* — The encryption question every build answers; set it in Info.plist to unblock testers.
55. **App Store Connect Help — Roles and permissions** — <https://developer.apple.com/help/app-store-connect/reference/role-permissions> · *doc* — Pick the least role for the ops account (SECURITY_CHECKLIST §8.4).
56. **App Store Connect Help — Submit an app for review** — <https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-for-review> · *doc* — The submission step on the M5 release checklist.
57. **App Store Connect Help — Phased release** — <https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases> · *doc* — Staged rollout to watch crash-free rate before 100 %.
58. **App Store Connect Help — Manage app privacy** — <https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy> · *doc* — Privacy nutrition labels must be accurate (SPEC §9 item 6; §9.6).
59. **App Store Connect Help — Screenshot specifications** — <https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications> · *doc* — Required screenshot sizes for the M5 diorama hero set (OWNER_LAUNCH_CHECKLIST).
60. **App Store Connect Help — App preview specifications** — <https://developer.apple.com/help/app-store-connect/reference/app-preview-specifications> · *doc* — Preview video constraints for the optional storyboard (Design Skills rule 28).
61. **App Store Connect Help — Age ratings** — <https://developer.apple.com/help/app-store-connect/reference/age-ratings> · *doc* — Age-rating questionnaire; UGC and the 13+ gate affect answers (SPEC §3.9).
62. **Apple — Offering account deletion in your app** — <https://developer.apple.com/support/offering-account-deletion-in-your-app/> · *doc* — In-app deletion is a review requirement; QA verifies it before submission.
63. **Apple — Privacy manifest files** — <https://developer.apple.com/documentation/bundleresources/privacy-manifest-files> · *doc* — PrivacyInfo.xcprivacy and required-reason APIs; SDKs like Sentry must ship one.
64. **Apple — Upcoming requirements** — <https://developer.apple.com/news/upcoming-requirements/> · *doc* — SDK/Xcode minimums that can block uploads; check before each release.
65. **Apple — App Store Connect API** — <https://developer.apple.com/documentation/appstoreconnectapi> · *doc* — Scriptable build status, TestFlight groups and review state for release ops.

## D. App Store Review Guidelines and store policy

66. **App Store Review Guidelines** — <https://developer.apple.com/app-store/review/guidelines/> · *doc* — The rulebook; 1.2 (UGC), 2.1 (completeness), 2.3 (accurate metadata), 3.1 (IAP), 5.1 (privacy) apply to GJ.
67. **Apple — App Review** — <https://developer.apple.com/distribute/app-review/> · *doc* — Review process, timelines and how to reply or appeal.
68. **Apple — Human Interface Guidelines: Accessibility** — <https://developer.apple.com/design/human-interface-guidelines/accessibility> · *doc* — Accessibility expectations QA spot-checks (DESIGN_SYSTEM decision 10).
69. **Apple — In-App Purchase** — <https://developer.apple.com/in-app-purchase/> · *doc* — The two launch SKUs (SPEC §3.8): restore and Family Sharing behaviour to test.
70. **Apple — StoreKit testing in Xcode** — <https://developer.apple.com/documentation/xcode/setting-up-storekit-testing-in-xcode> · *doc* — Local IAP test configs so purchase flows are tested without real money.
71. **Apple — Testing in-app purchases with sandbox** — <https://developer.apple.com/documentation/storekit/testing-in-app-purchases-with-sandbox> · *doc* — Sandbox accounts for QA purchase/restore passes.
72. **Apple — User privacy and data use** — <https://developer.apple.com/app-store/user-privacy-and-data-use/> · *doc* — ATT and data-use rules; GJ collects pseudonymous telemetry only (SPEC §7).
73. **Apple — App privacy details on the App Store** — <https://developer.apple.com/app-store/app-privacy-details/> · *doc* — Label definitions to cross-check against the actual SDK data flows.
74. **Apple — Guidelines for using Apple trademarks in marketing** — <https://developer.apple.com/app-store/marketing/guidelines/> · *doc* — Badge and device-frame rules for store assets and the launch video (M5-DUO-01).
75. **Apple — Getting featured on the App Store** — <https://developer.apple.com/app-store/getting-featured/> · *doc* — The featuring nomination in M5-DUO-01.
76. **Apple — App Store product page** — <https://developer.apple.com/app-store/product-page/> · *doc* — Name, subtitle, screenshots and preview best practices for the listing.
77. **Google Play — Developer Policy Center** — <https://play.google/developer-content-policy/> · *doc* — Play policy for the v1.1 Android release (AUTH #003 defers Android).
78. **Google Play — User-generated content policy** — <https://support.google.com/googleplay/android-developer/answer/9876937> · *doc* — Play's UGC moderation rules, the Android counterpart of Apple 1.2.
79. **Google Play Console Help — Set up an open, closed or internal test** — <https://support.google.com/googleplay/android-developer/answer/9845334> · *doc* — Play test tracks, the TestFlight equivalent for v1.1.
80. **Google Play Console Help — Data safety section** — <https://support.google.com/googleplay/android-developer/answer/10787469> · *doc* — Play's privacy disclosure, mirrors Apple's labels for v1.1.

## E. Device matrix, performance and on-device profiling

81. **Apple Support — iPhone manuals, specs and downloads** — <https://support.apple.com/specs/iphone> · *doc* — Source of truth for the device tier matrix (chip, RAM, display, ProMotion).
82. **Apple — Identifying your iPhone model** — <https://support.apple.com/en-us/108044> · *doc* — Map model identifiers in crash/perf reports to marketing names.
83. **Apple Developer — App Store support (iOS and iPadOS usage figures)** — <https://developer.apple.com/support/app-store/> · *doc* — iOS version adoption: informs the minimum iOS the Unity build requires (SPEC §11).
84. **Unity — System requirements for Unity 6** — <https://docs.unity3d.com/6000.0/Documentation/Manual/system-requirements.html> · *doc* — Minimum iOS version and GPU requirements for Unity 6 players.
85. **Unity — Profiler overview** — <https://docs.unity3d.com/6000.0/Documentation/Manual/Profiler.html> · *doc* — Profiler screenshots are the QA perf evidence (Design Skills §4; M0-QA-02).
86. **Unity — Profiling your application on a target device** — <https://docs.unity3d.com/6000.0/Documentation/Manual/profiler-profiling-applications.html> · *doc* — Development builds + autoconnect for real-iPhone measurements (SPEC §6).
87. **Unity — Frame Debugger** — <https://docs.unity3d.com/6000.0/Documentation/Manual/FrameDebugger.html> · *doc* — Verify the single HUD overlay pass and no full-screen blur (REVIEW_RUBRIC D5).
88. **Unity — Memory Profiler package** — <https://docs.unity3d.com/Packages/com.unity.memoryprofiler@1.1/manual/index.html> · *doc* — Memory snapshots on older iPhones where jetsam kills are likely.
89. **Unity — Profile Analyzer** — <https://docs.unity3d.com/Packages/com.unity.performance.profile-analyzer@1.2/manual/index.html> · *doc* — Compare before/after captures for D1 evidence.
90. **Unity — Adaptive Performance** — <https://docs.unity3d.com/Packages/com.unity.adaptiveperformance@5.1/manual/index.html> · *doc* — Thermal and performance-state APIs relevant to automatic quality tiers (SPEC §6).
91. **Unity — URP quality settings** — <https://docs.unity3d.com/6000.0/Documentation/Manual/urp/configure-for-better-performance.html> · *doc* — Per-tier URP assets (M0-UNITY-01 AT-2) that QA verifies switch correctly.
92. **Apple — Gathering information about memory use** — <https://developer.apple.com/documentation/xcode/gathering-information-about-memory-use> · *doc* — Memory graph and allocations workflow for older-iPhone memory passes.
93. **Apple — Reducing your app's memory use** — <https://developer.apple.com/documentation/xcode/reducing-your-app-s-memory-use> · *doc* — Memory limits and jetsam: older iPhones in the matrix hit these first.
94. **Apple — Improving your app's performance** — <https://developer.apple.com/documentation/xcode/improving-your-app-s-performance> · *doc* — Apple's hub for launch time, hangs, battery and thermal work.
95. **Apple — Metal debugger / GPU frame capture** — <https://developer.apple.com/documentation/xcode/capturing-a-metal-workload-in-xcode> · *doc* — GPU capture to diagnose splat-sort glitches on device (M1-UNITY-01 AT-2).
96. **Apple — ProcessInfo.ThermalState** — <https://developer.apple.com/documentation/foundation/processinfo/thermalstate-swift.enum> · *doc* — Record thermal state alongside fps in device reports.
97. **Apple — Optimizing ProMotion refresh rates** — <https://developer.apple.com/documentation/quartzcore/optimizing-promotion-refresh-rates-for-iphone-13-pro-and-ipad-pro> · *doc* — 60 fps at up to 120 Hz on newest iPhones (SPEC §6 row 1).
98. **aras-p UnityGaussianSplatting** — <https://github.com/aras-p/UnityGaussianSplatting> · *repo* — The baseline renderer QA measures; issue history documents the Metal sort risk (M1-UNITY-01).
99. **aras-p UnityGaussianSplatting issue #226** — <https://github.com/aras-p/UnityGaussianSplatting/issues/226> · *postmortem* — The Metal radix-sort glitch QA must look for on device (M1-UNITY-01 AT-2).

## F. Crash analytics and triage

100. **Sentry for Unity** — <https://docs.sentry.io/platforms/unity/> · *vendor guide* — Primary crash tool in research/vendors/crash-reporting.md (AUTH #017 free tier).
101. **Sentry Unity — Known limitations** — <https://docs.sentry.io/platforms/unity/troubleshooting/known-limitations/> · *vendor guide* — IL2CPP line-mapping caveats to expect during triage.
102. **Sentry Unity — Data collected** — <https://docs.sentry.io/platforms/unity/data-management/data-collected/> · *vendor guide* — Confirms sendDefaultPii=false posture for privacy labels (§10.1).
103. **Sentry — Scrubbing sensitive data** — <https://docs.sentry.io/security-legal-pii/scrubbing/> · *vendor guide* — Server-side scrubbing so crash payloads carry no PII (REVIEW_RUBRIC C10).
104. **Sentry — Release health** — <https://docs.sentry.io/product/releases/health/> · *vendor guide* — Crash-free sessions/users: the metric for the ≥ 99 % target (SPEC §6).
105. **Sentry — Issue grouping** — <https://docs.sentry.io/concepts/data-management/event-grouping/> · *vendor guide* — Fingerprinting rules so one bug is one issue during triage.
106. **Sentry — Debug information files (dSYMs)** — <https://docs.sentry.io/platforms/unity/data-management/debug-files/> · *vendor guide* — Symbol upload for IL2CPP/native stacks; verify on the first TestFlight build.
107. **Sentry — Quotas and spike protection** — <https://docs.sentry.io/pricing/quotas/> · *vendor guide* — Free-tier event cap watch item; sampling to avoid a crash storm exhausting it.
108. **Firebase Crashlytics — Get started (Unity)** — <https://firebase.google.com/docs/crashlytics/get-started?platform=unity> · *vendor guide* — Fallback tool in the vendor research if Sentry's cap binds.
109. **Firebase Crashlytics — Crash-free metrics** — <https://firebase.google.com/docs/crashlytics/crash-free-metrics> · *vendor guide* — Reference definition of crash-free users vs sessions.
110. **Apple — Acquiring crash reports and diagnostic logs** — <https://developer.apple.com/documentation/xcode/acquiring-crash-reports-and-diagnostic-logs> · *doc* — Organizer, TestFlight and device crash logs: the first-party supplement.
111. **Apple — Diagnosing issues using crash reports and device logs** — <https://developer.apple.com/documentation/xcode/diagnosing-issues-using-crash-reports-and-device-logs> · *doc* — Reading exception types and termination reasons.
112. **Apple — Adding identifiable symbol names to a crash report** — <https://developer.apple.com/documentation/xcode/adding-identifiable-symbol-names-to-a-crash-report> · *doc* — Symbolication with dSYMs for release builds (symbols stripped per §9.7).
113. **Apple — Identifying the cause of common crashes** — <https://developer.apple.com/documentation/xcode/identifying-the-cause-of-common-crashes> · *doc* — Triage patterns: EXC_BAD_ACCESS, watchdog, jetsam.
114. **Apple — Addressing watchdog terminations** — <https://developer.apple.com/documentation/xcode/addressing-watchdog-terminations> · *doc* — Launch/resume timeouts; relevant to heavy splat loads at startup.
115. **Apple — Identifying high-memory use with jetsam event reports** — <https://developer.apple.com/documentation/xcode/identifying-high-memory-use-with-jetsam-event-reports> · *doc* — Memory kills don't appear as crashes in SDKs; check here for older iPhones.
116. **Apple — MetricKit** — <https://developer.apple.com/documentation/metrickit> · *doc* — On-device diagnostics (hangs, crashes, CPU) as the privacy-strong supplement.
117. **Unity — Managed stack traces on iOS (IL2CPP)** — <https://docs.unity3d.com/6000.0/Documentation/Manual/il2cpp-managed-stack-traces.html> · *doc* — Getting usable C# stacks from IL2CPP builds.
118. **Unity — Cloud Diagnostics deprecation / crash reporting** — <https://docs.unity.com/ugs/en-us/manual/cloud-diagnostics/manual/CrashandExceptionReporting/SettingupCrashandExceptionReporting> · *vendor guide* — Unity's own option, noted so the choice stays documented (not in AUTH #017).
119. **Google SRE Book — Postmortem culture** — <https://sre.google/sre-book/postmortem-culture/> · *doc* — Blameless postmortems for S1 defects and release incidents (SECURITY_CHECKLIST §11).
120. **Google SRE Book — Managing incidents** — <https://sre.google/sre-book/managing-incidents/> · *doc* — Incident roles and comms for a bad release.
121. **PagerDuty — Incident response documentation** — <https://response.pagerduty.com/> · *doc* — Open incident-response process; severity levels map onto S1–S4 (M0-QA-02).

## G. Visual QA, evidence and defect process

122. **Unity — ScreenCapture.CaptureScreenshot** — <https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ScreenCapture.CaptureScreenshot.html> · *doc* — Player-side screenshots for evidence sets named qa/evidence/<ticket>/<nn>-<what>.png.
123. **Unity — Recorder package** — <https://docs.unity3d.com/Packages/com.unity.recorder@5.1/manual/index.html> · *doc* — Editor clip capture for ≤ 30 s PR clips (never committed, M0-QA-02).
124. **Apple Support — Take a screenshot on iPhone** — <https://support.apple.com/en-us/102616> · *doc* — Device evidence from the Owner's iPhones.
125. **Apple — Record the screen on your iPhone** — <https://support.apple.com/en-us/102653> · *doc* — Screen recordings for device clips attached to PRs.
126. **Apple — Capturing screenshots and videos from devices and Simulator** — <https://developer.apple.com/documentation/xcode/capturing-screenshots-and-videos-from-simulator> · *doc* — xcrun simctl io for scripted simulator evidence on macOS runners.
127. **Pillow — Image module** — <https://pillow.readthedocs.io/en/stable/reference/Image.html> · *doc* — Resize/compress evidence PNGs to the ≤ 2 MB rule and strip metadata.
128. **GitHub Docs — Attaching files** — <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/attaching-files> · *doc* — How clips get attached to PRs instead of committed.
129. **GitHub Docs — Issue templates** — <https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/configuring-issue-templates-for-your-repository> · *doc* — A DEFECT template with S1–S4 severity for the M0-QA-02 flow.
130. **Martin Fowler — Test pyramid** — <https://martinfowler.com/bliki/TestPyramid.html> · *doc* — Many EditMode tests, fewer PlayMode, very few device passes.
131. **Google Testing Blog — Flaky tests at Google** — <https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html> · *doc* — Quarantine rules for flaky PlayMode tests (REVIEW_RUBRIC F3, F4).
132. **Game Accessibility Guidelines** — <https://gameaccessibilityguidelines.com/> · *doc* — Checklist items QA re-checks alongside DESIGN_SYSTEM decision 10.
133. **Xbox Accessibility Guidelines** — <https://learn.microsoft.com/en-us/gaming/accessibility/guidelines> · *doc* — Detailed, testable game accessibility criteria for QA passes.
134. **Coblis — Color blindness simulator** — <https://www.color-blindness.com/coblis-color-blindness-simulator/> · *doc* — Deuteranopia check on evidence screenshots (Design Skills §4).
