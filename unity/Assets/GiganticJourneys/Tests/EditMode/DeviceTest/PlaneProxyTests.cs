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
        public void CommittedDescriptors_KeepPlaneProxiesOff()
        {
            foreach (var path in SplatRoomScene.DescriptorPaths())
            {
                var d = SplatRoomDescriptor.Parse(File.ReadAllText(path));
                Assert.IsFalse(d.HasPlaneProxies, $"{path}: plane proxies must stay off by default");
            }
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
            d.planeProxies = new[] { new SplatRoomDescriptor.PlaneProxy { corners = new float[5] } };
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
