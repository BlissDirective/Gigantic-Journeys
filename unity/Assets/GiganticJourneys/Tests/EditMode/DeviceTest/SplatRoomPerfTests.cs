using System.IO;
using GiganticJourneys.DeviceTest;
using GiganticJourneys.Splats;
using NUnit.Framework;

namespace GiganticJourneys.Tests.DeviceTest
{
    /// <summary>Build 50 follow-ups: the room's sort cadence sticks, and frame times split by sort frames.</summary>
    public class SplatRoomPerfTests
    {
        [Test]
        public void RoomProfile_WinsOverTheTier_ForShOrderAndSortCadence()
        {
            Assert.AreEqual(1, SplatRenderSettingsApplier.EffectiveShOrder(3, 1));
            Assert.AreEqual(3, SplatRenderSettingsApplier.EffectiveShOrder(3, -1));
            Assert.AreEqual(
                0,
                SplatRenderSettingsApplier.EffectiveShOrder(3, 0),
                "SH 0 is a valid override"
            );
            Assert.AreEqual(2, SplatRenderSettingsApplier.EffectiveSortNth(1, 2));
            Assert.AreEqual(1, SplatRenderSettingsApplier.EffectiveSortNth(1, 0));
        }

        [Test]
        public void Loader_RoutesTheRoomCadence_ThroughTheTierApplier()
        {
            // Build 50 regression: the loader wrote the sort's cadence directly, and the sort then
            // adopted the tier cadence (1) the applier had written to the renderer.
            var src = File.ReadAllText("Assets/GiganticJourneys/DeviceTest/SplatRoomLoader.cs");
            StringAssert.Contains("applier.sortEveryNthFrameOverride = d.sortEveryNthFrame;", src);
            StringAssert.Contains("applier.shOrderOverride = d.shOrder;", src);
            StringAssert.Contains("applier.Apply();", src);
        }

        [Test]
        public void FrameTimeSplit_KeepsPercentilesPerKind()
        {
            var split = new FrameTimeSplit(100);
            for (var i = 0; i < 99; i++)
                split.Add(FrameTimeSplit.Kind.Other, 16.7f);
            split.Add(FrameTimeSplit.Kind.Other, 33.4f);
            for (var i = 0; i < 10; i++)
                split.Add(FrameTimeSplit.Kind.Sort, i < 5 ? 16.7f : 33.4f);
            Assert.AreEqual(16.7f, split.Percentile(FrameTimeSplit.Kind.Other, 50), 1e-4);
            Assert.AreEqual(16.7f, split.Percentile(FrameTimeSplit.Kind.Other, 99), 1e-4);
            Assert.AreEqual(33.4f, split.Percentile(FrameTimeSplit.Kind.Other, 100), 1e-4);
            Assert.AreEqual(33.4f, split.Percentile(FrameTimeSplit.Kind.Sort, 99), 1e-4);
            Assert.AreEqual(10, split.Count(FrameTimeSplit.Kind.Sort));
            Assert.AreEqual("no frames", split.Summary(FrameTimeSplit.Kind.Label));
            StringAssert.StartsWith(
                "p50 16.7 / p99 33.4 ms (10 frames)",
                split.Summary(FrameTimeSplit.Kind.Sort)
            );
        }

        [Test]
        public void FrameTimeSplit_RingKeepsTheNewestFrames()
        {
            var split = new FrameTimeSplit(4);
            for (var i = 0; i < 4; i++)
                split.Add(FrameTimeSplit.Kind.Sort, 50f);
            for (var i = 0; i < 4; i++)
                split.Add(FrameTimeSplit.Kind.Sort, 10f);
            Assert.AreEqual(4, split.Count(FrameTimeSplit.Kind.Sort));
            Assert.AreEqual(10f, split.Percentile(FrameTimeSplit.Kind.Sort, 100), 1e-4);
        }
    }
}
