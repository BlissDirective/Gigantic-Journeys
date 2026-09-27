using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using GaussianSplatting.Runtime;
using GiganticJourneys.EditorTools.Splats;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditorInternal;
using UnityEngine;
using UnityEngine.Rendering;
using Debug = UnityEngine.Debug;

namespace GiganticJourneys.EditorTools.QA
{
    /// <summary>
    /// Scripted editor smoke task (ticket M0-QA-01), driven by
    /// <c>qa/scripts/editor_smoke.py</c>. Runs in <c>-batchmode</c> WITH a
    /// graphics device (a virtual X display on Linux), because the screenshot
    /// needs a real renderer; <c>-nographics</c> makes the capture step fail.
    ///
    /// Steps: record the project open, import the sample splat, open the sample
    /// scene, render the scene camera (the Game-view camera) to a PNG, and write
    /// a JSON result that the Python driver turns into
    /// <c>qa/reports/M0-editor-smoke.md</c>. Exits 0 when every required step
    /// passes, 1 otherwise.
    ///
    /// Arguments: <c>-gjSmokeOut &lt;dir&gt;</c> (PNG + result.json),
    /// <c>-gjSmokeWidth</c> / <c>-gjSmokeHeight</c> (default 1280x720).
    /// </summary>
    public static class EditorSmoke
    {
        public const string SplatFolder = SampleSplat.Folder;
        public const string SplatScene = SampleSplat.ScenePath;
        public const string FallbackScene = "Assets/Scenes/SampleScene.unity";
        const string LogTag = "[GJ-SMOKE]";

        [Serializable]
        public class StepResult
        {
            public string name;
            public string status; // pass | fail | pending
            public double seconds;
            public string detail;
        }

        [Serializable]
        public class SmokeResult
        {
            public string unityVersion;
            public string unityFullVersion;
            public string platform;
            public string graphicsDevice;
            public string activeBuildTarget;
            public bool iosModuleInstalled;
            public double secondsSinceEditorStart;
            public string scenePath;
            public string screenshotFile;
            public int screenshotWidth;
            public int screenshotHeight;
            public int sceneTextureCount;
            public string splatSource;
            public int splatCount;
            public long splatAssetBytes;
            public bool splatBytesMatchCommitted;
            public double splatCoveragePercent;
            public List<string> sceneTextures = new List<string>();
            public int consoleErrorsOnOpen;
            public int consoleWarningsOnOpen;
            public int errorCount;
            public int exceptionCount;
            public int warningCount;
            public List<string> errors = new List<string>();
            public List<StepResult> steps = new List<StepResult>();
            public bool passed;
        }

        static SmokeResult _result;

        public static void Run()
        {
            var code = 1;
            try
            {
                code = Execute(Environment.GetCommandLineArgs()) ? 0 : 1;
            }
            catch (Exception e)
            {
                Debug.LogError($"{LogTag} unhandled: {e}");
            }
            EditorApplication.Exit(code);
        }

        /// <summary>
        /// Headless open check: logs the Console error/warning counts after the
        /// project loads and exits non-zero on any error (used for Editor upgrades).
        /// </summary>
        public static void ConsoleCheck()
        {
            var (errors, warnings) = ConsoleCounts();
            Debug.Log(
                $"{LogTag} console after open: {errors} error(s), {warnings} warning(s); "
                    + $"{InternalEditorUtility.GetFullUnityVersion()}"
            );
            EditorApplication.Exit(errors == 0 ? 0 : 1);
        }

        public static bool Execute(string[] args)
        {
            var outDir = Arg(args, "-gjSmokeOut") ?? Path.GetFullPath("../qa/evidence/M0-QA-01");
            var width = int.TryParse(Arg(args, "-gjSmokeWidth"), out var w) ? w : 1280;
            var height = int.TryParse(Arg(args, "-gjSmokeHeight"), out var h) ? h : 720;
            Directory.CreateDirectory(outDir);

            _result = new SmokeResult
            {
                unityVersion = Application.unityVersion,
                unityFullVersion = InternalEditorUtility.GetFullUnityVersion(),
                platform = SystemInfo.operatingSystem,
                graphicsDevice =
                    $"{SystemInfo.graphicsDeviceType} ({SystemInfo.graphicsDeviceName})",
                activeBuildTarget = EditorUserBuildSettings.activeBuildTarget.ToString(),
                iosModuleInstalled = IsIosModuleInstalled(),
                secondsSinceEditorStart = EditorApplication.timeSinceStartup,
            };
            (_result.consoleErrorsOnOpen, _result.consoleWarningsOnOpen) = ConsoleCounts();
            Application.logMessageReceivedThreaded += OnLog;
            try
            {
                Step(
                    "open project",
                    () =>
                        Pass(
                            $"domain loaded {EditorApplication.timeSinceStartup:F1}s after Editor start; "
                                + $"compile errors: {(EditorUtility.scriptCompilationFailed ? "yes" : "none")}; "
                                + $"console on open: {_result.consoleErrorsOnOpen} error(s), "
                                + $"{_result.consoleWarningsOnOpen} warning(s)",
                            !EditorUtility.scriptCompilationFailed
                                && _result.consoleErrorsOnOpen == 0
                        )
                );
                Step("import sample splat", ImportSampleSplat);
                Step("open sample scene", OpenSampleScene);
                Step("capture screenshot", () => Capture(outDir, width, height));
            }
            finally
            {
                Application.logMessageReceivedThreaded -= OnLog;
            }

            _result.passed =
                _result.steps.All(s => s.status != "fail")
                && _result.errorCount == 0
                && _result.exceptionCount == 0;
            File.WriteAllText(
                Path.Combine(outDir, "result.json"),
                JsonUtility.ToJson(_result, true)
            );
            Debug.Log($"{LogTag} result: {(_result.passed ? "PASS" : "FAIL")}");
            return _result.passed;
        }

        static void OnLog(string condition, string stackTrace, LogType type)
        {
            if (condition.StartsWith(LogTag, StringComparison.Ordinal))
                return;
            switch (type)
            {
                case LogType.Error:
                case LogType.Assert:
                    _result.errorCount++;
                    _result.errors.Add(condition);
                    break;
                case LogType.Exception:
                    _result.exceptionCount++;
                    _result.errors.Add(condition);
                    break;
                case LogType.Warning:
                    _result.warningCount++;
                    break;
            }
        }

        static void Step(string name, Func<(string status, string detail)> body)
        {
            var sw = Stopwatch.StartNew();
            (string status, string detail) r;
            try
            {
                r = body();
            }
            catch (Exception e)
            {
                r = ("fail", e.GetType().Name + ": " + e.Message);
            }
            sw.Stop();
            _result.steps.Add(
                new StepResult
                {
                    name = name,
                    status = r.status,
                    seconds = Math.Round(sw.Elapsed.TotalSeconds, 3),
                    detail = r.detail,
                }
            );
            Debug.Log($"{LogTag} {name}: {r.status} ({sw.Elapsed.TotalSeconds:F2}s) {r.detail}");
        }

        static (string, string) Pass(string detail, bool ok = true) =>
            (ok ? "pass" : "fail", detail);

        static (string, string) ImportSampleSplat()
        {
            // Regenerate the procedural sample (PLY in Temp/) and convert it with the
            // renderer's importer into Assets/Capture/Samples. Generation is seeded, so the
            // converted bytes must equal the committed ones.
            var before = SampleDataHash();
            var asset = SampleSplat.ImportSample();
            var after = SampleDataHash();
            _result.splatSource = SampleSplat.Source;
            _result.splatCount = asset.splatCount;
            _result.splatAssetBytes = SampleDataBytes();
            _result.splatBytesMatchCommitted = before != null && before == after;
            return (
                "pass",
                $"generated {SampleSplat.PlyPath} and imported {SampleSplat.AssetPath}: "
                    + $"{asset.splatCount} splats, {_result.splatAssetBytes / 1024} KiB converted data, "
                    + $"bytes identical to the committed asset: {(_result.splatBytesMatchCommitted ? "yes" : "NO")}"
            );
        }

        static string[] SampleDataFiles() =>
            Directory.Exists(SplatFolder)
                ? Directory
                    .GetFiles(SplatFolder, SampleSplat.SampleName + "*")
                    .Where(f =>
                        f.EndsWith(".bytes", StringComparison.Ordinal)
                        || f.EndsWith(".asset", StringComparison.Ordinal)
                    )
                    .OrderBy(f => f, StringComparer.Ordinal)
                    .ToArray()
                : Array.Empty<string>();

        static long SampleDataBytes() => SampleDataFiles().Sum(f => new FileInfo(f).Length);

        static string SampleDataHash()
        {
            var files = SampleDataFiles();
            if (files.Length == 0)
                return null;
            using var sha = SHA256.Create();
            foreach (var f in files)
            {
                var bytes = File.ReadAllBytes(f);
                sha.TransformBlock(bytes, 0, bytes.Length, null, 0);
            }
            sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
            return BitConverter.ToString(sha.Hash).Replace("-", "");
        }

        static (string, string) OpenSampleScene()
        {
            var path = File.Exists(SplatScene) ? SplatScene : FallbackScene;
            var scene = EditorSceneManager.OpenScene(path, OpenSceneMode.Single);
            _result.scenePath = path;
            if (!scene.IsValid() || !scene.isLoaded)
                return ("fail", $"could not open {path}");
            CollectSceneTextures();
            if (path != SplatScene)
                return ("fail", $"{SplatScene} is missing; opened the fallback {path}");
            var splats = UnityEngine.Object.FindObjectsByType<GaussianSplatRenderer>(
                FindObjectsSortMode.None
            );
            var ready = splats.Count(r => r.HasValidAsset && r.HasValidRenderSetup);
            return (
                ready > 0 ? "pass" : "fail",
                $"opened {path}, {scene.rootCount} root object(s), "
                    + $"{ready}/{splats.Length} GaussianSplatRenderer(s) with a valid asset and GPU data"
            );
        }

        static void CollectSceneTextures()
        {
            var textures = EditorUtility
                .CollectDependencies(
                    UnityEngine.Object.FindObjectsByType<GameObject>(FindObjectsSortMode.None)
                )
                .OfType<Texture>()
                .Select(AssetDatabase.GetAssetPath)
                .Where(p =>
                    !string.IsNullOrEmpty(p) && p.StartsWith("Assets/", StringComparison.Ordinal)
                )
                .Distinct()
                .OrderBy(p => p)
                .ToList();
            _result.sceneTextures = textures;
            _result.sceneTextureCount = textures.Count;
        }

        static (string, string) Capture(string outDir, int width, int height)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                return (
                    "fail",
                    "no graphics device (-nographics); run under a display, e.g. xvfb-run"
                );
            var cam =
                Camera.main
                ?? UnityEngine
                    .Object.FindObjectsByType<Camera>(FindObjectsSortMode.None)
                    .FirstOrDefault();
            if (cam == null)
                return ("fail", "no camera in the scene");

            // Baseline with the splat renderers off, then the real frame with them on:
            // the pixel difference proves the splat itself rendered (not just the sky).
            var splats = UnityEngine
                .Object.FindObjectsByType<GaussianSplatRenderer>(FindObjectsSortMode.None)
                .Where(r => r.enabled)
                .ToArray();
            foreach (var r in splats)
                r.enabled = false;
            var baseline = RenderCamera(cam, width, height);
            foreach (var r in splats)
                r.enabled = true;
            RenderCamera(cam, width, height, discard: true); // first frame primes the sort
            var tex = RenderCamera(cam, width, height);

            var pixels = tex.GetPixels32();
            var basePixels = baseline.GetPixels32();
            var changed = 0;
            for (var i = 0; i < pixels.Length; i++)
            {
                var a = pixels[i];
                var b = basePixels[i];
                if (Math.Abs(a.r - b.r) + Math.Abs(a.g - b.g) + Math.Abs(a.b - b.b) > 24)
                    changed++;
            }
            UnityEngine.Object.DestroyImmediate(baseline);
            _result.splatCoveragePercent = Math.Round(100.0 * changed / pixels.Length, 2);
            var distinct = pixels
                .Select(p => (p.r << 16) | (p.g << 8) | p.b)
                .Distinct()
                .Take(64)
                .Count();
            var file = Path.Combine(outDir, "01-editor-smoke.png");
            File.WriteAllBytes(file, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);

            _result.screenshotFile = Path.GetFileName(file);
            _result.screenshotWidth = width;
            _result.screenshotHeight = height;
            if (distinct < 2)
                return (
                    "fail",
                    $"screenshot is a flat single colour ({width}x{height}); renderer produced nothing"
                );
            if (splats.Length > 0 && _result.splatCoveragePercent < 1.0)
                return (
                    "fail",
                    $"splat renderer produced no visible splats ({_result.splatCoveragePercent}% of pixels changed)"
                );
            return (
                "pass",
                $"{cam.name} rendered {width}x{height} -> {_result.screenshotFile} ({distinct}+ colours); "
                    + $"splats cover {_result.splatCoveragePercent}% of the frame vs a splat-off baseline"
            );
        }

        static Texture2D RenderCamera(Camera cam, int width, int height, bool discard = false)
        {
            var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            var previousTarget = cam.targetTexture;
            var previousActive = RenderTexture.active;
            try
            {
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                tex.Apply();
            }
            finally
            {
                cam.targetTexture = previousTarget;
                RenderTexture.active = previousActive;
                rt.Release();
                UnityEngine.Object.DestroyImmediate(rt);
            }
            if (!discard)
                return tex;
            UnityEngine.Object.DestroyImmediate(tex);
            return null;
        }

        /// <summary>Error and warning counts in the Editor Console (internal LogEntries API).</summary>
        public static (int errors, int warnings) ConsoleCounts()
        {
            var type = typeof(EditorWindow).Assembly.GetType("UnityEditor.LogEntries");
            var method = type?.GetMethod(
                "GetCountsByType",
                System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public
            );
            if (method == null)
                return (-1, -1);
            var args = new object[] { 0, 0, 0 };
            method.Invoke(null, args);
            return ((int)args[0], (int)args[1]);
        }

        static bool IsIosModuleInstalled()
        {
            var editorDir = Path.GetDirectoryName(EditorApplication.applicationPath) ?? "";
            return Directory.Exists(
                    Path.Combine(editorDir, "Data", "PlaybackEngines", "iOSSupport")
                ) || BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.iOS, BuildTarget.iOS);
        }

        static string Arg(string[] args, string name)
        {
            var i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }
    }
}
