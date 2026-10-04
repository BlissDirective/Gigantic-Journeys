using System.Collections.Generic;
using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Movement.Intent;
using GiganticJourneys.Splats.Sorting;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Touch camera orbit (M1-UNITY-01 device-test request; Bible §8 orbit) and the
    /// motion-gated Tier B sort.
    /// </summary>
    public class CameraOrbitTests
    {
        const float Ppp = 3f;
        static readonly TouchLayout Layout = new TouchLayout(new Rect(0, 0, 2532, 1170), Ppp);

        static List<OrbitTouch> One(int id, Vector2 start, Vector2 pos, bool down = true) =>
            new List<OrbitTouch> { new OrbitTouch(id, start, pos, down) };

        // Mid-screen, upper half: outside the left-third stick zone and away from the jump pad.
        static readonly Vector2 Free = new Vector2(1500, 800);

        [Test]
        public void OneFingerDrag_OutsideStickAndJump_Orbits_AfterTheDeadzone()
        {
            var g = new CameraOrbitGesture();
            Assert.IsFalse(Layout.InStickZone(Free) || Layout.OnJumpPad(Free));
            var d = g.Update(One(1, Free, Free), Layout, Ppp);
            Assert.AreEqual(0f, d.YawDeg);
            // 5 pt: still inside the 10 pt deadzone, so a tap on a button never turns the view.
            d = g.Update(One(1, Free, Free + new Vector2(15, 0)), Layout, Ppp);
            Assert.AreEqual(0f, d.YawDeg);
            Assert.IsFalse(g.Orbiting);
            d = g.Update(One(1, Free, Free + new Vector2(60, 0)), Layout, Ppp);
            Assert.IsTrue(g.Orbiting);
            d = g.Update(One(1, Free, Free + new Vector2(120, 30)), Layout, Ppp);
            Assert.That(
                d.YawDeg,
                Is.EqualTo(60f / Ppp * ProvisionalTuning.CameraOrbit.YawDegPerPt).Within(1e-4f)
            );
            Assert.That(d.PitchDeg, Is.LessThan(0f), "dragging up lowers the camera");
            d = g.Update(One(1, Free, Free + new Vector2(120, 30), false), Layout, Ppp);
            Assert.AreEqual(0f, d.YawDeg);
            Assert.IsFalse(g.Orbiting);
        }

        [Test]
        public void StickAndJumpTouches_NeverOrbit()
        {
            var g = new CameraOrbitGesture();
            var stick = new Vector2(200, 300);
            var jump = Layout.JumpCenter;
            Assert.IsTrue(Layout.InStickZone(stick));
            for (var i = 0; i < 4; i++)
            {
                var touches = new List<OrbitTouch>
                {
                    new OrbitTouch(1, stick, stick + new Vector2(80 * i, 0), true),
                    new OrbitTouch(2, jump, jump + new Vector2(0, 60 * i), true),
                };
                var d = g.Update(touches, Layout, Ppp);
                Assert.AreEqual(0f, d.YawDeg);
                Assert.AreEqual(0f, d.PitchDeg);
                Assert.AreEqual(1f, d.Zoom);
            }
            Assert.IsFalse(g.Orbiting);
        }

        [Test]
        public void ThreeFingerTap_IsLeftToTheOverlay_UntilThoseFingersLift()
        {
            var g = new CameraOrbitGesture();
            var b = Free + new Vector2(200, 0);
            var c = Free + new Vector2(400, 0);
            var three = new List<OrbitTouch>
            {
                new OrbitTouch(1, Free, Free, true),
                new OrbitTouch(2, b, b, true),
                new OrbitTouch(3, c, c, true),
            };
            Assert.AreEqual(0f, g.Update(three, Layout, Ppp).YawDeg);
            // Two lift; the third finger drags: still ignored (it was part of the tap).
            var d = g.Update(One(1, Free, Free + new Vector2(200, 0)), Layout, Ppp);
            d = g.Update(One(1, Free, Free + new Vector2(300, 0)), Layout, Ppp);
            Assert.AreEqual(0f, d.YawDeg);
            Assert.IsFalse(g.Orbiting);
            // After it lifts, a fresh finger orbits again.
            g.Update(new List<OrbitTouch>(), Layout, Ppp);
            g.Update(One(4, Free, Free + new Vector2(60, 0)), Layout, Ppp);
            d = g.Update(One(4, Free, Free + new Vector2(90, 0)), Layout, Ppp);
            Assert.That(d.YawDeg, Is.GreaterThan(0f));
        }

        [Test]
        public void TwoFingerPinch_Zooms()
        {
            var g = new CameraOrbitGesture();
            var a = new Vector2(1300, 700);
            var b = new Vector2(1700, 700);
            List<OrbitTouch> Pair(float spread) =>
                new List<OrbitTouch>
                {
                    new OrbitTouch(1, a, a - new Vector2(spread, 0), true),
                    new OrbitTouch(2, b, b + new Vector2(spread, 0), true),
                };
            g.Update(Pair(0), Layout, Ppp);
            var d = g.Update(Pair(100), Layout, Ppp);
            Assert.That(d.Zoom, Is.LessThan(1f), "fingers apart zoom in");
            Assert.AreEqual(0f, d.YawDeg, "no orbit while pinching");
            d = g.Update(Pair(20), Layout, Ppp);
            Assert.That(d.Zoom, Is.GreaterThan(1f), "fingers together zoom out");
        }

        [Test]
        public void Elevation_IsClamped_AndZoomStaysInRange()
        {
            Assert.That(
                FollowCamera.ElevationDeg(1f, 1f, 0f),
                Is.EqualTo(45f).Within(1e-3f),
                "no orbit = the scene's elevation"
            );
            Assert.AreEqual(
                ProvisionalTuning.CameraOrbit.MaxElevationDeg,
                FollowCamera.ElevationDeg(1f, 1f, 500f)
            );
            Assert.AreEqual(
                ProvisionalTuning.CameraOrbit.MinElevationDeg,
                FollowCamera.ElevationDeg(1f, 1f, -500f)
            );
            var go = new GameObject("cam", typeof(Camera));
            try
            {
                var f = go.AddComponent<FollowCamera>();
                f.Orbit(350f, 0f);
                Assert.That(f.OrbitYawDeg, Is.EqualTo(-10f).Within(1e-3f), "yaw wraps");
                f.ZoomBy(100f);
                Assert.AreEqual(ProvisionalTuning.CameraOrbit.MaxZoom, f.Zoom);
                f.ZoomBy(0.0001f);
                Assert.AreEqual(ProvisionalTuning.CameraOrbit.MinZoom, f.Zoom);
                f.ZoomBy(float.NaN);
                Assert.AreEqual(ProvisionalTuning.CameraOrbit.MinZoom, f.Zoom);
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void TierBSort_SkipsWhileTheCameraIsStill()
        {
            var p = new Vector3(1, 2, 3);
            var r = Quaternion.Euler(10, 20, 0);
            Assert.IsTrue(MetalSafeSplatSort.NeedsResort(false, p, r, p, r, 0.03f, 1.5f), "first");
            Assert.IsTrue(MetalSafeSplatSort.NeedsResort(true, p, r, p, r, 0f, 0f), "gating off");
            Assert.IsFalse(MetalSafeSplatSort.NeedsResort(true, p, r, p, r, 0.03f, 1.5f), "still");
            Assert.IsFalse(
                MetalSafeSplatSort.NeedsResort(
                    true,
                    p,
                    r,
                    p + Vector3.right * 0.01f,
                    r,
                    0.03f,
                    1.5f
                )
            );
            Assert.IsTrue(
                MetalSafeSplatSort.NeedsResort(
                    true,
                    p,
                    r,
                    p + Vector3.right * 0.05f,
                    r,
                    0.03f,
                    1.5f
                ),
                "moved"
            );
            Assert.IsTrue(
                MetalSafeSplatSort.NeedsResort(
                    true,
                    p,
                    r,
                    p,
                    r * Quaternion.Euler(0, 2f, 0),
                    0.03f,
                    1.5f
                ),
                "turned"
            );
        }
    }
}
