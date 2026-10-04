using GaussianSplatting.Runtime;
using GiganticJourneys.Splats.Sorting;
using UnityEngine;

namespace GiganticJourneys.Splats
{
    /// <summary>
    /// Applies <see cref="SplatRenderSettings"/> to the <see cref="GaussianSplatRenderer"/>
    /// on the same GameObject: per-tier SH order, splat and opacity scale, sort cadence,
    /// the splat budget, and whole-object distance and frustum culling (M0-UNITY-02 AT-5).
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(GaussianSplatRenderer))]
    public class SplatRenderSettingsApplier : MonoBehaviour
    {
        public SplatRenderSettings settings;

        [Tooltip("Camera used for culling; defaults to Camera.main.")]
        public Camera cullingCamera;

        GaussianSplatRenderer _renderer;
        int _appliedQuality = -1;
        int _frame;
        bool _culled;
        bool _budgetWarned;
        readonly Plane[] _planes = new Plane[6];

        public bool IsCulled => _culled;

        /// <summary>
        /// A per-scene SH order that wins over the tier's (-1 = use the tier). Set by
        /// <c>SplatRoomLoader</c> from the room's device profile; survives quality changes.
        /// </summary>
        [System.NonSerialized]
        public int shOrderOverride = -1;

        /// <summary>
        /// A per-scene sort cadence that wins over the tier's (0 = use the tier). It must go
        /// through here: <see cref="MetalSafeSplatSort"/> adopts whatever cadence this component
        /// last wrote to the renderer, so setting the sort's cadence directly was overwritten
        /// (build 50 reported sort_every_nth_frame 1 although the room asked for 2).
        /// </summary>
        [System.NonSerialized]
        public int sortEveryNthFrameOverride;

        void OnEnable()
        {
            _renderer = GetComponent<GaussianSplatRenderer>();
            // Every tiered splat gets the Metal-safe sort (M1-UNITY-01); it stays dormant off Metal.
            if (Application.isPlaying && GetComponent<MetalSafeSplatSort>() == null)
                gameObject.AddComponent<MetalSafeSplatSort>();
            _appliedQuality = -1;
            Apply();
        }

        void OnValidate() => _appliedQuality = -1;

        void LateUpdate()
        {
            if (settings == null || _renderer == null)
                return;
            if (_appliedQuality != QualitySettings.GetQualityLevel())
                Apply();
            if (Application.isPlaying && ++_frame % settings.cullCheckIntervalFrames == 0)
                UpdateCulling();
        }

        /// <summary>The scene's SH order when set (>= 0), else the tier's.</summary>
        public static int EffectiveShOrder(int tierShOrder, int overrideShOrder) =>
            overrideShOrder >= 0 ? overrideShOrder : tierShOrder;

        /// <summary>The scene's sort cadence when set (> 0), else the tier's.</summary>
        public static int EffectiveSortNth(int tierNth, int overrideNth) =>
            overrideNth > 0 ? overrideNth : tierNth;

        /// <summary>Pushes the current tier's knobs onto the renderer.</summary>
        public void Apply()
        {
            if (settings == null || _renderer == null)
                return;
            _appliedQuality = QualitySettings.GetQualityLevel();
            var tier = settings.TierFor(_appliedQuality);
            _renderer.m_SHOrder = EffectiveShOrder(tier.shOrder, shOrderOverride);
            _renderer.m_SplatScale = tier.splatScale;
            _renderer.m_OpacityScale = tier.opacityScale;
            _renderer.m_SortNthFrame = EffectiveSortNth(
                tier.sortEveryNthFrame,
                sortEveryNthFrameOverride
            );

            var count = _renderer.m_Asset != null ? _renderer.m_Asset.splatCount : 0;
            var overBudget = count > tier.maxSplats;
            if (overBudget && !_budgetWarned)
            {
                Debug.LogWarning(
                    $"[GJ-SPLAT] {name}: {count} splats exceeds the {tier.name} tier budget of {tier.maxSplats}"
                );
                _budgetWarned = true;
            }
            if (settings.enforceBudget && overBudget)
                SetCulled(true);
        }

        void UpdateCulling()
        {
            var cam = cullingCamera != null ? cullingCamera : Camera.main;
            if (cam == null || _renderer.m_Asset == null)
                return;
            var tier = settings.TierFor(_appliedQuality);
            if (settings.enforceBudget && _renderer.m_Asset.splatCount > tier.maxSplats)
                return;

            var bounds = WorldBounds(_renderer.m_Asset, transform);
            var hide = false;
            if (tier.maxRenderDistance > 0f)
            {
                var d = Mathf.Sqrt(bounds.SqrDistance(cam.transform.position));
                var limit = tier.maxRenderDistance + (_culled ? -settings.distanceHysteresis : 0f);
                hide = d > limit;
            }
            if (!hide && settings.frustumCulling)
            {
                GeometryUtility.CalculateFrustumPlanes(cam, _planes);
                hide = !GeometryUtility.TestPlanesAABB(_planes, bounds);
            }
            SetCulled(hide);
        }

        void SetCulled(bool culled)
        {
            if (_culled == culled)
                return;
            _culled = culled;
            _renderer.enabled = !culled;
        }

        /// <summary>World-space AABB of a splat asset's local bounds under a transform.</summary>
        public static Bounds WorldBounds(GaussianSplatAsset asset, Transform tr)
        {
            var local = new Bounds();
            local.SetMinMax(asset.boundsMin, asset.boundsMax);
            var world = new Bounds(tr.TransformPoint(local.center), Vector3.zero);
            var e = local.extents;
            for (var i = 0; i < 8; i++)
            {
                var corner =
                    local.center
                    + new Vector3(
                        (i & 1) == 0 ? -e.x : e.x,
                        (i & 2) == 0 ? -e.y : e.y,
                        (i & 4) == 0 ? -e.z : e.z
                    );
                world.Encapsulate(tr.TransformPoint(corner));
            }
            return world;
        }
    }
}
