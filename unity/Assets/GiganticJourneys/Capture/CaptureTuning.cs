namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Every capture-coaching number in one place (M1-CAPT-01). Values marked LOCKED come from
    /// DESIGN_SYSTEM §6 (AUTH #005); the rest are PROVISIONAL starting points for the quality
    /// gate (capture-ux-coaching-v1 §3), to be tuned on the Owner's device against the corpus
    /// (reconstruction outcome vs readiness score) and then frozen by gj-capture.
    /// </summary>
    public static class CaptureTuning
    {
        /// <summary>Progress ring and Done (DESIGN_SYSTEM §6 "Progress and timing").</summary>
        public static class Timing
        {
            /// <summary>LOCKED: the ring fills over 90 s, a target not a limit.</summary>
            public const float RingTargetSec = 90f;

            /// <summary>LOCKED: past three minutes the ring turns amber ("Long captures rebuild worse").</summary>
            public const float LongCaptureSec = 180f;

            /// <summary>LOCKED: Done appears at 60 % coverage or 60 s, whichever comes first.</summary>
            public const float DoneCoverage = 0.60f;

            /// <summary>LOCKED: see <see cref="DoneCoverage"/>.</summary>
            public const float DoneSec = 60f;

            /// <summary>LOCKED: the preview before upload shows the last 5 s.</summary>
            public const float PreviewSec = 5f;
        }

        /// <summary>Speed arc (DESIGN_SYSTEM §6 "Speed").</summary>
        public static class Speed
        {
            /// <summary>PROVISIONAL: room walkthrough, fastest good linear pace (m/s).</summary>
            public const float RoomMaxLinear = 0.60f;

            /// <summary>PROVISIONAL: tabletop orbit, fastest good linear pace (m/s); the phone is closer to the subject.</summary>
            public const float TabletopMaxLinear = 0.35f;

            /// <summary>PROVISIONAL: fastest good turn rate (deg/s) in either mode.</summary>
            public const float MaxAngularDeg = 60f;

            /// <summary>PROVISIONAL: smoothing time constant of the speed estimate (s).</summary>
            public const float SmoothingSec = 0.25f;

            /// <summary>LOCKED: "Slow down a little" appears after a full second of amber.</summary>
            public const float SlowDownHintAfterSec = 1.0f;
        }

        /// <summary>Blur rejection (DESIGN_SYSTEM §6 "Blur and low light").</summary>
        public static class Blur
        {
            /// <summary>PROVISIONAL: a frame is blurred below this share of the recent median sharpness.</summary>
            public const float RelativeThreshold = 0.35f;

            /// <summary>PROVISIONAL: absolute floor on Laplacian variance (0–255 luma), catches a uniformly soft start.</summary>
            public const float AbsoluteFloor = 12f;

            /// <summary>PROVISIONAL: frames in the running-median window.</summary>
            public const int MedianWindow = 31;
        }

        /// <summary>Low light (DESIGN_SYSTEM §6 "Blur and low light").</summary>
        public static class Light
        {
            /// <summary>PROVISIONAL: mean luma (0–1) under which a frame counts as dark.</summary>
            public const float DarkLuma = 0.16f;

            /// <summary>PROVISIONAL: the low-light card shows after this long in the dark (s), once per session.</summary>
            public const float CardAfterSec = 1.5f;

            /// <summary>PROVISIONAL: median luma that scores 0 for the light component.</summary>
            public const float ScoreZeroLuma = 0.08f;

            /// <summary>PROVISIONAL: median luma that scores 1 for the light component.</summary>
            public const float ScoreFullLuma = 0.28f;
        }

        /// <summary>Coverage map (DESIGN_SYSTEM §6 "Coverage", "Missed corner").</summary>
        public static class Coverage
        {
            /// <summary>PROVISIONAL: room view-sphere azimuth bins (15° each).</summary>
            public const int RoomAzimuthBins = 24;

            /// <summary>PROVISIONAL: room view-sphere elevation bins.</summary>
            public const int RoomElevationBins = 6;

            /// <summary>PROVISIONAL: lowest room view elevation mapped (deg; floor under furniture).</summary>
            public const float RoomElevationMinDeg = -60f;

            /// <summary>PROVISIONAL: highest room view elevation mapped (deg; tops of shelves).</summary>
            public const float RoomElevationMaxDeg = 60f;

            /// <summary>PROVISIONAL: tabletop orbit azimuth bins (20° each).</summary>
            public const int OrbitAzimuthBins = 18;

            /// <summary>PROVISIONAL: tabletop height bands, low and high (the orbital script's two heights).</summary>
            public const int OrbitElevationBins = 2;

            /// <summary>PROVISIONAL: lowest camera elevation above the build centre (deg).</summary>
            public const float OrbitElevationMinDeg = -10f;

            /// <summary>PROVISIONAL: highest camera elevation above the build centre (deg).</summary>
            public const float OrbitElevationMaxDeg = 70f;

            /// <summary>PROVISIONAL: accepted frames needed before a bin paints.</summary>
            public const int FramesToPaint = 2;
        }

        /// <summary>Overlap / parallax: camera-position spread (capture-ux-coaching-v1 §3).</summary>
        public static class Parallax
        {
            /// <summary>PROVISIONAL: RMS distance of room camera positions from their centroid that scores 1 (m).</summary>
            public const float RoomTargetSpread = 0.75f;

            /// <summary>PROVISIONAL: same for the tabletop orbit (m).</summary>
            public const float TabletopTargetSpread = 0.25f;
        }

        /// <summary>Tracking continuity (capture-ux-coaching-v1 §5).</summary>
        public static class Tracking
        {
            /// <summary>PROVISIONAL: tracking not normal for longer than this pauses coaching and asks to relocalize (s).</summary>
            public const float RelocalizeAfterSec = 0.5f;
        }

        /// <summary>Readiness score (SPEC §3.1 quality gate; AUTH #025).</summary>
        public static class Readiness
        {
            /// <summary>PROVISIONAL weights; they sum to 1.</summary>
            public const float WeightCoverage = 0.35f;

            /// <summary>See <see cref="WeightCoverage"/>.</summary>
            public const float WeightParallax = 0.20f;

            /// <summary>See <see cref="WeightCoverage"/>.</summary>
            public const float WeightSharpness = 0.20f;

            /// <summary>See <see cref="WeightCoverage"/>.</summary>
            public const float WeightLight = 0.15f;

            /// <summary>See <see cref="WeightCoverage"/>.</summary>
            public const float WeightTracking = 0.10f;

            /// <summary>PROVISIONAL bars: a component under its bar is a weakness the gate coaches on.</summary>
            public const float BarCoverage = 0.60f;

            /// <summary>See <see cref="BarCoverage"/>.</summary>
            public const float BarParallax = 0.50f;

            /// <summary>See <see cref="BarCoverage"/>.</summary>
            public const float BarSharpness = 0.70f;

            /// <summary>See <see cref="BarCoverage"/>.</summary>
            public const float BarLight = 0.50f;

            /// <summary>See <see cref="BarCoverage"/>.</summary>
            public const float BarTracking = 0.90f;
        }
    }
}
