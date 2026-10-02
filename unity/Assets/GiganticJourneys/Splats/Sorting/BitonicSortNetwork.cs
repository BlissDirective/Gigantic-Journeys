using System;
using System.Collections.Generic;

namespace GiganticJourneys.Splats.Sorting
{
    /// <summary>
    /// The dispatch schedule of the Metal-safe splat sort (<c>MetalSafeSplatSort.compute</c>,
    /// ticket M1-UNITY-01) plus a CPU mirror of every kernel, so the network is proven on any
    /// machine (EditMode, no GPU) and the GPU path only has to match it. Flip/disperse bitonic:
    /// every comparison is ascending, so a count that is not a power of two sorts correctly by
    /// treating indices at or above the count as +infinity.
    /// </summary>
    public static class BitonicSortNetwork
    {
        /// <summary>Threads per group in the compute shader.</summary>
        public const int Threads = 256;

        /// <summary>Elements a group sorts in threadgroup memory (2 per thread).</summary>
        public const int Block = 2 * Threads;

        public enum Kernel
        {
            LocalSort,
            Flip,
            Disperse,
            LocalDisperse,
        }

        /// <summary>One dispatch: the kernel, its k / j constants and its group count.</summary>
        public readonly struct Step
        {
            public readonly Kernel Kernel;
            public readonly uint K;
            public readonly uint J;
            public readonly int Groups;

            public Step(Kernel kernel, uint k, uint j, int groups)
            {
                Kernel = kernel;
                K = k;
                J = j;
                Groups = groups;
            }

            public override string ToString() => $"{Kernel}(k={K}, j={J}, groups={Groups})";
        }

        /// <summary>Smallest power of two at or above <paramref name="n"/> (1 for 0).</summary>
        public static uint NextPow2(uint n)
        {
            uint p = 1;
            while (p < n)
                p <<= 1;
            return p;
        }

        /// <summary>The ordered dispatches that sort <paramref name="count"/> elements.</summary>
        public static List<Step> Schedule(int count)
        {
            var steps = new List<Step>();
            if (count <= 1)
                return steps;
            var n = (uint)count;
            var pow2 = NextPow2(n);
            var blocks = (int)((n + Block - 1) / Block);
            var pairGroups = (int)Math.Max(1, (pow2 / 2 + Threads - 1) / Threads);
            steps.Add(new Step(Kernel.LocalSort, Block, 0, blocks));
            for (uint k = 2 * Block; k <= pow2; k <<= 1)
            {
                steps.Add(new Step(Kernel.Flip, k, 0, pairGroups));
                for (var j = k >> 2; j >= Block; j >>= 1)
                    steps.Add(new Step(Kernel.Disperse, k, j, pairGroups));
                steps.Add(new Step(Kernel.LocalDisperse, k, Block / 2, blocks));
            }
            return steps;
        }

        /// <summary>Runs the schedule on the CPU, kernel by kernel (reference + tests).</summary>
        public static void SortOnCpu(uint[] keys, uint[] values, int count)
        {
            if (keys == null || values == null)
                throw new ArgumentNullException(keys == null ? nameof(keys) : nameof(values));
            if (count > keys.Length || count > values.Length)
                throw new ArgumentOutOfRangeException(nameof(count));
            foreach (var s in Schedule(count))
            {
                switch (s.Kernel)
                {
                    case Kernel.LocalSort:
                        for (var g = 0; g < s.Groups; g++)
                            LocalSort(keys, values, count, g);
                        break;
                    case Kernel.LocalDisperse:
                        for (var g = 0; g < s.Groups; g++)
                            LocalDisperse(keys, values, count, g, Block / 2);
                        break;
                    case Kernel.Flip:
                        for (uint t = 0; t < (uint)s.Groups * Threads; t++)
                        {
                            var half = s.K >> 1;
                            var start = t / half * s.K;
                            var o = t % half;
                            Swap(keys, values, count, start + o, start + s.K - 1 - o);
                        }
                        break;
                    case Kernel.Disperse:
                        for (uint t = 0; t < (uint)s.Groups * Threads; t++)
                        {
                            var i = t / s.J * (s.J << 1) + t % s.J;
                            Swap(keys, values, count, i, i + s.J);
                        }
                        break;
                }
            }
        }

        static void Swap(uint[] keys, uint[] values, int count, uint i, uint l)
        {
            if (l >= (uint)count)
                return;
            if (keys[i] > keys[l])
            {
                (keys[i], keys[l]) = (keys[l], keys[i]);
                (values[i], values[l]) = (values[l], values[i]);
            }
        }

        // Threadgroup kernels: the block is copied out with +inf padding, exactly as on the GPU.
        static void LocalSort(uint[] keys, uint[] values, int count, int group)
        {
            var (k2, v2) = Load(keys, values, count, group);
            for (uint k = 2; k <= Block; k <<= 1)
            {
                for (uint t = 0; t < Threads; t++)
                {
                    var half = k >> 1;
                    var start = t / half * k;
                    var o = t % half;
                    Swap(k2, v2, Block, start + o, start + k - 1 - o);
                }
                Disperse(k2, v2, k >> 2);
            }
            Store(keys, values, count, group, k2, v2);
        }

        static void LocalDisperse(uint[] keys, uint[] values, int count, int group, uint fromJ)
        {
            var (k2, v2) = Load(keys, values, count, group);
            Disperse(k2, v2, fromJ);
            Store(keys, values, count, group, k2, v2);
        }

        static void Disperse(uint[] k2, uint[] v2, uint fromJ)
        {
            for (var j = fromJ; j > 0; j >>= 1)
            {
                for (uint t = 0; t < Threads; t++)
                {
                    var i = t / j * (j << 1) + t % j;
                    Swap(k2, v2, Block, i, i + j);
                }
            }
        }

        static (uint[], uint[]) Load(uint[] keys, uint[] values, int count, int group)
        {
            var k2 = new uint[Block];
            var v2 = new uint[Block];
            for (var s = 0; s < Block; s++)
            {
                var g = group * Block + s;
                k2[s] = g < count ? keys[g] : uint.MaxValue;
                v2[s] = g < count ? values[g] : 0u;
            }
            return (k2, v2);
        }

        static void Store(uint[] keys, uint[] values, int count, int group, uint[] k2, uint[] v2)
        {
            for (var s = 0; s < Block; s++)
            {
                var g = group * Block + s;
                if (g < count)
                {
                    keys[g] = k2[s];
                    values[g] = v2[s];
                }
            }
        }
    }
}
