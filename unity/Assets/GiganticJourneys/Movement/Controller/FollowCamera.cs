using System.Collections.Generic;
using GiganticJourneys.Movement.Intent;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace GiganticJourneys.Movement.Controller
{
    /// <summary>
    /// Follow camera (Bible §8 subset; collision and per-verb rules are M1): distance 4A,
    /// height 1.6A, look-ahead 0.8A in the travel direction, +0.5A and +4° FOV at run/sprint,
    /// and no vertical follow for the first 0.2 s of a jump. Numbers from movement.json
    /// <c>camera</c> (<see cref="MovementConfig.CameraSection"/>, AUTH #036; DESIGN_SYSTEM
    /// decision 5). The yaw starts where the scene placed the camera; with
    /// <see cref="touchOrbit"/> a one-finger drag outside the stick zone and jump pad orbits it
    /// (yaw, clamped pitch), a two-finger pinch zooms, and a gamepad's right stick orbits too
    /// (<see cref="CameraOrbitGesture"/>; provisional numbers in
    /// <see cref="ProvisionalTuning.CameraOrbit"/>). The stick already moves relative to the
    /// camera, so walking follows the orbited view. No auto-recenter yet (movement.json
    /// <c>recenterSec</c> is reserved for it).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class FollowCamera : MonoBehaviour
    {
        [SerializeField]
        TraversalController target;

        [Tooltip("Touch drag / pinch and gamepad right-stick orbit and zoom.")]
        [SerializeField]
        bool touchOrbit = true;

        readonly CameraOrbitGesture _gesture = new CameraOrbitGesture();
        readonly List<OrbitTouch> _touches = new List<OrbitTouch>();
        float _orbitYawDeg;
        float _orbitPitchDeg;
        float _zoom = 1f;

        Camera _camera;
        Vector3 _yawForward;
        float _trackedY;
        float _trackedYVelocity;
        float _distanceA;
        float _distanceVelocity;
        float _fovBonus;
        float _fovVelocity;
        Vector3 _lookAhead;
        Vector3 _lookAheadVelocity;
        bool _initialized;

        public TraversalController Target
        {
            get => target;
            set
            {
                target = value;
                _initialized = false;
            }
        }

        public bool TouchOrbit
        {
            get => touchOrbit;
            set => touchOrbit = value;
        }

        /// <summary>Yaw added to the scene's starting direction (degrees).</summary>
        public float OrbitYawDeg => _orbitYawDeg;

        /// <summary>Pitch added to the default elevation (degrees, after clamping).</summary>
        public float OrbitPitchDeg => _orbitPitchDeg;

        /// <summary>Follow distance multiplier from pinch.</summary>
        public float Zoom => _zoom;

        public CameraOrbitGesture Gesture => _gesture;

        /// <summary>Turns the camera around the character (pitch is clamped in <see cref="LateUpdate"/>).</summary>
        public void Orbit(float yawDeg, float pitchDeg)
        {
            _orbitYawDeg = Mathf.DeltaAngle(0f, _orbitYawDeg + yawDeg);
            _orbitPitchDeg += pitchDeg;
        }

        /// <summary>Multiplies the follow distance (clamped).</summary>
        public void ZoomBy(float factor)
        {
            if (factor > 0f && !float.IsNaN(factor))
                _zoom = Mathf.Clamp(
                    _zoom * factor,
                    ProvisionalTuning.CameraOrbit.MinZoom,
                    ProvisionalTuning.CameraOrbit.MaxZoom
                );
        }

        /// <summary>Elevation angle of the eye above the look-at point for a pitch offset, clamped.</summary>
        public static float ElevationDeg(float heightAboveLookAt, float distance, float pitchDeg) =>
            Mathf.Clamp(
                Mathf.Atan2(heightAboveLookAt, distance) * Mathf.Rad2Deg + pitchDeg,
                ProvisionalTuning.CameraOrbit.MinElevationDeg,
                ProvisionalTuning.CameraOrbit.MaxElevationDeg
            );

        void ReadOrbitInput()
        {
            var screen = Touchscreen.current;
            if (screen != null)
            {
                _touches.Clear();
                foreach (TouchControl t in screen.touches)
                {
                    _touches.Add(
                        new OrbitTouch(
                            t.touchId.ReadValue(),
                            t.startPosition.ReadValue(),
                            t.position.ReadValue(),
                            t.isInProgress
                        )
                    );
                }
                var d = _gesture.Update(
                    _touches,
                    target.Touch.Layout,
                    TouchLayout.PixelsPerPoint(Screen.dpi)
                );
                Orbit(d.YawDeg, d.PitchDeg);
                ZoomBy(d.Zoom);
            }
            var pad = Gamepad.current;
            if (pad != null)
            {
                var r = pad.rightStick.ReadValue();
                if (r.magnitude > ProvisionalTuning.CameraOrbit.GamepadDeadzone)
                    Orbit(
                        r.x * ProvisionalTuning.CameraOrbit.GamepadYawDegPerSec * Time.deltaTime,
                        -r.y * ProvisionalTuning.CameraOrbit.GamepadPitchDegPerSec * Time.deltaTime
                    );
            }
        }

        void Awake()
        {
            _camera = GetComponent<Camera>();
            var f = transform.forward;
            _yawForward = new Vector3(f.x, 0f, f.z);
            if (_yawForward.sqrMagnitude <= 0f)
                _yawForward = Vector3.forward;
            _yawForward.Normalize();
        }

        void LateUpdate()
        {
            if (target == null || target.Motor == null)
                return;
            var motor = target.Motor;
            var scale = motor.Scale;
            var pos = target.transform.position;
            var running = motor.Gait == Gait.Run || motor.Gait == Gait.Sprint;
            var cam = motor.Config.Camera;
            var blend = cam.BlendSec;

            if (!_initialized)
            {
                _trackedY = pos.y;
                _distanceA = cam.FollowA;
                _lookAhead = Vector3.zero;
                _camera.fieldOfView = cam.BaseFovDeg;
                _initialized = true;
            }

            if (touchOrbit)
                ReadOrbitInput();

            var holdY = !motor.Grounded && motor.AirborneSeconds < cam.JumpHoldSec;
            if (!holdY)
                _trackedY = Mathf.SmoothDamp(_trackedY, pos.y, ref _trackedYVelocity, blend);

            var wantDistance = cam.FollowA + (running ? cam.RunPullBackA : 0f);
            _distanceA = Mathf.SmoothDamp(_distanceA, wantDistance, ref _distanceVelocity, blend);
            var wantFov = running ? cam.RunFovDeg : 0f;
            _fovBonus = Mathf.SmoothDamp(_fovBonus, wantFov, ref _fovVelocity, blend);
            _camera.fieldOfView = cam.BaseFovDeg + _fovBonus;

            var travel = motor.Velocity;
            travel.y = 0f;
            var wantAhead =
                travel.sqrMagnitude > 0f
                    ? travel.normalized * scale.ToWorld(cam.LookAheadA)
                    : Vector3.zero;
            _lookAhead = Vector3.SmoothDamp(_lookAhead, wantAhead, ref _lookAheadVelocity, blend);

            var focus = new Vector3(pos.x, _trackedY, pos.z) + _lookAhead;
            var lookAt = focus + Vector3.up * scale.ToWorld(motor.Config.AvatarHeightA * 0.5f);
            // With no orbit this is exactly focus - yawForward * distance + up * height.
            var distance = scale.ToWorld(_distanceA);
            var rise = scale.ToWorld(cam.HeightA - motor.Config.AvatarHeightA * 0.5f);
            var baseElevation = Mathf.Atan2(rise, distance) * Mathf.Rad2Deg;
            var elevation = ElevationDeg(rise, distance, _orbitPitchDeg);
            _orbitPitchDeg = elevation - baseElevation;
            var forward = Quaternion.AngleAxis(_orbitYawDeg, Vector3.up) * _yawForward;
            var radius = Mathf.Sqrt(distance * distance + rise * rise) * _zoom;
            var e = elevation * Mathf.Deg2Rad;
            var eye =
                lookAt - forward * (radius * Mathf.Cos(e)) + Vector3.up * (radius * Mathf.Sin(e));
            transform.position = eye;
            transform.rotation = Quaternion.LookRotation(lookAt - eye, Vector3.up);
        }
    }
}
