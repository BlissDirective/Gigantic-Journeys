# M1-CAPT-01: guided capture core and the capture → reconstruction contract

2026-09-29, gj-operator (overnight worker, acting for gj-capture).

**Built:** the device-independent core of the capture flow, plus the upload contract.

**Blocked:**
- the ARKit adapter and the on-screen UI, which wait on the AR stack decision;
- the device evidence, which waits on TestFlight, i.e. the Admin-role ASC key.

Nothing here touches a camera, a real scan or the network.

## What was built

| Piece | Where |
|---|---|
| Upload contract v1.0 (JSON Schema 2020-12) and README | `services/reconstruction/bundle/capture_bundle.schema.json`, `bundle/README.md` |
| Bundle validator: schema, cross-field and privacy rules, `--media` | `services/reconstruction/tools/capture_bundle.py` |
| Golden bundles written by the Unity writer (room with LiDAR, tabletop without) | `services/reconstruction/bundle/fixtures/` |
| Flow state machine (Framing → Recording ⇄ Relocalizing / Interrupted → MissedCornerCheck → QualityGate → Preview → Confirmed) | `unity/Assets/GiganticJourneys/Capture/CaptureSession.cs` |
| Live signals | `SpeedMeter`, `BlurGate` + `FrameMetrics` (Laplacian variance, mean luma), `LightMeter`, `CoverageMap` (room view-sphere; tabletop orbit around a least-squares build centre; missed-corner search), `ParallaxMeter`, `TrackingMeter` |
| Readiness score + weakest signal + one kind line | `ReadinessScore`, `CoachingCopy` |
| Deterministic writer | `CaptureBundleWriter` (manifest.json + frames.jsonl; invariant culture; no location field) |
| Synthetic frame stream for tests | `SyntheticCapture` |
| Every number, marked LOCKED (DESIGN_SYSTEM §6) or PROVISIONAL | `CaptureTuning` |

## Tests

- **Unity EditMode:** 134/134 passed locally (Unity 6000.0.84f1, `-batchmode -nographics`). 39 of them are
  the new capture tests: `CaptureMetersTests`, `CaptureSessionTests`, `CaptureBundleWriterTests`.
  Results: `qa/reports/M1-CAPT-01/editmode-results.xml`. The capture code is EditMode-only logic, so
  PlayMode is unchanged.
- **pytest:** 23 tests in `services/reconstruction/tests/test_capture_bundle.py`. They validate both
  golden bundles, then run one mutation per rule (a GPS key, a location key in a frame, a time of day, a
  scaled pose, a mirrored pose, the counts, the passes, the coverage fraction and shape, depth without
  LiDAR, gravity, media files, the CLI).
- **The C# writer is tied to the contract:** the EditMode golden test keeps the fixtures byte-identical
  to the writer's output, and the Python test validates the same files.

## Acceptance tests

| AT | Status | Notes |
|---|---|---|
| AT-1 bundle with poses, intrinsics, depth, gravity, scale, mode, readiness, coverage map, matching the upload contract; a real-room session makes a valid bundle | **Contract + writer done; real-room run pending** | The shape is defined, written and validated. Coverage and readiness share the corpus-manifest shape. A real room needs the ARKit adapter and a device. |
| AT-2 coverage feedback, speed meter, blur rejection, missed-corner hint, driven by the capture | **Logic done; UI pending** | Covered by tests: speed amber + one haptic + "Slow down a little" after 1 s; blur rejection that a blurry burst can't game; coverage fraction with Done at 60 % / 60 s; the missed-corner direction points at the unseen side (room) or the unseen height (tabletop). The on-screen wash, arc, ring and arrow need the AR layer. |
| AT-3 on-device readiness score (coverage, parallax, blur, light, tracking), kind warnings, never hard-stops, retake, no crash | **Logic done** | Weighted score + weakest signal → one line (e.g. "Too dark here. Turn on a lamp?"). Upload anyway is always available at the check and the gate. Retake/Start over keep the mode. A user action in the wrong state returns false; it never throws (tested). |
| AT-4 GPS/EXIF stripped on device; no location in the bundle | **Bundle side done; video strip pending** | The manifest has no field for a location, the date carries no time, the device is a model id, and the validator rejects location-like keys anywhere. The video writer (native) must write no metadata track; that needs a device check. |
| AT-5 active capture < 90 s on the Owner's iPhone (suggested) | **Needs the device** | The ring targets 90 s; `ActiveSeconds` excludes pauses. |
| AT-6 tracking loss relocalizes and keeps coverage; interruption offers Resume / Start over; free retry after a downstream failure; one-time first-run coach-through | **Logic done; device check pending** | Tested: coverage is kept and not painted while lost, and relocalizing starts a new pass. Resume adds a new pass and the pause isn't active time; Start over clears but keeps the mode. `RetryAfterReconstructionFailure` keeps the mode and shows the kind line. The first-run cue fires once. |

## Decisions and follow-ups

1. **AR stack (Owner / Coordinator decision, probably an ADR addendum like #035):** AR Foundation 6 +
   Apple ARKit XR Plugin (Unity-supported, free), or a small native ARKit plugin. Recommendation: AR
   Foundation for poses, tracking, depth and the camera image, with a native AVAssetWriter for the video,
   so the metadata track is under our control. Nothing was added to `Packages/manifest.json`.
2. **PROVISIONAL tuning** (speed limits, blur ratio, light thresholds, readiness weights and bars) should
   be calibrated against the corpus: readiness score vs reconstruction outcome, with M1-CAPT-04's
   predictor.
3. **One PROVISIONAL line of copy** needs gj-design sign-off: tabletop parallax, "One more slow circle, a
   little higher".
4. The map is a platform-neutral grid (view directions / orbit positions). The on-device wash that paints
   real surfaces from the ARKit mesh is the adapter's job; the grid is what the bundle records.
