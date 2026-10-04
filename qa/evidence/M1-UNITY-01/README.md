# M1-UNITY-01 evidence: splat room on a physical iPhone (AT-2, AT-3)

Standard: `qa/VISUAL_QA.md` (M0-QA-02). Captured by the Owner on **2026-10-04 (about 2:27 PM CT)** on his
**iPhone 14 (`iPhone14,7`, Apple A15 GPU, Metal, iOS 26.6.1)** with **internal-debug TestFlight build 50**
(`0.0.206 (0)`, overlay SHA `15257ef`, Unity `6000.0.84f1`), scene `SplatRoom`: Winchester Great Hall splat room
v2 (400,000 splats after the display prune, Tier B Metal-safe bitonic sort, render scale 0.7, SH order 1, MSAA/HDR off).
Screenshots are the Owner's own portrait captures (1170x2532), re-encoded losslessly as RGB PNGs to fit the 2 MB limit.

- `01-splat-room-v2-round-table-iphone-14.png`: the Round Table end, looking up at the table on the wall. Sharp
  table, correct back-to-front ordering, the capsule shaded normally (the build-48 black-character bug is fixed by
  the alpha-safe composite). The floor in front is the smeared low-coverage area. (AT-2)
- `02-splat-room-v2-off-capture-blobs-iphone-14.png`: the camera orbited towards an area the source video never
  looked at: white blown-out blobs and dark shapes (reconstruction gaps, not a sort error). Motivates the camera and
  play-area limits in the next build. (AT-2 context)
- `03-splat-room-v2-column-smear-iphone-14.png`: a column and the floor near it, smeared and over-bright; the
  character is in front of the splats and ordered correctly. (AT-2 context)
- `perf-report-iphone-14-build-50.txt`: the overlay's saved performance report (60 s window, 3,470 frames):
  **fps p50 60.0, avg 57.8, frame ms p50 16.7 / p99 33.4**, 400,000 splats, Tier B, render 0.70, 711 sorts issued,
  1,797 skipped while the camera was still, 67 dispatches per sort. (AT-3)

AT-2 verdict (Owner, verbal): no sort popping or ordering glitches while orbiting and walking; render confirmed. A
device video is the ticket's suggested evidence; the Owner's report plus these screenshots stand in for it.

Known issue in this report: `sort_every_nth_frame: 1` although the room asked for 2. Cause: the tier applier
re-applied the High tier's cadence (1) to the renderer after the Metal-safe sort parked the package sort, and the
sort adopts whatever the applier last wrote. Fixed after build 50 (the room's cadence now goes through
`SplatRenderSettingsApplier.sortEveryNthFrameOverride`); see `tickets/M1-UNITY-01.json`.

Profiler: not measured (no Unity Profiler session on the Owner's device; the overlay report above stands in, per
VISUAL_QA §4).

Clips: none.

**Privacy:** the evidence contains no faces, addresses, documents, or screens with personal data. Content: the
corpus room splat (Winchester Great Hall, CC BY 3.0 source video, no people visible), the placeholder capsule, and
the debug overlay (device model, build version and SHA only).
