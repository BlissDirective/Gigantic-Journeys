using System.Collections.Generic;
using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Deterministic stand-in for the ARKit frame stream (tests and Editor demos; no device, no
    /// camera, no user imagery). Generates a room walkthrough (a chest-height arc that sweeps the
    /// view around the room at six heights) or a tabletop orbit (circles around
    /// a build at two heights), with optional faults: too fast, a blur burst, darkness, tracking loss.
    /// </summary>
    public sealed class SyntheticCapture
    {
        /// <summary>Frames per second of the stream.</summary>
        public float Fps = 30f;

        /// <summary>Stream length (s).</summary>
        public float Seconds = 75f;

        /// <summary>Multiplies the motion speed (1 = a good pace).</summary>
        public float SpeedFactor = 1f;

        /// <summary>Fraction of the full sweep performed (room: of 360° view; tabletop: of the two circles).</summary>
        public float SweepFraction = 1f;

        /// <summary>Sharpness of a good frame.</summary>
        public float GoodSharpness = 180f;

        /// <summary>Luma of a normally lit frame.</summary>
        public float GoodLuma = 0.45f;

        /// <summary>Seconds [start, end) with blurred frames (none when start &gt;= end).</summary>
        public Vector2 BlurWindow = new Vector2(-1f, -1f);

        /// <summary>When &gt; 1, every Nth frame is blurred (a shaky hand), throughout.</summary>
        public int BlurEveryNth;

        /// <summary>Seconds [start, end) that are dark.</summary>
        public Vector2 DarkWindow = new Vector2(-1f, -1f);

        /// <summary>Seconds [start, end) with tracking limited.</summary>
        public Vector2 TrackingLossWindow = new Vector2(-1f, -1f);

        /// <summary>True when frames carry depth (every 3rd frame, like a LiDAR device at 10 Hz depth over 30 fps video).</summary>
        public bool Depth;

        /// <summary>Tabletop build centre.</summary>
        public Vector3 BuildCentre = new Vector3(0.3f, 0.75f, 1.2f);

        /// <summary>Generates the frames for the mode.</summary>
        public List<CaptureFrame> Generate(CaptureMode mode)
        {
            int count = Mathf.Max(1, Mathf.RoundToInt(Seconds * Fps));
            var frames = new List<CaptureFrame>(count);
            for (int i = 0; i < count; i++)
            {
                float t = i / Fps;
                float u = Mathf.Clamp01(t / Seconds * SpeedFactor) * SweepFraction;
                Pose(mode, u, out var position, out var rotation);
                bool blurred =
                    InWindow(t, BlurWindow) || (BlurEveryNth > 1 && i % BlurEveryNth == 1);
                bool dark = InWindow(t, DarkWindow);
                bool lost = InWindow(t, TrackingLossWindow);
                frames.Add(
                    new CaptureFrame(
                        i,
                        t,
                        position,
                        rotation,
                        lost ? TrackingQuality.Limited : TrackingQuality.Normal,
                        blurred ? GoodSharpness * 0.1f : GoodSharpness * (0.9f + 0.2f * Hash(i)),
                        dark ? 0.06f : GoodLuma,
                        Depth && i % 3 == 0
                    )
                );
            }

            return frames;
        }

        private void Pose(CaptureMode mode, float u, out Vector3 position, out Quaternion rotation)
        {
            if (mode == CaptureMode.Room)
            {
                // Walk a 2 m arc along one side of the room while the view turns six full circles,
                // one per 20° band from looking down at the floor (-50°) to up at the shelves (+50°);
                // each tilt eases over a fifth of a turn so the motion stays calm.
                float turns = 6f * u;
                float pitch = -50f;
                for (int band = 1; band < 6; band++)
                {
                    pitch += 20f * Mathf.SmoothStep(0f, 1f, (turns - band + 0.1f) / 0.2f);
                }

                position = new Vector3(Mathf.Sin(u * Mathf.PI) * 1.2f, 1.35f, u * 2f - 1f);
                rotation = Quaternion.Euler(-pitch, turns * 360f, 0f);
                return;
            }

            // Tabletop: a low circle, then a higher one (two heights), always looking at the build.
            float laps = 2f * u;
            float azimuth = laps * 360f * Mathf.Deg2Rad;
            float elevation =
                Mathf.Lerp(10f, 45f, Mathf.SmoothStep(0f, 1f, (laps - 0.9f) / 0.2f))
                * Mathf.Deg2Rad;
            const float radius = 0.45f;
            position =
                BuildCentre
                + new Vector3(
                    radius * Mathf.Cos(elevation) * Mathf.Sin(azimuth),
                    radius * Mathf.Sin(elevation),
                    radius * Mathf.Cos(elevation) * Mathf.Cos(azimuth)
                );
            rotation = Quaternion.LookRotation(BuildCentre - position, Vector3.up);
        }

        private static bool InWindow(float t, Vector2 window) =>
            window.x < window.y && t >= window.x && t < window.y;

        private static float Hash(int i)
        {
            unchecked
            {
                uint h = (uint)i * 2654435761u;
                h ^= h >> 13;
                return (h & 0xFFFF) / 65535f;
            }
        }
    }
}
