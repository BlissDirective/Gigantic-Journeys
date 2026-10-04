# iOS lane (ios-build.yml): TestFlight upload findings (M0-REPO-06 AT-3)

2026-10-02, gj-operator. Covers the first real `testflight` runs after the Owner installed the
Admin-role App Store Connect key (secrets replaced on 2026-09-29).

## Failing runs and root cause
| Run | Trigger | Result |
|---|---|---|
| 36577265750 | dispatch, internal-debug | Unity build, signing and export passed; **upload failed** (build 36) |
| 36760847904 | push, 2026-09-30 | same failure at the upload step (build 37) |

The fastlane `pilot` logs (jobs 109441862808 and 110052976346) show that the API key authenticated and the
app record exists (App Store Connect app id 6815794301), so no key, record or agreement problem. App Store Connect then
rejected the binary at validation with two **409** errors:
1. **SDK version issue.** The app was built with the iOS 17.5 SDK (the `macos-14` runner, Xcode 15.4). App Store Connect now
   requires apps to be built with the iOS 26 SDK or later.
2. **Missing app icon.** There was no 1024×1024 App Store icon in the asset catalog. The Unity project had no
   iOS icons assigned.

## Fixes (commit 65787409)
- `ios-build.yml`: macOS jobs default to `macos-26`. Every macOS job runs **"Select Xcode with the iOS 26+
  SDK"**, which picks the newest Xcode (or the optional repo variable `IOS_XCODE_APP`) and fails early with a clear
  message if the iphoneos SDK is below 26.
- A placeholder brand icon `unity/Assets/Art/AppIcon/AppIcon-1024.png` (opaque RGB, no alpha) is assigned to the
  default icon and every iOS slot in `ProjectSettings.asset`. The step **"App Store (1024 px, opaque) icon is in the
  Xcode project"** (`.github/scripts/ios_app_icon.py`, 6 pytest cases) fails the build before archiving if the
  exported asset catalog lacks it. EditMode tests `IosAppStoreIconIsAssignedAt1024` and
  `IosAppIconsAreAllAssigned` guard the project settings.
- The Info.plist step also sets `ITSAppUsesNonExemptEncryption = false`, so builds skip the per-build
  export-compliance prompt in App Store Connect (the app uses only OS-provided HTTPS).
- Follow-up commit 4d5aadc: the two icon EditMode tests read `ProjectSettings.asset` directly, because the unity-tests
  image has no iOS module, so `UnityEditor.iOS` failed to compile in run 37037914874. unity-tests 37040933185 is green.
- Build-number path confirmed: `CFBundleVersion` = the workflow run number (`PlistBuddy`), and each upload uses a
  fresh, monotonically increasing number. There were no collisions.

## Verified uploads
| Build | Run | Flavor | Result |
|---|---|---|---|
| **38** | 37036868207 (push of 6578740, release lane) | release | Xcode 26.6 / iphoneos SDK 26.5. "Successfully uploaded the new binary to App Store Connect", 2026-10-02 12:23 PM CT |
| **39** | 37040933103 (push of 4d5aadc, release lane) | release | uploaded 2026-10-02 12:55 PM CT |
| **40** | 37046098523 (workflow_dispatch on 686156b, lane=macos) | internal-debug | uploaded 2026-10-02 1:41 PM CT (TestFlight internal-testing-only, debug overlay included). This is the build for the M0-UNITY-04 on-device check |
| **41** | 37053104250 (push of 9b16f0f, release lane) | release | uploaded 2026-10-02 2:48 PM CT. First release build that includes the M0-UNITY-03 lockstep, the M1-UNITY-01 Metal-safe sort, the M1-GAME-01 loader and the M1-AVAT-01 roster/picker |
| **42** | 37080628299 (push of 7ea409b, release lane) | release | uploaded 2026-10-02 7:34 PM CT (Xcode 26.6 / iphoneos SDK 26.5). **First build with the Owner-selected final app icon** |
| **43** | 37082996930 (push of ab5c034) | release | cancelled (superseded by the launch-scene fix; still booted SampleScene) |
| **44** | 37084777722 (push of b14190d, release lane) | release | uploaded 2026-10-02 (green). **First build that boots into the playable MovementTest scene** (build index 0), with the final icon and the 60 fps cap |
| **45** | 37086752760 (workflow_dispatch on b14190d, lane=macos) | internal-debug | uploaded 2026-10-02 ~9:02 PM CT (green). MovementTest boot + debug overlay; Owner's next device check / perf report |
| **46** | 37132813101 (push of ca38c31, release lane) | release | uploaded 2026-10-03 10:45 AM CT (green). Release export check: SplatRoom scene absent, splat absent |
| **47** | 37134798525 (push of 2e479fc, release lane) | release | uploaded 2026-10-03 11:29 AM CT (green). Release export check: SplatRoom scene absent, splat absent |
| **48** | 37137079024 (workflow_dispatch on 83afba4 = code of 2e479fc, lane=macos, splat_url set) | internal-debug | uploaded 2026-10-03 12:01 PM CT (green; splat fetched and SHA-256 verified; export check: scene and splat present). **M1-UNITY-01 device-test splat room** (Winchester Great Hall, 780,004 splats): three-finger tap → **SplatRoom** button under Save report |
| **49** | 37165955870 (push of 3d07bae, release lane) | release | green, uploaded. Release export check: SplatRoom scene absent, splat absent; first release build with the touch orbit camera in MovementTest |
| **50** | 37167356135 (workflow_dispatch on 15257ef = code of 3d07bae, lane=macos, splat_url = v2 package) | internal-debug | uploaded 2026-10-03 8:36 PM CT (green; v2 package fetched, 400,000 splats, SHA-256 verified; export check: scene and splat present). **Splat room v2**: 400K pruned splats, alpha-safe composite (no black capsule), render scale 0.7 / SH 1 / motion-gated sort, touch orbit (drag right side, pinch zoom) |

## Owner follow-ups
- ~~The icon is a **placeholder**~~ **Done 2026-10-02:** the Owner selected the final app icon (white "GJ", a tiny figure
  leaping from an armchair toward a coffee table, amber glow on a dark room). It replaced `AppIcon-1024.png` at the same
  path and GUID, as 1024×1024 RGB with no transparency. See "Final app icon" below.
- **Confirm the export-compliance answer.** `ITSAppUsesNonExemptEncryption=false` declares that the app uses only
  exempt (OS-provided) encryption. If that ever changes, flip it and file the annual self-classification.
- **Install build 40 on the iPhone** from TestFlight (internal group) to run the M0-UNITY-04 debug-overlay device
  check (three-finger tap, then Save report).

Note on the release item: builds 38 and 39 are release-flavor runs of the same `testflight` lane (push-triggered, both
uploaded). No separate release `workflow_dispatch` was run because it would have re-uploaded identical code.

## Final app icon (2026-10-02)
The Owner selected the final icon on 2026-10-02. `unity/Assets/Art/AppIcon/AppIcon-1024.png` now holds the new master,
1024×1024 RGB with no alpha and square corners (iOS applies the mask). It was cropped from the Owner's 1152×1712 mockup to the
largest square inside the rounded corners and grey border (934 px), then upscaled with LANCZOS. The path, GUID
(`6b73e1a8…`) and import settings are unchanged (uncompressed, no mipmaps, alpha source None, max 1024), so every
`ProjectSettings.asset` icon slot and the EditMode icon guards still apply as before.

## Launch scene (2026-10-02)
Builds through 42 booted into `SampleScene`, an empty URP scene, which is what the build 40 device report shows. From the next
build on, **`Assets/Scenes/MovementTest.unity` is build index 0** (`ProjectIdentity.BootScenePath`, `EditorBuildSettings`).
It is the playable M0 movement scene: an orange capsule on a 12 m floor with 1 A distance stripes, a floating
touch stick in the left third of the safe area, a jump pad bottom-right, and the M0 fixed follow camera (it trails and
looks ahead automatically; touch camera orbit is M1). The debug overlay bootstraps independently of the scene
(`RuntimeInitializeOnLoadMethod(AfterSceneLoad)` on a DontDestroyOnLoad object), so the three-finger tap works there in
internal-debug builds. Guards: EditMode `BootSceneIsThePlayableMovementTestScene`, PlayMode
`BootScene_BuildIndexZero_IsPlayable` (build index 0 loads with TraversalController, TouchControlsView and FollowCamera).
`FrameRatePolicy` (ab5c034) caps mobile at 60 fps (SPEC §6), not the iOS default of 30.

## Device-test splat room (2026-10-03, M1-UNITY-01)
Internal-debug builds now carry `Assets/Scenes/DeviceTest/SplatRoom.unity`, appended to the build list on the
runner only (`ios_debug_flavor.py add-scene`). The overlay's new scene-switcher row reaches it. Boot is unchanged
(MovementTest, build index 0). The splat is not in git: the dispatch input `splat_url` carries a ≤15 min signed URL
to the private staging bucket, minted by gj-operator right before dispatch. CI masks it, verifies its SHA-256 and
unpacks it into a gitignored Resources folder. A dispatch without it still builds, and the room then reports "splat not
in this build". The step "Device-test scene and splat only in the internal-debug flavor" checks the exported player
data, so release builds fail if either one leaks in. Details: `qa/reports/M1-ios-splat-render.md`.

## Splat room v2 (2026-10-03, M1-UNITY-01)
After the Owner's check of build 48 (20–23 fps, floaters, black capsule), the internal-debug splat room got a pruned
400K-splat package (`splat-room-unity-v2-400k.tar.gz`, new size/sha pin), an alpha-safe splat composite, a device perf
profile and a touch-orbit follow camera. **Orbit controls (also in MovementTest):** drag one finger anywhere outside the
left-third stick zone and the jump pad to orbit (left/right = yaw, up/down = pitch, clamped); pinch with two fingers to
zoom (0.5–2.5×). Taps (under 10 pt of movement) never turn the view, and the three-finger overlay tap is left alone.
The stick walks in the direction the camera faces. Details: `qa/reports/M1-ios-splat-render.md`.
