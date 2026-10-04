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
    /// A scene can narrow the orbit (<see cref="Limits"/>: elevation, zoom and a world view-yaw
    /// window), keep the eye inside a box (<see cref="SetCameraBounds"/>) and, with
    /// <see cref="cameraCollision"/>, pull the eye in front of colliders on the ray from the
    /// look-at point. The splat room sets all three from the training camera coverage so the
    /// view stays where the capture looked (M1-UNITY-01).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class FollowCamera : MonoBehaviour
    {
        [SerializeField]
        TraversalController target;

        [Tooltip("Touch drag / pinch and gamepad right-stick orbit and zoom.")]
        [SerializeField]
        bool touchOrbit = true;

        [Tooltip("Pull the eye in front of colliders between the look-at point and the eye.")]
        [SerializeField]
        bool cameraCollision;

        [SerializeField]
        LayerMask collisionMask = Physics.DefaultRaycastLayers;

        /// <summary>Orbit limits; elevation in degrees above the look-at point, zoom as a follow-distance multiple.</summary>
        public struct OrbitLimits
        {
            public float MinElevationDeg;
            public float MaxElevationDeg;
            public float MinZoom;
            public float MaxZoom;

            /// <summary>World yaw (degrees, 0 = +Z) the view may turn around.</summary>
            public float YawCenterDeg;

            /// <summary>How far the view may turn from <see cref="YawCenterDeg"/> either way (180 = free).</summary>
            public float YawHalfRangeDeg;

            public static OrbitLimits Default =>
                new OrbitLimits
                {
                    MinElevationDeg = ProvisionalTuning.CameraOrbit.MinElevationDeg,
                    MaxElevationDeg = ProvisionalTuning.CameraOrbit.MaxElevationDeg,
                    MinZoom = ProvisionalTuning.CameraOrbit.MinZoom,
                    MaxZoom = ProvisionalTuning.CameraOrbit.MaxZoom,
                    YawCenterDeg = 0f,
                    YawHalfRangeDeg = ProvisionalTuning.CameraOrbit.FreeYawHalfRangeDeg,
                };
        }

        OrbitLimits _limits = OrbitLimits.Default;
        bool _hasBounds;
        Bounds _bounds;

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

        public OrbitLimits Limits
        {
            get => _limits;
            set
            {
                _limits = value;
                _zoom = Mathf.Clamp(_zoom, value.MinZoom, value.MaxZoom);
            }
        }

        public bool CameraCollision
        {
            get => cameraCollision;
            set => cameraCollision = value;
        }

        /// <summary>Keeps the eye inside <paramref name="bounds"/> (pulled in along the look-at ray).</summary>
        public void SetCameraBounds(Bounds bounds)
        {
            _bounds = bounds;
            _hasBounds = true;
        }

        public void ClearCameraBounds() => _hasBounds = false;

        public bool HasCameraBounds => _hasBounds;
        public Bounds CameraBounds => _bounds;

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
                _zoom = Mathf.Clamp(_zoom * factor, _limits.MinZoom, _limits.MaxZoom);
        }

        /// <summary>Elevation angle of the eye above the look-at point for a pitch offset, clamped.</summary>
        public static float ElevationDeg(float heightAboveLookAt, float distance, float pitchDeg) =>
            ElevationDeg(heightAboveLookAt, distance, pitchDeg, OrbitLimits.Default);

        /// <summary>As <see cref="ElevationDeg(float, float, float)"/> with explicit limits.</summary>
        public static float ElevationDeg(
            float heightAboveLookAt,
            float distance,
            float pitchDeg,
            OrbitLimits limits
        ) =>
            Mathf.Clamp(
                Mathf.Atan2(heightAboveLookAt, distance) * Mathf.Rad2Deg + pitchDeg,
                limits.MinElevationDeg,
                limits.MaxElevationDeg
            );

        /// <summary>World yaw (degrees, 0 = +Z) clamped into the limits' view window.</summary>
        public static float ClampViewYaw(float worldYawDeg, OrbitLimits limits)
        {
            if (limits.YawHalfRangeDeg >= ProvisionalTuning.CameraOrbit.FreeYawHalfRangeDeg)
                return worldYawDeg;
            var d = Mathf.DeltaAngle(limits.YawCenterDeg, worldYawDeg);
            return limits.YawCenterDeg
                + Mathf.Clamp(d, -limits.YawHalfRangeDeg, limits.YawHalfRangeDeg);
        }

        /// <summary>
        /// Distance along the unit <paramref name="dir"/> from <paramref name="origin"/> to where the
        /// ray leaves <paramref name="box"/>; +infinity when the origin is outside (nothing to keep in).
        /// </summary>
        public static float ExitDistance(Bounds box, Vector3 origin, Vector3 dir)
        {
            if (!box.Contains(origin))
                return float.PositiveInfinity;
            return Mathf.Min(
                AxisExit(box.min.x, box.max.x, origin.x, dir.x),
                Mathf.Min(
                    AxisExit(box.min.y, box.max.y, origin.y, dir.y),
                    AxisExit(box.min.z, box.max.z, origin.z, dir.z)
                )
            );
        }

        static float AxisExit(float lo, float hi, float o, float d) =>
            d > 0f ? (hi - o) / d
            : d < 0f ? (lo - o) / d
            : float.PositiveInfinity;

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
            var elevation = ElevationDeg(rise, distance, _orbitPitchDeg, _limits);
            _orbitPitchDeg = elevation - baseElevation;
            var forward = Quaternion.AngleAxis(_orbitYawDeg, Vector3.up) * _yawForward;
            var worldYaw = Mathf.Atan2(forward.x, forward.z) * Mathf.Rad2Deg;
            var clampedYaw = ClampViewYaw(worldYaw, _limits);
            if (!Mathf.Approximately(clampedYaw, worldYaw))
            {
                _orbitYawDeg = Mathf.DeltaAngle(0f, _orbitYawDeg + (clampedYaw - worldYaw));
                forward = Quaternion.AngleAxis(_orbitYawDeg, Vector3.up) * _yawForward;
            }
            var radius = Mathf.Sqrt(distance * distance + rise * rise) * _zoom;
            var e = elevation * Mathf.Deg2Rad;
            var toEye = -forward * Mathf.Cos(e) + Vector3.up * Mathf.Sin(e);
            transform.position = lookAt + toEye * PulledInRadius(lookAt, toEye, radius);
            transform.rotation = Quaternion.LookRotation(-toEye, Vector3.up);
        }

        // The eye distance after the camera box and (optionally) colliders on the way.
        float PulledInRadius(Vector3 lookAt, Vector3 toEye, float radius)
        {
            if (_hasBounds)
                radius = Mathf.Min(radius, ExitDistance(_bounds, lookAt, toEye));
            if (
                cameraCollision
                && Physics.SphereCast(
                    lookAt,
                    ProvisionalTuning.CameraOrbit.CollisionRadiusM,
                    toEye,
                    out var hit,
                    radius,
                    collisionMask,
                    QueryTriggerInteraction.Ignore
                )
            )
                radius = Mathf.Min(radius, hit.distance);
            return radius;
        }
    }
}
