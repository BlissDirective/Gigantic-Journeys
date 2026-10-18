using System;
using System.IO;
using GiganticJourneys.DeviceTest;
using GiganticJourneys.EditorTools.DeviceTest;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Bedroom cleanup stage 3 (M1-PIPE-02): planar proxies behind the splats. Default off in
    /// every committed descriptor, validated only when enabled, quad mesh UVs match the Python
    /// texture bake (corner 0 = texture bottom-left), and the shader compiles.
    /// </summary>
    public class PlaneProxyTests
    {
        static SplatRoomDescriptor Base() =>
            SplatRoomDescriptor.Parse(File.ReadAllText(SplatRoomScene.DescriptorPath));

        static SplatRoomDescriptor.PlaneProxy Quad(float size) =>
            new SplatRoomDescriptor.PlaneProxy
            {
                name = "P00",
                label = "floor",
                corners = new[] { 0f, 0f, 0f, size, 0f, 0f, size, 0f, size, 0f, 0f, size },
                texture = "P00-floor",
            };

        [Test]
        public void CommittedDescriptors_OnlyTheBedroomEnablesItsFloorProxy()
        {
            // Stage 3 (2026-10-18): the bedroom ships the textured floor quad (the only plane
            // that passed the fill / height filters); every other room keeps proxies off.
            foreach (var path in SplatRoomScene.DescriptorPaths())
            {
                var d = SplatRoomDescriptor.Parse(File.ReadAllText(path));
                if (d.slug != "owner-room-01")
                {
                    Assert.IsFalse(d.HasPlaneProxies, $"{path}: plane proxies stay off");
                    continue;
                }
                Assert.IsTrue(d.HasPlaneProxies, "bedroom stage-3 floor proxy");
                Assert.AreEqual(1, d.planeProxies.Length);
                var floor = d.planeProxies[0];
                Assert.AreEqual("floor", floor.label);
                Assert.AreEqual("P00-floor", floor.texture);
                var c = floor.Corners;
                foreach (var v in c)
                    Assert.That(v.y, Is.InRange(-0.2f, 0.05f), "floor at room height ~0");
                Assert.Greater(floor.Area, 4f, "spans the open floor");
            }
        }

        [Test]
        public void PlaneTexture_PackedAsFlatBytes_AndMissingFallsBackToColour()
        {
            var d = Base();
            Assert.AreEqual(
                d.resource + "-planes-P00-floor",
                SplatRoomLoader.PlaneTextureBytesName(d, "P00-floor")
            );
            StringAssert.StartsWith(
                "GJSplatRoom/" + d.slug,
                SplatRoomLoader.PlaneTextureBytesName(d, "P00-floor"),
                "the CI unpacker only accepts flat <slug>* entries"
            );
            Assert.IsNull(SplatRoomLoader.LoadPlaneTexture(d, "no-such-texture"));
            Assert.IsNull(SplatRoomLoader.LoadPlaneTexture(d, ""));
        }

        [Test]
        public void Disabled_IgnoresDegeneratePlanes()
        {
            var d = Base();
            d.planeProxies = new[] { Quad(0f) };
            d.planeProxiesEnabled = false;
            Assert.DoesNotThrow(d.Validate);
            Assert.IsFalse(d.HasPlaneProxies);
        }

        [Test]
        public void Enabled_RejectsDegenerateAndBadCorners()
        {
            var d = Base();
            d.planeProxiesEnabled = true;
            d.planeProxies = new[] { Quad(0f) };
            Assert.Throws<FormatException>(d.Validate);
            d.planeProxies = new[]
            {
                new SplatRoomDescriptor.PlaneProxy { corners = new float[5] },
            };
            Assert.Throws<FormatException>(d.Validate);
            d.planeProxies = new[] { Quad(2f) };
            Assert.DoesNotThrow(d.Validate);
            Assert.IsTrue(d.HasPlaneProxies);
            Assert.AreEqual(4f, d.planeProxies[0].Area, 1e-4f);
            Assert.AreEqual(d.resource + "-planes", d.PlaneTextureFolder);
        }

        [Test]
        public void Mesh_MapsCorner0ToTextureBottomLeft()
        {
            var m = SplatRoomLoader.PlaneProxyMesh(Quad(1f).Corners);
            Assert.AreEqual(4, m.vertexCount);
            CollectionAssert.AreEqual(new[] { 0, 1, 2, 0, 2, 3 }, m.triangles);
            Assert.AreEqual(Vector2.zero, m.uv[0]);
            Assert.AreEqual(Vector2.one, m.uv[2]);
            Assert.AreEqual(1f, Mathf.Abs(m.normals[0].y), 1e-4f);
            Assert.Throws<ArgumentException>(() => SplatRoomLoader.PlaneProxyMesh(new Vector3[3]));
            UnityEngine.Object.DestroyImmediate(m);
        }

        [Test]
        public void Shader_ExistsCompilesAndIsOpaqueQueue()
        {
            var shader = Shader.Find(SplatRoomLoader.PlaneProxyShader);
            Assert.IsNotNull(shader, "GJ/PlaneProxy must be in a Resources folder");
            Assert.IsFalse(ShaderUtil.ShaderHasError(shader), "GJ/PlaneProxy has compile errors");
            // Opaque/alpha-test queue (< 2500): drawn before the ZTest-Always splat composite,
            // so splats always land on top of the planes.
            Assert.Less(new Material(shader).renderQueue, 2500);
        }
    }
}
