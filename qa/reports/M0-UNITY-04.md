# M0-UNITY-04 — debug overlay — build notes and QA pass

2026-09-27, gj-operator (Builder work, then the gj-qa-release hat per `qa/VISUAL_QA.md`, first live use).
Delivered as a direct commit to `main` (Owner-approved Operator precedent), so there is no PR to comment on:
this file carries the QA verdict comment (§8) instead.

## What was built
- **Assembly** `GiganticJourneys.DebugOverlay` (`unity/Assets/GiganticJourneys/DebugOverlay/`), define
  constraint `UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG`: compiled in the Editor, in Development builds,
  and in any build that sets the `GJ_DEBUG` scripting define; **absent from release builds**.
- **`DebugOverlay`** (UI Toolkit `UIDocument` with a runtime `PanelSettings`, no assets): created hidden after
  the first scene loads. Toggle: **three-finger tap**, **F3**, gamepad **L3 + R3**. Line 1: fps (1 s average),
  p99 over 5 s, frame ms. Line 2: version (and build number), git short SHA, scene, device model
  (`SystemInfo.deviceModel`, never the user-chosen device name). **Save report** button (and F4).
  Top-right inside `Screen.safeArea`, font 2.5 % and hard cap 8 % of the landscape height, 72 % black scrim.
- **`FrameStats`**: 60 s ring buffer at up to 240 fps; fps pNN = 1000 / pNN frame time.
- **`PerformanceReport`**: `gj-perf-report-<utc>.txt` in `Application.persistentDataPath` (Documents on iOS)
  with fps p50/p99/avg over 60 s, frame ms p50/p99, device model, OS, GPU, version, SHA, Unity, scene,
  quality level; then the **iOS share sheet** (`Plugins/iOS/GJShareSheet.mm`, `UIActivityViewController`).
- **`Assets/Editor/Build/BuildInfoHook.cs`** (debug builds only): writes the SHA/build-number resource into the
  git-ignored `Assets/Generated/` and deletes it after the build; keeps `GJShareSheet.mm` out of release builds
  (include-in-build delegate); sets `UIFileSharingEnabled` + `LSSupportsOpeningDocumentsInPlace` on iOS
  Development builds so reports appear in the Files app.
- **Evidence tooling**: `OverlayCapture.cs` (capture mode, Development builds only, `-gjOverlayCapture`),
  `Assets/Editor/QA/OverlayEvidence.cs` + `qa/scripts/overlay_evidence.py`.

## Tests (local, Unity 6000.0.84f1, `-batchmode -nographics`)
| Suite | Result | File |
|---|---|---|
| EditMode | **26/26 passed** (14 new) | `M0-UNITY-04/editmode-results.xml` |
| PlayMode | **7/7 passed** (6 new) | `M0-UNITY-04/playmode-results.xml` |

AT-2 test: **`GiganticJourneys.Tests.DebugOverlayReleaseExclusionTests.ReleasePlayerScripts_ExcludeDebugOverlayType`**
compiles the real player scripts (`PlayerBuildInterface.CompilePlayerScripts`, Linux target) as a release build
and asserts `GiganticJourneys.DebugOverlay` is absent and no `GiganticJourneys*.dll` mentions `DebugOverlay`.
Its controls: `DevelopmentPlayerScripts_IncludeDebugOverlay`, `GjDebugDefine_ForcesOverlayIntoNonDevelopmentPlayer`,
plus `OverlayAssembly_HasDebugDefineConstraint`, `ReleaseDefines_DoNotForceGjDebug`,
`SharePlugin_IsIosOnly_AndExcludedFromReleaseBuilds`. Build-level confirmation: `qa/evidence/M0-UNITY-04/run/builds.json`
(Linux players and iOS Xcode exports, Development vs release).

PlayMode: `Visible_ShowsFpsP99FrameTimeBuildShaSceneDevice`, `Layout_TopRightInsideSafeArea_NoTallerThan8Percent`,
`F3_TogglesOverlay`, `ThreeFingerTap_TogglesOverlay` (simulated Input System keyboard and touchscreen),
`SaveButton_WritesSixtySecondReport` (a submit event on the real button), `Overlay_IsCreatedAutomatically_HiddenByDefault_WithUiToolkit`.

## Acceptance tests
| AT | Level | Status | Evidence |
|---|---|---|---|
| AT-1 toggle + fields + save report | required | **Met on Editor/desktop; device part pending** | 01; PlayMode tests; `run/perf-report-linux-lavapipe.txt`. Pending: three-finger tap, Documents file and share sheet on an Owner iPhone (Development build) |
| AT-2 excluded from release via GJ_DEBUG | required | **Met** | `DebugOverlayReleaseExclusionTests.ReleasePlayerScripts_ExcludeDebugOverlayType`; `run/builds.json` |
| AT-3 UI Toolkit, top-right in safe area, ≤ 8 %, scrim, bright + dark | suggested | **Met** (stand-in scans, simulated safe area) | 01, 02, 03; `Layout_…` test |
| AT-4 PR timeline Foreman → Bot PR → QA → Coordinator merge | required | **Not met by this delivery** | Direct commit to main on the Owner's instruction, so there is no PR timeline. The Coordinator decides whether this commit counts for the M0 exit test or a PR-flow re-run is needed (`governance/CHECKPOINTS/M0.md`) |

## QA verdict (VISUAL_QA §8)
```
QA pass — M0-UNITY-04 — PASS WITH DEFECTS
Build: main @ 408e90a · Unity 6000.0.84f1 · Debian 13 x86_64, Xvfb, Vulkan on Mesa lavapipe (llvmpipe, CPU)
Checklist: §5.1 + §5.3 — 10 pass, 0 fail, 8 n/a (below)
Evidence: qa/evidence/M0-UNITY-04/ (01-overlay-bright-scan, 02-overlay-dark-scan, 03-overlay-safe-area-iphone-15-pro, run/) · clips: none (no PR)
Profiler: not measured (no Development build on an Owner iPhone yet; lavapipe numbers are not performance data)
Defects: none filed against the overlay; one S4 environment note on the sample scene (below)
Privacy: the evidence contains no faces, addresses, documents, or screens with personal data. Content: procedural summit splat, overlay text, QA guide lines.
```

§5.1: ✅ build noted · ✅ each visual AT has a named screenshot (AT-1 device part pending) · ✅ console clean in the
capture runs (0 errors / 0 exceptions, `capture-*.json`) · ✅ evidence follows §2, privacy line present ·
✅ Profiler line present ("not measured", §4).
§5.3: ✅ screenshots on bright and dark stand-ins (n/a cluttered: no corpus scan yet; the overlay sits over sky) ·
✅ contrast measured on the PNGs: 9.3:1 (bright), 21:1 (dark) ≥ 4.5:1 · n/a glass fallback (opaque scrim, no glass) ·
✅ safe-area insets respected (simulated iPhone 15 Pro, 03) · touch target: the Save report button was 80 px tall at
1179 px = 27 pt, **below the 44 pt guideline** (fixed 2026-09-28, see "Follow-up: 44 pt Save button" below) ·
✅ one primary action (Save report) · n/a waits (report write is instant) · n/a deuteranopia (no state colours) ·
✅ copy is short ("Save report", "Saved <file>").

Notes for the Coordinator:
- **Touch target vs 8 % rule.** At 8 % of 1179 px the whole overlay is ≤ 94 px (31 pt), so a 44 pt button cannot fit
  inside the HUD band that Design Skills rule 21 asks for. The button is debug-only (compiled out of release). If the
  Owner prefers 44 pt, the button would have to sit below the band while visible. **→ Done 2026-09-28** (below).
- **S4 environment note (not an overlay defect):** on the Linux Development player under lavapipe, the URP camera
  clear is lost on the HDR color buffer (black background) and 4x MSAA logs a render-pass sample-count error. The
  capture mode turns HDR and MSAA off for evidence. Worth a look in M1-UNITY-01 (splat render integration), which
  owns device rendering.
- The build step logs `Kernel 'InitDeviceRadixSort' not found` from the splat package in a `-nographics` Editor
  (no GPU); pre-existing, harmless for builds.

## What remains (needs the Owner's iPhone)
1. Install a **Development** build (TestFlight builds are release builds, so they will not contain the overlay
   by design; a Development build from the macOS lane or Xcode is needed).
2. Three-finger tap → overlay; tap **Save report** → share sheet; confirm the file in Files → On My iPhone →
   Gigantic Journeys. Screenshot `04-overlay-device-<model>.png` + `perf-report-<model>.txt` into this folder.

## Follow-up: 44 pt Save button (2026-09-28, gj-operator)

Owner/operator request: move **Save report** below the panel and make it a ≥ 44 × 44 pt touch target (Apple HIG),
safe-area aware, keeping the top-right placement and the F4 shortcut. The ticket stays **done** (the Coordinator
closed it 2026-09-28 before this follow-up; the change resolves the one accepted QA defect and is recorded in the
ticket history, not a reopen).

**What changed** (`DebugOverlay.cs`): the panel and the button now sit in one container anchored top-right inside
the safe area; the panel (scrim + two text lines) keeps the ≤ 8 % cap, and the button is right-aligned directly
**below** it (one padding gap) with `minWidth = minHeight = ceil(44 pt × pixels-per-point)`. Pixels per point is the
iOS screen scale estimated as `round(Screen.dpi / 163)` clamped to 1–3 (iPhone 15 Pro 460 dpi → 3×, SE/11 326 → 2×,
iPad 264 → 2×, desktop/unknown → 1×); `DebugOverlay.PixelsPerPointOverride` lets QA/tests simulate a device. The
button shows only while the overlay is visible, so it sits outside the HUD band only while debugging (Design Skills
rule 21 applies to the panel). Same scrim as the panel plus a 1 px light edge. F4 still saves while visible.

| Measurement (simulated iPhone 15 Pro landscape, 2556×1179, 3×) | Before (`408e90a`) | After |
|---|---|---|
| Save button position | inside the panel, right of the text | below the panel, right-aligned, inside the safe area |
| Save button size | ≈ 80 px tall = **27 pt** (width text-sized) | **218 × 132 px = 72.7 × 44 pt** at (2155, 92) |
| Panel | 727 × 80 px, 6.8 % of height | 525 × 80 px, **6.8 %** of height (narrower: button moved out) |
| Desktop 1280×720 (1×) | button inside the 50 px panel | panel 50 px (6.9 %); button 119 × 44 px = 44 pt tall, below it |

Evidence (regenerated with `python qa/scripts/overlay_evidence.py --ios`, working tree on `fadeb33` + this change,
so the overlay shows `fadeb33`): `qa/evidence/M0-UNITY-04/03-overlay-safe-area-iphone-15-pro.png` (the 44 pt button
under the panel, inside the yellow safe-area guide), `01-`/`02-` (bright/dark scans), measured rects in
`run/capture-*.json` (`saveButtonRect`, `saveButtonWidthPt/HeightPt`, `saveButtonBelowPanel`,
`saveButtonInsideSafeArea`, `saveButtonMeets44pt`, all true); the script now fails the capture if any of these is
false. `run/builds.json`: Linux + iOS Development/release builds re-checked, release still excludes the overlay.

Tests (local, Unity 6000.0.84f1, `-batchmode -nographics`): **EditMode 34/34** (new
`EstimatePixelsPerPoint_MatchesIosScreenScale` ×7, `MinTouchTarget_Is44Points`), **PlayMode 11/11** (new
`SaveButton_BelowPanel_AtLeast44Points_InsideSafeArea` at 1×/2×/3× — asserts the button is not inside the panel,
its top is at or below the panel's bottom, width and height ≥ 44 pt, inside the safe area, right-aligned with the
panel, and the panel alone still ≤ 8 %; new `F4_SavesReport_WhileVisible`). Results:
`M0-UNITY-04/editmode-results.xml`, `M0-UNITY-04/playmode-results.xml`.
