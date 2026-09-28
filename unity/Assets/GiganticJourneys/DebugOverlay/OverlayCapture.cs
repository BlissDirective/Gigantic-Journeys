using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// QA capture mode for the overlay's visual evidence (ticket M0-UNITY-04,
    /// driven by <c>qa/scripts/overlay_evidence.py</c>). Debug builds only, like
    /// the rest of this assembly. Active only when the player is started with
    /// <c>-gjOverlayCapture &lt;dir&gt;</c>:
    /// <list type="bullet">
    /// <item><c>-gjOverlaySet scans</c> (default): shows the overlay, lets 6 s of frame
    /// stats accumulate, then captures it over a bright and a dark exposure of the
    /// scene (URP post exposure, standing in for bright and dark scans), saves a
    /// performance report through the overlay's own button handler, and quits.</item>
    /// <item><c>-gjOverlaySet safe-area</c>: applies the iPhone 15 Pro landscape
    /// safe-area insets (59/59 pt sides, 21 pt bottom at 3x, scaled to the window)
    /// and its 3x screen scale (for the 44 pt Save button),
    /// draws the safe area and the 8 % line as guides, and captures.</item>
    /// </list>
    /// Writes <c>&lt;name&gt;.png</c> files plus <c>capture.json</c> with the measured layout.
    /// </summary>
    public sealed class OverlayCapture : MonoBehaviour
    {
        const string LogTag = "[GJ-OVERLAY-QA]";
        const float MaxPngWidth = 1600f;

        // iPhone 15 Pro, landscape: 2556 x 1179 px, safe-area insets 177 px left/right, 63 px bottom.
        public const float RefWidth = 2556f;
        public const float RefHeight = 1179f;
        public const float RefInsetSide = 177f;
        public const float RefInsetBottom = 63f;
        public const float RefPixelsPerPoint = 3f;

        [Serializable]
        public class Shot
        {
            public string name;
            public float postExposure;
            public Color background;
            public int screenWidth;
            public int screenHeight;
            public Rect safeArea;
            public Rect overlayRect; // panel coordinates, origin top-left, pixels
            public float overlayHeightFraction; // of the landscape screen height
            public bool insideSafeArea;
            public bool anchoredTopRight;
            public float pixelsPerPoint;
            public Rect saveButtonRect; // panel coordinates, origin top-left, pixels
            public float saveButtonWidthPt;
            public float saveButtonHeightPt;
            public bool saveButtonBelowPanel;
            public bool saveButtonInsideSafeArea;
            public bool saveButtonMeets44pt;
            public string statsText;
            public string infoText;
            public string file;
        }

        [Serializable]
        public class Result
        {
            public string set;
            public string unityVersion;
            public string graphicsDevice;
            public string deviceModel;
            public string gitSha;
            public string scene;
            public bool developmentBuild;
            public string reportFile;
            public int errorCount;
            public List<string> errors = new List<string>();
            public List<Shot> shots = new List<Shot>();
        }

        string _outDir;
        string _set;
        Result _result;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Bootstrap()
        {
            var args = Environment.GetCommandLineArgs();
            var dir = Arg(args, "-gjOverlayCapture");
            if (string.IsNullOrEmpty(dir))
                return;
            // A virtual X display gives the window no focus; keep the player loop running.
            Application.runInBackground = true;
            Debug.Log($"{LogTag} capture mode: set {Arg(args, "-gjOverlaySet") ?? "scans"}");
            var go = new GameObject("GJ Overlay Capture");
            DontDestroyOnLoad(go);
            var c = go.AddComponent<OverlayCapture>();
            c._outDir = dir;
            c._set = Arg(args, "-gjOverlaySet") ?? "scans";
        }

        static string Arg(string[] args, string name)
        {
            var i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        void OnEnable() => Application.logMessageReceived += OnLog;

        void OnDisable() => Application.logMessageReceived -= OnLog;

        void OnLog(string condition, string stackTrace, LogType type)
        {
            if (_result == null || type == LogType.Log || type == LogType.Warning)
                return;
            _result.errorCount++;
            _result.errors.Add(condition);
        }

        IEnumerator Start()
        {
            Directory.CreateDirectory(_outDir);
            _result = new Result
            {
                set = _set,
                unityVersion = Application.unityVersion,
                graphicsDevice =
                    $"{SystemInfo.graphicsDeviceType} ({SystemInfo.graphicsDeviceName})",
                deviceModel = SystemInfo.deviceModel,
                gitSha = BuildInfo.GitSha,
                scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene().name,
                developmentBuild = Debug.isDebugBuild,
            };
            // Evidence hygiene on the QA box: hide the Development Console; turn MSAA off
            // (lavapipe rejects the 4x MSAA attachment mix) and HDR off (lavapipe loses the
            // camera clear on the HDR color buffer, leaving the background black).
            Debug.developerConsoleEnabled = false;
            Debug.developerConsoleVisible = false;
            var cam = Camera.main != null ? Camera.main : FindFirstObjectByType<Camera>();
            if (cam != null)
            {
                cam.allowMSAA = false;
                cam.allowHDR = false;
            }
            yield return null;
            var overlay =
                DebugOverlay.Instance != null ? DebugOverlay.Instance : DebugOverlay.Create();
            overlay.ReportDirectory = _outDir;

            if (_set == "safe-area")
            {
                float sx = Screen.width / RefWidth;
                float sy = Screen.height / RefHeight;
                DebugOverlay.SafeAreaOverride = new Rect(
                    RefInsetSide * sx,
                    RefInsetBottom * sy,
                    Screen.width - 2f * RefInsetSide * sx,
                    Screen.height - RefInsetBottom * sy
                );
                DebugOverlay.PixelsPerPointOverride = RefPixelsPerPoint * sy;
                AddGuides(overlay);
            }
            overlay.SetVisible(true);
            yield return new WaitForSecondsRealtime(6f);

            if (_set == "safe-area")
            {
                yield return Capture(overlay, "safe-area", 0f, new Color(0.53f, 0.68f, 0.84f));
            }
            else
            {
                // Stand-ins for a bright and a dark room scan: a near-white sky behind the
                // overlay plus +1 EV, and a near-black one plus -3 EV.
                yield return Capture(overlay, "bright-scan", 1f, new Color(0.86f, 0.91f, 0.96f));
                yield return Capture(overlay, "dark-scan", -3f, new Color(0.02f, 0.02f, 0.03f));
                // Same handler as the on-screen button (and F4).
                var path = overlay.SaveReport();
                _result.reportFile = path != null ? Path.GetFileName(path) : null;
            }

            File.WriteAllText(
                Path.Combine(_outDir, "capture.json"),
                JsonUtility.ToJson(_result, true)
            );
            Debug.Log(
                $"{LogTag} done: {_result.shots.Count} shot(s), {_result.errorCount} error(s)"
            );
            Application.Quit(_result.errorCount == 0 ? 0 : 1);
        }

        IEnumerator Capture(DebugOverlay overlay, string name, float postExposure, Color sky)
        {
            SetExposure(postExposure);
            var cam = Camera.main != null ? Camera.main : FindFirstObjectByType<Camera>();
            if (cam != null)
            {
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = sky;
            }
            yield return new WaitForSecondsRealtime(1.5f);
            overlay.Refresh();
            yield return null;
            yield return new WaitForEndOfFrame();

            var shot = ScreenCapture.CaptureScreenshotAsTexture();
            var png = Downscale(shot);
            var file = name + ".png";
            File.WriteAllBytes(Path.Combine(_outDir, file), png.EncodeToPNG());
            if (png != shot)
                Destroy(png);
            Destroy(shot);

            var safe = DebugOverlay.SafeAreaOverride ?? Screen.safeArea;
            var r = overlay.Box.worldBound;
            var landscapeH = Mathf.Min(Screen.width, Screen.height);
            var safeTop = Screen.height - safe.yMax;
            var safeRight = safe.xMax;
            var b = overlay.SaveButton.worldBound;
            var ppp = DebugOverlay.PixelsPerPoint;
            var s = new Shot
            {
                name = name,
                postExposure = postExposure,
                background = sky,
                screenWidth = Screen.width,
                screenHeight = Screen.height,
                safeArea = safe,
                overlayRect = r,
                overlayHeightFraction = r.height / landscapeH,
                insideSafeArea =
                    r.xMin >= safe.xMin - 0.5f
                    && r.xMax <= safeRight + 0.5f
                    && r.yMin >= safeTop - 0.5f
                    && r.yMax <= Screen.height - safe.yMin + 0.5f,
                anchoredTopRight =
                    safeRight - r.xMax <= landscapeH * 0.02f
                    && r.yMin - safeTop <= landscapeH * 0.02f,
                pixelsPerPoint = ppp,
                saveButtonRect = b,
                saveButtonWidthPt = b.width / ppp,
                saveButtonHeightPt = b.height / ppp,
                saveButtonBelowPanel = b.yMin >= r.yMax - 0.5f,
                saveButtonInsideSafeArea =
                    b.xMin >= safe.xMin - 0.5f
                    && b.xMax <= safeRight + 0.5f
                    && b.yMin >= safeTop - 0.5f
                    && b.yMax <= Screen.height - safe.yMin + 0.5f,
                saveButtonMeets44pt =
                    b.width / ppp >= DebugOverlay.MinTouchTargetPoints - 0.01f
                    && b.height / ppp >= DebugOverlay.MinTouchTargetPoints - 0.01f,
                statsText = overlay.StatsLabel.text,
                infoText = overlay.InfoLabel.text,
                file = file,
            };
            _result.shots.Add(s);
            Debug.Log(
                $"{LogTag} captured {file}: overlay {r} = {s.overlayHeightFraction:P1} of height; "
                    + $"save button {b} = {s.saveButtonWidthPt:0.#}x{s.saveButtonHeightPt:0.#} pt"
            );
        }

        static Texture2D Downscale(Texture2D src)
        {
            if (src.width <= MaxPngWidth)
                return src;
            var w = src.width / 2;
            var h = src.height / 2;
            var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
            Graphics.Blit(src, rt);
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var dst = new Texture2D(w, h, TextureFormat.RGB24, false);
            dst.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            dst.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            return dst;
        }

        Volume _volume;

        void SetExposure(float ev)
        {
            var cam = Camera.main != null ? Camera.main : FindFirstObjectByType<Camera>();
            if (cam != null)
                cam.GetUniversalAdditionalCameraData().renderPostProcessing = ev != 0f;
            if (_volume == null)
            {
                var go = new GameObject("GJ QA exposure");
                _volume = go.AddComponent<Volume>();
                _volume.isGlobal = true;
                _volume.priority = 1000f;
                var profile = ScriptableObject.CreateInstance<VolumeProfile>();
                profile.Add<ColorAdjustments>(true);
                _volume.sharedProfile = profile;
            }
            if (_volume.sharedProfile.TryGet<ColorAdjustments>(out var ca))
                ca.postExposure.Override(ev);
        }

        static void AddGuides(DebugOverlay overlay)
        {
            var root = overlay.Document.rootVisualElement;
            var safe = DebugOverlay.SafeAreaOverride.Value;
            float sh = Screen.height;
            var guide = new VisualElement
            {
                name = "gj-qa-safe-area",
                pickingMode = PickingMode.Ignore,
            };
            guide.style.position = Position.Absolute;
            guide.style.left = safe.xMin;
            guide.style.top = sh - safe.yMax;
            guide.style.width = safe.width;
            guide.style.height = safe.height;
            var yellow = new Color(1f, 0.85f, 0f, 1f);
            guide.style.borderLeftColor = guide.style.borderRightColor = yellow;
            guide.style.borderTopColor = guide.style.borderBottomColor = yellow;
            guide.style.borderLeftWidth = guide.style.borderRightWidth = 3f;
            guide.style.borderTopWidth = guide.style.borderBottomWidth = 3f;

            var line = new VisualElement { name = "gj-qa-8pct", pickingMode = PickingMode.Ignore };
            line.style.position = Position.Absolute;
            line.style.left = 0;
            line.style.right = 0;
            line.style.top = Mathf.Min(Screen.width, sh) * DebugOverlay.LandscapeHeightFraction;
            line.style.height = 3f;
            line.style.backgroundColor = new Color(1f, 0f, 1f, 1f);

            var legend = new Label(
                "QA guides: yellow = simulated iPhone 15 Pro landscape safe area; magenta = 8 % of screen height"
            )
            {
                pickingMode = PickingMode.Ignore,
            };
            legend.style.position = Position.Absolute;
            legend.style.left = safe.xMin + 12f;
            legend.style.bottom = safe.yMin + 12f;
            legend.style.fontSize = Mathf.Round(Mathf.Min(Screen.width, sh) * 0.022f);
            legend.style.color = Color.white;
            legend.style.backgroundColor = new Color(0f, 0f, 0f, 0.6f);
            legend.style.paddingLeft = legend.style.paddingRight = 8f;

            root.Insert(0, guide);
            root.Insert(1, line);
            root.Insert(2, legend);
        }
    }
}
