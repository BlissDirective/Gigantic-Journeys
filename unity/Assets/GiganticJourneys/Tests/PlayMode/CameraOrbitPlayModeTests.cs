using System.Collections;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Movement.Intent;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Follow-camera orbit in the MovementTest scene (M1-UNITY-01 device-test request): orbiting
    /// turns the view around the character without moving it, and the stick then walks in the
    /// orbited camera's direction.
    /// </summary>
    public class CameraOrbitPlayModeTests
    {
        sealed class Push : IIntentSource
        {
            public Vector2 Move;

            public IntentFrame Read() => new IntentFrame(Move, false, false);
        }

        static Vector3 Flat(Vector3 v)
        {
            v.y = 0f;
            return v.normalized;
        }

        [UnityTest]
        public IEnumerator Orbit_TurnsTheView_AndTheStickFollowsIt()
        {
            yield return SceneManager.LoadSceneAsync("MovementTest", LoadSceneMode.Additive);
            var scene = SceneManager.GetSceneByName("MovementTest");
            try
            {
                var follow = Object.FindAnyObjectByType<FollowCamera>();
                var controller = Object.FindAnyObjectByType<TraversalController>();
                Assert.IsNotNull(follow);
                Assert.IsTrue(follow.TouchOrbit, "orbit is on in MovementTest");
                var push = new Push();
                controller.IntentOverride = push;
                for (var i = 0; i < 10; i++)
                    yield return null;
                var before = Flat(follow.transform.forward);
                var start = controller.transform.position;
                var distBefore = Vector3.Distance(follow.transform.position, start);

                follow.Orbit(90f, 0f);
                for (var i = 0; i < 3; i++)
                    yield return null;
                var after = Flat(follow.transform.forward);
                Assert.That(
                    Vector3.SignedAngle(before, after, Vector3.up),
                    Is.EqualTo(90f).Within(2f)
                );
                Assert.That(
                    Vector3.Distance(controller.transform.position, start),
                    Is.LessThan(0.01f),
                    "orbit alone does not move the character"
                );
                Assert.That(
                    Vector3.Distance(follow.transform.position, controller.transform.position),
                    Is.EqualTo(distBefore).Within(distBefore * 0.05f),
                    "same follow distance"
                );

                push.Move = Vector2.up;
                for (var i = 0; i < 30; i++)
                    yield return null;
                push.Move = Vector2.zero;
                var walked = Flat(controller.transform.position - start);
                Assert.That(
                    Vector3.Angle(walked, after),
                    Is.LessThan(15f),
                    "stick is camera-relative"
                );
            }
            finally
            {
                var c = Object.FindAnyObjectByType<TraversalController>();
                if (c != null)
                    c.IntentOverride = null;
            }
            yield return SceneManager.UnloadSceneAsync(scene);
        }
    }
}
