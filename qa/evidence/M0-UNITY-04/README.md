# M0-UNITY-04 evidence — debug overlay

Standard: `qa/VISUAL_QA.md` (M0-QA-02), first live use. Captured 2026-09-27 4:40 PM CT by gj-operator (QA hat)
with `python qa/scripts/overlay_evidence.py --ios`. QA verdict and checklist: `qa/reports/M0-UNITY-04.md`.

Build for every screenshot: commit `408e90a` (the overlay commit; the overlay shows this SHA), Development
Linux player of `Assets/Capture/Samples/SplatSample.unity`, Unity `6000.0.84f1`, host Debian 13 x86_64 under
Xvfb, **Vulkan on Mesa lavapipe** (`llvmpipe (LLVM 19.1.7)`, a CPU rasterizer). The capture mode
(`OverlayCapture.cs`, Development builds only) shows the overlay, lets 6 s of frame stats build up, then
captures. MSAA and HDR are off on the camera for these captures only, because lavapipe mishandles them
(the HDR camera clear comes out black). **The fps numbers are lavapipe numbers, not performance data.**

- `01-overlay-bright-scan.png`: 1280x720. The overlay over a **bright-scan stand-in**: near-white sky
  behind it plus +1 EV post exposure. Shows fps (1 s average), p99 over 5 s, frame ms, version `v1.0`,
  SHA `408e90a`, scene `SplatSample`, device model (`PC` on a Linux desktop; `iPhone16,1`-style
  identifiers on iOS). Scrim `#474747` behind white text measured on this PNG: **9.3:1**. Height 50 px =
  **6.9 %** of 720. (AT-1, AT-3)
- `02-overlay-dark-scan.png`: 1280x720. The same over a **dark-scan stand-in**: near-black sky plus -3 EV.
  White text on the scrim: **21:1**. Height 6.9 %. (AT-3)
- `03-overlay-safe-area-iphone-15-pro.png`: rendered at 2556x1179 (iPhone 15 Pro landscape pixels),
  downscaled 50 % to keep it under 2 MB. The **iPhone 15 Pro landscape safe area is simulated** (177 px
  side insets, 63 px bottom inset = 59/59/21 pt at 3x) through `DebugOverlay.SafeAreaOverride`. QA guides:
  yellow = safe area, magenta = 8 % of the screen height. Overlay rect 1646,6 727x80 px: **inside the safe
  area, anchored top-right, 6.8 % of the height**. (AT-3)
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

Scans: until the M0-OWNER-01 corpus exists, "bright scan" and "dark scan" are the procedural sample splat
with a bright and a dark background and exposure, as `VISUAL_QA.md` §9 allows (labelled substitution).

**Privacy:** the evidence contains no faces, addresses, documents, or screens with personal data. Content: procedural summit splat only (terrain, trees, a flag), the overlay's own text (version, commit SHA, scene name, the generic device model "PC"), and QA guide lines; checked by eye on each of the three PNGs. The report sidecar has no device name, user name or path.
