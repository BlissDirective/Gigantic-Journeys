using GiganticJourneys.Capture;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests.Capture
{
    /// <summary>M1-CAPT-01 AT-2: the live coaching signals (speed, blur, light, coverage, parallax).</summary>
    public class CaptureMetersTests
    {
        private static CaptureFrame Frame(
            int i,
            float t,
            Vector3 p,
            Quaternion r,
            float sharp = 150f,
            float luma = 0.5f,
            TrackingQuality tracking = TrackingQuality.Normal
        ) => new CaptureFrame(i, t, p, r, tracking, sharp, luma, false);

        [Test]
        public void LaplacianVariance_IsHighForDetailAndZeroForFlat()
        {
            const int w = 32,
                h = 24;
            var flat = new byte[w * h];
            var checker = new byte[w * h];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    flat[y * w + x] = 128;
                    checker[y * w + x] = (byte)(((x + y) & 1) == 0 ? 20 : 230);
                }
            }

            Assert.That(FrameMetrics.LaplacianVariance(flat, w, h), Is.EqualTo(0f).Within(1e-4f));
            Assert.That(FrameMetrics.LaplacianVariance(checker, w, h), Is.GreaterThan(1000f));
            Assert.That(FrameMetrics.MeanLuma(flat, w, h), Is.EqualTo(128f / 255f).Within(1e-4f));
            Assert.That(FrameMetrics.LaplacianVariance(null, w, h), Is.EqualTo(0f));
            Assert.That(FrameMetrics.LaplacianVariance(flat, 2, 2), Is.EqualTo(0f));
        }

        [Test]
        public void SpeedMeter_GoodPaceStaysTeal()
        {
            var meter = new SpeedMeter(CaptureMode.Room);
            for (int i = 0; i < 90; i++)
            {
                meter.Add(
                    Frame(
                        i,
                        i / 30f,
                        new Vector3(0.3f * i / 30f, 1.4f, 0f),
                        Quaternion.Euler(0f, 20f * i / 30f, 0f)
                    )
                );
                Assert.That(meter.IsAmber, Is.False, $"frame {i}");
            }

            Assert.That(meter.LinearSpeed, Is.EqualTo(0.3f).Within(0.02f));
            Assert.That(meter.AngularSpeed, Is.EqualTo(20f).Within(1f));
        }

        [Test]
        public void SpeedMeter_TooFastTurnsAmberWithOneHapticThenTheHintAfterASecond()
        {
            var meter = new SpeedMeter(CaptureMode.Room);
            int haptics = 0;
            float hintAt = -1f;
            for (int i = 0; i < 90; i++)
            {
                float t = i / 30f;
                meter.Add(Frame(i, t, new Vector3(1.5f * t, 1.4f, 0f), Quaternion.identity));
                haptics += meter.HapticThisFrame ? 1 : 0;
                if (hintAt < 0f && meter.ShowSlowDownHint)
                {
                    hintAt = t;
                }
            }

            Assert.That(meter.IsAmber, Is.True);
            Assert.That(haptics, Is.EqualTo(1));
            Assert.That(hintAt, Is.GreaterThan(1.0f).And.LessThan(1.6f));

            // slowing down clears the hint
            for (int i = 90; i < 150; i++)
            {
                meter.Add(Frame(i, i / 30f, new Vector3(4.5f, 1.4f, 0f), Quaternion.identity));
            }

            Assert.That(meter.IsAmber, Is.False);
            Assert.That(meter.ShowSlowDownHint, Is.False);
        }

        [Test]
        public void SpeedMeter_TabletopIsStricterThanRoom()
        {
            var room = new SpeedMeter(CaptureMode.Room);
            var table = new SpeedMeter(CaptureMode.Tabletop);
            for (int i = 0; i < 60; i++)
            {
                var f = Frame(i, i / 30f, new Vector3(0.5f * i / 30f, 1f, 0f), Quaternion.identity);
                room.Add(f);
                table.Add(f);
            }

            Assert.That(room.IsAmber, Is.False);
            Assert.That(table.IsAmber, Is.True);
        }

        [Test]
        public void BlurGate_RejectsABurstWithoutDraggingTheMedianDown()
        {
            var gate = new BlurGate();
            for (int i = 0; i < 20; i++)
            {
                Assert.That(gate.Accept(200f), Is.True);
            }

            for (int i = 0; i < 20; i++)
            {
                Assert.That(gate.Accept(30f), Is.False, "blurred frame accepted");
            }

            Assert.That(gate.Median, Is.EqualTo(200f));
            Assert.That(gate.Rejected, Is.EqualTo(20));
            Assert.That(gate.AcceptedRatio, Is.EqualTo(0.5f).Within(1e-4f));
            Assert.That(gate.Accept(5f), Is.False, "below the absolute floor");
        }

        [Test]
        public void LightMeter_ShowsTheCardOnceAfterSustainedDark()
        {
            var meter = new LightMeter();
            int cards = 0;
            for (int i = 0; i < 180; i++)
            {
                float t = i / 30f;
                bool dark = (t >= 1f && t < 3f) || t >= 4f;
                meter.Add(
                    Frame(i, t, Vector3.zero, Quaternion.identity, luma: dark ? 0.05f : 0.5f)
                );
                cards += meter.ShowCardThisFrame ? 1 : 0;
            }

            Assert.That(cards, Is.EqualTo(1));
            Assert.That(meter.CardShown, Is.True);
        }

        [Test]
        public void LightMeter_BriefDipDoesNotShowTheCard()
        {
            var meter = new LightMeter();
            for (int i = 0; i < 90; i++)
            {
                float t = i / 30f;
                meter.Add(
                    Frame(
                        i,
                        t,
                        Vector3.zero,
                        Quaternion.identity,
                        luma: t >= 1f && t < 2f ? 0.05f : 0.5f
                    )
                );
            }

            Assert.That(meter.CardShown, Is.False);
            Assert.That(meter.Score, Is.EqualTo(1f));
        }

        [Test]
        public void Room_FullSweepPaintsNearlyEverything()
        {
            var map = new CoverageMap(CaptureMode.Room);
            foreach (var f in new SyntheticCapture().Generate(CaptureMode.Room))
            {
                map.Add(f);
            }

            Assert.That(map.Kind, Is.EqualTo("view-sphere"));
            Assert.That(map.Fraction, Is.GreaterThan(0.9f));
        }

        [Test]
        public void Room_PartialSweepPointsTheArrowAtTheUnseenSide()
        {
            var map = new CoverageMap(CaptureMode.Room);
            // one level half-turn: yaw 0..180 only
            for (int i = 0; i < 180; i++)
            {
                map.Add(Frame(i, i / 30f, new Vector3(0f, 1.4f, 0f), Quaternion.Euler(0f, i, 0f)));
            }

            Assert.That(map.Fraction, Is.GreaterThan(0f).And.LessThan(0.2f));
            Assert.That(map.TryGetMissedCorner(out var dir, out int size), Is.True);
            Assert.That(size, Is.GreaterThan(map.AzimuthBins * map.ElevationBins / 2));
            // the unseen half is x < 0 (yaw 180..360)
            Assert.That(dir.x, Is.LessThan(0f));
        }

        [Test]
        public void Room_PaintedRowsMatchTheGridAndTheFraction()
        {
            var map = new CoverageMap(CaptureMode.Room);
            for (int i = 0; i < 360; i++)
            {
                map.Add(Frame(i, i / 30f, Vector3.zero, Quaternion.Euler(-10f, i, 0f)));
            }

            string[] rows = map.PaintedRows();
            Assert.That(rows.Length, Is.EqualTo(map.ElevationBins));
            int painted = 0;
            foreach (var row in rows)
            {
                Assert.That(row.Length, Is.EqualTo(map.AzimuthBins));
                Assert.That(row, Does.Match("^[01]+$"));
                painted += row.Split('1').Length - 1;
            }

            Assert.That(
                (float)painted / (map.AzimuthBins * map.ElevationBins),
                Is.EqualTo(map.Fraction).Within(1e-6f)
            );
            Assert.That(
                rows[3],
                Is.EqualTo(new string('1', map.AzimuthBins)),
                "elevation 10° row is fully painted"
            );
        }

        [Test]
        public void Tabletop_FindsTheBuildCentreAndPaintsBothHeights()
        {
            var synth = new SyntheticCapture();
            var map = new CoverageMap(CaptureMode.Tabletop);
            foreach (var f in synth.Generate(CaptureMode.Tabletop))
            {
                map.Add(f);
            }

            Assert.That(map.Kind, Is.EqualTo("orbit"));
            Assert.That(Vector3.Distance(map.OrbitCentre, synth.BuildCentre), Is.LessThan(0.05f));
            Assert.That(map.Fraction, Is.EqualTo(1f));
            Assert.That(map.TryGetMissedCorner(out _, out _), Is.False);
        }

        [Test]
        public void Tabletop_OnlyTheLowCircleLeavesTheHighBandUnseen()
        {
            var synth = new SyntheticCapture { SweepFraction = 0.45f };
            var map = new CoverageMap(CaptureMode.Tabletop);
            foreach (var f in synth.Generate(CaptureMode.Tabletop))
            {
                map.Add(f);
            }

            Assert.That(map.PaintedRows()[0], Does.Contain("1"));
            Assert.That(map.PaintedRows()[1], Does.Not.Contain("1"));
            Assert.That(map.TryGetMissedCorner(out var dir, out _), Is.True);
            Assert.That(dir.y, Is.GreaterThan(0.3f), "arrow points up at the unseen high band");
        }

        [Test]
        public void Parallax_GrowsWithBaselineAndSaturates()
        {
            var still = new ParallaxMeter(CaptureMode.Room);
            var walked = new ParallaxMeter(CaptureMode.Room);
            for (int i = 0; i < 100; i++)
            {
                still.Add(new Vector3(0f, 1.4f, 0f));
                walked.Add(new Vector3(i * 0.03f, 1.4f, 0f));
            }

            Assert.That(still.Score, Is.EqualTo(0f));
            Assert.That(walked.Spread, Is.EqualTo(0.866f).Within(0.01f)); // 3 m line: L / sqrt(12)
            Assert.That(walked.Score, Is.EqualTo(1f));
        }

        [Test]
        public void Tracking_AsksToRelocalizeOnlyAfterASustainedLoss()
        {
            var meter = new TrackingMeter();
            for (int i = 0; i < 10; i++)
            {
                meter.Add(
                    Frame(
                        i,
                        i / 30f,
                        Vector3.zero,
                        Quaternion.identity,
                        tracking: TrackingQuality.Limited
                    )
                );
            }

            Assert.That(meter.NeedsRelocalize, Is.False);
            for (int i = 10; i < 30; i++)
            {
                meter.Add(
                    Frame(
                        i,
                        i / 30f,
                        Vector3.zero,
                        Quaternion.identity,
                        tracking: TrackingQuality.Limited
                    )
                );
            }

            Assert.That(meter.NeedsRelocalize, Is.True);
            meter.Add(Frame(30, 1f, Vector3.zero, Quaternion.identity));
            Assert.That(meter.NeedsRelocalize, Is.False);
            Assert.That(meter.NormalFraction, Is.EqualTo(1f / 31f).Within(1e-5f));
        }
    }
}
