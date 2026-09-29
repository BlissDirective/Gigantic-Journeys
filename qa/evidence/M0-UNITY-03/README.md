# M0-UNITY-03 evidence — traversal controller scaffold (capsule, touch + gamepad)

Standard: `qa/VISUAL_QA.md` (M0-QA-02). Captured 2026-09-28 9:47 PM CT by gj-operator (gj-qa-release hat)
with the explicit PlayMode capture `GiganticJourneys.Tests.MovementEvidenceCapture` (not run in CI):
Unity `6000.0.84f1`, host Debian 13 x86_64 under Xvfb, **Vulkan on Mesa lavapipe** (a CPU rasterizer,
`-force-vulkan -force-device-index 0`). Scene `Assets/Scenes/MovementTest.unity`, rendered at 1920x1080
into a render texture with the UI Toolkit touch-controls panel composited on top. The touch layout is
simulated at @2x (a 1920x1080-pixel phone), and touches are simulated through the Input System
(`Touchscreen` device + `TouchState` events), the same path a real touchscreen uses.

- `01-touch-stick-run.png`: a thumb down in the left third at (330, 280) px dragged up-right: the
  **floating stick** base appears where the thumb landed and the knob sits at the deflection
  (0.35, 0.94). The capsule runs forward-right (`gait=Run`, `verb=run`). Jump pad low-right, idle.
  Distance stripes every 1 A (every 5 A wide); 1 A = 0.1458 m at 1:12. (AT-5)
- `02-touch-jump-pad-running-jump.png`: a second thumb on the **jump pad** (72 pt, highlighted while
  held) 0.45 s earlier: the capsule is mid **running jump** (`verb=running-jump`, airborne, shadow below).
  (AT-5, AT-4)

Gamepad (AT-5): covered by the PlayMode test `Gamepad_DrivesTheIntentLayer` (a simulated Input System
`Gamepad`: left stick → run, south button → running jump). Touch: `Touch_FloatingStickAndJumpPad_DriveTheSameIntentLayer`.
Both feed the same `IntentAggregator`. The AT-5 **clip** (≤ 30 s, attached to the delivery, never committed)
and a real-device screenshot need an Owner iPhone with a Bluetooth controller: **not captured**.

Profiler / performance (AT-6): **not measured**. lavapipe frame times are not performance data; the
SPEC §6 check needs a TestFlight build on an Owner iPhone with the debug overlay (M0-UNITY-04).

Privacy: synthetic scene only (procedural floor, primitive capsule); no camera imagery, people, scans,
account names or device identifiers appear in any screenshot.
