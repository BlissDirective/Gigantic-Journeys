using System;

namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// Rolling frame-time statistics for the debug overlay (ticket M0-UNITY-04).
    /// A ring buffer of (end time, frame time) samples covering at least
    /// <see cref="HistorySeconds"/> of play at up to <see cref="MaxFps"/>.
    ///
    /// Percentile convention: "fps p99" is the frame rate implied by the 99th
    /// percentile frame time (1000 / p99 ms), i.e. the rate 99 % of frames meet
    /// or beat. "fps p50" is the rate implied by the median frame time. The
    /// "1 s average" is frames divided by the time they took in the window.
    /// </summary>
    public sealed class FrameStats
    {
        public const float HistorySeconds = 60f;
        public const int MaxFps = 240;

        readonly float[] _time;
        readonly float[] _dt;
        readonly float[] _scratch;
        int _head; // next write index
        int _count;

        public FrameStats(int capacity = (int)HistorySeconds * MaxFps)
        {
            if (capacity < 2)
                throw new ArgumentOutOfRangeException(nameof(capacity));
            _time = new float[capacity];
            _dt = new float[capacity];
            _scratch = new float[capacity];
        }

        public int Count => _count;

        /// <summary>Time of the latest sample (seconds, caller's clock), or 0 when empty.</summary>
        public float LatestTime => _count == 0 ? 0f : _time[Index(_count - 1)];

        public void Clear()
        {
            _head = 0;
            _count = 0;
        }

        /// <summary>Record one frame that ended at <paramref name="time"/> and took <paramref name="deltaSeconds"/>.</summary>
        public void Add(float time, float deltaSeconds)
        {
            if (deltaSeconds <= 0f || float.IsNaN(deltaSeconds) || float.IsInfinity(deltaSeconds))
                return;
            _time[_head] = time;
            _dt[_head] = deltaSeconds;
            _head = (_head + 1) % _time.Length;
            if (_count < _time.Length)
                _count++;
        }

        // Logical index 0 = oldest sample.
        int Index(int logical) => (_head - _count + logical + _time.Length) % _time.Length;

        /// <summary>Copies the frame times (seconds) of the last <paramref name="windowSeconds"/> into the scratch buffer.</summary>
        int Collect(float windowSeconds)
        {
            if (_count == 0)
                return 0;
            var cutoff = LatestTime - windowSeconds;
            var n = 0;
            for (var i = _count - 1; i >= 0; i--)
            {
                var k = Index(i);
                if (_time[k] <= cutoff)
                    break;
                _scratch[n++] = _dt[k];
            }
            return n;
        }

        /// <summary>Frames in the window divided by the time they took; 0 when empty.</summary>
        public float AverageFps(float windowSeconds)
        {
            var n = Collect(windowSeconds);
            if (n == 0)
                return 0f;
            double sum = 0;
            for (var i = 0; i < n; i++)
                sum += _scratch[i];
            return sum > 0 ? (float)(n / sum) : 0f;
        }

        /// <summary>Mean frame time in milliseconds over the window; 0 when empty.</summary>
        public float AverageFrameMs(float windowSeconds)
        {
            var fps = AverageFps(windowSeconds);
            return fps > 0 ? 1000f / fps : 0f;
        }

        /// <summary>
        /// The <paramref name="percentile"/> (0-100) frame time in milliseconds over the
        /// window, nearest-rank method; 0 when empty.
        /// </summary>
        public float FrameMsPercentile(float percentile, float windowSeconds)
        {
            var n = Collect(windowSeconds);
            if (n == 0)
                return 0f;
            Array.Sort(_scratch, 0, n);
            var p = Math.Min(100f, Math.Max(0f, percentile));
            var rank = (int)Math.Ceiling(p / 100f * n) - 1;
            rank = Math.Min(n - 1, Math.Max(0, rank));
            return _scratch[rank] * 1000f;
        }

        /// <summary>Frame rate implied by the percentile frame time (1000 / ms); 0 when empty.</summary>
        public float FpsAtPercentile(float percentile, float windowSeconds)
        {
            var ms = FrameMsPercentile(percentile, windowSeconds);
            return ms > 0 ? 1000f / ms : 0f;
        }

        /// <summary>Seconds actually covered by samples inside the window.</summary>
        public float CoveredSeconds(float windowSeconds)
        {
            var n = Collect(windowSeconds);
            double sum = 0;
            for (var i = 0; i < n; i++)
                sum += _scratch[i];
            return (float)sum;
        }

        /// <summary>Number of samples inside the window.</summary>
        public int CountInWindow(float windowSeconds) => Collect(windowSeconds);
    }
}
