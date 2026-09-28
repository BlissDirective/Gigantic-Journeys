using System;
using GiganticJourneys.DebugTools;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>Pure logic of the debug overlay (ticket M0-UNITY-04 AT-1).</summary>
    public class DebugOverlayLogicTests
    {
        static FrameStats Steady(float fps, float seconds, float start = 0f)
        {
            var s = new FrameStats();
            var dt = 1f / fps;
            var t = start;
            for (var i = 0; i < (int)(seconds * fps); i++)
            {
                t += dt;
                s.Add(t, dt);
            }
            return s;
        }

        [Test]
        public void FrameStats_SteadyRate_AverageAndPercentilesMatch()
        {
            var s = Steady(60f, 10f);
            Assert.That(s.AverageFps(1f), Is.EqualTo(60f).Within(0.5f));
            Assert.That(s.FpsAtPercentile(99f, 5f), Is.EqualTo(60f).Within(0.5f));
            Assert.That(s.AverageFrameMs(1f), Is.EqualTo(16.67f).Within(0.1f));
        }

        [Test]
        public void FrameStats_P99_CatchesHitches_AverageDoesNot()
        {
            var s = new FrameStats();
            var t = 0f;
            for (var i = 0; i < 300; i++)
            {
                // 294 frames at 60 fps and 6 hitches of 100 ms (2 % of frames).
                var dt = i % 50 == 25 ? 0.1f : 1f / 60f;
                t += dt;
                s.Add(t, dt);
            }
            Assert.That(s.FrameMsPercentile(99f, 10f), Is.EqualTo(100f).Within(0.01f));
            Assert.That(s.FpsAtPercentile(99f, 10f), Is.EqualTo(10f).Within(0.01f));
            Assert.That(s.FpsAtPercentile(50f, 10f), Is.EqualTo(60f).Within(0.5f));
            Assert.That(s.AverageFps(10f), Is.EqualTo(300f / 5.5f).Within(0.5f));
        }

        [Test]
        public void FrameStats_WindowsOnlyCountRecentFrames()
        {
            var s = Steady(30f, 30f);
            var t = s.LatestTime;
            for (var i = 0; i < 120; i++)
            {
                t += 1f / 120f;
                s.Add(t, 1f / 120f);
            }
            Assert.That(
                s.AverageFps(0.9f),
                Is.EqualTo(120f).Within(1f),
                "short window = recent frames only"
            );
            Assert.That(s.CountInWindow(60f), Is.EqualTo(900 + 120));
        }

        [Test]
        public void FrameStats_KeepsSixtySecondsAtMaxRate_AndIgnoresBadSamples()
        {
            var s = Steady(FrameStats.MaxFps, 70f);
            Assert.That(s.CoveredSeconds(FrameStats.HistorySeconds), Is.EqualTo(60f).Within(0.1f));
            s.Add(s.LatestTime + 1f, 0f);
            s.Add(s.LatestTime + 1f, float.NaN);
            Assert.That(s.Count, Is.EqualTo((int)FrameStats.HistorySeconds * FrameStats.MaxFps));
            Assert.That(new FrameStats().AverageFps(1f), Is.EqualTo(0f));
            Assert.That(new FrameStats().FpsAtPercentile(99f, 5f), Is.EqualTo(0f));
        }

        [Test]
        public void ThreeFingerTap_FiresOncePerGesture()
        {
            var d = new ThreeFingerTapDetector();
            Assert.That(d.Update(1, 0.00f), Is.False);
            Assert.That(d.Update(2, 0.05f), Is.False);
            Assert.That(d.Update(3, 0.10f), Is.True);
            Assert.That(d.Update(3, 0.20f), Is.False, "holding does not toggle again");
            Assert.That(d.Update(4, 0.30f), Is.False);
            Assert.That(d.Update(0, 0.40f), Is.False);
            Assert.That(d.Update(3, 1.00f), Is.True, "re-armed after all fingers lift");
        }

        [Test]
        public void ThreeFingerTap_IgnoresSlowGatherAndTwoFingers()
        {
            var d = new ThreeFingerTapDetector();
            d.Update(1, 0f);
            d.Update(2, 0.3f);
            Assert.That(d.Update(3, 1.2f), Is.False, "fingers landing over > 0.5 s are not a tap");
            d.Update(0, 1.3f);
            Assert.That(d.Update(2, 2f), Is.False);
            d.Update(0, 2.1f);
        }

        [Test]
        public void BuildInfo_ParsesKeyValueResource()
        {
            var map = BuildInfo.Parse("# c\ngit_sha=abc1234\r\nbuild_number = 42\nbad line\n=x\n");
            Assert.That(map["git_sha"], Is.EqualTo("abc1234"));
            Assert.That(map["build_number"], Is.EqualTo("42"));
            Assert.That(map.Count, Is.EqualTo(2));
            Assert.That(BuildInfo.GitSha, Is.Not.Empty);
        }

        [Test]
        public void PerformanceReport_HasTheOwnersFields_AndNoDeviceName()
        {
            var text = PerformanceReport.Build(
                Steady(60f, 61f),
                new DateTime(2026, 9, 27, 12, 0, 0)
            );
            foreach (
                var key in new[]
                {
                    "fps_p50: ",
                    "fps_p99: ",
                    "window_s: 60.0",
                    "device_model: " + SystemInfo.deviceModel,
                    "build_version: ",
                    "git_sha: ",
                    "created_utc: 2026-09-27T12:00:00Z",
                }
            )
                StringAssert.Contains(key, text);
            StringAssert.Contains("fps_p50: 60.0", text);
            StringAssert.DoesNotContain("device_name", text);
        }

        [TestCase(460f, 3f)] // iPhone 15 Pro
        [TestCase(476f, 3f)] // iPhone 13 mini
        [TestCase(326f, 2f)] // iPhone SE / 11
        [TestCase(264f, 2f)] // iPad
        [TestCase(96f, 1f)] // desktop
        [TestCase(0f, 1f)] // unknown density
        [TestCase(800f, 3f)] // clamped
        public void EstimatePixelsPerPoint_MatchesIosScreenScale(float dpi, float expected)
        {
            Assert.That(DebugOverlay.EstimatePixelsPerPoint(dpi), Is.EqualTo(expected));
        }

        [Test]
        public void MinTouchTarget_Is44Points()
        {
            Assert.That(DebugOverlay.MinTouchTargetPoints, Is.EqualTo(44f));
        }
    }
}
