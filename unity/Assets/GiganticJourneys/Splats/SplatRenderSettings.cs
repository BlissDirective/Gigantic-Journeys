using System;
using UnityEngine;

namespace GiganticJourneys.Splats
{
    /// <summary>
    /// The single place for Gaussian splat LOD and culling knobs (ticket M0-UNITY-02 AT-5),
    /// so gj-gameplay can tune them without touching renderer code. One entry per URP
    /// quality tier (index = QualitySettings level: 0 Low, 1 Medium, 2 High), applied at
    /// runtime by <see cref="SplatRenderSettingsApplier"/> onto the pinned renderer
    /// (aras-p/UnityGaussianSplatting, ADR-0001 addendum).
    ///
    /// The renderer has no built-in LOD or streaming, so "LOD" here is the per-tier
    /// SH order, splat size, sort cadence and splat budget, and "culling" is
    /// whole-object distance and frustum culling. Finer LOD (chunked streaming) is
    /// M1-UNITY-01 work.
    /// </summary>
    [CreateAssetMenu(
        fileName = "SplatRenderSettings",
        menuName = "Gigantic Journeys/Splat Render Settings"
    )]
    public class SplatRenderSettings : ScriptableObject
    {
        [Serializable]
        public class Tier
        {
            [Tooltip("Label only; the tier is chosen by QualitySettings level index.")]
            public string name = "High";

            [Tooltip(
                "Spherical-harmonics order used for view-dependent colour (0 = flat colour, cheapest; 3 = full)."
            )]
            [Range(0, 3)]
            public int shOrder = 3;

            [Tooltip("Multiplier on every splat's size (lower = thinner, faster, more gaps).")]
            [Range(0.1f, 2f)]
            public float splatScale = 1f;

            [Tooltip("Multiplier on every splat's opacity.")]
            [Range(0.05f, 20f)]
            public float opacityScale = 1f;

            [Tooltip(
                "Re-sort splats by depth every Nth frame (1 = every frame, correct; higher = cheaper, may pop)."
            )]
            [Range(1, 30)]
            public int sortEveryNthFrame = 1;

            [Tooltip(
                "Splat budget for this tier. An asset over budget logs a warning, and is hidden when enforceBudget is on (use the textured-mesh fallback instead)."
            )]
            [Min(1)]
            public int maxSplats = 2_000_000;

            [Tooltip(
                "Hide the whole splat object when the camera is farther than this (metres). 0 = never."
            )]
            [Min(0f)]
            public float maxRenderDistance = 0f;
        }

        [Tooltip("Per quality tier, lowest first. Index = QualitySettings level.")]
        public Tier[] tiers =
        {
            new Tier
            {
                name = "Low",
                shOrder = 1,
                splatScale = 1f,
                sortEveryNthFrame = 2,
                maxSplats = 1_000_000,
                maxRenderDistance = 60f,
            },
            new Tier
            {
                name = "Medium",
                shOrder = 2,
                sortEveryNthFrame = 1,
                maxSplats = 1_500_000,
                maxRenderDistance = 90f,
            },
            new Tier
            {
                name = "High",
                shOrder = 3,
                sortEveryNthFrame = 1,
                maxSplats = 2_500_000,
                maxRenderDistance = 0f,
            },
        };

        [Tooltip("Hide splat objects whose bounds are outside the main camera frustum.")]
        public bool frustumCulling = true;

        [Tooltip("Hide an asset that exceeds its tier's maxSplats (otherwise only warn).")]
        public bool enforceBudget = false;

        [Tooltip(
            "Frames between culling checks. Hiding and showing reallocates GPU buffers, so keep this above 1."
        )]
        [Range(1, 120)]
        public int cullCheckIntervalFrames = 10;

        [Tooltip("Distance hysteresis (metres) so objects do not flicker at the cull boundary.")]
        [Min(0f)]
        public float distanceHysteresis = 2f;

        /// <summary>The tier for a QualitySettings level (clamped to the defined tiers).</summary>
        public Tier TierFor(int qualityLevel)
        {
            if (tiers == null || tiers.Length == 0)
                return new Tier();
            return tiers[Mathf.Clamp(qualityLevel, 0, tiers.Length - 1)];
        }
    }
}
