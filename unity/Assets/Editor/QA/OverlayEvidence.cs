using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GiganticJourneys.EditorTools.Splats;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace GiganticJourneys.EditorTools.QA
{
    /// <summary>
    /// Builds the players behind the debug overlay's evidence (ticket M0-UNITY-04,
    /// driven by <c>qa/scripts/overlay_evidence.py</c>): a Development and a
    /// release player of the splat sample scene, then inspects both for the
    /// overlay assembly (and, with <c>-gjOverlayIos</c>, iOS Xcode exports for the
    /// share-sheet plugin). The Development player is what the driver runs in
    /// capture mode; the release inspection is AT-2's build-level evidence.
    ///
    /// Arguments: <c>-gjEvidenceOut &lt;dir&gt;</c> (writes <c>builds.json</c>),
    /// <c>-gjBuildRoot &lt;dir&gt;</c> (default <c>Builds/overlay</c>), <c>-gjOverlayIos</c>.
    /// </summary>
    public static class OverlayEvidence
    {
        public const string OverlayAssembly = "GiganticJourneys.DebugOverlay";
        public const string SharePlugin = "GJShareSheet.mm";
        const string LogTag = "[GJ-OVERLAY-BUILD]";

        [Serializable]
        public class BuildCheck
        {
            public string name;
            public string target;
            public bool development;
            public string result;
            public string outputPath;
            public double seconds;
            public bool overlayAssemblyPresent;
            public bool overlayTypeNamePresent;
            public bool sharePluginPresent;
            public List<string> managedAssemblies = new List<string>();
        }

        [Serializable]
        public class Result
        {
            public string unityVersion;
            public List<BuildCheck> builds = new List<BuildCheck>();
            public bool passed;
        }

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

        static string Arg(string[] args, string name)
        {
            var i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        public static bool Execute(string[] args)
        {
            var outDir = Arg(args, "-gjEvidenceOut") ?? Path.GetFullPath("Temp/overlay-evidence");
            var root = Path.GetFullPath(Arg(args, "-gjBuildRoot") ?? "Builds/overlay");
            Directory.CreateDirectory(outDir);
            var result = new Result { unityVersion = Application.unityVersion };
            var scenes = new[] { SampleSplat.ScenePath };

            result.builds.Add(BuildLinux("linux-development", root, scenes, true));
            result.builds.Add(BuildLinux("linux-release", root, scenes, false));
            if (Array.IndexOf(args, "-gjOverlayIos") >= 0)
            {
                result.builds.Add(BuildIos("ios-development", root, scenes, true));
                result.builds.Add(BuildIos("ios-release", root, scenes, false));
            }

            result.passed = result.builds.All(b =>
                b.result == "Succeeded"
                && b.overlayAssemblyPresent == b.development
                && (b.target != "iOS" || b.sharePluginPresent == b.development)
                && (b.development || !b.overlayTypeNamePresent)
            );
            File.WriteAllText(
                Path.Combine(outDir, "builds.json"),
                JsonUtility.ToJson(result, true)
            );
            Debug.Log($"{LogTag} result: {(result.passed ? "PASS" : "FAIL")}");
            return result.passed;
        }

        static BuildCheck BuildLinux(string name, string root, string[] scenes, bool dev)
        {
            var dir = Path.Combine(root, name);
            var check = Build(
                name,
                BuildTarget.StandaloneLinux64,
                Path.Combine(dir, "gj.x86_64"),
                scenes,
                dev
            );
            var managed = Path.Combine(dir, "gj_Data", "Managed");
            if (Directory.Exists(managed))
            {
                var dlls = Directory.GetFiles(managed, "GiganticJourneys*.dll");
                check.managedAssemblies = dlls.Select(Path.GetFileName).OrderBy(n => n).ToList();
                check.overlayAssemblyPresent = check.managedAssemblies.Contains(
                    OverlayAssembly + ".dll"
                );
                check.overlayTypeNamePresent = dlls.Any(f =>
                    ContainsAscii(File.ReadAllBytes(f), "DebugOverlay")
                );
            }
            return check;
        }

        static BuildCheck BuildIos(string name, string root, string[] scenes, bool dev)
        {
            var dir = Path.Combine(root, name);
            var check = Build(name, BuildTarget.iOS, dir, scenes, dev);
            if (Directory.Exists(dir))
            {
                check.sharePluginPresent = Directory
                    .GetFiles(dir, SharePlugin, SearchOption.AllDirectories)
                    .Any();
                var cpp = Path.Combine(dir, "Il2CppOutputProject", "Source", "il2cppOutput");
                check.overlayAssemblyPresent =
                    Directory.Exists(cpp)
                    && Directory
                        .GetFiles(cpp, "*.cpp")
                        .Any(f =>
                            Path.GetFileName(f)
                                .StartsWith(OverlayAssembly, StringComparison.Ordinal)
                        );
                check.overlayTypeNamePresent = check.overlayAssemblyPresent;
                // About 1 GB per export; only the inspection result is kept.
                Directory.Delete(dir, true);
            }
            return check;
        }

        static BuildCheck Build(
            string name,
            BuildTarget target,
            string path,
            string[] scenes,
            bool dev
        )
        {
            var started = DateTime.UtcNow;
            if (Directory.Exists(Path.GetDirectoryName(path)) && target != BuildTarget.iOS)
                Directory.Delete(Path.GetDirectoryName(path), true);
            if (target == BuildTarget.iOS && Directory.Exists(path))
                Directory.Delete(path, true);
            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                target = target,
                targetGroup = BuildPipeline.GetBuildTargetGroup(target),
                locationPathName = path,
                options = dev ? BuildOptions.Development : BuildOptions.None,
            };
            var report = BuildPipeline.BuildPlayer(options);
            var check = new BuildCheck
            {
                name = name,
                target = target.ToString(),
                development = dev,
                result = report.summary.result.ToString(),
                outputPath = path,
                seconds = Math.Round((DateTime.UtcNow - started).TotalSeconds, 1),
            };
            Debug.Log($"{LogTag} {name}: {check.result} in {check.seconds}s -> {path}");
            return check;
        }

        static bool ContainsAscii(byte[] haystack, string needle)
        {
            var n = System.Text.Encoding.ASCII.GetBytes(needle);
            for (var i = 0; i <= haystack.Length - n.Length; i++)
            {
                var j = 0;
                while (j < n.Length && haystack[i + j] == n[j])
                    j++;
                if (j == n.Length)
                    return true;
            }
            return false;
        }
    }
}
