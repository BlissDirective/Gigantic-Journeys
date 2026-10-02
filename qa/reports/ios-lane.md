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

## Owner follow-ups
- The icon is a **placeholder** (amber summit beam over an isometric room, on charcoal). gj-design should replace
  `AppIcon-1024.png` with the final mark. Keep it 1024×1024 RGB with no transparency.
- **Confirm the export-compliance answer.** `ITSAppUsesNonExemptEncryption=false` declares that the app uses only
  exempt (OS-provided) encryption. If that ever changes, flip it and file the annual self-classification.
- **Install build 40 on the iPhone** from TestFlight (internal group) to run the M0-UNITY-04 debug-overlay device
  check (three-finger tap, then Save report).

Note on the release item: builds 38 and 39 are release-flavor runs of the same `testflight` lane (push-triggered, both
uploaded). No separate release `workflow_dispatch` was run because it would have re-uploaded identical code.
