using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// The speed arc under the record button (DESIGN_SYSTEM §6 "Speed"): smoothed linear and angular
    /// camera speed as a 0–1+ pace (1 = the fastest good pace), amber above 1, one haptic on turning
    /// amber, and "Slow down a little" after a full second of amber.
    /// </summary>
    public sealed class SpeedMeter
    {
        private readonly float _maxLinear;
        private bool _hasPrevious;
        private Vector3 _previousPosition;
        private Quaternion _previousRotation;
        private double _previousTime;
        private double _amberSince = -1;
        private bool _hintShown;

        /// <summary>Creates a meter tuned for the capture mode.</summary>
        public SpeedMeter(CaptureMode mode)
        {
            _maxLinear =
                mode == CaptureMode.Room
                    ? CaptureTuning.Speed.RoomMaxLinear
                    : CaptureTuning.Speed.TabletopMaxLinear;
        }

        /// <summary>Smoothed linear speed (m/s).</summary>
        public float LinearSpeed { get; private set; }

        /// <summary>Smoothed angular speed (deg/s).</summary>
        public float AngularSpeed { get; private set; }

        /// <summary>Pace: the larger of linear and angular speed over their limits (1 = limit).</summary>
        public float Pace =>
            Mathf.Max(LinearSpeed / _maxLinear, AngularSpeed / CaptureTuning.Speed.MaxAngularDeg);

        /// <summary>True while the arc shows amber.</summary>
        public bool IsAmber => Pace > 1f;

        /// <summary>Set on the frame the arc turns amber (one gentle haptic).</summary>
        public bool HapticThisFrame { get; private set; }

        /// <summary>Set once amber has lasted a full second ("Slow down a little"); cleared when pace recovers.</summary>
        public bool ShowSlowDownHint => _hintShown;

        /// <summary>Forgets the previous pose (after a pause or relocalization) so no false spike is measured.</summary>
        public void Reset()
        {
            _hasPrevious = false;
            _amberSince = -1;
            _hintShown = false;
            HapticThisFrame = false;
        }

        /// <summary>Feeds one frame.</summary>
        public void Add(in CaptureFrame frame)
        {
            HapticThisFrame = false;
            if (!_hasPrevious || frame.Time <= _previousTime)
            {
                Remember(frame);
                return;
            }

            float dt = (float)(frame.Time - _previousTime);
            float linear = Vector3.Distance(frame.Position, _previousPosition) / dt;
            float angular = Quaternion.Angle(frame.Rotation, _previousRotation) / dt;
            float alpha = 1f - Mathf.Exp(-dt / CaptureTuning.Speed.SmoothingSec);
            LinearSpeed += (linear - LinearSpeed) * alpha;
            AngularSpeed += (angular - AngularSpeed) * alpha;

            if (IsAmber)
            {
                if (_amberSince < 0)
                {
                    _amberSince = frame.Time;
                    HapticThisFrame = true;
                }
                else if (frame.Time - _amberSince >= CaptureTuning.Speed.SlowDownHintAfterSec)
                {
                    _hintShown = true;
                }
            }
            else
            {
                _amberSince = -1;
                _hintShown = false;
            }

            Remember(frame);
        }

        private void Remember(in CaptureFrame frame)
        {
            _hasPrevious = true;
            _previousPosition = frame.Position;
            _previousRotation = frame.Rotation;
            _previousTime = frame.Time;
        }
    }
}
