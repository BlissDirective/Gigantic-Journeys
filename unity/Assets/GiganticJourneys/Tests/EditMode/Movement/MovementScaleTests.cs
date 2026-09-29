using GiganticJourneys.Movement;
using NUnit.Framework;

namespace GiganticJourneys.Tests
{
    public class MovementScaleTests
    {
        static MovementConfig Config => MovementConfigLoader.Current;

        [Test]
        public void OneToTwelve_DefaultAvatar_IsAbout14Point6Centimeters()
        {
            var s = MovementScale.Create(Config, 1.75f, 12f);
            Assert.That(s.WorldUnitsPerA, Is.EqualTo(0.14583f).Within(1e-4f));
            Assert.That(s.ToA(s.ToWorld(2.5f)), Is.EqualTo(2.5f).Within(1e-5f));
        }

        [Test]
        public void Gravity_FollowsBibleSection1()
        {
            // Bible §1: g = 9.81 × (1/scale) × gravityScale in world m/s².
            var s = MovementScale.Create(Config, 1.75f, 12f);
            var worldG = s.GravityA * s.WorldUnitsPerA;
            Assert.That(worldG, Is.EqualTo(9.81f * (1f / 12f) * Config.GravityScale).Within(1e-4f));
            // In A units gravity does not depend on the environment multiplier.
            Assert.That(
                MovementScale.Create(Config, 1.75f, 1f).GravityA,
                Is.EqualTo(s.GravityA).Within(1e-5f)
            );
        }

        [Test]
        public void Ballistics_ApexAndRangeMatchTheRequest()
        {
            var arc = JumpBallistics.Solve(1.1f, 1.2f, 4.5f);
            var apex = arc.VerticalSpeed * arc.VerticalSpeed / (2f * 4.5f);
            Assert.That(apex, Is.EqualTo(1.1f).Within(1e-4f));
            Assert.That(arc.HorizontalSpeed * arc.AirTime, Is.EqualTo(1.2f).Within(1e-4f));
        }
    }
}
