using System;
using System.Collections.Generic;
using System.Globalization;
using GaussianSplatting.Runtime;
using GiganticJourneys.DebugTools;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Splats;
using GiganticJourneys.Splats.Sorting;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

namespace GiganticJourneys.DeviceTest
{
    /// <summary>
    /// Loads the device-test splat room (ticket M1-UNITY-01 AT-2/AT-3) into the
    /// <c>SplatRoom</c> scene: places the splat from <see cref="SplatRoomDescriptor"/>,
    /// builds an invisible floor and boundary walls for the movement character, shows a small
    /// label (room, splat count, sort tier, credit) and adds splat lines to the debug overlay's
    /// performance report.
    ///
    /// Debug-only: this assembly compiles only under
    /// <c>UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG</c>, and the scene is added to the
    /// build list only by the internal-debug CI lane, so release builds keep booting
    /// MovementTest and contain neither the scene nor the splat.
    /// </summary>
    [DefaultExecutionOrder(-500)]
    public sealed class SplatRoomLoader : MonoBehaviour
    {
        public const string LogTag = "[GJ-SPLAT-ROOM]";
        public const float WallHeight = 2.5f;
        public const float WallThickness = 0.2f;

        [Tooltip("splat-room.json (placement, credit, integrity hash): the default room.")]
        public TextAsset descriptorJson;

        [Tooltip(
            "Further rooms (splat-room-<slug>.json), chosen from the debug overlay's scene switcher."
        )]
        public TextAsset[] extraDescriptors = new TextAsset[0];

        public const string SceneName = "SplatRoom";

        /// <summary>
        /// The extra rooms the overlay offers as SplatRoom variants (slug, button label). Must
        /// match <see cref="extraDescriptors"/> (EditMode test); the default room keeps the plain
        /// "SplatRoom" button.
        /// </summary>
        public static readonly KeyValuePair<string, string>[] ExtraRooms =
        {
            new KeyValuePair<string, string>("owner-room-01", "Bedroom"),
        };

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void RegisterRoomVariants() =>
            DebugOverlay.SceneVariantProvider = name => name == SceneName ? ExtraRooms : null;

        /// <summary>
        /// The descriptor for <paramref name="slug"/> among <paramref name="jsons"/> (the first
        /// is the default, used when the slug is empty).
        /// </summary>
        public static SplatRoomDescriptor Select(IReadOnlyList<string> jsons, string slug)
        {
            if (jsons == null || jsons.Count == 0)
                throw new FormatException("no splat room descriptor");
            if (string.IsNullOrEmpty(slug))
                return SplatRoomDescriptor.Parse(jsons[0]);
            foreach (var j in jsons)
            {
                var d = SplatRoomDescriptor.Parse(j);
                if (d.slug == slug)
                    return d;
            }
            throw new FormatException($"no splat room '{slug}' in this scene");
        }

        List<string> DescriptorTexts()
        {
            var list = new List<string> { descriptorJson != null ? descriptorJson.text : null };
            foreach (var t in extraDescriptors ?? new TextAsset[0])
            {
                if (t != null)
                    list.Add(t.text);
            }
            return list;
        }

        [Tooltip("Inactive splat renderer in the scene (shader/compute references assigned).")]
        public GaussianSplatRenderer splatRenderer;

        [Tooltip("The movement character; moved to the descriptor's spawn.")]
        public Transform player;

        [Tooltip("Material for the descriptor's solid occluders (the room floor material).")]
        public Material occluderMaterial;

        public bool showLabel = true;

        [Tooltip(
            "Apply the descriptor's renderScale in the editor too (it edits the active URP asset until the scene unloads; players always apply it)."
        )]
        public bool renderScaleInEditor;

        public SplatRoomDescriptor Descriptor { get; private set; }
        public GaussianSplatAsset Asset { get; private set; }
        public bool Loaded => Asset != null;
        public string Error { get; private set; }
        public Transform Colliders { get; private set; }
        public Transform Occluders { get; private set; }
        public FollowCamera Follow { get; private set; }
        public Label RoomLabel { get; private set; }

        UIDocument _doc;
        PanelSettings _panel;
        float _nextLabel;
        UniversalRenderPipelineAsset _scaledPipeline;
        float _previousRenderScale;

        /// <summary>The URP render scale in effect while the room is loaded.</summary>
        public float RenderScale =>
            GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp
                ? urp.renderScale
                : 1f;

        void Awake()
        {
            try
            {
                Descriptor = Select(DescriptorTexts(), DebugOverlay.RequestedSceneVariant);
            }
            catch (FormatException e)
            {
                Error = "descriptor: " + e.Message;
                Debug.LogError($"{LogTag} {Error}");
                return;
            }
            BuildColliders(Descriptor);
            BuildOccluders(Descriptor);
            PlacePlayer(Descriptor);
            ApplyCameraLimits(Descriptor);
            Asset = Resources.Load<GaussianSplatAsset>(Descriptor.resource);
            if (Asset == null)
            {
                Error = "splat not in this build";
                Debug.LogWarning(
                    $"{LogTag} {Descriptor.resource} is not in this build (only the internal-debug lane fetches it)"
                );
                return;
            }
            if (
                !SystemInfo.supportsComputeShaders
                || SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null
            )
            {
                // -nographics test runs: the package's sorter would throw on a null device.
                Asset = null;
                Error = "no compute device";
                Debug.LogWarning($"{LogTag} {Error}; splat not rendered");
                return;
            }
            if (splatRenderer == null)
            {
                Error = "no splat renderer in the scene";
                Debug.LogError($"{LogTag} {Error}");
                return;
            }
            var t = splatRenderer.transform;
            t.SetLocalPositionAndRotation(Descriptor.Position, Descriptor.Rotation);
            t.localScale = Descriptor.Scale;
            splatRenderer.m_Asset = Asset;
            splatRenderer.gameObject.SetActive(true);
            ApplyPerformanceProfile(Descriptor);
            Debug.Log(
                $"{LogTag} loaded {Descriptor.slug}: {Asset.splatCount} splats on {SystemInfo.graphicsDeviceType}"
            );
        }

        void OnEnable() => PerformanceReport.ExtraLines += WriteReport;

        void OnDisable() => PerformanceReport.ExtraLines -= WriteReport;

        void Start()
        {
            if (showLabel)
                BuildLabel();
        }

        void Update()
        {
            SampleFrameTime();
            if (RoomLabel == null || Time.unscaledTime < _nextLabel)
                return;
            _nextLabel = Time.unscaledTime + 1f;
            RoomLabel.text = LabelText();
            _labelFrame = Time.frameCount;
        }

        // Frame N's delta is how long frame N-1 took: tag it with what frame N-1 did.
        void SampleFrameTime()
        {
            var sort = Sort;
            if (sort == null || !sort.Engaged)
                return;
            var previous = Time.frameCount - 1;
            var kind =
                sort.LastSortFrame == previous ? FrameTimeSplit.Kind.Sort
                : _labelFrame == previous ? FrameTimeSplit.Kind.Label
                : FrameTimeSplit.Kind.Other;
            FrameTimes.Add(kind, Time.unscaledDeltaTime * 1000f);
        }

        void OnDestroy()
        {
            RestoreRenderScale();
            if (Follow != null)
                Follow.QaStandingLookAtHeightM = 0f;
            if (_panel != null)
            {
                Destroy(_panel.themeStyleSheet);
                Destroy(_panel);
            }
        }

        /// <summary>Frame times by what the previous frame did (Tier B only), for the report.</summary>
        public readonly FrameTimeSplit FrameTimes = new FrameTimeSplit(FrameTimeWindow);

        // About a minute at 60 fps per kind, like the overlay's report window.
        const int FrameTimeWindow = 3600;
        int _labelFrame = -1;

        public MetalSafeSplatSort Sort =>
            splatRenderer != null ? splatRenderer.GetComponent<MetalSafeSplatSort>() : null;

        public int SplatCount => Asset != null ? Asset.splatCount : 0;

        /// <summary>The sort path that orders this frame's splats.</summary>
        public string SortTier
        {
            get
            {
                if (!Loaded)
                    return "none (no splat)";
                var sort = Sort;
                return SortTierLabel(sort != null && sort.Engaged, SystemInfo.graphicsDeviceType);
            }
        }

        public static string SortTierLabel(bool tierBEngaged, GraphicsDeviceType api)
        {
            if (tierBEngaged)
                return "Tier B (Metal-safe bitonic)";
            return api == GraphicsDeviceType.Metal
                ? "package radix (Tier B NOT engaged)"
                : $"package radix ({api})";
        }

        public string LabelText()
        {
            if (Descriptor == null)
                return "Splat room: " + Error;
            var head = Loaded
                ? $"{Descriptor.displayName}  ·  {SplatRoomDescriptor.FormatCount(SplatCount)} splats  ·  sort: {SortTier}  ·  render {RenderScale.ToString("0.##", CultureInfo.InvariantCulture)}x"
                : $"{Descriptor.displayName}: {Error}";
            if (Descriptor.HasQaStandingViewer)
                head +=
                    $"\nQA standing viewer · look-at {Descriptor.qaStandingLookAtHeightM.ToString("0.##", CultureInfo.InvariantCulture)} m (capture height; miniature stays on the floor)";
            return head + "\n" + Descriptor.credit;
        }

        /// <summary>Lines appended to the debug overlay's performance report while this scene runs.</summary>
        public void WriteReport(PerformanceReport.LineWriter line)
        {
            var ci = CultureInfo.InvariantCulture;
            line("splat_room", Descriptor != null ? Descriptor.slug : "invalid descriptor");
            line("splat_loaded", Loaded ? "true" : "false (" + Error + ")");
            line("splat_count", SplatCount.ToString(ci));
            line("sort_tier", SortTier);
            var sort = Sort;
            if (sort != null && sort.Engaged)
            {
                line("sort_every_nth_frame", sort.sortEveryNthFrame.ToString(ci));
                line("sorts_issued", sort.SortsIssued.ToString(ci));
                line("sorts_skipped_still", sort.SortsSkippedStill.ToString(ci));
                line(
                    "resort_threshold",
                    $"{sort.resortMoveMeters.ToString("0.###", ci)} m / {sort.resortAngleDeg.ToString("0.#", ci)} deg"
                );
                line("frame_ms_after_sort", FrameTimes.Summary(FrameTimeSplit.Kind.Sort));
                line("frame_ms_after_label", FrameTimes.Summary(FrameTimeSplit.Kind.Label));
                line("frame_ms_other", FrameTimes.Summary(FrameTimeSplit.Kind.Other));
                line(
                    "sort_dispatches_per_sort",
                    (1 + BitonicSortNetwork.Schedule(SplatCount).Count).ToString(ci)
                );
            }
            if (Loaded)
                line("sh_order", splatRenderer.m_SHOrder.ToString(ci));
            line("render_scale", RenderScale.ToString("0.00", ci));
            var cam = Camera.main;
            if (cam != null)
                line(
                    "camera_msaa_hdr",
                    $"{(cam.allowMSAA ? "on" : "off")}/{(cam.allowHDR ? "on" : "off")}"
                );
            if (Follow != null)
            {
                var l = Follow.Limits;
                line(
                    "camera_limits",
                    $"mode {(Descriptor != null && Descriptor.IsFreeLook ? "free" : "coverage")}, elev {l.MinElevationDeg.ToString("0.#", ci)}..{l.MaxElevationDeg.ToString("0.#", ci)} deg, "
                        + $"zoom {l.MinZoom.ToString("0.##", ci)}..{l.MaxZoom.ToString("0.##", ci)}, "
                        + $"yaw {l.YawCenterDeg.ToString("0.#", ci)} +- {l.YawHalfRangeDeg.ToString("0.#", ci)} deg, "
                        + $"box {(Follow.HasCameraBounds ? "on" : "off")}, collision {(Follow.CameraCollision ? "on" : "off")}, "
                        + $"occluders {(Occluders != null ? Occluders.childCount : 0).ToString(ci)}"
                );
                line(
                    "qa_standing_viewer",
                    Descriptor != null && Descriptor.HasQaStandingViewer
                        ? $"look-at {Descriptor.qaStandingLookAtHeightM.ToString("0.##", ci)} m"
                        : "off"
                );
            }
            // The sort runs on the GPU inside the frame; this build has no GPU timer for it,
            // so compare frame_ms against MovementTest (same build) for its cost.
            line("sort_ms", "not instrumented (GPU); see frame_ms");
        }

        /// <summary>The room's device profile on top of the quality tier (see <see cref="SplatRoomDescriptor.renderScale"/>).</summary>
        void ApplyPerformanceProfile(SplatRoomDescriptor d)
        {
            var sort = Sort;
            if (sort != null)
            {
                sort.resortMoveMeters = d.resortMoveMeters;
                sort.resortAngleDeg = d.resortAngleDeg;
            }
            // SH order and cadence go through the tier applier (it re-applies the tier on
            // quality changes, and the Metal-safe sort adopts the cadence it writes).
            var applier = splatRenderer.GetComponent<SplatRenderSettingsApplier>();
            if (applier != null)
            {
                applier.shOrderOverride = d.shOrder;
                applier.sortEveryNthFrameOverride = d.sortEveryNthFrame;
                applier.Apply();
            }
            else
            {
                if (d.shOrder >= 0)
                    splatRenderer.m_SHOrder = d.shOrder;
                if (d.sortEveryNthFrame > 0)
                    splatRenderer.m_SortNthFrame = d.sortEveryNthFrame;
            }
            if (sort != null && sort.Engaged && d.sortEveryNthFrame > 0)
                sort.sortEveryNthFrame = d.sortEveryNthFrame;
            if (
                d.renderScale > 0f
                && (!Application.isEditor || renderScaleInEditor)
                && GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset urp
            )
            {
                _scaledPipeline = urp;
                _previousRenderScale = urp.renderScale;
                urp.renderScale = d.renderScale;
            }
        }

        void RestoreRenderScale()
        {
            if (_scaledPipeline == null)
                return;
            _scaledPipeline.renderScale = _previousRenderScale;
            _scaledPipeline = null;
        }

        void BuildColliders(SplatRoomDescriptor d)
        {
            Colliders = new GameObject("Room colliders (invisible)").transform;
            Colliders.SetParent(transform, false);
            var lo = d.WalkMin;
            var hi = d.WalkMax;
            var c = (lo + hi) * 0.5f;
            var size = hi - lo;
            Box(
                "Floor",
                new Vector3(c.x, -0.05f, c.y),
                new Vector3(size.x + 1f, 0.1f, size.y + 1f)
            );
            var h = WallHeight;
            var t = WallThickness;
            Box(
                "Wall -X",
                new Vector3(lo.x - t * 0.5f, h * 0.5f, c.y),
                new Vector3(t, h, size.y + 2f * t)
            );
            Box(
                "Wall +X",
                new Vector3(hi.x + t * 0.5f, h * 0.5f, c.y),
                new Vector3(t, h, size.y + 2f * t)
            );
            Box("Wall -Z", new Vector3(c.x, h * 0.5f, lo.y - t * 0.5f), new Vector3(size.x, h, t));
            Box("Wall +Z", new Vector3(c.x, h * 0.5f, hi.y + t * 0.5f), new Vector3(size.x, h, t));
            foreach (var b in d.blockers ?? new SplatRoomDescriptor.Occluder[0])
                Box("Blocker " + b.name, b.Center, b.Size);
        }

        void Box(string name, Vector3 center, Vector3 size)
        {
            var go = new GameObject(name);
            go.transform.SetParent(Colliders, false);
            go.transform.localPosition = center;
            go.AddComponent<BoxCollider>().size = size;
            // The floor, the boundary walls and the furniture blockers only stop the character.
            // The camera keeps out of them on its own (its box is the room's walls, and it
            // never drops under the floor), so they stay out of its collision cast: with the
            // blockers in it, turning past the bed snapped the eye into the character, and the
            // 0.15 m cast sphere grazing the floor did the same whenever the view looked up
            // (build 61). Nothing else in the game raycasts against them.
            go.layer = LayerMask.NameToLayer("Ignore Raycast");
        }

        void BuildOccluders(SplatRoomDescriptor d)
        {
            Occluders = new GameObject("Room occluders").transform;
            Occluders.SetParent(transform, false);
            foreach (var o in d.occluders ?? new SplatRoomDescriptor.Occluder[0])
            {
                var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
                go.name = "Occluder " + o.name;
                go.transform.SetParent(Occluders, false);
                go.transform.localPosition = o.Center;
                go.transform.localScale = o.Size;
                var r = go.GetComponent<MeshRenderer>();
                if (occluderMaterial != null)
                    r.sharedMaterial = occluderMaterial;
                r.shadowCastingMode = ShadowCastingMode.Off;
            }
        }

        /// <summary>The room's orbit limits, camera box and camera collision (see the descriptor).</summary>
        void ApplyCameraLimits(SplatRoomDescriptor d)
        {
            var cam = Camera.main;
            Follow = cam != null ? cam.GetComponent<FollowCamera>() : null;
            if (Follow == null)
                return;
            Follow.Limits = OrbitLimitsFor(d);
            if (d.HasCameraBox)
                Follow.SetCameraBounds(d.CameraBox);
            Follow.CameraCollision = true;
            // Bedroom QA: raise the look-at to standing / capture height so free look matches
            // the training views; the 1:12 character stays on the floor (build 69).
            Follow.QaStandingLookAtHeightM = d.qaStandingLookAtHeightM;
        }

        public static FollowCamera.OrbitLimits OrbitLimitsFor(SplatRoomDescriptor d)
        {
            var l = FollowCamera.OrbitLimits.Default;
            if (d.IsFreeLook)
            {
                // Every direction: full yaw, wide pitch; the camera box and collision still apply.
                l.MinElevationDeg = d.freeOrbit.minElevationDeg;
                l.MaxElevationDeg = d.freeOrbit.maxElevationDeg;
                l.MinZoom = d.freeOrbit.minZoom;
                l.MaxZoom = d.freeOrbit.maxZoom;
                l.YawCenterDeg = 0f;
                l.YawHalfRangeDeg = 180f; // a full turn either way (= no yaw limit)
                return l;
            }
            if (d.HasOrbitElevation)
            {
                l.MinElevationDeg = d.orbitMinElevationDeg;
                l.MaxElevationDeg = d.orbitMaxElevationDeg;
            }
            if (d.HasOrbitZoom)
            {
                l.MinZoom = d.orbitMinZoom;
                l.MaxZoom = d.orbitMaxZoom;
            }
            if (d.viewYawHalfRangeDeg > 0f)
            {
                l.YawCenterDeg = d.viewYawCenterDeg;
                l.YawHalfRangeDeg = d.viewYawHalfRangeDeg;
            }
            return l;
        }

        void PlacePlayer(SplatRoomDescriptor d)
        {
            if (player == null)
                return;
            var cc = player.GetComponent<CharacterController>();
            if (cc != null)
                cc.enabled = false;
            player.SetPositionAndRotation(d.Spawn, Quaternion.Euler(0f, d.spawnYawDeg, 0f));
            if (cc != null)
                cc.enabled = true;
        }

        void BuildLabel()
        {
            var filter = Debug.unityLogger.filterLogType;
            Debug.unityLogger.filterLogType = LogType.Error; // "No Theme Style Sheet" before assignment
            try
            {
                _panel = ScriptableObject.CreateInstance<PanelSettings>();
            }
            finally
            {
                Debug.unityLogger.filterLogType = filter;
            }
            _panel.name = "GJ Splat Room Label";
            _panel.scaleMode = PanelScaleMode.ConstantPixelSize;
            _panel.sortingOrder = 31000;
            _panel.clearColor = false;
            _panel.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();
            _doc = gameObject.AddComponent<UIDocument>();
            _doc.panelSettings = _panel;
            var root = _doc.rootVisualElement;
            root.pickingMode = PickingMode.Ignore;
            root.style.unityFontDefinition = FontDefinition.FromFont(
                Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf")
            );
            RoomLabel = new Label
            {
                name = "gj-splat-room-label",
                pickingMode = PickingMode.Ignore,
            };
            var landscapeH = Mathf.Min(Screen.width, Screen.height);
            var font = Mathf.Max(8f, Mathf.Floor(landscapeH * 0.02f));
            var pad = Mathf.Max(2f, Mathf.Round(landscapeH * 0.005f));
            var safe = Screen.safeArea;
            RoomLabel.style.position = Position.Absolute;
            RoomLabel.style.left = safe.xMin + pad;
            RoomLabel.style.top = Mathf.Max(0f, Screen.height - safe.yMax) + pad;
            RoomLabel.style.maxWidth = safe.width * 0.55f;
            RoomLabel.style.fontSize = font;
            RoomLabel.style.color = Color.white;
            RoomLabel.style.whiteSpace = WhiteSpace.Normal;
            RoomLabel.style.backgroundColor = new Color(0f, 0f, 0f, 0.55f);
            RoomLabel.style.paddingLeft = RoomLabel.style.paddingRight = pad * 2f;
            RoomLabel.style.paddingTop = RoomLabel.style.paddingBottom = pad;
            RoomLabel.text = LabelText();
            root.Add(RoomLabel);
        }
    }
}
