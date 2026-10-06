using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GaussianSplatting.Runtime;
using GiganticJourneys.DebugTools;
using GiganticJourneys.DeviceTest;
using GiganticJourneys.EditorTools.DeviceTest;
using GiganticJourneys.EditorTools.Splats;
using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Controller;
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

        [Test]
        public void CommittedDescriptor_LimitsTheCameraToTheCapturedZone()
        {
            var d = SplatRoomDescriptor.Parse(Committed);
            Assert.IsTrue(d.HasCameraBox, "camera box from room_limits.py");
            var box = d.CameraBox;
            Assert.IsTrue(box.Contains(d.Spawn + Vector3.up), "spawn inside the camera box");
            Assert.That(
                d.orbitMaxElevationDeg,
                Is.InRange(10f, 45f),
                "captured views rarely looked down"
            );
            Assert.That(d.orbitMinElevationDeg, Is.LessThan(d.orbitMaxElevationDeg));
            Assert.That(d.viewYawHalfRangeDeg, Is.InRange(30f, 180f));
            Assert.That(d.orbitMaxZoom, Is.InRange(1f, 2.5f));
            Assert.That(
                Mathf.Abs(Mathf.DeltaAngle(d.viewYawCenterDeg, d.spawnYawDeg)),
                Is.LessThanOrEqualTo(d.viewYawHalfRangeDeg),
                "spawn faces into the view window"
            );
            foreach (var o in d.occluders)
            {
                var ob = new Bounds(o.Center, o.Size);
                Assert.IsFalse(
                    ob.Intersects(
                        new Bounds(
                            new Vector3(
                                (d.WalkMin.x + d.WalkMax.x) / 2f,
                                1f,
                                (d.WalkMin.y + d.WalkMax.y) / 2f
                            ),
                            new Vector3(d.WalkMax.x - d.WalkMin.x, 2f, d.WalkMax.y - d.WalkMin.y)
                        )
                    ),
                    $"occluder {o.name} stays out of the walk area"
                );
            }
            // Coverage mode applies the coverage window.
            var coverage = SplatRoomDescriptor.Parse(Committed);
            coverage.cameraMode = SplatRoomDescriptor.CameraModeCoverage;
            var l = SplatRoomLoader.OrbitLimitsFor(coverage);
            Assert.AreEqual(d.orbitMaxElevationDeg, l.MaxElevationDeg);
            Assert.AreEqual(d.orbitMaxZoom, l.MaxZoom);
            Assert.AreEqual(d.viewYawCenterDeg, l.YawCenterDeg);
            Assert.AreEqual(d.viewYawHalfRangeDeg, l.YawHalfRangeDeg);
        }

        [Test]
        public void CommittedDescriptor_WinchesterUsesFreeLook_EveryDirection()
        {
            var d = SplatRoomDescriptor.Parse(Committed);
            Assert.IsTrue(
                d.IsFreeLook,
                "Owner asked for every direction and angle (build 54 check)"
            );
            var l = SplatRoomLoader.OrbitLimitsFor(d);
            Assert.AreEqual(180f, l.YawHalfRangeDeg, "full 360 degree yaw");
            Assert.AreEqual(-60f, l.MinElevationDeg);
            Assert.AreEqual(80f, l.MaxElevationDeg);
            Assert.AreEqual(0.5f, l.MinZoom);
            Assert.AreEqual(2.5f, l.MaxZoom);
            Assert.IsTrue(d.HasCameraBox, "free look keeps the camera box");
            Assert.That(FollowCamera.ClampViewYaw(-170f, l), Is.EqualTo(-170f).Within(1e-3f));
        }

        [Test]
        public void Descriptor_EmptyCameraModeMeansCoverage()
        {
            var d = JsonUtility.FromJson<SplatRoomDescriptor>(Committed);
            d.cameraMode = "";
            d.Validate();
            Assert.IsFalse(d.IsFreeLook);
            Assert.AreEqual(
                d.viewYawHalfRangeDeg,
                SplatRoomLoader.OrbitLimitsFor(d).YawHalfRangeDeg
            );
        }

        [TestCase("cameraBox")]
        [TestCase("cameraBoxMissesWalk")]
        [TestCase("elevation")]
        [TestCase("zoom")]
        [TestCase("yaw")]
        [TestCase("occluder")]
        [TestCase("cameraMode")]
        [TestCase("freeElevation")]
        [TestCase("freeZoom")]
        public void Descriptor_RejectsBadCameraLimits(string field)
        {
            var d = JsonUtility.FromJson<SplatRoomDescriptor>(Committed);
            switch (field)
            {
                case "cameraBox":
                    d.cameraMax = new[] { d.cameraMin[0] - 1f, 3f, 3f };
                    break;
                case "cameraBoxMissesWalk":
                    d.cameraMin = new[] { 0f, 0.25f, 0f };
                    break;
                case "elevation":
                    d.orbitMinElevationDeg = 30f;
                    d.orbitMaxElevationDeg = 20f;
                    break;
                case "zoom":
                    d.orbitMinZoom = 1.5f;
                    break;
                case "yaw":
                    d.viewYawHalfRangeDeg = 200f;
                    break;
                case "cameraMode":
                    d.cameraMode = "orbit";
                    break;
                case "freeElevation":
                    d.freeOrbit.minElevationDeg = -90f;
                    break;
                case "freeZoom":
                    d.freeOrbit.maxZoom = 0.8f;
                    break;
                case "occluder":
                    d.occluders = new[]
                    {
                        new SplatRoomDescriptor.Occluder
                        {
                            name = "flat",
                            center = new[] { 0f, 1f, 0f },
                            size = new[] { 1f, 0f, 1f },
                        },
                    };
                    break;
            }
            Assert.Throws<FormatException>(() => d.Validate());
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
                CollectionAssert.AreEqual(
                    SplatRoomScene.DescriptorPaths().Skip(1).ToArray(),
                    loader.extraDescriptors.Select(AssetDatabase.GetAssetPath).ToArray(),
                    "every splat-room-<slug>.json is wired as an extra room"
                );
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
                Assert.AreEqual(
                    SampleSplat.AlphaSafeCompositePath,
                    AssetDatabase.GetAssetPath(r.m_ShaderComposite),
                    "GJ alpha-safe composite (the package's turns opaque objects black on Metal)"
                );
                Assert.IsNotNull(r.m_CSSplatUtilities);
                var applier = r.GetComponent<SplatRenderSettingsApplier>();
                Assert.IsNotNull(
                    applier != null ? applier.settings : null,
                    "tier settings assigned"
                );
                Assert.IsNotNull(Camera.main, "main camera");
                Assert.IsFalse(Camera.main.allowMSAA, "no MSAA store/reload around the splat pass");
                Assert.IsFalse(Camera.main.allowHDR, "LDR camera target in the splat room");
                Assert.IsTrue(Camera.main.GetComponent<FollowCamera>().TouchOrbit, "orbit on");
                Assert.IsTrue(
                    roots.Any(g =>
                        g.name == "Floor (visual)" && g.GetComponent<MeshRenderer>() != null
                    ),
                    "visual floor under the splats"
                );
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
        public void CommittedDescriptor_CarriesTheDevicePerformanceProfile()
        {
            var d = SplatRoomScene.LoadDescriptor();
            Assert.That(d.renderScale, Is.InRange(0.6f, 0.75f), "reduced splat-pass resolution");
            Assert.That(d.shOrder, Is.InRange(0, 2));
            Assert.That(d.sortEveryNthFrame, Is.GreaterThanOrEqualTo(1));
            Assert.That(d.resortMoveMeters, Is.GreaterThan(0f));
            Assert.That(d.resortAngleDeg, Is.GreaterThan(0f));
            Assert.That(d.splatCount, Is.InRange(300_000, 400_000), "pruned display splat");
        }

        [TestCase("renderScale", "0.3")]
        [TestCase("shOrder", "4")]
        [TestCase("resortAngleDeg", "-1")]
        public void Descriptor_RejectsBadPerformanceProfile(string field, string value)
        {
            var json = File.ReadAllText(SplatRoomScene.DescriptorPath);
            json = System.Text.RegularExpressions.Regex.Replace(
                json,
                "\"" + field + "\":\\s*[^,\\n]+",
                "\"" + field + "\": " + value
            );
            Assert.Throws<System.FormatException>(() => SplatRoomDescriptor.Parse(json));
        }

        [Test]
        public void AlphaSafeComposite_SkipsEmptyPixels_AndClamps()
        {
            var src = File.ReadAllText(SampleSplat.AlphaSafeCompositePath);
            StringAssert.Contains("discard", src);
            StringAssert.Contains("!(col.a >= 1.0 / 255.0)", src, "NaN-safe empty-pixel test");
            StringAssert.Contains("saturate(col.rgb / col.a)", src);
            Assert.IsNotNull(Shader.Find("Hidden/GJ/Gaussian Splatting/Composite Alpha-Safe"));
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
        public void SceneSwitcher_OffersSceneVariants_ExceptTheRunningOne()
        {
            var names = new[] { "MovementTest", "SplatRoom" };
            IReadOnlyList<KeyValuePair<string, string>> Rooms(string scene) =>
                scene == "SplatRoom"
                    ? new[] { new KeyValuePair<string, string>("owner-room-01", "Bedroom") }
                    : null;
            string Labels(List<DebugOverlay.SwitchTarget> t) =>
                string.Join(",", t.Select(x => $"{x.BuildIndex}:{x.Variant ?? "-"}:{x.Label}"));

            Assert.AreEqual(
                "1:-:SplatRoom,1:owner-room-01:Bedroom",
                Labels(DebugOverlay.SwitchTargetsWithVariants(names, 0, null, Rooms))
            );
            Assert.AreEqual(
                "0:-:MovementTest,1:owner-room-01:Bedroom",
                Labels(DebugOverlay.SwitchTargetsWithVariants(names, 1, null, Rooms))
            );
            Assert.AreEqual(
                "0:-:MovementTest,1:-:SplatRoom",
                Labels(DebugOverlay.SwitchTargetsWithVariants(names, 1, "owner-room-01", Rooms))
            );
            Assert.AreEqual(
                "1:-:SplatRoom",
                Labels(DebugOverlay.SwitchTargetsWithVariants(names, 0, null, null))
            );
        }

        [Test]
        public void ExtraRooms_MatchTheDescriptorFiles_AndSelectBySlug()
        {
            var paths = SplatRoomScene.DescriptorPaths();
            var extras = paths.Skip(1).Select(p => SplatRoomDescriptor.Parse(File.ReadAllText(p)));
            CollectionAssert.AreEquivalent(
                SplatRoomLoader.ExtraRooms.Select(r => r.Key).ToArray(),
                extras.Select(d => d.slug).ToArray(),
                "each overlay room variant has exactly one splat-room-<slug>.json"
            );
            foreach (var p in paths.Skip(1))
            {
                var d = SplatRoomDescriptor.Parse(File.ReadAllText(p));
                Assert.AreEqual($"splat-room-{d.slug}.json", Path.GetFileName(p));
                Assert.AreEqual($"GJSplatRoom/{d.slug}", d.resource, "same Resources folder");
            }
            var texts = paths.Select(File.ReadAllText).ToArray();
            var main = SplatRoomDescriptor.Parse(Committed).slug;
            Assert.AreEqual(main, SplatRoomLoader.Select(texts, null).slug, "default room");
            Assert.AreEqual(main, SplatRoomLoader.Select(texts, "").slug);
            foreach (var r in SplatRoomLoader.ExtraRooms)
                Assert.AreEqual(r.Key, SplatRoomLoader.Select(texts, r.Key).slug);
            Assert.Throws<FormatException>(() => SplatRoomLoader.Select(texts, "no-such-room"));
        }

        [Test]
        public void OwnerRoom_IsPrivate_MetricsAndPointersOnly()
        {
            // AUTH #046: the repo holds only a hash, a private-bucket path and numbers.
            var path = $"{SplatRoomScene.DeviceTestFolder}/splat-room-owner-room-01.json";
            var d = SplatRoomDescriptor.Parse(File.ReadAllText(path));
            StringAssert.StartsWith("environments/_devtest/owner-room-01/", d.packageObject);
            StringAssert.Contains("AUTH #046", d.credit);
            Assert.IsTrue(d.IsFreeLook, "free-look camera");
            Assert.IsTrue(d.HasCameraBox, "camera box from room_limits");
            // Sharpness A/B (M1-PIPE-02 phase 2a): the small bedroom renders the splat pass
            // at 0.85 with SH order 2; Winchester keeps the A15 profile (0.7, SH 1).
            Assert.AreEqual(0.85f, d.renderScale, 1e-4f, "bedroom sharpness A/B render scale");
            Assert.AreEqual(2, d.shOrder, "bedroom sharpness A/B SH order");
            Assert.That(d.splatCount, Is.InRange(300_000, 400_000), "display budget splat");
            var size = d.WalkMax - d.WalkMin;
            Assert.Greater(Mathf.Min(size.x, size.y), 2.5f, "the walk bounds span the bedroom");

            // The open floor around the bed (walk rectangle minus the furniture blockers).
            Assert.Greater(d.blockers.Length, 0, "furniture blockers from room_limits --blockers");
            var open = 0;
            for (var x = d.WalkMin.x + 0.05f; x < d.WalkMax.x; x += 0.1f)
            for (var z = d.WalkMin.y + 0.05f; z < d.WalkMax.y; z += 0.1f)
                if (!d.IsBlocked(new Vector2(x, z)))
                    open++;
            Assert.Greater(open * 0.01f, 4f, "at least 4 m2 of open floor to walk");
            Assert.IsFalse(d.IsBlocked(new Vector2(d.Spawn.x, d.Spawn.z)), "spawn on open floor");

            // Real metric scale with a miniature character: the room is many body heights wide.
            var a = MovementScale
                .Create(
                    MovementConfigLoader.LoadFile(MovementConfigLoader.DefaultPath),
                    ProvisionalTuning.Body.DefaultRealHeightMeters,
                    ProvisionalTuning.Environment.DefaultScale
                )
                .WorldUnitsPerA;
            Assert.Greater(Mathf.Max(size.x, size.y) / a, 20f, "the bedroom reads giant");
        }

        [Test]
        public void Descriptor_RejectsSpawnInsideABlocker_AndEmptyBlockers()
        {
            var d = JsonUtility.FromJson<SplatRoomDescriptor>(Committed);
            d.blockers = new[]
            {
                new SplatRoomDescriptor.Occluder
                {
                    name = "bed",
                    center = new[] { d.spawn[0], 0.3f, d.spawn[2] },
                    size = new[] { 0.5f, 0.6f, 0.5f },
                },
            };
            Assert.Throws<FormatException>(() => d.Validate());
            d.blockers[0].center = new[] { d.spawn[0] + 2f, 0.3f, d.spawn[2] };
            d.Validate();
            d.blockers[0].size = new[] { 0.5f, 0f, 0.5f };
            Assert.Throws<FormatException>(() => d.Validate());
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
