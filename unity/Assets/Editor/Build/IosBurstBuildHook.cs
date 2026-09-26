using System;
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace GiganticJourneys.EditorTools.Build
{
    /// <summary>
    /// iOS Burst state (ticket M3-UNITY-01). The committed state is ENABLED:
    /// <c>ProjectSettings/BurstAotSettings_iOS.json</c> has
    /// <c>"EnableBurstCompilation": true</c>, so a fresh checkout builds iOS with
    /// Burst AOT on (the macOS player-build lane, for perf and TestFlight builds).
    ///
    /// The fast Linux compile-check export passes the command-line flag
    /// <c>-gjIosBurstOff</c> (game-ci <c>customParameters</c>). For that build
    /// only, this hook writes <c>EnableBurstCompilation: false</c> before Burst's
    /// AOT step reads the file and restores the committed file after the build.
    /// Every iOS build logs one <c>[GJ-BURST]</c> line with the effective state.
    /// </summary>
    public class IosBurstBuildHook : IPreprocessBuildWithReport, IPostprocessBuildWithReport
    {
        public const string SettingsPath = "ProjectSettings/BurstAotSettings_iOS.json";
        public const string DisableFlag = "-gjIosBurstOff";
        const string LogTag = "[GJ-BURST]";
        static readonly Regex EnabledField = new Regex(
            "(\"EnableBurstCompilation\"\\s*:\\s*)(true|false)"
        );

        static string _committedJson;

        // Before Burst's own build callbacks (callbackOrder 0).
        public int callbackOrder => -100;

        /// <summary>The iOS Burst state in the settings file, or null if the file or field is missing.</summary>
        public static bool? ReadEnabled(string json)
        {
            if (string.IsNullOrEmpty(json))
                return null;
            var m = EnabledField.Match(json);
            return m.Success ? m.Groups[2].Value == "true" : (bool?)null;
        }

        public static bool? CommittedEnabled() =>
            File.Exists(SettingsPath) ? ReadEnabled(File.ReadAllText(SettingsPath)) : null;

        public static bool DisableRequested(string[] args) => Array.IndexOf(args, DisableFlag) >= 0;

        public void OnPreprocessBuild(BuildReport report)
        {
            if (report.summary.platform != BuildTarget.iOS)
                return;
            var host = Application.platform;
            var committed = CommittedEnabled();
            if (committed == null)
                throw new BuildFailedException(
                    $"{LogTag} {SettingsPath} is missing or has no EnableBurstCompilation field (M3-UNITY-01)"
                );
            if (!DisableRequested(Environment.GetCommandLineArgs()))
            {
                Debug.Log(
                    $"{LogTag} iOS Burst AOT {(committed.Value ? "ENABLED" : "DISABLED")} "
                        + $"(committed {SettingsPath}; host {host})"
                );
                return;
            }
            _committedJson = File.ReadAllText(SettingsPath);
            File.WriteAllText(SettingsPath, EnabledField.Replace(_committedJson, "${1}false"));
            Debug.Log(
                $"{LogTag} iOS Burst AOT DISABLED for this build only ({DisableFlag}; host {host}); "
                    + $"the committed {SettingsPath} stays ENABLED and is restored after the build"
            );
        }

        public void OnPostprocessBuild(BuildReport report)
        {
            if (report.summary.platform != BuildTarget.iOS || _committedJson == null)
                return;
            File.WriteAllText(SettingsPath, _committedJson);
            _committedJson = null;
            Debug.Log($"{LogTag} restored the committed {SettingsPath}");
        }
    }
}
