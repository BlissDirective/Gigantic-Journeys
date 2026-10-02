using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using GiganticJourneys.Environments;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.TestTools;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Ticket M1-GAME-01 AT-1: the C# loader agrees with services/packages/package.py on the
    /// golden desk-tabletop package (binary assets as presence-only stubs, as the Python
    /// reference does) and rejects the same failure modes.
    /// </summary>
    public class EnvironmentPackageTests
    {
        const string Golden = "Assets/GiganticJourneys/Tests/Environments/desk-tabletop";
        static readonly string[] Docs =
        {
            "environment_spec.json",
            "scene_graph.json",
            "traversal_graph.json",
        };
        static readonly string[] Stubs = { "splat.spz", "collision.glb", "thumbnail.webp" };
        string _dir;

        [SetUp]
        public void Materialise()
        {
            _dir = Path.Combine(Path.GetTempPath(), "gj-env-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_dir);
            foreach (var d in Docs)
                File.Copy(Path.Combine(Golden, d), Path.Combine(_dir, d));
            foreach (var s in Stubs)
                File.WriteAllBytes(Path.Combine(_dir, s), new byte[] { 0 });
        }

        [TearDown]
        public void Cleanup()
        {
            if (Directory.Exists(_dir))
                Directory.Delete(_dir, true);
        }

        void Edit(string doc, string from, string to)
        {
            var path = Path.Combine(_dir, doc);
            var text = File.ReadAllText(path);
            StringAssert.Contains(from, text, $"fixture edit anchor missing in {doc}");
            File.WriteAllText(path, text.Replace(from, to));
        }

        void AssertRejects(string because)
        {
            var e = Assert.Throws<EnvironmentPackageException>(() => EnvironmentPackage.Load(_dir));
            StringAssert.Contains(because, e.Message);
        }

        [Test]
        public void GoldenLoadsAgainstTheShippedMovementConfig()
        {
            var sha = EnvironmentLoader.ShippedMovementSha();
            Assert.IsNotNull(sha, "StreamingAssets/movement.json missing");
            var p = EnvironmentPackage.Load(_dir, sha);
            Assert.AreEqual("3c2b1a09-8f7e-4d6c-b5a4-938271605f4e", p.EnvironmentId);
            Assert.AreEqual("tabletop", p.CaptureMode);
            Assert.AreEqual("splat.spz", p.Assets["splat"]);
            Assert.AreEqual("collision.glb", p.Assets["collision_mesh"]);
            Assert.AreEqual(10, p.Nodes.Count);
            Assert.AreEqual(12, p.Edges.Count);
            Assert.AreEqual(2, p.Routes.Count);
            Assert.AreEqual(2, p.Vistas.Count);
            Assert.AreEqual("node-1", p.SpawnNodeId);
            Assert.AreEqual(90f, p.SpawnFacingDeg);
            Assert.AreEqual("node-6", p.SummitNodeId);
            Assert.IsFalse(p.SummitTruePeak);
            Assert.AreEqual(
                8,
                p.SurfaceMeshes.Count + 0,
                "every desk surface maps to collision triangles"
            );
        }

        [Test]
        public void ShippedMovementShaIsTheBytesOfConfigMovementJson()
        {
            var repoConfig = Path.GetFullPath(
                Path.Combine(Application.dataPath, "../../config/movement.json")
            );
            Assume.That(File.Exists(repoConfig), "repo checkout not present");
            Assert.AreEqual(
                EnvironmentPackage.Sha256File(repoConfig),
                EnvironmentLoader.ShippedMovementSha()
            );
        }

        [Test]
        public void StaleMovementShaIsRejected()
        {
            var e = Assert.Throws<EnvironmentPackageException>(() =>
                EnvironmentPackage.Load(_dir, new string('0', 64))
            );
            StringAssert.Contains("config_sha256", e.Message);
        }

        [Test]
        public void MissingManifestIsRejected()
        {
            File.Delete(Path.Combine(_dir, "environment_spec.json"));
            AssertRejects("environment_spec.json missing");
        }

        [TestCase("splat.spz")]
        [TestCase("collision.glb")]
        [TestCase("traversal_graph.json")]
        public void MissingAssetIsRejected(string file)
        {
            File.Delete(Path.Combine(_dir, file));
            AssertRejects("missing from the package");
        }

        [TestCase("../splat.spz")]
        [TestCase("https://cdn.example/splat.spz")]
        [TestCase("sub/splat.spz")]
        [TestCase("C:\\\\splat.spz")]
        [TestCase(".hidden")]
        public void NonPackageRelativeAssetNameIsRejected(string name)
        {
            Edit("environment_spec.json", "\"splat\": \"splat.spz\"", $"\"splat\": \"{name}\"");
            AssertRejects("not a package-relative file name");
        }

        [Test]
        public void WrongSchemaVersionIsRejected()
        {
            Edit(
                "scene_graph.json",
                "\"schema_version\": \"1.0.0\"",
                "\"schema_version\": \"2.0.0\""
            );
            AssertRejects("schema_version must be 1.0.0");
        }

        [Test]
        public void MismatchedEnvironmentIdIsRejected()
        {
            Edit(
                "traversal_graph.json",
                "\"environment_id\": \"3c2b1a09-8f7e-4d6c-b5a4-938271605f4e\"",
                "\"environment_id\": \"00000000-0000-4000-8000-000000000000\""
            );
            AssertRejects("traversal_graph.environment_id differs");
        }

        [Test]
        public void RouteNamingAnUnknownEdgeIsRejected()
        {
            var text = File.ReadAllText(Path.Combine(_dir, "environment_spec.json"));
            var m = Regex.Match(text, "\"edge_ids\":\\s*\\[\\s*\"(edge-\\d+)\"");
            Assert.IsTrue(m.Success);
            Edit("environment_spec.json", m.Value, m.Value.Replace(m.Groups[1].Value, "edge-999"));
            AssertRejects("unknown edge edge-999");
        }

        [Test]
        public void MalformedJsonIsRejectedWithTheFileName()
        {
            File.WriteAllText(Path.Combine(_dir, "scene_graph.json"), "{ not json");
            AssertRejects("scene_graph.json");
        }

        [Test]
        public void RoutePolylineWalksTheBeatEdgesInOrder()
        {
            var p = EnvironmentPackage.Load(_dir);
            var route = p.Routes[0];
            var line = GoalPlacement.RoutePolyline(p, route.Id);
            var first = p.Edges[route.Beats[0].EdgeIds[0]];
            var lastBeat = route.Beats[route.Beats.Count - 1];
            var last = p.Edges[lastBeat.EdgeIds[lastBeat.EdgeIds.Count - 1]];
            Assert.AreEqual(p.Nodes[first.From].Position, line[0]);
            Assert.AreEqual(p.Nodes[last.To].Position, line[line.Count - 1]);
            for (var i = 1; i < line.Count; i++)
                Assert.AreNotEqual(line[i - 1], line[i], "repeated joints are collapsed");
            Assert.IsEmpty(GoalPlacement.RoutePolyline(p, "no-such-route"));
        }

        [Test]
        public void FootprintsAreEvenlySpacedAndAlternate()
        {
            var line = new[] { Vector3.zero, new Vector3(0, 0, 10), new Vector3(10, 0, 10) };
            var marks = GoalPlacement.Footprints(line, 2.5f);
            Assert.AreEqual(9, marks.Count, "0..20 A at 2.5 A spacing");
            for (var i = 1; i < marks.Count; i++)
            {
                Assert.AreNotEqual(marks[i - 1].left, marks[i].left);
                var along = (marks[i].position - marks[i - 1].position).magnitude;
                Assert.LessOrEqual(along, 2.5f + 1e-4f);
            }
            Assert.AreEqual(new Vector3(10, 0, 10), marks[8].position);
            Assert.AreEqual(Quaternion.LookRotation(Vector3.right), marks[8].rotation);
        }

        [Test]
        public void SpawnFacingIsUnityYaw()
        {
            var p = EnvironmentPackage.Load(_dir);
            var fwd = GoalPlacement.SpawnRotation(p) * Vector3.forward;
            Assert.That(Vector3.Distance(Vector3.right, fwd), Is.LessThan(1e-5f), "90° faces +x");
        }

        [Test]
        public void LoaderBuildsTheGoalElementsWithNoConsoleErrors()
        {
            var go = new GameObject("loader");
            try
            {
                var loader = go.AddComponent<EnvironmentLoader>();
                loader.loadOnStart = false;
                LogAssert.Expect(LogType.Log, new Regex("runtime .spz decode not built yet"));
                LogAssert.Expect(LogType.Log, new Regex("runtime .glb import not built yet"));
                var p = loader.Load(_dir);

                Assert.AreEqual(p.SpawnPosition, loader.Spawn.localPosition);
                Assert.AreEqual(p.SummitPosition, loader.Beacon.localPosition);
                Assert.IsTrue(loader.Beacon.gameObject.activeSelf, "beam on by default");
                var beamMat = loader.Beacon.GetComponent<MeshRenderer>().sharedMaterial;
                Assert.IsNotNull(beamMat, "marker shader missing from Resources");
                Assert.AreEqual("GJ/OnTopMarker", beamMat.shader.name);
                Assert.AreEqual(p.Vistas.Count, loader.VistaMarkers.Count);
                Assert.AreEqual(0, loader.RouteRoot.childCount, "routes off by default");

                loader.SelectRoute(p.Routes[0].Id);
                Assert.Greater(loader.RouteRoot.childCount, 2);
                Assert.AreEqual(p.Routes[0].Id, loader.SelectedRouteId);
                loader.SelectRoute(null);
                Assert.AreEqual(0, loader.RouteRoot.childCount);

                loader.SetSummitBeam(false);
                Assert.IsFalse(loader.Beacon.gameObject.activeSelf);
                LogAssert.NoUnexpectedReceived();
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void MarkerShaderCompilesAndDrawsOnTop()
        {
            var shader = Resources.Load<Shader>(EnvironmentLoader.MarkerShaderResource);
            Assert.IsNotNull(shader);
            Assert.IsFalse(ShaderUtil.ShaderHasError(shader), "GJ/OnTopMarker has compile errors");
            var src = File.ReadAllText(AssetDatabase.GetAssetPath(shader));
            StringAssert.Contains("ZTest Always", src);
            StringAssert.Contains("ZWrite Off", src);
        }

        [Test]
        public void PackageRelativeNames()
        {
            Assert.IsTrue(EnvironmentPackage.IsPackageRelative("splat.spz"));
            foreach (var bad in new[] { "", " ", "..", ".", "a/b", "a\\b", "s3:x", "/abs" })
                Assert.IsFalse(EnvironmentPackage.IsPackageRelative(bad), bad);
            Assert.AreEqual(Docs.Length + Stubs.Length, Directory.GetFiles(_dir).Length);
            Assert.IsTrue(Docs.All(d => File.Exists(Path.Combine(_dir, d))));
        }
    }
}
