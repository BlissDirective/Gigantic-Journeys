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

        [Test]
        public void ViewYaw_ClampsIntoTheRoomWindow_OrStaysFree()
        {
            var free = FollowCamera.OrbitLimits.Default;
            Assert.AreEqual(170f, FollowCamera.ClampViewYaw(170f, free), 1e-4f);
            var room = free;
            room.YawCenterDeg = 5f;
            room.YawHalfRangeDeg = 45f;
            Assert.AreEqual(30f, FollowCamera.ClampViewYaw(30f, room), 1e-4f);
            Assert.AreEqual(50f, FollowCamera.ClampViewYaw(120f, room), 1e-4f);
            Assert.AreEqual(-40f, FollowCamera.ClampViewYaw(-100f, room), 1e-4f);
            Assert.AreEqual(50f, FollowCamera.ClampViewYaw(-190f + 360f, room), 1e-4f, "wraps");
        }

        [Test]
        public void EyeRadius_PullsInAtOnce_AndSpringsBackSmoothly()
        {
            var v = 0f;
            Assert.AreEqual(1.2f, FollowCamera.NextEyeRadius(-1f, 1.2f, ref v, 0.35f, 1f / 60f));
            // An obstacle: straight in, no easing (never clip through it).
            Assert.AreEqual(0.1f, FollowCamera.NextEyeRadius(1.2f, 0.1f, ref v, 0.35f, 1f / 60f));
            Assert.AreEqual(0f, v);
            // Clear again: eases out, monotonically, never past the allowed distance.
            var r = 0.1f;
            var prev = r;
            for (var i = 0; i < 6; i++)
            {
                r = FollowCamera.NextEyeRadius(r, 1.2f, ref v, 0.35f, 1f / 60f);
                Assert.That(r, Is.GreaterThan(prev).And.LessThanOrEqualTo(1.2f));
                prev = r;
            }
            Assert.That(r, Is.LessThan(0.6f), "a tenth of a second in it is still on its way out");
            for (var i = 0; i < 120; i++)
                r = FollowCamera.NextEyeRadius(r, 1.2f, ref v, 0.35f, 1f / 60f);
            Assert.That(r, Is.EqualTo(1.2f).Within(0.01f), "back out within two seconds");
            Assert.AreEqual(0.5f, FollowCamera.NextEyeRadius(0.1f, 0.5f, ref v, 0f, 1f / 60f));
        }

        [Test]
        public void Character_IsHiddenOnlyWithTheEyeInsideTheFadeDistance()
        {
            Assert.IsTrue(FollowCamera.HidesTarget(0.1f, 0.22f));
            Assert.IsFalse(FollowCamera.HidesTarget(0.22f, 0.22f));
            Assert.IsFalse(FollowCamera.HidesTarget(0.6f, 0.22f));
        }

        [Test]
        public void LookingUp_KeepsTheEyeOut_AtTheGroundInsteadOfInsideTheCharacter()
        {
            var fwd = Vector3.forward;
            // Level or above: the plain orbit direction.
            var level = FollowCamera.EyeDirection(fwd, 20f, 0.6f, 0.05f);
            Assert.That(level.y, Is.EqualTo(Mathf.Sin(20f * Mathf.Deg2Rad)).Within(1e-5f));
            // Looking up from -60 degrees with the look-at point 5 cm above the floor: the eye
            // stays at the full radius, exactly at the floor, not 2 cm from the character.
            var up = FollowCamera.EyeDirection(fwd, -60f, 0.6f, 0.05f);
            Assert.That(up.magnitude, Is.EqualTo(1f).Within(1e-5f));
            Assert.That(up.y * 0.6f, Is.EqualTo(-0.05f).Within(1e-4f));
            Assert.That(up.z, Is.LessThan(-0.99f), "still behind the character");
            // Plenty of room under the look-at point: the asked-for angle.
            var high = FollowCamera.EyeDirection(fwd, -30f, 0.6f, 2f);
            Assert.That(high.y, Is.EqualTo(-0.5f).Within(1e-4f));
        }

        [Test]
        public void CameraBox_PullsTheEyeInAlongTheRay()
        {
            var box = new Bounds(Vector3.zero, new Vector3(4f, 2f, 10f));
            Assert.AreEqual(2f, FollowCamera.ExitDistance(box, Vector3.zero, Vector3.right), 1e-4f);
            Assert.AreEqual(1f, FollowCamera.ExitDistance(box, Vector3.zero, Vector3.up), 1e-4f);
            var diag = new Vector3(0f, 1f, -1f).normalized;
            Assert.AreEqual(
                Mathf.Sqrt(2f),
                FollowCamera.ExitDistance(box, Vector3.zero, diag),
                1e-4f
            );
            Assert.IsTrue(
                float.IsPositiveInfinity(
                    FollowCamera.ExitDistance(box, new Vector3(9f, 0f, 0f), Vector3.right)
                ),
                "outside the box: nothing to keep in"
            );
        }

        [Test]
        public void RoomLimits_NarrowElevationAndZoom()
        {
            var room = FollowCamera.OrbitLimits.Default;
            room.MaxElevationDeg = 22f;
            room.MaxZoom = 1.3f;
            Assert.AreEqual(22f, FollowCamera.ElevationDeg(1f, 1f, 60f, room), 1e-4f);
            var go = new GameObject("cam", typeof(Camera));
            try
            {
                var f = go.AddComponent<FollowCamera>();
                f.ZoomBy(2f);
                f.Limits = room;
                Assert.AreEqual(1.3f, f.Zoom, 1e-4f, "a narrower range re-clamps the zoom");
                f.ZoomBy(5f);
                Assert.AreEqual(1.3f, f.Zoom, 1e-4f);
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }
    }
}
