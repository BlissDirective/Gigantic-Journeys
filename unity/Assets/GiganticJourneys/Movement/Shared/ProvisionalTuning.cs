namespace GiganticJourneys.Movement
{
    /// <summary>
    /// The ONLY place movement-adjacent numbers live outside movement.json, pending an AUTH.
    /// <para>Movement Bible §3.1/§3.3/§8 and DESIGN_SYSTEM decision 5 give these values, but
    /// <c>config/movement.json</c> (Bible §10) has no <c>intent</c> or <c>camera</c> section yet, and
    /// adding one is a protected change (DESIGN_SYSTEM decision 5: "added by AUTH when M1
    /// introduces it"). The proposed sections are filed at
    /// <c>governance/auth-requests/M0-UNITY-03-movement-json-intent-camera.md</c>; once approved,
    /// each constant here moves into movement.json + MovementConfig and this class is deleted.</para>
    /// <para>An EditMode test (MovementLiteralScanTests, M0-UNITY-03 AT-7) fails if a movement
    /// assembly source outside this file contains a tuning literal.</para>
    /// </summary>
    public static class ProvisionalTuning
    {
        /// <summary>Stick → gait bands and intent timings (Bible §3.1, §3.4, §2).</summary>
        public static class Intent
        {
            /// <summary>Walk below 40 % stick deflection (Bible §3.1).</summary>
            public const float WalkMaxStick = 0.40f;

            /// <summary>Jog from 40 % to 85 %; run above (Bible §3.1).</summary>
            public const float JogMaxStick = 0.85f;

            /// <summary>Run held this long becomes sprint (Bible §3.1).</summary>
            public const float SprintHoldSec = 1.5f;

            /// <summary>Airborne longer than this is a fall (Bible §3.4).</summary>
            public const float FallAfterSec = 0.35f;

            /// <summary>Trajectory prediction horizon (Bible §2 Intent layer).</summary>
            public const float TrajectoryHorizonSec = 0.6f;

            /// <summary>Stick deflection below this reads as no input (touch stick; the gamepad uses the Input System deadzone).</summary>
            public const float StickDeadzone = 0.1f;
        }

        /// <summary>Fixed follow camera (Bible §8; DESIGN_SYSTEM decision 5).</summary>
        public static class Camera
        {
            public const float FollowDistanceA = 4f;
            public const float HeightA = 1.6f;
            public const float LookAheadA = 0.8f;
            public const float RunDistanceBonusA = 0.5f;
            public const float RunFovBonusDeg = 4f;
            public const float BaseVerticalFovDeg = 60f;

            /// <summary>No vertical follow for the first 0.2 s of a jump (Bible §8).</summary>
            public const float JumpVerticalHoldSec = 0.2f;

            /// <summary>Smoothing time for distance/FOV/look-ahead/height changes (no Bible value; proposed).</summary>
            public const float BlendSec = 0.25f;
        }

        /// <summary>Character body data (roster rigs in M2; Bible §1 default avatar).</summary>
        public static class Body
        {
            /// <summary>Default avatar real height, meters (Bible §1).</summary>
            public const float DefaultRealHeightMeters = 1.75f;

            /// <summary>Capsule radius in A for the M0 stand-in (no Bible value; the roster rig defines it in M2).</summary>
            public const float CapsuleRadiusA = 0.15f;

            /// <summary>Character-controller skin width as a fraction of the radius (Unity guidance: 10 %).</summary>
            public const float SkinWidthOfRadius = 0.1f;
        }

        /// <summary>Environment defaults until M1-GAME-01 reads the environment spec.</summary>
        public static class Environment
        {
            /// <summary>1:12 (Bible §1).</summary>
            public const float DefaultScale = 12f;
        }

        /// <summary>Touch controls (DESIGN_SYSTEM decision 5; tokens arrive with M0-DSGN-02).</summary>
        public static class Touch
        {
            /// <summary>Floating stick lives anywhere in the left third of the screen.</summary>
            public const float StickZoneWidthFraction = 1f / 3f;

            /// <summary>Stick travel radius, points (play controls ≥ 56 pt).</summary>
            public const float StickRadiusPt = 56f;

            /// <summary>Jump pad diameter, points, low-right.</summary>
            public const float JumpPadPt = 72f;

            /// <summary>Jump pad inset from the safe-area corner, points.</summary>
            public const float JumpPadInsetPt = 32f;

            /// <summary>iOS points reference density (1 pt = 1 px at 163 dpi).</summary>
            public const float PointsReferenceDpi = 163f;

            /// <summary>Largest iPhone screen scale (@3x).</summary>
            public const float MaxPixelsPerPoint = 3f;

            /// <summary>Settings › Controls size slider range, points (DESIGN_SYSTEM decision 5: 56–96 pt).</summary>
            public const float ButtonSizeMinPt = 56f;
            public const float ButtonSizeMaxPt = 96f;

            /// <summary>Opacity slider: lowest idle opacity, and the default (~60 % scrim discs, decision 5).</summary>
            public const float OpacityMin = 0.2f;
            public const float OpacityDefault = 0.6f;

            /// <summary>Furthest a dragged control may move from its default anchor, points (the layout also clamps to the safe area).</summary>
            public const float DragOffsetMaxPt = 400f;
        }
    }
}
