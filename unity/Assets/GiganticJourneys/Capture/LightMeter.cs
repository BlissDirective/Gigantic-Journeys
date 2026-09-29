using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Low light (DESIGN_SYSTEM §6): after a stretch of dark frames, one card "Too dark here. Turn on
    /// a lamp?" with Continue anyway, once per session; also the light component of the readiness
    /// score (median luma mapped to 0–1).
    /// </summary>
    public sealed class LightMeter
    {
        // 64 luma buckets are plenty for a median and keep this allocation-free.
        private readonly int[] _histogram = new int[64];
        private int _frames;
        private double _darkSince = -1;

        /// <summary>True on the frame the low-light card should appear (once per session).</summary>
        public bool ShowCardThisFrame { get; private set; }

        /// <summary>True once the card has been shown this session.</summary>
        public bool CardShown { get; private set; }

        /// <summary>Median luma so far (0–1).</summary>
        public float MedianLuma
        {
            get
            {
                if (_frames == 0)
                {
                    return 0f;
                }

                int half = (_frames + 1) / 2;
                int running = 0;
                for (int b = 0; b < _histogram.Length; b++)
                {
                    running += _histogram[b];
                    if (running >= half)
                    {
                        return (b + 0.5f) / _histogram.Length;
                    }
                }

                return 1f;
            }
        }

        /// <summary>Light component of the readiness score.</summary>
        public float Score =>
            Mathf.Clamp01(
                (MedianLuma - CaptureTuning.Light.ScoreZeroLuma)
                    / (CaptureTuning.Light.ScoreFullLuma - CaptureTuning.Light.ScoreZeroLuma)
            );

        /// <summary>Feeds one frame.</summary>
        public void Add(in CaptureFrame frame)
        {
            ShowCardThisFrame = false;
            int bucket = Mathf.Clamp(
                (int)(frame.Luma * _histogram.Length),
                0,
                _histogram.Length - 1
            );
            _histogram[bucket]++;
            _frames++;

            if (frame.Luma < CaptureTuning.Light.DarkLuma)
            {
                if (_darkSince < 0)
                {
                    _darkSince = frame.Time;
                }
                else if (!CardShown && frame.Time - _darkSince >= CaptureTuning.Light.CardAfterSec)
                {
                    CardShown = true;
                    ShowCardThisFrame = true;
                }
            }
            else
            {
                _darkSince = -1;
            }
        }
    }
}
