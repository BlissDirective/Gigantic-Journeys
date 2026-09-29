using System;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Blur rejection (DESIGN_SYSTEM §6: one soft haptic tick and an amber edge pulse, no words).
    /// A frame is rejected when its sharpness falls below a share of the recent median or under an
    /// absolute floor. Relative-to-median keeps it fair across textured and plain rooms.
    /// </summary>
    public sealed class BlurGate
    {
        private readonly float[] _window = new float[CaptureTuning.Blur.MedianWindow];
        private readonly float[] _scratch = new float[CaptureTuning.Blur.MedianWindow];
        private int _count;
        private int _next;

        /// <summary>Frames seen.</summary>
        public int Seen { get; private set; }

        /// <summary>Frames rejected as blurred.</summary>
        public int Rejected { get; private set; }

        /// <summary>Share of frames accepted (1 before any frame).</summary>
        public float AcceptedRatio => Seen == 0 ? 1f : 1f - (float)Rejected / Seen;

        /// <summary>Median sharpness of the recent window (0 before any frame).</summary>
        public float Median
        {
            get
            {
                if (_count == 0)
                {
                    return 0f;
                }

                Array.Copy(_window, _scratch, _count);
                Array.Sort(_scratch, 0, _count);
                return _count % 2 == 1
                    ? _scratch[_count / 2]
                    : 0.5f * (_scratch[_count / 2 - 1] + _scratch[_count / 2]);
            }
        }

        /// <summary>Judges a frame; returns true when it is accepted (sharp enough).</summary>
        public bool Accept(float sharpness)
        {
            Seen++;
            float median = Median;
            bool blurred =
                sharpness < CaptureTuning.Blur.AbsoluteFloor
                || (_count >= 3 && sharpness < median * CaptureTuning.Blur.RelativeThreshold);

            // The window tracks accepted frames only, so a blurry burst cannot drag the median down.
            if (!blurred)
            {
                _window[_next] = sharpness;
                _next = (_next + 1) % _window.Length;
                _count = Math.Min(_count + 1, _window.Length);
            }
            else
            {
                Rejected++;
            }

            return !blurred;
        }
    }
}
