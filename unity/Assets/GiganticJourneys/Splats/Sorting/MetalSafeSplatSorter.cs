using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.Splats.Sorting
{
    /// <summary>
    /// Records the Metal-safe bitonic sort (<see cref="BitonicSortNetwork"/>) into a command
    /// buffer: (uint key, uint value) pairs in two structured buffers, sorted ascending in place.
    /// Loads <c>Resources/GJ/MetalSafeSplatSort.compute</c>. Ticket M1-UNITY-01, Tier B.
    /// </summary>
    public sealed class MetalSafeSplatSorter
    {
        public const string ShaderResource = "GJ/MetalSafeSplatSort";

        static readonly int KeysId = UnityEngine.Shader.PropertyToID("_Keys");
        static readonly int ValuesId = UnityEngine.Shader.PropertyToID("_Values");
        static readonly int CountId = UnityEngine.Shader.PropertyToID("_Count");
        static readonly int KId = UnityEngine.Shader.PropertyToID("_K");
        static readonly int JId = UnityEngine.Shader.PropertyToID("_J");

        readonly ComputeShader _cs;
        readonly int _calcKeys;
        readonly int _localSort;
        readonly int _flip;
        readonly int _disperse;
        readonly int _localDisperse;

        public MetalSafeSplatSorter(ComputeShader cs)
        {
            _cs = cs ? cs : throw new ArgumentNullException(nameof(cs));
            _calcKeys = cs.FindKernel("CSCalcKeys");
            _localSort = cs.FindKernel("CSLocalSort");
            _flip = cs.FindKernel("CSFlip");
            _disperse = cs.FindKernel("CSDisperse");
            _localDisperse = cs.FindKernel("CSLocalDisperse");
        }

        public ComputeShader Compute => _cs;
        public int CalcKeysKernel => _calcKeys;

        /// <summary>The sorter on the bundled shader, or null when compute is unavailable.</summary>
        public static MetalSafeSplatSorter TryCreate()
        {
            if (
                !SystemInfo.supportsComputeShaders
                || SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null
            )
                return null;
            var cs = Resources.Load<ComputeShader>(ShaderResource);
            // Kernels exist only once compiled for the active device (none under -nographics).
            return cs && cs.HasKernel("CSCalcKeys") ? new MetalSafeSplatSorter(cs) : null;
        }

        /// <summary>Appends the sort of the first <paramref name="count"/> pairs to <paramref name="cmd"/>.</summary>
        public void Sort(CommandBuffer cmd, GraphicsBuffer keys, GraphicsBuffer values, int count)
        {
            if (count <= 1)
                return;
            cmd.SetComputeIntParam(_cs, CountId, count);
            foreach (var s in BitonicSortNetwork.Schedule(count))
            {
                var kernel = KernelFor(s.Kernel);
                cmd.SetComputeBufferParam(_cs, kernel, KeysId, keys);
                cmd.SetComputeBufferParam(_cs, kernel, ValuesId, values);
                cmd.SetComputeIntParam(_cs, KId, (int)s.K);
                cmd.SetComputeIntParam(_cs, JId, (int)s.J);
                cmd.DispatchCompute(_cs, kernel, s.Groups, 1, 1);
            }
        }

        int KernelFor(BitonicSortNetwork.Kernel k)
        {
            switch (k)
            {
                case BitonicSortNetwork.Kernel.LocalSort:
                    return _localSort;
                case BitonicSortNetwork.Kernel.Flip:
                    return _flip;
                case BitonicSortNetwork.Kernel.Disperse:
                    return _disperse;
                default:
                    return _localDisperse;
            }
        }
    }
}
