# iPhone Duo research spike: what iOS 27 exposes to a Unity app (M1-DUO-01)

2026-09-29 · gj-operator (overnight worker, drafted for gj-gameplay) · **Desk research only.** There is no Duo
device or iPhone Duo simulator on the Linux build box; the simulator ships with Xcode 27.1 on macOS. The
feature track stays optional and additive: the app must be complete and equal in value on every iPhone
(SPEC §11, AUTH #003).

**Source quality.** Apple's own pages (the iOS 27.1 SDK reference and the Tech Talks 111463–111465) are
behind developer.apple.com and weren't fetched directly. The API names below come from an Apple-docs
mirror and several independent developer write-ups that quote the SDK and the Tech Talks, and they agree
with each other. **Re-verify every name against the Xcode 27.1 SDK headers before building.** All sources
were retrieved on 2026-09-29.

## 1. Fold posture and hinge angle (AT-1)

- **APIs (iOS 27.1):** SwiftUI `onHingeChange(isEnabled:_:)` delivers `DeviceHingeContext` →
  `hinge: DeviceHinge?` with `angle` (an `Angle`, 180° when flat) and `status` (`.closed`,
  `.partiallyOpen`, `.fullyOpen`). UIKit `UIHingeInteraction` has an update handler; `UIHinge.angle` is a
  `CGFloat` in radians and its status adds `.unknown`. On non-foldables `hinge` is `nil`. [1][2][3][4]
- **Events and latency:** the handler runs once with the initial state and again on every change. **The
  update rate and precision are "system policy" and undocumented**, and Apple doesn't document the angle
  range. Nobody has published a latency figure; the write-ups advise against mapping absolute angles to
  frames. [2][3]
- **Apple's rule:** the hinge is for **interactions and effects, never layout**. Layout uses **reserved
  regions** (`reservedRegions(kind: .division | .occlusion)`, SwiftUI geometry proxy / `UIView`; the fold
  division is active only when partly folded, and the simulator observed it at 40 pt wide) and
  **arrangements** (`ArrangementView` / `UIArrangementViewController`). [1][3][4][5]
- **Postures:** closed portrait, closed landscape, open vertical, open horizontal, plus the partly folded
  book and tent. [4] The stand (about 90°) posture the M3-DUO-01 layout needs corresponds to
  `status == .partiallyOpen` with the angle near 90°, together with the horizontal division region.

## 2. Unity 6 support (AT-1)

- **No first-party Unity binding** for the hinge, reserved regions or arrangements. Reading them needs a
  **native iOS plugin**: Swift or Objective-C behind a C ABI, called through `[DllImport("__Internal")]`,
  following Unity's native-plugin sample. The UIKit side (`UIHingeInteraction`,
  `UIView.reservedRegions`) is reachable from Objective-C, so the plugin can attach to Unity's root view. [6][7][1]
- **What works without a plugin:** `Screen.safeArea` (use it as a rect, because left and right insets now
  differ) and polling `Screen.width/height` for changes. [6]
- **What breaks:**
  - Sizes, canvas scalers and input regions cached in `Start()` go stale, because the resolution changes
    mid-play on fold, unfold and Split View. **Relevant to us:** `TouchLayout` (M0-UNITY-03) must recompute
    stick and jump-pad rects when the screen size changes. That becomes a BACKLOG item.
  - Pausing only on `OnApplicationPause`: folding can move the app between displays without backgrounding
    it.
  - Critical HUD in the centre of the inner display lands on the fold. [6]

## 3. Split View and display changes (AT-1)

- iPhone Duo brings Split View (two apps side by side) and multiple windows of one app, and **every app
  participates**. New windows open only on the inner display. [4]
- For a Unity app this appears as **resolution and aspect changes while running**: the inner display is
  about 1.42:1 against the roughly 2.17:1 most phone games are tuned for; Split View is half-width with
  asymmetric insets; the size class is regular×regular on the inner display and compact on the outer. The
  inner display **does not honour supported interface orientations**, so orientation callbacks can't be
  used as a layout signal and size and safe-area changes must be used instead. [4][6]
- Apple's game guidance, as reported: a game may lock portrait or landscape but must fill the screen as the
  pose changes; prefer changing the aspect over letterboxing; if bars are unavoidable, fill them with
  artwork. [6]
- Build requirement: only the **iOS 27.1 SDK** gets full edge-to-edge on the inner display (older SDKs
  letterbox). That is our Xcode version in `ios-build.yml` on the macOS lane. [4]

## 4. Rendering to the outer display while folded ("Duo Preview") (AT-1)

- **While folded,** the outer display *is* the app's display. Nothing special is needed; it behaves like a
  compact iPhone screen. [4]
- **Both displays at once** (inner display for the main UI, outer display for supplementary content) goes
  through **scene accessories**:
  - `sceneAccessory(content:)` (iOS 27.0, originally for external displays).
  - The Duo-specific **`CameraCaptureAccessory`**, presented **only while the app is in the foreground,
    full-screen on the inner display, with a camera capture session running**. The system can toggle it at
    any time (folding removes it), so `onAvailabilityChange` must drive the UI.
  - It is **SwiftUI-only**; a UIKit app falls back to a second `UIWindow` on another `UIWindowScene`
    with external-display semantics. [8][9][10][11]
- **Open question for Unity:** whether an ARKit `ARSession` (which owns its own capture pipeline) counts as
  "a capture session running" for `CameraCaptureAccessory`. Nothing published answers this. It decides
  whether outer-display capture coaching is possible without dropping ARKit. It needs a device or
  simulator test.

## 5. Apple Pencil in Unity (for later) (AT-1)

Apple Pencil support on the Duo arrives later in 2026 (`design/proposals/iphone-duo-track.md` §1). In Unity
the Input System's `Pen` device (pressure, tilt, barrel button) is the path on iPad today and should carry
over. There's no v1 feature that uses it, so it stays deferred.

## 6. Feasibility per selected feature (AT-2)

| Ticket | Feature | Call | Effort | Stopping risk |
|---|---|---|---|---|
| **M3-DUO-01** | Stand-mode console layout: upper half photo, lower half controls | **Needs a native plugin** (a small one): hinge status + angle and the division region, exposed to C# through `UIHingeInteraction` + `UIView.reservedRegions`. The rest is Unity (camera viewport split, HUD relayout on resize). | ~3–5 dev-days: plugin 1–2, layout 2–3, plus simulator QA | Hinge update rate is "system policy"; if updates lag, posture switching feels late. Mitigation: switch layout on `status` + the division region (layout APIs), never on raw angle (which follows Apple's rule anyway). |
| **M3-DUO-02** | Unfold triggers the signature transition across outer → inner | **Feasible in Unity + a tiny plugin.** Detect `.closed` → open via the hinge status, or simply a display change plus the resolution jump, which Unity already sees. Play the existing transition. | ~2–3 dev-days once the decision-3 transition exists | The app moves displays **without** backgrounding, so the transition must start from the resize event. The render surface may briefly letterbox or stretch mid-change; the first frames need testing on a device. |
| **M2-DUO-01** | Rear-camera **avatar** capture with outer-display framing | **Obsolete as written.** AUTH #020 removed avatar capture from v1 (pre-made characters, no biometric). | — | Recommend the Owner **cancel or reframe** it. A natural reframe is **outer-display room-capture coaching** (the subject-facing screen is less useful for rooms, but a tent-mode tabletop capture could use it). That hinges on the §4 ARKit question and on `CameraCaptureAccessory` being SwiftUI-only, which means a SwiftUI host view inside the Unity app. High effort (~1–2 weeks) and uncertain. |

**Cross-cutting (applies to all iPhones in effect and is cheap):** handle mid-session resolution changes
(`TouchLayout`, camera aspect, UI Toolkit scale) and keep critical HUD away from the centre of the inner
display. Recommend a small M1/M3 ticket, "resize-safe HUD and touch layout", independent of the Duo
features.

## 7. Prototype (AT-3, suggested): not done

A throwaway scene that logs posture and Split View resizes needs the iPhone Duo simulator (Xcode 27.1,
macOS) or a device. Neither is available to the Linux build box. The macOS CI runner could build it, but it
can't drive the simulator's fold controls unattended. Recommended as a hands-on task once a Mac session or
device is available (Owner).

## Sources (retrieved 2026-09-29)

1. Dodecaidr, "The Hinge as a Sensor: iPhone Duo Hinge and Camera APIs": https://dodecaidr.pro/en/articles/iphone-duo-hinge-camera-api/ (cites Tech Talks 111463–111465)
2. BleepingSwift, "Reading the iPhone Duo Hinge Angle with onHingeChange in SwiftUI": https://bleepingswift.com/blog/onhingechange-hinge-angle-swiftui
3. A. Novichkov, "iPhone Duo by Examples" (SwiftUI samples, iOS 27.1; simulator observations): https://github.com/artemnovichkov/iPhone-Duo-by-Examples
4. DEV Community, "iPhone Duo for iOS Developers: What Actually Changes in Your Swift Code" (2026-09-09): https://dev.to/arshtechpro/iphone-duo-for-ios-developers-what-actually-changes-in-your-swift-code-5gc5
5. ZipLyne, "iPhone Duo for Developers: Screen Sizes, Layout Rules, and the New APIs": https://ziplyne.agency/blog/iphone-duo-for-developers-screen-sizes-layout-rules-and-the-new-apis
6. iPhone Duo Support, "Unity on iPhone Duo": https://iphoneduosupport.com/frameworks/unity/
7. Unity Manual, native plug-in example for iOS (6000.x): https://docs.unity3d.com/6000.6/Documentation/Manual/ios-native-plugin-bonjour-sample.html
8. Apple Developer documentation (mirror), `sceneAccessory(content:)`: https://apple-docs.everest.mt/docs/swiftui/view/sceneaccessory(content:)/
9. iPhone Duo Support, "Consider scene accessories to use both displays at once": https://iphoneduosupport.com/checklist/scene-accessories-camera/
10. BleepingSwift, "Building a Teleprompter for iPhone Duo's Outer Display with CameraCaptureAccessory": https://bleepingswift.com/blog/cameracaptureaccessory-iphone-duo-teleprompter (iPhone Duo on sale October 23)
11. sunyazhou, "Adapting Apps to iPhone Duo in iOS 27: Six New APIs, Swift vs. Objective-C" (2026-09): https://www.sunyazhou.com/en/2026/09/adapting-apps-to-iphone-duo-in-ios-27/
