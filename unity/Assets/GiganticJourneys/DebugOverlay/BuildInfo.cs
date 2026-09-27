using System;
using System.Collections.Generic;
using UnityEngine;

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// Build identity shown by the debug overlay and written into performance
    /// reports: app version, build number, git short SHA (ticket M0-UNITY-04).
    ///
    /// In a player the values come from the <c>gj_build_info</c> text resource
    /// that <c>Assets/Editor/Build/BuildInfoHook.cs</c> generates for debug
    /// builds only (it is git-ignored and deleted after the build). In the
    /// Editor the SHA comes from <c>GITHUB_SHA</c> or <c>git rev-parse</c>.
    /// </summary>
    public static class BuildInfo
    {
        public const string ResourceName = "gj_build_info";
        public const string Unknown = "unknown";

        static bool _loaded;
        static string _gitSha = Unknown;
        static string _buildNumber = Unknown;
        static string _builtUtc = Unknown;

        public static string Version => Application.version;

        public static string GitSha
        {
            get
            {
                Load();
                return _gitSha;
            }
        }

        public static string BuildNumber
        {
            get
            {
                Load();
                return _buildNumber;
            }
        }

        public static string BuiltUtc
        {
            get
            {
                Load();
                return _builtUtc;
            }
        }

        /// <summary>"1.0 (42)" or just "1.0" when the build number is unknown.</summary>
        public static string VersionLabel =>
            BuildNumber == Unknown ? Version : $"{Version} ({BuildNumber})";

        /// <summary>Parses the key=value lines of the build-info resource.</summary>
        public static Dictionary<string, string> Parse(string text)
        {
            var map = new Dictionary<string, string>(StringComparer.Ordinal);
            if (string.IsNullOrEmpty(text))
                return map;
            foreach (var raw in text.Split('\n'))
            {
                var line = raw.Trim();
                var eq = line.IndexOf('=');
                if (line.Length == 0 || line[0] == '#' || eq <= 0)
                    continue;
                map[line.Substring(0, eq).Trim()] = line.Substring(eq + 1).Trim();
            }
            return map;
        }

        static void Load()
        {
            if (_loaded)
                return;
            _loaded = true;
#if UNITY_EDITOR
            _gitSha = EditorGitSha();
            _builtUtc = "editor";
#else
            var asset = Resources.Load<TextAsset>(ResourceName);
            if (asset == null)
                return;
            var map = Parse(asset.text);
            if (map.TryGetValue("git_sha", out var sha) && sha.Length > 0)
                _gitSha = sha;
            if (map.TryGetValue("build_number", out var number) && number.Length > 0)
                _buildNumber = number;
            if (map.TryGetValue("built_utc", out var built) && built.Length > 0)
                _builtUtc = built;
            Resources.UnloadAsset(asset);
#endif
        }

#if UNITY_EDITOR
        static string EditorGitSha()
        {
            var env = Environment.GetEnvironmentVariable("GITHUB_SHA");
            if (!string.IsNullOrEmpty(env))
                return env.Length > 7 ? env.Substring(0, 7) : env;
            try
            {
                var psi = new System.Diagnostics.ProcessStartInfo("git", "rev-parse --short HEAD")
                {
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                };
                using var p = System.Diagnostics.Process.Start(psi);
                if (p == null)
                    return Unknown;
                var output = p.StandardOutput.ReadToEnd().Trim();
                p.WaitForExit(3000);
                return p.ExitCode == 0 && output.Length > 0 ? output : Unknown;
            }
            catch (Exception)
            {
                return Unknown;
            }
        }
#endif
    }
}
