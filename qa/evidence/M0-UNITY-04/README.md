# M0-UNITY-04 evidence — debug overlay

Standard: `qa/VISUAL_QA.md` (M0-QA-02), first live use. Captured 2026-09-27 4:40 PM CT by gj-operator (QA hat)
with `python qa/scripts/overlay_evidence.py --ios`; **re-captured 2026-09-28 1:07 PM CT** after the 44 pt Save
button follow-up (button moved below the panel; the overlay now shows `fadeb33`, the base of that change). QA verdict and checklist: `qa/reports/M0-UNITY-04.md`.

Build for every screenshot: originally commit `408e90a`; the current PNGs are from the 2026-09-28 follow-up
(working tree on `fadeb33` + the button change; the overlay shows `fadeb33`), Development
Linux player of `Assets/Capture/Samples/SplatSample.unity`, Unity `6000.0.84f1`, host Debian 13 x86_64 under
Xvfb, **Vulkan on Mesa lavapipe** (`llvmpipe (LLVM 19.1.7)`, a CPU rasterizer). The capture mode
(`OverlayCapture.cs`, Development builds only) shows the overlay, lets 6 s of frame stats build up, then
captures. MSAA and HDR are off on the camera for these captures only, because lavapipe mishandles them
(the HDR camera clear comes out black). **The fps numbers are lavapipe numbers, not performance data.**

- `01-overlay-bright-scan.png`: 1280x720. The overlay over a **bright-scan stand-in**: near-white sky
  behind it plus +1 EV post exposure. Shows fps (1 s average), p99 over 5 s, frame ms, version `v1.0`,
  SHA (`408e90a` originally, `fadeb33` in the re-capture), scene `SplatSample`, device model (`PC` on a Linux desktop; `iPhone16,1`-style
  identifiers on iOS). Scrim `#474747` behind white text measured on this PNG: **9.3:1**. Height 50 px =
  **6.9 %** of 720. (AT-1, AT-3)
- `02-overlay-dark-scan.png`: 1280x720. The same over a **dark-scan stand-in**: near-black sky plus -3 EV.
  White text on the scrim: **21:1**. Height 6.9 %. (AT-3)
- `03-overlay-safe-area-iphone-15-pro.png`: rendered at 2556x1179 (iPhone 15 Pro landscape pixels),
  downscaled 50 % to keep it under 2 MB. The **iPhone 15 Pro landscape safe area is simulated** (177 px
  side insets, 63 px bottom inset = 59/59/21 pt at 3x) through `DebugOverlay.SafeAreaOverride`. QA guides:
  yellow = safe area, magenta = 8 % of the screen height. Overlay rect (original) 1646,6 727x80 px: **inside the safe
  area, anchored top-right, 6.8 % of the height** (re-capture: panel 1848,6 525x80 px, 6.8 %). The **Save report
  button** sits directly below the panel, right-aligned, inside the safe area: 2155,92 218x132 px = **72.7 x 44 pt**
  at the simulated 3x scale (before: ~27 pt tall inside the panel). (AT-1, AT-3, HIG 44 pt)
- `run/builds.json`: Development and release players built and inspected (AT-2, build level).
  Linux: `GiganticJourneys.DebugOverlay.dll` in Development only; no `DebugOverlay` string in any release
  `GiganticJourneys*.dll`. iOS Xcode exports: the overlay's IL2CPP output and `GJShareSheet.mm` in
  Development only; the Development `Info.plist` gets `UIFileSharingEnabled`.
- `run/capture-scans.json`, `run/capture-safe-area.json`: measured layout per shot (screen, safe area,
  overlay rect, height fraction, inside-safe-area and anchored-top-right flags, label text), 0 errors.
- `run/perf-report-linux-lavapipe.txt`: the report written by the overlay's **Save report** handler (the
  same handler as the on-screen button and F4) in the capture run. Shows the format only; lavapipe numbers.

Not in this set (needs the Owner's iPhone): the three-finger tap and the share sheet on a device, a
`04-overlay-device-<model>.png`, and a device `perf-report-<model>.txt`. Clips: none (no PR to attach to;
the toggle is covered by the PlayMode tests `F3_TogglesOverlay` and `ThreeFingerTap_TogglesOverlay`).

## Owner device check (2026-10-02, TestFlight build 40, internal-debug)
The Owner ran TestFlight **build 40** (run 37046098523, internal-debug, commit `686156b`) on an **iPhone 14**
(`iPhone14,7`, iOS 26.6.1, Apple A15 GPU, Metal, 1170x2532). The **three-finger tap toggled the overlay** and **Save report
wrote the file and opened the share sheet**, so the AT-1 device part passes. The scene was **`SampleScene`** (the boot
scene, `ProjectIdentity.BootScenePath`), not the splat sample. No device screenshot was supplied, so there is no `04-overlay-device-*.png`.

- `run/perf-report-iphone14-7.txt`: the report exactly as the device's Save report handler wrote it
  (created 2026-10-03 00:08:45 UTC = 2026-10-02 7:08 PM CT).
- Reading it: **fps_p50 30.0 / frame_ms_p50 33.3**. That is the iOS default cap: `target_frame_rate: -1` runs at
  30 fps on mobile, so the median frame is vsync-locked at 30, not GPU-bound. **fps_avg 1.6, frame_ms_p99 696.8, 145 frames
  over covered_s 89.3** (more than the 60 s window): 145 frames × 33 ms is only about 5 s of rendering, so about 84 s fell in a few long
  gaps. That is consistent with the app being backgrounded or covered by the share sheet or TestFlight UI during the window. So p99 and
  avg are **not performance data**; only the p50 is meaningful.
- Follow-up: SPEC §6 sets a 60 fps target on current iPhones (30 fps on older ones through quality tiering), which the
  default 30 fps cap made unreachable. `GiganticJourneys.FrameRatePolicy` now sets `Application.targetFrameRate = 60`
  on mobile before the first scene loads (`vSyncCount` is ignored on iOS). A re-measure needs a build with that commit.
- Oddity: the report's `build_version` reads `0.0.181 (0)`, not the TestFlight build number 40. The baked
  build-info resource has `build_number` 0, because CFBundleVersion is set after export with PlistBuddy. It is cosmetic.

Scans: until the M0-OWNER-01 corpus exists, "bright scan" and "dark scan" are the procedural sample splat
with a bright and a dark background and exposure, as `VISUAL_QA.md` §9 allows (labelled substitution).

**Privacy:** the evidence contains no faces, addresses, documents, or screens with personal data. Content: procedural summit splat only (terrain, trees, a flag), the overlay's own text (version, commit SHA, scene name, the generic device model "PC"), and QA guide lines; checked by eye on each of the three PNGs. The report sidecars have no device name, user name or path. The device report holds only the generic model identifier `iPhone14,7`, the OS and GPU versions, and the screen size.
