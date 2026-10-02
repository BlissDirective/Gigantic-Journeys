using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Movement.Intent;
using GiganticJourneys.Movement.Query;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// The capsule's movement model on an ideal flat floor (M0-UNITY-03 AT-3 speeds, AT-4 jump
    /// heights and distances), stepped at 60 Hz without Unity physics.
    /// </summary>
    public class LocomotionMotorTests
    {
        const float Dt = 1f / 60f;
        static MovementConfig Config => MovementConfigLoader.Current;

        sealed class Sim
        {
            public readonly LocomotionMotor Motor;
            public Vector3 Position; // A
            public float MaxHeight;

            public Sim(bool assist = false)
            {
                Motor = new LocomotionMotor(
                    Config,
                    MovementScale.Create(
                        Config,
                        ProvisionalTuning.Body.DefaultRealHeightMeters,
                        ProvisionalTuning.Environment.DefaultScale
                    ),
                    assist
                );
            }

            public void Step(Vector2 stick, bool jump)
            {
                Position += Motor.Step(new IntentFrame(stick, jump, jump), Vector3.forward, Dt);
                var grounded = Position.y <= 0f;
                if (grounded)
                    Position.y = 0f;
                MaxHeight = Mathf.Max(MaxHeight, Position.y);
                Motor.AfterMove(grounded);
            }

            /// <summary>Jumps once and returns the take-off → landing horizontal distance.</summary>
            public float JumpAndLand(Vector2 stick)
            {
                var start = Position;
                MaxHeight = 0f;
                Step(stick, true);
                Assert.That(Motor.Grounded, Is.False, "left the ground");
                var frames = 0;
                while (!Motor.Grounded && frames++ < 600)
                    Step(stick, false);
                var d = Position - start;
                d.y = 0f;
                return d.magnitude;
            }
        }

        [TestCase(0.3f, Gait.Walk)]
        [TestCase(0.6f, Gait.Jog)]
        [TestCase(1f, Gait.Run)]
        public void GroundSpeed_Over5Seconds_WithinTwoPercent(float stick, Gait gait)
        {
            var sim = new Sim();
            // Run held 1.5 s becomes sprint (Bible §3.1); cap at the gait to time a full 5 s.
            sim.Motor.MaxGait = gait;
            var frames = Mathf.RoundToInt(5f / Dt);
            for (var i = 0; i < frames; i++)
                sim.Step(new Vector2(0f, stick), false);
            var speed = sim.Position.z / 5f;
            var expected = GaitSelector.SpeedA(gait, Config);
            Assert.That(speed, Is.EqualTo(expected).Within(expected * 0.02f), $"{gait} speed A/s");
            Assert.That(sim.Motor.Gait, Is.EqualTo(gait));
        }

        [Test]
        public void GaitCap_HoldsRunBelowSprint()
        {
            var sim = new Sim();
            sim.Motor.MaxGait = Gait.Walk;
            for (var i = 0; i < 200; i++)
                sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Gait, Is.EqualTo(Gait.Walk));
            Assert.That(sim.Motor.Velocity.z, Is.EqualTo(Config.Speeds.Walk).Within(1e-4f));
        }

        [Test]
        public void Sprint_Over5Seconds_WithinTwoPercent()
        {
            var sim = new Sim();
            var hold = Mathf.CeilToInt(Config.Intent.SprintHoldSec / Dt) + 1;
            for (var i = 0; i < hold; i++)
                sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Gait, Is.EqualTo(Gait.Sprint));
            var z0 = sim.Position.z;
            var frames = Mathf.RoundToInt(5f / Dt);
            for (var i = 0; i < frames; i++)
                sim.Step(Vector2.up, false);
            var speed = (sim.Position.z - z0) / 5f;
            Assert.That(
                speed,
                Is.EqualTo(Config.Speeds.Sprint).Within(Config.Speeds.Sprint * 0.02f)
            );
        }

        [Test]
        public void StandingJump_Height1Point1A_Distance1Point2A_WithinFivePercent()
        {
            var sim = new Sim();
            var distance = sim.JumpAndLand(new Vector2(0f, 0.3f)); // from standstill, walk-band stick
            Assert.That(sim.Motor.LastJumpVerb, Is.EqualTo(Verbs.StandingJump));
            Assert.That(
                sim.MaxHeight,
                Is.EqualTo(Config.Jump.StandingHeight).Within(Config.Jump.StandingHeight * 0.05f)
            );
            Assert.That(
                distance,
                Is.EqualTo(Config.Jump.StandingDistance)
                    .Within(Config.Jump.StandingDistance * 0.05f)
            );
        }

        [Test]
        public void RunningJump_Height1Point2A_Distance2Point4A_WithinFivePercent()
        {
            var sim = new Sim();
            for (var i = 0; i < 30; i++)
                sim.Step(Vector2.up, false); // run for 0.5 s
            var distance = sim.JumpAndLand(Vector2.up);
            Assert.That(sim.Motor.LastJumpVerb, Is.EqualTo(Verbs.RunningJump));
            Assert.That(
                sim.MaxHeight,
                Is.EqualTo(Config.Jump.RunningHeight).Within(Config.Jump.RunningHeight * 0.05f)
            );
            Assert.That(
                distance,
                Is.EqualTo(Config.Jump.RunningDistance).Within(Config.Jump.RunningDistance * 0.05f)
            );
        }

        [Test]
        public void JogJump_IsARunningJump()
        {
            var sim = new Sim();
            for (var i = 0; i < 30; i++)
                sim.Step(new Vector2(0f, 0.6f), false);
            var distance = sim.JumpAndLand(new Vector2(0f, 0.6f));
            Assert.That(sim.Motor.LastJumpVerb, Is.EqualTo(Verbs.RunningJump));
            Assert.That(
                distance,
                Is.EqualTo(Config.Jump.RunningDistance).Within(Config.Jump.RunningDistance * 0.05f)
            );
        }

        [Test]
        public void SprintJump_Distance3A_WithinFivePercent()
        {
            var sim = new Sim();
            for (var i = 0; i < 100; i++)
                sim.Step(Vector2.up, false); // > 1.5 s at run → sprint
            Assert.That(sim.Motor.Gait, Is.EqualTo(Gait.Sprint));
            var distance = sim.JumpAndLand(Vector2.up);
            Assert.That(sim.Motor.LastJumpVerb, Is.EqualTo(Verbs.SprintJump));
            Assert.That(
                distance,
                Is.EqualTo(Config.Jump.SprintDistance).Within(Config.Jump.SprintDistance * 0.05f)
            );
        }

        [Test]
        public void JumpWithoutStick_GoesStraightUp()
        {
            var sim = new Sim();
            var distance = sim.JumpAndLand(Vector2.zero);
            Assert.That(distance, Is.EqualTo(0f).Within(1e-4f));
            Assert.That(
                sim.MaxHeight,
                Is.EqualTo(Config.Jump.StandingHeight).Within(Config.Jump.StandingHeight * 0.05f)
            );
        }

        [Test]
        public void Assist_AddsTheJumpBonus()
        {
            var sim = new Sim(assist: true);
            sim.JumpAndLand(Vector2.zero);
            var expected = Config.Jump.StandingHeight * (1f + Config.Assist.JumpBonus);
            Assert.That(sim.MaxHeight, Is.EqualTo(expected).Within(expected * 0.05f));
        }

        [Test]
        public void NoAirControl_ArcIsCommittedAtTakeoff()
        {
            var sim = new Sim();
            sim.Step(Vector2.up, true);
            var vx0 = sim.Motor.Velocity.x;
            for (var i = 0; i < 20; i++)
                sim.Step(Vector2.right, false);
            Assert.That(sim.Motor.Velocity.x, Is.EqualTo(vx0));
        }

        [Test]
        public void BufferedJump_FiresOnLanding_InTheMotor()
        {
            var sim = new Sim();
            sim.Step(Vector2.zero, true);
            var frames = 0;
            // Fall until about 3 frames (50 ms) above the floor.
            while (sim.Motor.Velocity.y > 0f || sim.Position.y > -sim.Motor.Velocity.y * Dt * 3f)
            {
                sim.Step(Vector2.zero, false);
                Assert.That(frames++, Is.LessThan(600));
            }
            Assert.That(sim.Motor.Grounded, Is.False, "press happens in the air");
            sim.Step(Vector2.zero, true);
            Assert.That(sim.Motor.Velocity.y, Is.LessThan(0f), "an airborne press does not jump");
            var launched = false;
            for (var i = 0; i < 6 && !launched; i++)
            {
                sim.Step(Vector2.zero, false);
                launched = sim.Motor.Velocity.y > 0f;
            }
            Assert.That(launched, Is.True, "buffered press launched a second jump on landing");
        }

        [Test]
        public void Verbs_IdleWalkAirborneFall()
        {
            var sim = new Sim();
            sim.Step(Vector2.zero, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Idle));
            sim.Step(new Vector2(0f, 0.3f), false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Walk));
            sim.Step(Vector2.zero, true);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.StandingJump));
            for (var i = 0; i < 40; i++)
                sim.Step(Vector2.zero, false);
            Assert.That(
                sim.Motor.Verb,
                Is.EqualTo(Verbs.StandingJump),
                "the committed arc keeps its verb"
            );
            while (!sim.Motor.Grounded)
                sim.Step(Vector2.zero, false);
            sim.Step(Vector2.zero, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Idle), "landed");
        }

        [Test]
        public void WalkingOffAnEdge_IsAirborneThenFall()
        {
            var sim = new Sim();
            sim.Step(Vector2.up, false);
            sim.Position.y = 10f; // the floor drops away
            sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Grounded, Is.False);
            sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Airborne));
            for (var i = 0; i < 30; i++)
                sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Fall), "airborne > 0.35 s");
        }

        sealed class ToolProvider : IVerbProvider
        {
            public string Id => "test.tool";

            public bool TryPropose(
                in VerbContext context,
                MovementConfig config,
                out VerbProposal proposal
            )
            {
                proposal = new VerbProposal("grapple-test", VerbPriority.Tool);
                return context.Grounded;
            }
        }

        [Test]
        public void VerbRegistry_HigherPriorityProviderWins_WithoutCoreChanges()
        {
            var sim = new Sim();
            sim.Motor.Registry.Register(new ToolProvider());
            sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo("grapple-test"));
            Assert.Throws<System.InvalidOperationException>(() =>
                sim.Motor.Registry.Register(new ToolProvider())
            );
            Assert.That(sim.Motor.Registry.Unregister("test.tool"), Is.True);
            sim.Step(Vector2.up, false);
            Assert.That(sim.Motor.Verb, Is.EqualTo(Verbs.Run));
        }
    }
}
