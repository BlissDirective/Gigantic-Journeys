#if UNITY_EDITOR
using System.Collections;
using System.Collections.Generic;
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

        [UnityTest]
        public IEnumerator SplatRoom_SpawnsCharacterOnFloor_AndReportsTheRoom()
        {
            yield return EditorSceneManager.LoadSceneAsyncInPlayMode(
                ScenePath,
                new LoadSceneParameters(LoadSceneMode.Single)
            );
            yield return null;
            var loader = Object.FindFirstObjectByType<SplatRoomLoader>();
            Assert.IsNotNull(loader, "loader in the scene");
            Assert.IsNotNull(loader.Descriptor, loader.Error);
            Assert.IsNotNull(loader.Colliders, "floor + walls built");
            Assert.AreEqual(5, loader.Colliders.childCount, "floor and four walls");

            for (var i = 0; i < 60; i++)
                yield return null;
            var p = loader.player.position;
            var spawn = loader.Descriptor.Spawn;
            Assert.That(p.y, Is.InRange(-0.05f, 0.3f), "character rests on the floor, not falling");
            Assert.That(new Vector2(p.x - spawn.x, p.z - spawn.z).magnitude, Is.LessThan(0.5f));

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
    }
}
#endif
