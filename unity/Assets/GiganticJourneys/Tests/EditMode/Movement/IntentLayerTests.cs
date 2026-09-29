using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Intent;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>Intent layer: coyote time, jump buffer, gait bands, touch stick (M0-UNITY-03 AT-4, AT-5).</summary>
    public class IntentLayerTests
    {
        const float Dt = 1f / 60f;
        static MovementConfig Config => MovementConfigLoader.Current;

        [Test]
        public void Windows_ComeFromMovementJson()
        {
            var t = new JumpTiming(Config);
            Assert.That(t.CoyoteSeconds, Is.EqualTo(0.100f).Within(1e-6f));
            Assert.That(t.BufferSeconds, Is.EqualTo(0.120f).Within(1e-6f));
            Assert.That(
                new JumpTiming(Config, assist: true).CoyoteSeconds,
                Is.EqualTo(0.200f).Within(1e-6f)
            );
        }

        [Test]
        public void GroundedPress_FiresImmediately()
        {
            var t = new JumpTiming(Config);
            Assert.That(t.Tick(1f, true, true), Is.True);
        }

        [TestCase(0.050f, true)]
        [TestCase(0.095f, true)]
        [TestCase(0.105f, false)]
        [TestCase(0.200f, false)]
        public void Coyote_JumpAfterWalkingOffAnEdge(float sinceEdge, bool fires)
        {
            var t = new JumpTiming(Config);
            Assert.That(t.Tick(1f, true, false), Is.False); // last grounded frame
            Assert.That(t.Tick(1f + sinceEdge, false, true), Is.EqualTo(fires));
        }

        [Test]
        public void Coyote_DoesNotGrantASecondJump()
        {
            var t = new JumpTiming(Config);
            Assert.That(t.Tick(1f, true, true), Is.True);
            Assert.That(t.Tick(1f + 0.05f, false, true), Is.False);
        }

        [TestCase(0.050f, true)]
        [TestCase(0.115f, true)]
        [TestCase(0.125f, false)]
        [TestCase(0.300f, false)]
        public void Buffer_PressBeforeLandingFiresOnLanding(float beforeLanding, bool fires)
        {
            var t = new JumpTiming(Config);
            t.Tick(0f, true, true); // take off
            Assert.That(
                t.Tick(2f - beforeLanding, false, true),
                Is.False,
                "airborne press is buffered"
            );
            Assert.That(t.Tick(2f, true, false), Is.EqualTo(fires));
        }

        [Test]
        public void Buffer_IsConsumedOnce()
        {
            var t = new JumpTiming(Config);
            t.Tick(0f, true, true);
            t.Tick(1.95f, false, true);
            Assert.That(t.Tick(2f, true, false), Is.True);
            Assert.That(t.Tick(2f + Dt, true, false), Is.False);
        }

        [TestCase(0.05f, Gait.Idle)]
        [TestCase(0.3f, Gait.Walk)]
        [TestCase(0.39f, Gait.Walk)]
        [TestCase(0.4f, Gait.Jog)]
        [TestCase(0.85f, Gait.Jog)]
        [TestCase(0.9f, Gait.Run)]
        [TestCase(1f, Gait.Run)]
        public void Gait_StickBands_Bible31(float stick, Gait expected)
        {
            Assert.That(GaitSelector.Band(stick), Is.EqualTo(expected));
        }

        [Test]
        public void Gait_RunHeld1Point5Seconds_BecomesSprint_AndResets()
        {
            var g = new GaitSelector();
            var t = 0f;
            while (t < 1.45f)
            {
                Assert.That(g.Update(1f, Dt), Is.EqualTo(Gait.Run));
                t += Dt;
            }
            for (var i = 0; i < 6; i++)
                g.Update(1f, Dt);
            Assert.That(g.Current, Is.EqualTo(Gait.Sprint));
            Assert.That(g.Update(0.6f, Dt), Is.EqualTo(Gait.Jog));
            Assert.That(g.Update(1f, Dt), Is.EqualTo(Gait.Run));
        }

        [Test]
        public void Gait_SpeedsComeFromMovementJson()
        {
            Assert.That(GaitSelector.SpeedA(Gait.Walk, Config), Is.EqualTo(Config.Speeds.Walk));
            Assert.That(GaitSelector.SpeedA(Gait.Jog, Config), Is.EqualTo(Config.Speeds.Jog));
            Assert.That(GaitSelector.SpeedA(Gait.Run, Config), Is.EqualTo(Config.Speeds.Run));
            Assert.That(GaitSelector.SpeedA(Gait.Sprint, Config), Is.EqualTo(Config.Speeds.Sprint));
            Assert.That(GaitSelector.SpeedA(Gait.Idle, Config), Is.EqualTo(0f));
        }

        [Test]
        public void FloatingStick_OriginAtFirstTouch_ClampsToRadius()
        {
            var s = new FloatingStick();
            s.Begin(7, new Vector2(100, 100));
            s.Drag(new Vector2(150, 100), 100f);
            Assert.That(s.Value.x, Is.EqualTo(0.5f).Within(1e-5f));
            s.Drag(new Vector2(100, 400), 100f);
            Assert.That(s.Value.magnitude, Is.EqualTo(1f).Within(1e-5f));
            Assert.That(s.TouchId, Is.EqualTo(7));
            s.End();
            Assert.That(s.Active, Is.False);
            Assert.That(s.Value, Is.EqualTo(Vector2.zero));
        }

        [Test]
        public void TouchLayout_StickInLeftThird_JumpPadLowRight()
        {
            var safe = new Rect(0, 0, 2556, 1179); // iPhone 15 Pro landscape, px
            var l = new TouchLayout(safe, 3f);
            Assert.That(l.InStickZone(new Vector2(800, 600)), Is.True);
            Assert.That(l.InStickZone(new Vector2(900, 600)), Is.False);
            Assert.That(l.JumpRadius * 2f, Is.EqualTo(72f * 3f).Within(1e-3f), "72 pt jump pad");
            Assert.That(l.OnJumpPad(l.JumpCenter), Is.True);
            Assert.That(l.JumpCenter.x, Is.GreaterThan(safe.width * 0.8f));
            Assert.That(l.JumpCenter.y, Is.LessThan(safe.height * 0.3f));
            Assert.That(TouchLayout.PixelsPerPoint(460f), Is.EqualTo(3f));
            Assert.That(TouchLayout.PixelsPerPoint(0f), Is.EqualTo(1f));
        }

        sealed class Fixed : IIntentSource
        {
            readonly IntentFrame _f;

            public Fixed(IntentFrame f) => _f = f;

            public IntentFrame Read() => _f;
        }

        [Test]
        public void Aggregator_StrongestStickWins_AnyJumpCounts()
        {
            var a = new IntentAggregator();
            a.Add(new Fixed(new IntentFrame(new Vector2(0.2f, 0f), false, false)));
            a.Add(new Fixed(new IntentFrame(new Vector2(0f, 0.9f), false, false)));
            a.Add(new Fixed(new IntentFrame(Vector2.zero, true, true)));
            var f = a.Read();
            Assert.That(f.Move, Is.EqualTo(new Vector2(0f, 0.9f)));
            Assert.That(f.JumpPressed, Is.True);
            Assert.That(f.JumpHeld, Is.True);
        }

        [Test]
        public void Trajectory_PredictsSixTenthsOfASecondAhead()
        {
            var samples = new Vector3[6];
            TrajectoryPredictor.Predict(Vector3.zero, new Vector3(0, 0, 2f), 4f, true, samples);
            Assert.That(samples[5].z, Is.EqualTo(1.2f).Within(1e-4f));
            Assert.That(samples[5].y, Is.EqualTo(0f));
        }
    }
}
