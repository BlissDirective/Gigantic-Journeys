using System;
using System.Globalization;

namespace GiganticJourneys.DeviceTest
{
    /// <summary>
    /// Frame times split by what the previous frame did (issued a splat sort, refreshed the
    /// room label, neither), so the device report can say whether the p99 spikes come from
    /// sort frames (build 50: frame_ms_p99 33.4 with p50 16.7). Fixed-size rings, no
    /// per-frame allocation.
    /// </summary>
    public sealed class FrameTimeSplit
    {
        public enum Kind
        {
            Sort = 0,
            Label = 1,
            Other = 2,
        }

        readonly float[][] _rings;
        readonly int[] _counts;
        readonly int[] _next;
        readonly float[] _scratch;

        public FrameTimeSplit(int capacityPerKind)
        {
            if (capacityPerKind <= 0)
                throw new ArgumentOutOfRangeException(nameof(capacityPerKind));
            var kinds = Enum.GetValues(typeof(Kind)).Length;
            _rings = new float[kinds][];
            for (var i = 0; i < kinds; i++)
                _rings[i] = new float[capacityPerKind];
            _counts = new int[kinds];
            _next = new int[kinds];
            _scratch = new float[capacityPerKind];
        }

        public void Add(Kind kind, float frameMs)
        {
            var k = (int)kind;
            var ring = _rings[k];
            ring[_next[k]] = frameMs;
            _next[k] = (_next[k] + 1) % ring.Length;
            if (_counts[k] < ring.Length)
                _counts[k]++;
        }

        public int Count(Kind kind) => _counts[(int)kind];

        /// <summary>Nearest-rank percentile (0..100) of the kept frame times; NaN when empty.</summary>
        public float Percentile(Kind kind, float pct)
        {
            var n = _counts[(int)kind];
            if (n == 0)
                return float.NaN;
            Array.Copy(_rings[(int)kind], _scratch, n);
            Array.Sort(_scratch, 0, n);
            var rank = (int)Math.Ceiling(pct / 100.0 * n);
            return _scratch[Math.Clamp(rank, 1, n) - 1];
        }

        /// <summary>"p50 / p99 ms (n frames)" for the report.</summary>
        public string Summary(Kind kind)
        {
            var n = Count(kind);
            if (n == 0)
                return "no frames";
            var ci = CultureInfo.InvariantCulture;
            return $"p50 {Percentile(kind, 50).ToString("0.0", ci)} / p99 {Percentile(kind, 99).ToString("0.0", ci)} ms ({n.ToString(ci)} frames)";
        }
    }
}
