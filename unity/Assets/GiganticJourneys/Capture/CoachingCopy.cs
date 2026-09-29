namespace GiganticJourneys.Capture
{
    /// <summary>
    /// The capture copy, one short line each. LOCKED lines are verbatim from DESIGN_SYSTEM §6 /
    /// capture-ux-coaching-v1 (AUTH #005, #025); PROVISIONAL lines need gj-design sign-off before
    /// they ship (and localisation keys once the string table exists).
    /// </summary>
    public static class CoachingCopy
    {
        /// <summary>LOCKED: after a full second of amber on the speed arc.</summary>
        public const string SlowDown = "Slow down a little";

        /// <summary>LOCKED: the low-light card.</summary>
        public const string TooDark = "Too dark here. Turn on a lamp?";

        /// <summary>LOCKED: the low-light card's action.</summary>
        public const string ContinueAnyway = "Continue anyway";

        /// <summary>LOCKED: the missed-corner arrow.</summary>
        public const string MissedCorner = "You missed this corner";

        /// <summary>LOCKED: missed-corner action that keeps recording.</summary>
        public const string GotIt = "Got it";

        /// <summary>LOCKED: always available at the missed-corner check and the gate.</summary>
        public const string UploadAnyway = "Upload anyway";

        /// <summary>LOCKED: past three minutes.</summary>
        public const string LongCapture = "Long captures rebuild worse";

        /// <summary>LOCKED (capture-ux §5): tracking loss.</summary>
        public const string Relocalize = "Point at a spot you've already scanned";

        /// <summary>LOCKED (capture-ux §2): room overlap coaching.</summary>
        public const string SweepBack = "Sweep back over what you've seen";

        /// <summary>LOCKED (capture-ux §2): tabletop keep-in-frame nudge.</summary>
        public const string KeepCentered = "Keep the build centered";

        /// <summary>LOCKED (capture-ux §2): room start.</summary>
        public const string RoomStart = "Stand in a doorway or corner and hold your phone up.";

        /// <summary>LOCKED (capture-ux §2): tabletop start.</summary>
        public const string TabletopStart = "Put the build in the middle and step back a little.";

        /// <summary>LOCKED (capture-ux §1, sentence-cased): framing / relocalize before recording.</summary>
        public const string Framing = "Move your phone to look around";

        /// <summary>LOCKED (capture-ux §5): downstream reconstruction failure, free retry.</summary>
        public const string ReconstructionFailed = "This one didn't come out — quick retake?";

        /// <summary>PROVISIONAL: tabletop parallax coaching (the script's "then one higher" circle).</summary>
        public const string TabletopSecondHeight = "One more slow circle, a little higher";

        /// <summary>The gate's one line for a weakness (null when there is nothing to coach).</summary>
        public static string ForWeakness(ReadinessWeakness weakness, CaptureMode mode)
        {
            switch (weakness)
            {
                case ReadinessWeakness.Coverage:
                    return MissedCorner;
                case ReadinessWeakness.Parallax:
                    return mode == CaptureMode.Room ? SweepBack : TabletopSecondHeight;
                case ReadinessWeakness.Sharpness:
                    return SlowDown;
                case ReadinessWeakness.Light:
                    return TooDark;
                case ReadinessWeakness.Tracking:
                    return Relocalize;
                case ReadinessWeakness.Duration:
                    return LongCapture;
                default:
                    return null;
            }
        }
    }
}
