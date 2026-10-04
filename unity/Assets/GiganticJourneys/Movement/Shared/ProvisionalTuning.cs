namespace GiganticJourneys.Movement
{
    /// <summary>
    /// The ONLY place movement-adjacent numbers live outside movement.json: character body data
    /// (roster rigs, M2), the environment default (environment spec, M1-GAME-01), and touch-control
    /// layout (design tokens, M0-DSGN-02) — none of them movement tuning, so none belong in
    /// <c>config/movement.json</c>. The stick/intent and follow-camera numbers moved into
    /// movement.json <c>intent</c> / <c>camera</c> under AUTH #036 (MovementConfig.Intent / .Camera).
    /// <para>An EditMode test (MovementLiteralScanTests, M0-UNITY-03 AT-7) fails if a movement
    /// assembly source outside this file contains a tuning literal.</para>
    /// </summary>
    public static class ProvisionalTuning
    {
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

        /// <summary>
        /// Touch / gamepad camera orbit (Bible §8 lists orbit for M1; movement.json has no orbit
        /// numbers yet, so these stay provisional and outside the AUTH-gated constants).
        /// </summary>
        public static class CameraOrbit
        {
            /// <summary>Yaw per point of one-finger drag.</summary>
            public const float YawDegPerPt = 0.3f;

            /// <summary>Pitch per point of one-finger drag (drag up looks down from higher).</summary>
            public const float PitchDegPerPt = 0.22f;

            /// <summary>Movement before a drag starts orbiting, so taps on buttons never turn the view.</summary>
            public const float DeadzonePt = 10f;

            /// <summary>Camera elevation above the look-at point, clamped (degrees).</summary>
            public const float MinElevationDeg = -10f;
            public const float MaxElevationDeg = 75f;

            /// <summary>Pinch zoom range as a multiple of the follow distance.</summary>
            public const float MinZoom = 0.5f;
            public const float MaxZoom = 2.5f;

            /// <summary>Gamepad right-stick orbit speed.</summary>
            public const float GamepadYawDegPerSec = 150f;
            public const float GamepadPitchDegPerSec = 90f;

            /// <summary>Right-stick magnitude below which the gamepad does not orbit.</summary>
            public const float GamepadDeadzone = 0.2f;

            /// <summary>Touches the debug overlay's toggle uses; at this many fingers the orbit steps aside.</summary>
            public const int OverlayTapFingers = 3;

            /// <summary>Lowest the eye may get above the ground under the character (m), looking up.</summary>
            public const float EyeAboveGroundM = 0.02f;

            /// <summary>View-yaw half range meaning "no yaw limit" (a full turn either way).</summary>
            public const float FreeYawHalfRangeDeg = 180f;

            /// <summary>Radius of the sphere cast that pulls the camera in front of colliders (m).</summary>
            public const float CollisionRadiusM = 0.15f;
        }
    }
}
