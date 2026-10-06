#if UNITY_EDITOR
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using GiganticJourneys.DebugTools;
using GiganticJourneys.DeviceTest;
using NUnit.Framework;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// The device-test splat room in play mode (ticket M1-UNITY-01): the character spawns on
    /// the invisible floor and stays inside the room whether or not this checkout has the splat
    /// (CI has none; only the internal-debug iOS lane fetches it), and the label and the debug
    /// report describe the room.
    /// </summary>
    public class SplatRoomPlayModeTests
    {
        const string ScenePath = "Assets/Scenes/DeviceTest/SplatRoom.unity";

        // Additive and unloaded afterwards: a leftover room (its character, floor and walls)
        // would leak into later scene tests (CI run 37132813149).
        [UnityTearDown]
        public IEnumerator UnloadRoom()
        {
            var scene = SceneManager.GetSceneByPath(ScenePath);
            if (scene.isLoaded)
                yield return SceneManager.UnloadSceneAsync(scene);
        }

        [UnityTest]
        public IEnumerator SplatRoom_SpawnsCharacterOnFloor_AndReportsTheRoom()
        {
            yield return EditorSceneManager.LoadSceneAsyncInPlayMode(
                ScenePath,
                new LoadSceneParameters(LoadSceneMode.Additive)
            );
            yield return null;
            Assert.IsTrue(SceneManager.GetSceneByPath(ScenePath).isLoaded);
            var loader = Object.FindFirstObjectByType<SplatRoomLoader>();
            Assert.IsNotNull(loader, "loader in the scene");
            Assert.IsNotNull(loader.Descriptor, loader.Error);
            Assert.IsNotNull(loader.Colliders, "floor + walls built");
            Assert.AreEqual(
                5 + loader.Descriptor.blockers.Length,
                loader.Colliders.childCount,
                "floor, four walls and the furniture blockers"
            );

            for (var i = 0; i < 60; i++)
                yield return null;
            var p = loader.player.position;
            var spawn = loader.Descriptor.Spawn;
            Assert.That(p.y, Is.InRange(-0.05f, 0.3f), "character rests on the floor, not falling");
            Assert.That(new Vector2(p.x - spawn.x, p.z - spawn.z).magnitude, Is.LessThan(0.5f));

            // Camera limits from the training coverage: eye inside the camera box, occluders built.
            var d = loader.Descriptor;
            Assert.IsNotNull(loader.Follow, "room camera found");
            Assert.IsTrue(loader.Follow.CameraCollision, "camera collision on in the room");
            var limits = SplatRoomLoader.OrbitLimitsFor(d);
            Assert.AreEqual(limits.YawHalfRangeDeg, loader.Follow.Limits.YawHalfRangeDeg);
            Assert.AreEqual(limits.MaxElevationDeg, loader.Follow.Limits.MaxElevationDeg);
            if (d.HasCameraBox)
            {
                var box = d.CameraBox;
                box.Expand(0.01f);
                box.SetMinMax(new Vector3(box.min.x, -0.05f, box.min.z), box.max); // low eyes: ground clamp
                Assert.IsTrue(
                    box.Contains(loader.Follow.transform.position),
                    $"eye {loader.Follow.transform.position} inside the camera box {box}"
                );
            }
            Assert.AreEqual(d.occluders.Length, loader.Occluders.childCount, "occluders built");
            loader.Follow.Orbit(170f, 80f);
            loader.Follow.ZoomBy(10f);
            for (var i = 0; i < 3; i++)
                yield return null;
            var eye = loader.Follow.transform.position;
            if (d.HasCameraBox)
            {
                var box = d.CameraBox;
                box.Expand(0.01f);
                box.SetMinMax(new Vector3(box.min.x, -0.05f, box.min.z), box.max); // low eyes: ground clamp
                Assert.IsTrue(box.Contains(eye), $"orbited eye {eye} still inside {box}");
            }
            var fwd = loader.Follow.transform.forward;
            var yaw = Mathf.Atan2(fwd.x, fwd.z) * Mathf.Rad2Deg;
            Assert.That(
                Mathf.Abs(Mathf.DeltaAngle(limits.YawCenterDeg, yaw)),
                Is.LessThanOrEqualTo(limits.YawHalfRangeDeg + 0.5f),
                "view yaw stays in the room's window"
            );
            Assert.That(loader.Follow.Zoom, Is.LessThanOrEqualTo(limits.MaxZoom + 1e-4f));
            if (d.IsFreeLook)
            {
                // Every direction: turn right round and look up from below; the eye stays in the box.
                loader.Follow.Orbit(180f, -200f);
                for (var i = 0; i < 3; i++)
                    yield return null;
                Assert.That(
                    loader.Follow.transform.forward.y,
                    Is.GreaterThan(0.3f),
                    "free look can look up from low down"
                );
                var low = loader.Follow.transform.position;
                Assert.That(
                    low.y,
                    Is.GreaterThanOrEqualTo(loader.player.position.y),
                    "looking up never puts the eye under the floor"
                );
                if (d.HasCameraBox)
                {
                    var box = d.CameraBox;
                    Assert.That(low.x, Is.InRange(box.min.x - 0.01f, box.max.x + 0.01f));
                    Assert.That(low.z, Is.InRange(box.min.z - 0.01f, box.max.z + 0.01f));
                }
            }

            StringAssert.Contains(loader.Descriptor.displayName, loader.LabelText());
            StringAssert.Contains("CC BY", loader.LabelText());
            if (!loader.Loaded)
                StringAssert.Contains(loader.Error, loader.LabelText());

            var lines = new Dictionary<string, string>();
            loader.WriteReport((k, v) => lines[k] = v);
            Assert.AreEqual(loader.Descriptor.slug, lines["splat_room"]);
            Assert.IsTrue(lines.ContainsKey("sort_tier"));
            StringAssert.Contains(
                "splat_room: " + loader.Descriptor.slug,
                PerformanceReport.Build(new FrameStats(), System.DateTime.UtcNow)
            );
        }

        // Build 61 (bedroom): turning the view swept the eye's collision cast into the furniture
        // blockers and the camera jammed into the character. A full turn at the spawn must keep
        // the eye out at its follow distance (no blocker pulls it in; the walls are far enough
        // away at both spawns) and never hide the character, in the bedroom and in Winchester.
        [UnityTest]
        public IEnumerator Orbit_FullTurn_NeverJamsTheEyeIntoTheCharacter(
            [Values("", "owner-room-01")] string room
        )
        {
            DebugOverlay.RequestedSceneVariant = room;
            try
            {
                yield return EditorSceneManager.LoadSceneAsyncInPlayMode(
                    ScenePath,
                    new LoadSceneParameters(LoadSceneMode.Additive)
                );
                for (var i = 0; i < 60; i++)
                    yield return null;
                var loader = Object.FindFirstObjectByType<SplatRoomLoader>();
                Assert.IsNotNull(loader.Descriptor, loader.Error);
                var follow = loader.Follow;
                Assert.IsNotNull(follow);
                follow.Orbit(0f, -follow.OrbitPitchDeg); // default elevation
                for (var i = 0; i < 30; i++)
                    yield return null;
                Assert.IsTrue(
                    loader
                        .Colliders.GetComponentsInChildren<Collider>()
                        .All(c => c.gameObject.layer == LayerMask.NameToLayer("Ignore Raycast")),
                    "room colliders stay out of the camera cast"
                );
                var start = follow.EyeDistance;
                Assert.That(start, Is.GreaterThan(0.2f), "eye starts out at a follow distance");
                var least = start;
                // Level, then looking up from low down (the eye below the look-at point), then
                // from high up: a full turn at each.
                foreach (var pitch in new[] { 0f, -200f, 400f })
                {
                    follow.Orbit(0f, pitch);
                    for (var i = 0; i < 60; i++)
                        yield return null; // a pitch change may spring the eye back out first
                    for (var step = 0; step < 24; step++)
                    {
                        follow.Orbit(15f, 0f);
                        yield return null;
                        yield return null;
                        least = Mathf.Min(least, follow.EyeDistance);
                        Assert.IsFalse(
                            follow.TargetHidden,
                            $"character hidden (pitch {pitch}, step {step})"
                        );
                    }
                }
                Assert.That(
                    least,
                    Is.GreaterThan(0.8f * start),
                    $"{loader.Descriptor.slug}: eye pulled in to {least:0.00} of {start:0.00} while turning"
                );
            }
            finally
            {
                DebugOverlay.RequestedSceneVariant = null;
            }
        }

        [UnityTest]
        public IEnumerator SplatRoom_UnloadsCleanly_LeavingNoCharacterOrReportHook()
        {
            yield return EditorSceneManager.LoadSceneAsyncInPlayMode(
                ScenePath,
                new LoadSceneParameters(LoadSceneMode.Additive)
            );
            yield return null;
            yield return SceneManager.UnloadSceneAsync(SceneManager.GetSceneByPath(ScenePath));
            yield return null;
            Assert.IsNull(Object.FindFirstObjectByType<SplatRoomLoader>());
            StringAssert.DoesNotContain(
                "splat_room:",
                PerformanceReport.Build(new FrameStats(), System.DateTime.UtcNow)
            );
        }
    }
}
#endif
