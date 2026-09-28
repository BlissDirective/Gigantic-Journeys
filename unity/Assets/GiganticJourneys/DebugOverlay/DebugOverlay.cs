using System;
using System.Globalization;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.UIElements;

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// In-game debug overlay (ticket M0-UNITY-04, the M0 exit-test ticket).
    ///
    /// Shows fps (1 s average and p99 over 5 s), frame time, build version, git
    /// short SHA, scene and device model in a UI Toolkit panel anchored top-right
    /// inside the safe area, never taller than 8 % of the landscape screen height
    /// (Design Skills rule 21), on a dark scrim so it reads over bright and dark
    /// scans (rule 1). A "Save report" button writes the 60 s performance report
    /// (<see cref="PerformanceReport"/>) and opens the iOS share sheet.
    ///
    /// Toggle: three-finger tap (device), F3 (keyboard, Editor), L3 + R3 together
    /// (gamepad). F4 saves a report while the overlay is visible.
    ///
    /// Release builds: this type lives in the <c>GiganticJourneys.DebugOverlay</c>
    /// assembly, whose define constraint is
    /// <c>UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG</c>, so a non-development
    /// player build without the <c>GJ_DEBUG</c> scripting define does not compile
    /// it at all (SECURITY_CHECKLIST §9.7, §9.8; EditMode test
    /// <c>DebugOverlayReleaseExclusionTests</c>).
    /// </summary>
    [DefaultExecutionOrder(-1000)]
    [DisallowMultipleComponent]
    public sealed class DebugOverlay : MonoBehaviour
    {
        public const float LandscapeHeightFraction = 0.08f;
        public const float FontFraction = 0.025f;
        public const float PaddingFraction = 0.005f;
        public const float AverageWindowSeconds = 1f;
        public const float P99WindowSeconds = 5f;
        public const float RefreshSeconds = 0.25f;
        public const float StatusSeconds = 3f;
        const string LogTag = "[GJ-DEBUG]";

        /// <summary>The running overlay, created automatically after the first scene loads.</summary>
        public static DebugOverlay Instance { get; private set; }

        /// <summary>Set false before play to stop the automatic creation (tests).</summary>
        public static bool AutoCreate = true;

        /// <summary>QA and tests: a simulated safe area in screen pixels (origin bottom-left).</summary>
        public static Rect? SafeAreaOverride;

        public FrameStats Stats { get; } = new FrameStats();
        public bool Visible { get; private set; }
        public UIDocument Document { get; private set; }
        public VisualElement Box { get; private set; }
        public Label StatsLabel { get; private set; }
        public Label InfoLabel { get; private set; }
        public Button SaveButton { get; private set; }
        public string LastReportPath { get; private set; }

        /// <summary>Directory for saved reports; null means <see cref="Application.persistentDataPath"/>.</summary>
        public string ReportDirectory { get; set; }

        public event Action<string> ReportSaved;

        readonly ThreeFingerTapDetector _tap = new ThreeFingerTapDetector();
        PanelSettings _panel;
        float _nextRefresh;
        float _statusUntil;
        string _status;
        bool _chordHeld;
        int _lastScreenW;
        int _lastScreenH;
        Rect _lastSafe;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void ResetStatics()
        {
            Instance = null;
            AutoCreate = true;
            SafeAreaOverride = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Bootstrap()
        {
            if (AutoCreate && Instance == null)
                Create();
        }

        /// <summary>Creates the overlay (hidden) on its own DontDestroyOnLoad object.</summary>
        public static DebugOverlay Create()
        {
            if (Instance != null)
                return Instance;
            var go = new GameObject("GJ Debug Overlay");
            DontDestroyOnLoad(go);
            return go.AddComponent<DebugOverlay>();
        }

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            BuildUi();
            SetVisible(false);
        }

        void OnDestroy()
        {
            if (Instance == this)
                Instance = null;
            if (_panel != null)
            {
                Destroy(_panel.themeStyleSheet);
                Destroy(_panel);
            }
        }

        void BuildUi()
        {
            // PanelSettings.OnEnable warns "No Theme Style Sheet" before a theme can be
            // assigned; the theme is set on the next line, so mute warnings for this one call.
            var filter = Debug.unityLogger.filterLogType;
            Debug.unityLogger.filterLogType = LogType.Error;
            try
            {
                _panel = ScriptableObject.CreateInstance<PanelSettings>();
            }
            finally
            {
                Debug.unityLogger.filterLogType = filter;
            }
            _panel.name = "GJ Debug Overlay Panel";
            _panel.scaleMode = PanelScaleMode.ConstantPixelSize;
            _panel.scale = 1f;
            _panel.sortingOrder = 32000;
            _panel.clearColor = false;
            // An empty runtime theme: every style the overlay needs is set inline, so the
            // overlay ships no theme or font asset of its own (nothing lands in release).
            _panel.themeStyleSheet = ScriptableObject.CreateInstance<ThemeStyleSheet>();

            Document = gameObject.AddComponent<UIDocument>();
            Document.panelSettings = _panel;

            var root = Document.rootVisualElement;
            root.pickingMode = PickingMode.Ignore;
            root.style.unityFontDefinition = FontDefinition.FromFont(
                Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf")
            );

            Box = new VisualElement { name = "gj-debug-overlay", pickingMode = PickingMode.Ignore };
            Box.style.position = Position.Absolute;
            Box.style.flexDirection = FlexDirection.Row;
            Box.style.alignItems = Align.Stretch;
            Box.style.overflow = Overflow.Hidden;
            Box.style.backgroundColor = new Color(0f, 0f, 0f, 0.72f); // scrim (Design Skills rule 1)

            var column = new VisualElement { pickingMode = PickingMode.Ignore };
            column.style.flexDirection = FlexDirection.Column;
            column.style.justifyContent = Justify.Center;
            column.style.flexShrink = 1;
            StatsLabel = MakeLabel("gj-debug-stats");
            InfoLabel = MakeLabel("gj-debug-info");
            column.Add(StatsLabel);
            column.Add(InfoLabel);

            SaveButton = new Button(() => SaveReport())
            {
                name = "gj-debug-save",
                text = "Save report",
            };
            SaveButton.style.color = Color.white;
            SaveButton.style.backgroundColor = new Color(1f, 1f, 1f, 0.2f);
            SaveButton.style.unityTextAlign = TextAnchor.MiddleCenter;
            SaveButton.style.flexShrink = 0;
            SetBorder(SaveButton, 0f);

            Box.Add(column);
            Box.Add(SaveButton);
            root.Add(Box);
        }

        static Label MakeLabel(string name)
        {
            var label = new Label { name = name, pickingMode = PickingMode.Ignore };
            label.style.color = Color.white;
            label.style.whiteSpace = WhiteSpace.NoWrap;
            label.style.overflow = Overflow.Hidden;
            label.style.textOverflow = TextOverflow.Ellipsis;
            label.style.unityTextAlign = TextAnchor.MiddleLeft;
            label.style.marginLeft = label.style.marginRight = 0;
            label.style.marginTop = label.style.marginBottom = 0;
            label.style.paddingLeft = label.style.paddingRight = 0;
            label.style.paddingTop = label.style.paddingBottom = 0;
            return label;
        }

        static void SetBorder(VisualElement e, float width)
        {
            e.style.borderLeftWidth = e.style.borderRightWidth = width;
            e.style.borderTopWidth = e.style.borderBottomWidth = width;
        }

        static void SetRadius(VisualElement e, float r)
        {
            e.style.borderTopLeftRadius = e.style.borderTopRightRadius = r;
            e.style.borderBottomLeftRadius = e.style.borderBottomRightRadius = r;
        }

        /// <summary>Anchors the box top-right inside the safe area and sizes it from the screen.</summary>
        void ApplyLayout()
        {
            float sw = Screen.width;
            float sh = Screen.height;
            var safe = SafeAreaOverride ?? Screen.safeArea;
            _lastScreenW = Screen.width;
            _lastScreenH = Screen.height;
            _lastSafe = safe;

            var landscapeH = Mathf.Min(sw, sh);
            var font = Mathf.Max(8f, Mathf.Floor(landscapeH * FontFraction));
            var pad = Mathf.Max(2f, Mathf.Round(landscapeH * PaddingFraction));

            Box.style.top = Mathf.Max(0f, sh - safe.yMax) + pad;
            Box.style.right = Mathf.Max(0f, sw - safe.xMax) + pad;
            Box.style.maxHeight = Mathf.Floor(landscapeH * LandscapeHeightFraction) - pad;
            Box.style.maxWidth = Mathf.Max(0f, safe.width - 2f * pad);
            Box.style.paddingLeft = Box.style.paddingRight = pad * 2f;
            Box.style.paddingTop = Box.style.paddingBottom = pad;
            SetRadius(Box, pad * 2f);

            StatsLabel.style.fontSize = font;
            InfoLabel.style.fontSize = font;
            InfoLabel.style.maxWidth = Mathf.Max(0f, sw * 0.5f);

            SaveButton.style.fontSize = font;
            SaveButton.style.marginLeft = pad * 2f;
            SaveButton.style.marginRight = SaveButton.style.marginTop = 0;
            SaveButton.style.marginBottom = 0;
            SaveButton.style.paddingLeft = SaveButton.style.paddingRight = pad * 2f;
            SaveButton.style.paddingTop = SaveButton.style.paddingBottom = 0;
            SetRadius(SaveButton, pad * 1.5f);
        }

        public void Toggle() => SetVisible(!Visible);

        public void SetVisible(bool visible)
        {
            Visible = visible;
            if (!visible)
                _status = null;
            if (Box == null)
                return;
            Box.style.display = visible ? DisplayStyle.Flex : DisplayStyle.None;
            if (visible)
            {
                ApplyLayout();
                Refresh();
            }
        }

        void Update()
        {
            var now = Time.realtimeSinceStartup;
            Stats.Add(now, Time.unscaledDeltaTime);
            HandleInput(now);
            if (!Visible)
                return;
            var safe = SafeAreaOverride ?? Screen.safeArea;
            if (Screen.width != _lastScreenW || Screen.height != _lastScreenH || safe != _lastSafe)
                ApplyLayout();
            if (now >= _nextRefresh)
                Refresh();
        }

        void HandleInput(float now)
        {
            var keyboard = Keyboard.current;
            if (keyboard != null)
            {
                if (keyboard.f3Key.wasPressedThisFrame)
                    Toggle();
                else if (Visible && keyboard.f4Key.wasPressedThisFrame)
                    SaveReport();
            }

            var pad = Gamepad.current;
            var chord =
                pad != null && pad.leftStickButton.isPressed && pad.rightStickButton.isPressed;
            if (chord && !_chordHeld)
                Toggle();
            _chordHeld = chord;

            var touches = 0;
            var screen = Touchscreen.current;
            if (screen != null)
            {
                foreach (var t in screen.touches)
                {
                    if (t.isInProgress)
                        touches++;
                }
            }
            if (_tap.Update(touches, now))
                Toggle();
        }

        /// <summary>Recomputes the two text lines now.</summary>
        public void Refresh()
        {
            var now = Time.realtimeSinceStartup;
            _nextRefresh = now + RefreshSeconds;
            if (StatsLabel == null)
                return;
            var ci = CultureInfo.InvariantCulture;
            var fps = Stats.AverageFps(AverageWindowSeconds);
            var p99 = Stats.FpsAtPercentile(99f, P99WindowSeconds);
            var ms = Stats.AverageFrameMs(AverageWindowSeconds);
            StatsLabel.text = string.Format(
                ci,
                "{0:0.0} fps (1 s)  ·  p99 {1:0.0} (5 s)  ·  {2:0.0} ms",
                fps,
                p99,
                ms
            );
            InfoLabel.text =
                _status != null && now < _statusUntil
                    ? _status
                    : string.Format(
                        ci,
                        "v{0}  ·  {1}  ·  {2}  ·  {3}",
                        BuildInfo.VersionLabel,
                        BuildInfo.GitSha,
                        SceneManager.GetActiveScene().name,
                        SystemInfo.deviceModel
                    );
        }

        /// <summary>Writes the 60 s performance report, opens the share sheet on iOS, returns the path.</summary>
        public string SaveReport()
        {
            try
            {
                LastReportPath = PerformanceReport.Save(Stats, ReportDirectory);
            }
            catch (Exception e) when (e is IOException || e is UnauthorizedAccessException)
            {
                Debug.LogWarning($"{LogTag} could not save the performance report: {e.Message}");
                ShowStatus("Report not saved: " + e.GetType().Name);
                return null;
            }
            var file = Path.GetFileName(LastReportPath);
            Debug.Log($"{LogTag} performance report saved: {file}");
            ShowStatus(
                ShareSheet.Share(LastReportPath) ? $"Saved {file}, sharing…" : $"Saved {file}"
            );
            ReportSaved?.Invoke(LastReportPath);
            return LastReportPath;
        }

        void ShowStatus(string text)
        {
            _status = text;
            _statusUntil = Time.realtimeSinceStartup + StatusSeconds;
            if (Visible)
                Refresh();
        }
    }
}
