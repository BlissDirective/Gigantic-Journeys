using System;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// The overlay's one-tap performance report (ticket M0-UNITY-04 AT-1):
    /// fps p50/p99 over the last 60 s, device model and build, written as a
    /// small text file to <see cref="Application.persistentDataPath"/> (the
    /// app's Documents folder on iOS) and handed to the share sheet.
    ///
    /// Privacy: the report carries the hardware model identifier (for example
    /// "iPhone16,1"), never <c>SystemInfo.deviceName</c>, which on iOS is the
    /// user-chosen name and often contains a person's name.
    /// </summary>
    public static class PerformanceReport
    {
        public const float WindowSeconds = FrameStats.HistorySeconds;
        public const string FilePrefix = "gj-perf-report-";

        public static string Build(FrameStats stats, DateTime utcNow)
        {
            var ci = CultureInfo.InvariantCulture;
            var sb = new StringBuilder();
            void Line(string key, string value) =>
                sb.Append(key).Append(": ").Append(value).Append('\n');
            string F(float v) => v.ToString("0.0", ci);

            sb.Append("# Gigantic Journeys performance report (debug overlay, M0-UNITY-04)\n");
            Line("created_utc", utcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", ci));
            Line("window_s", F(WindowSeconds));
            Line("covered_s", F(stats.CoveredSeconds(WindowSeconds)));
            Line("frames", stats.CountInWindow(WindowSeconds).ToString(ci));
            Line("fps_p50", F(stats.FpsAtPercentile(50f, WindowSeconds)));
            Line("fps_p99", F(stats.FpsAtPercentile(99f, WindowSeconds)));
            Line("fps_avg", F(stats.AverageFps(WindowSeconds)));
            Line("frame_ms_p50", F(stats.FrameMsPercentile(50f, WindowSeconds)));
            Line("frame_ms_p99", F(stats.FrameMsPercentile(99f, WindowSeconds)));
            Line("device_model", SystemInfo.deviceModel);
            Line("os", SystemInfo.operatingSystem);
            Line("gpu", $"{SystemInfo.graphicsDeviceName} ({SystemInfo.graphicsDeviceType})");
            Line("build_version", BuildInfo.VersionLabel);
            Line("git_sha", BuildInfo.GitSha);
            Line("built_utc", BuildInfo.BuiltUtc);
            Line("unity", Application.unityVersion);
            Line("scene", SceneManager.GetActiveScene().name);
            Line("quality_level", QualitySettings.names[QualitySettings.GetQualityLevel()]);
            Line("target_frame_rate", Application.targetFrameRate.ToString(ci));
            Line("screen", $"{Screen.width}x{Screen.height}");
            sb.Append(
                "# fps_pNN = 1000 / (NN-th percentile frame time); p99 is the rate 99% of frames meet or beat.\n"
            );
            return sb.ToString();
        }

        /// <summary>Writes the report and returns its full path.</summary>
        public static string Save(FrameStats stats, string directory = null)
        {
            var now = DateTime.UtcNow;
            directory ??= Application.persistentDataPath;
            Directory.CreateDirectory(directory);
            var name =
                FilePrefix + now.ToString("yyyyMMdd-HHmmss", CultureInfo.InvariantCulture) + ".txt";
            var path = Path.Combine(directory, name);
            File.WriteAllText(path, Build(stats, now));
            return path;
        }
    }
}
