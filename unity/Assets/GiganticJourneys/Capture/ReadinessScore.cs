using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>The signal the quality gate coaches on.</summary>
    public enum ReadinessWeakness
    {
        /// <summary>Every component cleared its bar.</summary>
        None,

        /// <summary>Too little of the space seen.</summary>
        Coverage,

        /// <summary>Too little baseline between views.</summary>
        Parallax,

        /// <summary>Too many blurred frames.</summary>
        Sharpness,

        /// <summary>Too dark.</summary>
        Light,

        /// <summary>Tracking dropped too often.</summary>
        Tracking,

        /// <summary>Everything cleared but the capture ran past three minutes.</summary>
        Duration,
    }

    /// <summary>
    /// The on-device reconstruction-readiness score (SPEC §3.1 quality gate; AUTH #025): a weighted
    /// blend of five 0–1 components plus the weakest one. Advisory only: the gate never hard-stops
    /// ("Upload anyway" is always available).
    /// </summary>
    public readonly struct ReadinessScore
    {
        /// <summary>Coverage component (the painted fraction).</summary>
        public readonly float Coverage;

        /// <summary>Parallax component.</summary>
        public readonly float Parallax;

        /// <summary>Sharpness component (share of frames accepted by the blur gate).</summary>
        public readonly float Sharpness;

        /// <summary>Light component.</summary>
        public readonly float Light;

        /// <summary>Tracking component (share of frames with normal tracking).</summary>
        public readonly float Tracking;

        /// <summary>Weighted score, 0–1.</summary>
        public readonly float Score;

        /// <summary>The component furthest under its bar (relative to the bar).</summary>
        public readonly ReadinessWeakness Weakest;

        /// <summary>Combines the components.</summary>
        public ReadinessScore(
            float coverage,
            float parallax,
            float sharpness,
            float light,
            float tracking,
            float activeSeconds
        )
        {
            Coverage = Mathf.Clamp01(coverage);
            Parallax = Mathf.Clamp01(parallax);
            Sharpness = Mathf.Clamp01(sharpness);
            Light = Mathf.Clamp01(light);
            Tracking = Mathf.Clamp01(tracking);
            Score = Mathf.Clamp01(
                CaptureTuning.Readiness.WeightCoverage * Coverage
                    + CaptureTuning.Readiness.WeightParallax * Parallax
                    + CaptureTuning.Readiness.WeightSharpness * Sharpness
                    + CaptureTuning.Readiness.WeightLight * Light
                    + CaptureTuning.Readiness.WeightTracking * Tracking
            );

            Weakest = ReadinessWeakness.None;
            float worst = 0f;
            Consider(
                ref Weakest,
                ref worst,
                ReadinessWeakness.Light,
                Light,
                CaptureTuning.Readiness.BarLight
            );
            Consider(
                ref Weakest,
                ref worst,
                ReadinessWeakness.Tracking,
                Tracking,
                CaptureTuning.Readiness.BarTracking
            );
            Consider(
                ref Weakest,
                ref worst,
                ReadinessWeakness.Sharpness,
                Sharpness,
                CaptureTuning.Readiness.BarSharpness
            );
            Consider(
                ref Weakest,
                ref worst,
                ReadinessWeakness.Coverage,
                Coverage,
                CaptureTuning.Readiness.BarCoverage
            );
            Consider(
                ref Weakest,
                ref worst,
                ReadinessWeakness.Parallax,
                Parallax,
                CaptureTuning.Readiness.BarParallax
            );
            if (
                Weakest == ReadinessWeakness.None
                && activeSeconds > CaptureTuning.Timing.LongCaptureSec
            )
            {
                Weakest = ReadinessWeakness.Duration;
            }
        }

        /// <summary>The weakness as recorded in the bundle ("none", "coverage", ...).</summary>
        public string WeakestId => Weakest.ToString().ToLowerInvariant();

        private static void Consider(
            ref ReadinessWeakness weakest,
            ref float worst,
            ReadinessWeakness kind,
            float value,
            float bar
        )
        {
            // Shortfall relative to the bar; ties keep the earlier (more fixable-in-place) signal.
            float shortfall = (bar - value) / bar;
            if (shortfall > worst)
            {
                worst = shortfall;
                weakest = kind;
            }
        }
    }
}
