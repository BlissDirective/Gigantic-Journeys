using System;
using System.Linq;
using GiganticJourneys.Splats.Sorting;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Ticket M1-UNITY-01: the Metal-safe splat sort. The CPU tests prove the flip/disperse
    /// network and its dispatch schedule (exactly what the GPU runs); the GPU test runs the
    /// real compute shader where compute exists (box: xvfb + Vulkan; CI -nographics skips it)
    /// and is the template for the on-device Metal check.
    /// </summary>
    public class MetalSafeSplatSortTests
    {
        static readonly int[] Counts =
        {
            0,
            1,
            2,
            3,
            7,
            255,
            511,
            512,
            513,
            1000,
            1024,
            1025,
            4097,
            70001,
        };

        static (uint[] keys, uint[] values) Random(int n, int seed, uint range = uint.MaxValue)
        {
            var rng = new System.Random(seed);
            var keys = new uint[n];
            var values = new uint[n];
            for (var i = 0; i < n; i++)
            {
                keys[i] = (uint)(rng.NextDouble() * range);
                values[i] = (uint)i;
            }
            return (keys, values);
        }

        static void AssertSortedPermutation(uint[] original, uint[] keys, uint[] values, int n)
        {
            for (var i = 1; i < n; i++)
                Assert.LessOrEqual(keys[i - 1], keys[i], $"not ascending at {i} of {n}");
            var seen = new bool[n];
            for (var i = 0; i < n; i++)
            {
                Assert.Less(values[i], (uint)n, "value out of range");
                Assert.IsFalse(seen[values[i]], $"value {values[i]} duplicated");
                seen[values[i]] = true;
                Assert.AreEqual(original[values[i]], keys[i], "key and value separated");
            }
        }

        [Test]
        public void CpuNetworkSortsEveryCountIncludingNonPowersOfTwo(
            [ValueSource(nameof(Counts))] int n
        )
        {
            var (keys, values) = Random(n, n + 1);
            var original = (uint[])keys.Clone();
            BitonicSortNetwork.SortOnCpu(keys, values, n);
            AssertSortedPermutation(original, keys, values, n);
        }

        [Test]
        public void CpuNetworkHandlesDuplicatesAndExtremes()
        {
            var (keys, values) = Random(3001, 7, 5);
            keys[0] = uint.MaxValue;
            keys[1] = 0;
            keys[2] = uint.MaxValue;
            var original = (uint[])keys.Clone();
            BitonicSortNetwork.SortOnCpu(keys, values, keys.Length);
            AssertSortedPermutation(original, keys, values, keys.Length);
        }

        [Test]
        public void CpuNetworkLeavesElementsPastCountUntouched()
        {
            var (keys, values) = Random(600, 3);
            var tail = keys.Skip(513).ToArray();
            BitonicSortNetwork.SortOnCpu(keys, values, 513);
            CollectionAssert.AreEqual(tail, keys.Skip(513).ToArray());
        }

        [Test]
        public void ScheduleShapeMatchesTheNetwork()
        {
            Assert.IsEmpty(BitonicSortNetwork.Schedule(1));
            var small = BitonicSortNetwork.Schedule(512);
            Assert.AreEqual(1, small.Count, "one block sorts entirely in threadgroup memory");
            Assert.AreEqual(BitonicSortNetwork.Kernel.LocalSort, small[0].Kernel);

            // 1M splats (High tier budget territory): log2(2^20/512)=11 merge stages.
            var big = BitonicSortNetwork.Schedule(1 << 20);
            Assert.AreEqual(11, big.Count(s => s.Kernel == BitonicSortNetwork.Kernel.Flip));
            Assert.AreEqual(
                11,
                big.Count(s => s.Kernel == BitonicSortNetwork.Kernel.LocalDisperse)
            );
            Assert.AreEqual(55, big.Count(s => s.Kernel == BitonicSortNetwork.Kernel.Disperse));
            Assert.IsTrue(
                big.All(s => s.Groups >= 1 && s.Groups <= 65535),
                "group count within Metal limits"
            );
            Assert.AreEqual(2048, big[0].Groups);
        }

        [Test]
        public void NextPow2()
        {
            Assert.AreEqual(1u, BitonicSortNetwork.NextPow2(0));
            Assert.AreEqual(1u, BitonicSortNetwork.NextPow2(1));
            Assert.AreEqual(512u, BitonicSortNetwork.NextPow2(512));
            Assert.AreEqual(1024u, BitonicSortNetwork.NextPow2(513));
        }

        [Test]
        public void PinnedPackageExposesTheFieldsTheTakeoverNeeds()
        {
            Assert.IsTrue(
                MetalSafeSplatSort.BindingsResolve,
                "GaussianSplatRenderer sort/pos/chunk buffers moved: re-pin or update MetalSafeSplatSort"
            );
        }

        [Test]
        public void AutoModeEngagesOnMetalOnly()
        {
            Assert.IsTrue(
                MetalSafeSplatSort.EngagesFor(
                    MetalSafeSplatSort.Mode.Auto,
                    GraphicsDeviceType.Metal
                )
            );
            Assert.IsFalse(
                MetalSafeSplatSort.EngagesFor(
                    MetalSafeSplatSort.Mode.Auto,
                    GraphicsDeviceType.Vulkan
                )
            );
            Assert.IsTrue(
                MetalSafeSplatSort.EngagesFor(
                    MetalSafeSplatSort.Mode.ForceOn,
                    GraphicsDeviceType.Vulkan
                )
            );
            Assert.IsFalse(
                MetalSafeSplatSort.EngagesFor(MetalSafeSplatSort.Mode.Off, GraphicsDeviceType.Metal)
            );
        }

        [Test]
        public void ComputeShaderShipsInResourcesWithAllKernels()
        {
            var cs = Resources.Load<ComputeShader>(MetalSafeSplatSorter.ShaderResource);
            Assert.IsNotNull(cs, "Resources/GJ/MetalSafeSplatSort.compute missing");
            var source = System.IO.File.ReadAllText(UnityEditor.AssetDatabase.GetAssetPath(cs));
            var kernels = new[]
            {
                "CSCalcKeys",
                "CSLocalSort",
                "CSFlip",
                "CSDisperse",
                "CSLocalDisperse",
            };
            foreach (var k in kernels)
                StringAssert.Contains($"#pragma kernel {k}", source);
            StringAssert.DoesNotContain(
                "Wave",
                source,
                "no wave intrinsics (the Metal failure mode)"
            );
            // Compiled kernels exist only with a graphics device (CI runs -nographics).
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                return;
            foreach (var k in kernels)
                Assert.IsTrue(cs.HasKernel(k), $"kernel {k} did not compile");
        }

        [Test]
        public void GpuSortMatchesCpuReference([Values(1, 513, 4097, 70001)] int n)
        {
            var sorter = MetalSafeSplatSorter.TryCreate();
            if (sorter == null || SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                Assert.Ignore(
                    "no compute device (-nographics); run with a GPU (box: xvfb -force-vulkan) or on device"
                );
            var (keys, values) = Random(n, 11 * n);
            var original = (uint[])keys.Clone();
            using var kb = new GraphicsBuffer(GraphicsBuffer.Target.Structured, n, sizeof(uint));
            using var vb = new GraphicsBuffer(GraphicsBuffer.Target.Structured, n, sizeof(uint));
            kb.SetData(keys);
            vb.SetData(values);
            using (var cmd = new CommandBuffer())
            {
                sorter.Sort(cmd, kb, vb, n);
                Graphics.ExecuteCommandBuffer(cmd);
            }
            var gk = new uint[n];
            var gv = new uint[n];
            kb.GetData(gk);
            vb.GetData(gv);
            AssertSortedPermutation(original, gk, gv, n);
            BitonicSortNetwork.SortOnCpu(keys, values, n);
            CollectionAssert.AreEqual(keys, gk, "GPU keys differ from the CPU reference");
        }
    }
}
