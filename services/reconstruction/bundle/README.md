# Capture bundle v1.0: the capture → reconstruction contract (M1-CAPT-01)

This is what the app writes after a guided capture and uploads for reconstruction (SPEC §3.1,
`design/proposals/capture-ux-coaching-v1.md` §4). It shares one shape with a row of the corpus
manifest (`../corpus/manifest.schema.json`: mode, source, captured_on, device, duration_s, readiness,
coverage), so corpus and live scans follow one contract. **Raw media never enters git**: the fixtures here
are synthetic (no camera, no video, no depth files).

```
<scan_id>/
  manifest.json      capture_bundle.schema.json (JSON Schema 2020-12)
  frames.jsonl       one line per recorded frame ($defs/frame): index, time, camera-to-world pose
                     (column-major 4x4, ARKit world, metres, +Y up), tracking, sharpness, luma, accepted
  video.mov|mp4      HEVC/H.264, written with NO metadata track (no GPS, no EXIF, no location atoms)
  depth/<i>.bin      LiDAR only: float16 little-endian metres, depth.width x depth.height
```

## Rules beyond the schema

`tools/capture_bundle.py` checks what a schema can't express:

- the counts and the tracking fraction match `frames.jsonl`;
- frame indices and times increase;
- every pose is rigid (orthonormal, no reflection, last row `0 0 0 1`);
- passes tile the frames;
- the coverage map has the declared shape and matches `coverage.fraction`;
- depth is present exactly when the device has LiDAR;
- gravity opposes up;
- no key anywhere looks like location or identity data.

```
python services/reconstruction/tools/capture_bundle.py <bundle-dir> [--media]
```

## Who writes it

The Unity assembly `GJ.Capture` (`unity/Assets/GiganticJourneys/Capture/`) holds the platform-neutral
capture logic:

- the flow state machine (`CaptureSession`);
- the live coaching signals: `SpeedMeter`, `BlurGate`, `LightMeter`, `CoverageMap`, `ParallaxMeter`,
  `TrackingMeter`;
- the readiness score and its one kind line (`ReadinessScore`, `CoachingCopy`);
- `CaptureBundleWriter`.

The golden bundles in `fixtures/` are that writer's output. The EditMode test
`CaptureBundleWriterTests.MatchesTheGoldenBundle` keeps them byte-identical, and
`services/reconstruction/tests/test_capture_bundle.py` validates them against this contract. Change
either side and one of the two fails. Regenerate them with `GJ_WRITE_CAPTURE_GOLDEN=1` on an EditMode run
after an intended change.

## What the device adapter must do (not built yet)

The adapter depends on the AR stack decision: AR Foundation + the ARKit XR plugin, or a native plugin.
See `qa/reports/M1-CAPT-01.md`. Its job:

1. **Feed frames.** Each AR frame becomes a `CaptureFrame`: ARCamera transform, tracking state, a
   box-filtered ~160x120 luma image passed through `FrameMetrics.LaplacianVariance` / `MeanLuma`, and
   whether depth was captured. Report tracking to `ReportFramingTracking` while in Framing.
2. **Record video only in `Recording` / `Relocalizing`.** Pause the writer in every other state (the
   bundle's frame indices may skip; the times are video presentation times). Write no metadata track, and
   never request location permission.
3. **Write depth** (LiDAR devices) for the frames it flags, in float16 metres.
4. **Fill `CaptureBundleInfo`** from the session format and the camera intrinsics. The device model comes
   from `hw.machine` (e.g. `iPhone16,1`), **never** the user-visible device name. `CapturedOn` is local
   date only.
5. **Drive the locked UI** (DESIGN_SYSTEM §6) from `CaptureSession` state and `DrainCues()`: the
   coverage wash (AR-anchored), the ring (`RingProgress` / `RingAmber`), the speed arc (`Speed.Pace`),
   haptics, the low-light card, the missed-corner arrow (`Coverage.TryGetMissedCorner`), the gate's
   line (`GateMessage`), Upload anyway, and Retake.
6. **Hand the bundle to upload** (M1-CAPT-02). The server re-verifies the strip (SECURITY_CHECKLIST §4.4).
