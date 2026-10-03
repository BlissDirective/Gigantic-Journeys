using System;
using System.IO;
using System.Linq;
using GaussianSplatting.Runtime;
using GiganticJourneys.DebugTools;
using GiganticJourneys.DeviceTest;
using GiganticJourneys.EditorTools.DeviceTest;
using GiganticJourneys.Splats;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// The internal-debug device-test splat room (ticket M1-UNITY-01 AT-2/AT-3): descriptor,
    /// scene wiring, debug-only packaging and the overlay's scene switcher / report hook.
    /// </summary>
    public class SplatRoomTests
    {
        static string Committed => File.ReadAllText(SplatRoomScene.DescriptorPath);

        [Test]
        public void CommittedDescriptor_IsValid_Attributed_AndUnmirrors()
        {
            var d = SplatRoomDescriptor.Parse(Committed);
            Assert.AreEqual("medieval-great-hall-winchester", d.slug);
            StringAssert.Contains("CC BY", d.license);
            StringAssert.Contains(
                "3Oc3M1MUHRg",
                d.credit,
                "credit names the source clip (OPEN_VIDEO_ATTRIBUTION.md)"
            );
            Assert.That(
                d.splatCount,
                Is.InRange(100_000, 2_500_000),
                "inside the iOS splat budget"
            );
            Assert.Less(d.LocalToWorld.determinant, 0f, "right-handed capture data is un-mirrored");
            var spawn = d.Spawn;
            Assert.That(spawn.y, Is.InRange(0f, 0.1f), "spawn stands on the floor (y = 0)");
            Assert.That(spawn.x, Is.InRange(d.WalkMin.x, d.WalkMax.x));
            Assert.That(spawn.z, Is.InRange(d.WalkMin.y, d.WalkMax.y));
        }

        [TestCase("credit", "")]
        [TestCase("packageSha256", "abc")]
        [TestCase("spawn", "[9.0, 0.0, 99.0]")]
        [TestCase("scale", "[1.0, 0.0, 1.0]")]
        public void Descriptor_RejectsBadFields(string field, string value)
        {
            var d = JsonUtility.FromJson<SplatRoomDescriptor>(Committed);
            switch (field)
            {
                case "credit":
                    d.credit = value;
                    break;
                case "packageSha256":
                    d.packageSha256 = value;
                    break;
                case "spawn":
                    d.spawn = new[] { 9f, 0f, 99f };
                    break;
                case "scale":
                    d.scale = new[] { 1f, 0f, 1f };
                    break;
            }
            Assert.Throws<FormatException>(() => d.Validate());
            Assert.Throws<FormatException>(() => SplatRoomDescriptor.Parse(""));
        }

        [Test]
        public void Scene_WiresLoader_Character_AndAnInactiveRenderer()
        {
            Assert.IsTrue(File.Exists(SplatRoomScene.ScenePath), SplatRoomScene.ScenePath);
            var scene = EditorSceneManager.OpenScene(
                SplatRoomScene.ScenePath,
                OpenSceneMode.Single
            );
            try
            {
                var roots = scene.GetRootGameObjects();
                var loader = roots
                    .Select(g => g.GetComponent<SplatRoomLoader>())
                    .Single(l => l != null);
                Assert.IsNotNull(loader.descriptorJson, "descriptor assigned");
                Assert.IsNotNull(loader.player, "player assigned");
                Assert.IsNotNull(loader.player.GetComponent<CharacterController>());
                var r = loader.splatRenderer;
                Assert.IsNotNull(r, "renderer assigned");
                Assert.IsFalse(
                    r.gameObject.activeSelf,
                    "renderer starts inactive (activated only with an asset)"
                );
                Assert.IsNull(r.m_Asset, "no splat asset is referenced by the committed scene");
                Assert.IsNotNull(r.m_ShaderSplats);
                Assert.IsNotNull(r.m_ShaderComposite);
                Assert.IsNotNull(r.m_CSSplatUtilities);
                var applier = r.GetComponent<SplatRenderSettingsApplier>();
                Assert.IsNotNull(
                    applier != null ? applier.settings : null,
                    "tier settings assigned"
                );
                Assert.IsNotNull(Camera.main, "main camera");
            }
            finally
            {
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            }
        }

        [Test]
        public void ReleaseBuildList_ExcludesTheDeviceTestScene()
        {
            Assert.IsFalse(
                SplatRoomScene.InCommittedBuildList(),
                "only the internal-debug CI lane adds SplatRoom (ios_debug_flavor.py add-scene)"
            );
            Assert.AreEqual(ProjectIdentity.BootScenePath, EditorBuildSettings.scenes[0].path);
        }

        [Test]
        public void DeviceTestAssembly_IsDebugOnly()
        {
            var json = File.ReadAllText(
                "Assets/GiganticJourneys/DeviceTest/GiganticJourneys.DeviceTest.asmdef"
            );
            StringAssert.Contains("UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG", json);
            StringAssert.Contains("\"autoReferenced\": false", json);
        }

        [Test]
        public void DownloadedSplat_IsGitignored()
        {
            var ignore = File.ReadAllText(Path.Combine("..", ".gitignore"));
            StringAssert.Contains("unity/Assets/GiganticJourneys/DeviceTest/Downloaded/", ignore);
            StringAssert.StartsWith(SplatRoomScene.DownloadFolder, SplatRoomScene.ResourcesFolder);
        }

        [Test]
        public void LocalSplat_WhenPresent_MatchesTheDescriptor()
        {
            var d = SplatRoomDescriptor.Parse(Committed);
            var asset = AssetDatabase.LoadAssetAtPath<GaussianSplatAsset>(
                $"{SplatRoomScene.ResourcesFolder}/{Path.GetFileName(d.resource)}.asset"
            );
            if (asset == null)
                Assert.Ignore(
                    "splat not fetched in this checkout (CI fetches it only for internal-debug builds)"
                );
            Assert.AreEqual(d.splatCount, asset.splatCount);
        }

        [Test]
        public void SortTierLabel_NamesThePath()
        {
            StringAssert.StartsWith(
                "Tier B",
                SplatRoomLoader.SortTierLabel(true, GraphicsDeviceType.Metal)
            );
            StringAssert.Contains(
                "NOT engaged",
                SplatRoomLoader.SortTierLabel(false, GraphicsDeviceType.Metal)
            );
            StringAssert.Contains(
                "Vulkan",
                SplatRoomLoader.SortTierLabel(false, GraphicsDeviceType.Vulkan)
            );
        }

        [Test]
        public void SceneSwitcher_OffersEveryOtherBuildScene()
        {
            CollectionAssert.AreEqual(new[] { 1, 2 }, DebugOverlay.SwitchTargets(3, 0));
            CollectionAssert.AreEqual(new[] { 0, 1 }, DebugOverlay.SwitchTargets(3, 2));
            CollectionAssert.AreEqual(new[] { 0 }, DebugOverlay.SwitchTargets(1, -1));
            CollectionAssert.IsEmpty(DebugOverlay.SwitchTargets(1, 0));
        }

        [Test]
        public void PerformanceReport_AppendsSceneLines_AndSurvivesAThrowingHandler()
        {
            Action<PerformanceReport.LineWriter> good = w => w("splat_count", "780004");
            Action<PerformanceReport.LineWriter> bad = _ =>
                throw new InvalidOperationException("boom");
            PerformanceReport.ExtraLines += good;
            PerformanceReport.ExtraLines += bad;
            try
            {
                var text = PerformanceReport.Build(new FrameStats(), DateTime.UtcNow);
                StringAssert.Contains("splat_count: 780004\n", text);
                StringAssert.Contains("extra_error: InvalidOperationException: boom", text);
            }
            finally
            {
                PerformanceReport.ExtraLines -= good;
                PerformanceReport.ExtraLines -= bad;
            }
            StringAssert.DoesNotContain(
                "splat_count",
                PerformanceReport.Build(new FrameStats(), DateTime.UtcNow)
            );
        }
    }
}
