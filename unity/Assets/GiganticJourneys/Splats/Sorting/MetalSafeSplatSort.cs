using System;
using System.Reflection;
using GaussianSplatting.Runtime;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.Splats.Sorting
{
    /// <summary>
    /// Takes over the per-frame depth sort of the <see cref="GaussianSplatRenderer"/> on this
    /// GameObject with the Metal-safe bitonic sort (ticket M1-UNITY-01, Tier B; upstream radix
    /// glitch aras-p/UnityGaussianSplatting#226). The pinned package stays unmodified: its own
    /// sort is pushed to "never" and, before each camera renders, this writes fresh
    /// (view-depth key, splat index) pairs into the package's sort buffers and sorts them, so
    /// the package draws in the same back-to-front order its radix sort would produce.
    /// <para>Auto mode engages on Metal only (iOS device, macOS editor); other APIs keep the
    /// package sort. The package fields are reached by reflection against the commit pinned in
    /// ADR-0001 addendum 1; <see cref="BindingsResolve"/> is asserted by an EditMode test so a
    /// package bump that renames them fails CI instead of silently falling back.</para>
    /// </summary>
    [RequireComponent(typeof(GaussianSplatRenderer))]
    public sealed class MetalSafeSplatSort : MonoBehaviour
    {
        public enum Mode
        {
            /// <summary>On under Metal, off elsewhere.</summary>
            Auto,
            ForceOn,
            Off,
        }

        public Mode mode = Mode.Auto;

        [Tooltip(
            "Sort every Nth frame (1 = every frame); the tier's sortEveryNthFrame is a good start."
        )]
        [Min(1)]
        public int sortEveryNthFrame = 1;

        [Tooltip(
            "Skip a due sort while the camera has moved less than this (world metres) since the last one. 0 = always sort on cadence."
        )]
        [Min(0f)]
        public float resortMoveMeters;

        [Tooltip(
            "Skip a due sort while the camera has turned less than this (degrees) since the last one. Used with resortMoveMeters."
        )]
        [Min(0f)]
        public float resortAngleDeg;

        const BindingFlags Any =
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
        static readonly Type R = typeof(GaussianSplatRenderer);
        static readonly FieldInfo SortDistances = R.GetField("m_GpuSortDistances", Any);
        static readonly FieldInfo SortKeys = R.GetField("m_GpuSortKeys", Any);
        static readonly FieldInfo PosData = R.GetField("m_GpuPosData", Any);
        static readonly FieldInfo Chunks = R.GetField("m_GpuChunks", Any);
        static readonly FieldInfo ChunksValid = R.GetField("m_GpuChunksValid", Any);

        static readonly int SplatPosId = Shader.PropertyToID("_SplatPos");
        static readonly int SplatChunksId = Shader.PropertyToID("_SplatChunks");
        static readonly int SplatChunkCountId = Shader.PropertyToID("_SplatChunkCount");
        static readonly int SplatFormatId = Shader.PropertyToID("_SplatFormat");
        static readonly int CountId = Shader.PropertyToID("_Count");
        static readonly int KeysId = Shader.PropertyToID("_Keys");
        static readonly int ValuesId = Shader.PropertyToID("_Values");
        static readonly int MatrixMvId = Shader.PropertyToID("_MatrixMV");

        /// <summary>True when every package field this component needs exists.</summary>
        public static bool BindingsResolve =>
            SortDistances != null
            && SortKeys != null
            && PosData != null
            && Chunks != null
            && ChunksValid != null;

        /// <summary>Whether the takeover applies to this graphics API under <paramref name="m"/>.</summary>
        public static bool EngagesFor(Mode m, GraphicsDeviceType api) =>
            m == Mode.ForceOn || (m == Mode.Auto && api == GraphicsDeviceType.Metal);

        GaussianSplatRenderer _renderer;
        MetalSafeSplatSorter _sorter;
        CommandBuffer _cmd;
        int _packageSortNth;
        int _frame;
        bool _engaged;
        bool _hasSorted;
        GraphicsBuffer _sortedKeys;
        Vector3 _sortedPos;
        Quaternion _sortedRot;

        /// <summary>True while this component (not the package) is sorting.</summary>
        public bool Engaged => _engaged;

        /// <summary>Camera renders sorted by this component (for the debug HUD / tests).</summary>
        public int SortsIssued { get; private set; }

        /// <summary>Due sorts skipped because the camera was (nearly) still.</summary>
        public int SortsSkippedStill { get; private set; }

        /// <summary>
        /// Whether a due sort is needed: always when gating is off (both thresholds 0) or nothing
        /// was sorted yet, else once the camera moved at least <paramref name="minMove"/> or turned
        /// at least <paramref name="minAngleDeg"/> since the last sort. The draw order depends on
        /// the view position and direction only, so a still camera keeps a valid order.
        /// </summary>
        public static bool NeedsResort(
            bool hasSorted,
            Vector3 lastPos,
            Quaternion lastRot,
            Vector3 pos,
            Quaternion rot,
            float minMove,
            float minAngleDeg
        )
        {
            if (!hasSorted || (minMove <= 0f && minAngleDeg <= 0f))
                return true;
            return (pos - lastPos).sqrMagnitude >= minMove * minMove
                || Quaternion.Angle(lastRot, rot) >= minAngleDeg;
        }

        void OnEnable()
        {
            _renderer = GetComponent<GaussianSplatRenderer>();
            _engaged =
                EngagesFor(mode, SystemInfo.graphicsDeviceType)
                && BindingsResolve
                && (_sorter = MetalSafeSplatSorter.TryCreate()) != null;
            if (!_engaged)
            {
                if (EngagesFor(mode, SystemInfo.graphicsDeviceType))
                    Debug.LogWarning(
                        "[GJ-SPLAT-SORT] Metal-safe sort unavailable (no compute or package fields moved); package radix sort stays on"
                    );
                return;
            }
            _cmd = new CommandBuffer { name = "GJ Metal-safe splat sort" };
            _packageSortNth = _renderer.m_SortNthFrame;
            _renderer.m_SortNthFrame = int.MaxValue; // package sorts once at frame 0, never again
            RenderPipelineManager.beginCameraRendering += OnBeginCamera;
            Debug.Log($"[GJ-SPLAT-SORT] engaged on {SystemInfo.graphicsDeviceType} for {name}");
        }

        void OnDisable()
        {
            if (!_engaged)
                return;
            RenderPipelineManager.beginCameraRendering -= OnBeginCamera;
            if (_renderer != null)
                _renderer.m_SortNthFrame = Mathf.Max(1, _packageSortNth);
            _cmd?.Release();
            _cmd = null;
            _engaged = false;
            _hasSorted = false;
        }

        void LateUpdate() => _frame++;

        // SplatRenderSettingsApplier re-applies the tier's cadence on quality changes: adopt it
        // and keep the package's own sort parked (checked right before each camera renders).
        void ParkPackageSort()
        {
            if (_renderer.m_SortNthFrame == int.MaxValue)
                return;
            sortEveryNthFrame = Mathf.Max(1, _renderer.m_SortNthFrame);
            _renderer.m_SortNthFrame = int.MaxValue;
        }

        void OnBeginCamera(ScriptableRenderContext ctx, Camera cam)
        {
            if (cam.cameraType == CameraType.Preview || _renderer == null)
                return;
            ParkPackageSort();
            if (_frame % Mathf.Max(1, sortEveryNthFrame) != 0)
                return;
            if (!_renderer.isActiveAndEnabled || !_renderer.HasValidRenderSetup)
                return;
            var keys = (GraphicsBuffer)SortDistances.GetValue(_renderer);
            var values = (GraphicsBuffer)SortKeys.GetValue(_renderer);
            var pos = (GraphicsBuffer)PosData.GetValue(_renderer);
            var chunks = (GraphicsBuffer)Chunks.GetValue(_renderer);
            var chunksValid = (bool)ChunksValid.GetValue(_renderer);
            var count = Mathf.Min(_renderer.splatCount, keys?.count ?? 0);
            if (keys == null || values == null || pos == null || chunks == null || count <= 0)
                return;
            var camTr = cam.transform;
            // A new buffer (asset swap, re-enable) always needs a sort.
            if (
                !NeedsResort(
                    _hasSorted && keys == _sortedKeys,
                    _sortedPos,
                    _sortedRot,
                    camTr.position,
                    camTr.rotation,
                    resortMoveMeters,
                    resortAngleDeg
                )
            )
            {
                SortsSkippedStill++;
                return;
            }

            // Same view-space z convention as the package's CalcDistances.
            var worldToCam = cam.worldToCameraMatrix;
            worldToCam.m20 *= -1;
            worldToCam.m21 *= -1;
            worldToCam.m22 *= -1;
            var mv = worldToCam * _renderer.transform.localToWorldMatrix;

            var cs = _sorter.Compute;
            var k = _sorter.CalcKeysKernel;
            _cmd.Clear();
            _cmd.SetComputeBufferParam(cs, k, SplatPosId, pos);
            _cmd.SetComputeBufferParam(cs, k, SplatChunksId, chunks);
            _cmd.SetComputeIntParam(cs, SplatChunkCountId, chunksValid ? chunks.count : 0);
            _cmd.SetComputeIntParam(cs, SplatFormatId, (int)_renderer.m_Asset.posFormat);
            _cmd.SetComputeMatrixParam(cs, MatrixMvId, mv);
            _cmd.SetComputeIntParam(cs, CountId, count);
            _cmd.SetComputeBufferParam(cs, k, KeysId, keys);
            _cmd.SetComputeBufferParam(cs, k, ValuesId, values);
            _cmd.DispatchCompute(
                cs,
                k,
                (count + BitonicSortNetwork.Threads - 1) / BitonicSortNetwork.Threads,
                1,
                1
            );
            _sorter.Sort(_cmd, keys, values, count);
            Graphics.ExecuteCommandBuffer(_cmd);
            SortsIssued++;
            _hasSorted = true;
            _sortedKeys = keys;
            _sortedPos = camTr.position;
            _sortedRot = camTr.rotation;
        }
    }
}
