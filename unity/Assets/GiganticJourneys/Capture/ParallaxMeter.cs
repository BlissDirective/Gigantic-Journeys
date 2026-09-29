using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// Overlap / parallax (capture-ux-coaching-v1 §3): multi-view reconstruction needs baseline
    /// between views, which players never think about. Measured as the RMS distance of accepted camera
    /// positions from their centroid (Welford, O(1) memory), scored against a per-mode target.
    /// </summary>
    public sealed class ParallaxMeter
    {
        private readonly float _target;
        private int _n;
        private Vector3 _mean;
        private float _m2;

        /// <summary>Creates a meter for the mode.</summary>
        public ParallaxMeter(CaptureMode mode)
        {
            _target =
                mode == CaptureMode.Room
                    ? CaptureTuning.Parallax.RoomTargetSpread
                    : CaptureTuning.Parallax.TabletopTargetSpread;
        }

        /// <summary>RMS distance of camera positions from their centroid (m).</summary>
        public float Spread => _n < 2 ? 0f : Mathf.Sqrt(_m2 / _n);

        /// <summary>Parallax component of the readiness score, 0–1.</summary>
        public float Score => Mathf.Clamp01(Spread / _target);

        /// <summary>Adds an accepted frame's camera position.</summary>
        public void Add(Vector3 position)
        {
            _n++;
            Vector3 delta = position - _mean;
            _mean += delta / _n;
            _m2 += Vector3.Dot(delta, position - _mean);
        }
    }

    /// <summary>Tracking continuity: share of recorded frames with normal tracking.</summary>
    public sealed class TrackingMeter
    {
        private int _frames;
        private int _normal;
        private double _notNormalSince = -1;

        /// <summary>Share of frames with normal tracking (1 before any frame).</summary>
        public float NormalFraction => _frames == 0 ? 1f : (float)_normal / _frames;

        /// <summary>True while tracking has been lost long enough to ask for relocalization.</summary>
        public bool NeedsRelocalize { get; private set; }

        /// <summary>Feeds one frame.</summary>
        public void Add(in CaptureFrame frame)
        {
            _frames++;
            if (frame.Tracking == TrackingQuality.Normal)
            {
                _normal++;
                _notNormalSince = -1;
                NeedsRelocalize = false;
                return;
            }

            if (_notNormalSince < 0)
            {
                _notNormalSince = frame.Time;
            }

            if (frame.Time - _notNormalSince >= CaptureTuning.Tracking.RelocalizeAfterSec)
            {
                NeedsRelocalize = true;
            }
        }
    }
}
