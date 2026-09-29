using GiganticJourneys.Movement.Intent;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Touch-control customization (DESIGN_SYSTEM decision 5: drag-to-reposition, 56–96 pt size,
    /// left-handed mirror, opacity, Reset) and the resize-safe layout (BACKLOG, M1-DUO-01).
    /// </summary>
    public class ControlCustomizationTests
    {
        const string TestKey = "gj.controls.test";
        static readonly Rect Safe = new Rect(177, 63, 2202, 1116); // iPhone 15 Pro landscape safe area, px
        const float Ppp = 3f;

        [TearDown]
        public void CleanPrefs() => PlayerPrefs.DeleteKey(TestKey);

        [Test]
        public void Default_MatchesTheUncustomizedLayout()
        {
            var a = new TouchLayout(Safe, Ppp);
            var b = new TouchLayout(Safe, Ppp, ControlCustomization.Default);
            Assert.That(b.JumpCenter, Is.EqualTo(a.JumpCenter));
            Assert.That(b.JumpRadius, Is.EqualTo(a.JumpRadius));
            Assert.That(b.StickZone, Is.EqualTo(a.StickZone));
            Assert.That(a.JumpRadius * 2f, Is.EqualTo(72f * Ppp).Within(1e-3f));
            Assert.That(a.LeftHanded, Is.False);
            Assert.That(ControlCustomization.Default.IsDefault, Is.True);
        }

        [TestCase(56f, 56f)]
        [TestCase(96f, 96f)]
        [TestCase(30f, 56f)]
        [TestCase(200f, 96f)]
        public void SizeSlider_IsClampedTo56Through96Points(float requested, float expected)
        {
            var c = new ControlCustomization { buttonSizePt = requested };
            var l = new TouchLayout(Safe, Ppp, c);
            Assert.That(l.JumpRadius * 2f, Is.EqualTo(expected * Ppp).Within(1e-3f));
            Assert.That(l.OnJumpPad(l.JumpCenter), Is.True);
        }

        [Test]
        public void LeftHanded_MirrorsStickZoneAndJumpPad()
        {
            var right = new TouchLayout(Safe, Ppp);
            var left = new TouchLayout(Safe, Ppp, new ControlCustomization { leftHanded = true });
            Assert.That(left.LeftHanded, Is.True);
            Assert.That(
                left.StickZone.xMax,
                Is.EqualTo(Safe.xMax).Within(1e-3f),
                "stick zone on the right third"
            );
            Assert.That(left.StickZone.width, Is.EqualTo(right.StickZone.width).Within(1e-3f));
            Assert.That(left.InStickZone(new Vector2(Safe.xMax - 10f, Safe.center.y)), Is.True);
            Assert.That(left.InStickZone(new Vector2(Safe.xMin + 10f, Safe.center.y)), Is.False);
            var mirroredX = Safe.xMin + (Safe.xMax - right.JumpCenter.x);
            Assert.That(
                left.JumpCenter.x,
                Is.EqualTo(mirroredX).Within(1e-3f),
                "jump pad low-left"
            );
            Assert.That(left.JumpCenter.y, Is.EqualTo(right.JumpCenter.y).Within(1e-3f));
        }

        [Test]
        public void DragOffset_MovesThePadTowardTheCentreInBothHands()
        {
            var offset = new Vector2(100f, 50f);
            var r0 = new TouchLayout(Safe, Ppp);
            var r1 = new TouchLayout(Safe, Ppp, new ControlCustomization { jumpOffsetPt = offset });
            Assert.That(r1.JumpCenter - r0.JumpCenter, Is.EqualTo(new Vector2(-300f, 150f)));
            var l0 = new TouchLayout(Safe, Ppp, new ControlCustomization { leftHanded = true });
            var l1 = new TouchLayout(
                Safe,
                Ppp,
                new ControlCustomization { leftHanded = true, jumpOffsetPt = offset }
            );
            Assert.That(l1.JumpCenter - l0.JumpCenter, Is.EqualTo(new Vector2(300f, 150f)));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void ExtremeOffsets_KeepThePadInsideTheSafeAreaAndOutOfTheStickZone(bool leftHanded)
        {
            foreach (
                var o in new[]
                {
                    new Vector2(-1e4f, -1e4f),
                    new Vector2(1e4f, 1e4f),
                    new Vector2(1e4f, -1e4f),
                }
            )
            {
                var l = new TouchLayout(
                    Safe,
                    Ppp,
                    new ControlCustomization
                    {
                        leftHanded = leftHanded,
                        jumpOffsetPt = o,
                        buttonSizePt = 96f,
                    }
                );
                var r = l.JumpRadius;
                Assert.That(l.JumpCenter.x - r, Is.GreaterThanOrEqualTo(Safe.xMin - 1e-3f), $"{o}");
                Assert.That(l.JumpCenter.x + r, Is.LessThanOrEqualTo(Safe.xMax + 1e-3f), $"{o}");
                Assert.That(l.JumpCenter.y - r, Is.GreaterThanOrEqualTo(Safe.yMin - 1e-3f), $"{o}");
                Assert.That(l.JumpCenter.y + r, Is.LessThanOrEqualTo(Safe.yMax + 1e-3f), $"{o}");
                var nearest = new Vector2(
                    Mathf.Clamp(l.JumpCenter.x, l.StickZone.xMin, l.StickZone.xMax),
                    Mathf.Clamp(l.JumpCenter.y, l.StickZone.yMin, l.StickZone.yMax)
                );
                Assert.That(
                    (nearest - l.JumpCenter).magnitude,
                    Is.GreaterThanOrEqualTo(r - 1e-3f),
                    $"pad clear of the stick zone at {o}"
                );
            }
        }

        [Test]
        public void Json_RoundTripsAndClamps()
        {
            var c = new ControlCustomization
            {
                buttonSizePt = 88f,
                opacity = 0.35f,
                leftHanded = true,
                jumpOffsetPt = new Vector2(12f, -8f),
            };
            var back = ControlCustomization.FromJson(c.ToJson());
            Assert.That(back, Is.EqualTo(c));
            var wild = ControlCustomization.FromJson(
                "{\"version\":1,\"buttonSizePt\":500,\"opacity\":0.01,\"leftHanded\":false,\"jumpOffsetPt\":{\"x\":9999,\"y\":-9999}}"
            );
            Assert.That(wild.buttonSizePt, Is.EqualTo(ControlCustomization.MaxSizePt));
            Assert.That(wild.opacity, Is.EqualTo(ControlCustomization.MinOpacity));
            Assert.That(
                wild.jumpOffsetPt,
                Is.EqualTo(
                    new Vector2(ControlCustomization.MaxOffsetPt, -ControlCustomization.MaxOffsetPt)
                )
            );
        }

        [TestCase("")]
        [TestCase("not json")]
        [TestCase("{\"version\":2,\"buttonSizePt\":60}")]
        [TestCase("{\"version\":0,\"buttonSizePt\":60}")]
        public void Json_BadOrNewerData_FallsBackToDefault(string json)
        {
            Assert.That(ControlCustomization.FromJson(json).IsDefault, Is.True);
        }

        [Test]
        public void NonFiniteValues_FallBackToDefaults()
        {
            var c = new ControlCustomization
            {
                buttonSizePt = float.NaN,
                opacity = float.PositiveInfinity,
                jumpOffsetPt = new Vector2(float.NaN, float.NegativeInfinity),
            }.Clamped();
            Assert.That(c.IsDefault, Is.True);
        }

        [Test]
        public void Store_SavesLoadsAndResets()
        {
            Assert.That(
                ControlCustomizationStore.Load(TestKey).IsDefault,
                Is.True,
                "nothing saved yet"
            );
            var c = new ControlCustomization { buttonSizePt = 60f, leftHanded = true };
            ControlCustomizationStore.Save(c, TestKey);
            Assert.That(ControlCustomizationStore.Load(TestKey), Is.EqualTo(c));
            Assert.That(ControlCustomizationStore.Reset(TestKey).IsDefault, Is.True);
            Assert.That(
                ControlCustomizationStore.Load(TestKey).IsDefault,
                Is.True,
                "Reset clears the saved layout"
            );
        }

        [Test]
        public void GeometryDiffers_DetectsFoldAndSplitView()
        {
            var a = new TouchLayout(Safe, Ppp);
            Assert.That(a.GeometryDiffers(new TouchLayout(Safe, Ppp)), Is.False);
            Assert.That(
                a.GeometryDiffers(
                    new TouchLayout(Safe, Ppp, new ControlCustomization { leftHanded = true })
                ),
                Is.False,
                "a customization change is not a geometry change"
            );
            Assert.That(
                a.GeometryDiffers(new TouchLayout(new Rect(0, 0, 1100, 1116), Ppp)),
                Is.True
            );
        }
    }
}
