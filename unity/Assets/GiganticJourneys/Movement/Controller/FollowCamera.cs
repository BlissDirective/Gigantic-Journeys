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
    /// Whatever pulls the eye in does so at once (it never clips through a wall) but the eye
    /// eases back out (<see cref="NextEyeRadius"/>), so turning past an obstacle no longer
    /// snaps the view into the character and out again; and when the eye does end up within
    /// movement.json <c>occluderFadeA</c> of the character (a tight corner), the character's
    /// renderers are hidden instead of filling the screen (build 61 device test).
    /// A splat room can raise the look-at point to a standing height for QA
    /// (<see cref="QaStandingLookAtHeightM"/>) so the eye matches the capture while the
    /// miniature character stays on the floor (build 69 bedroom fragmentation).
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
        float _eyeRadius = -1f;
        float _eyeRadiusVelocity;
        readonly List<Renderer> _hiddenRenderers = new List<Renderer>();

        /// <summary>
        /// When &gt; 0, the look-at point sits this many metres above the character's tracked
        /// floor height (instead of half the avatar), and the default follow rise is zero so the
        /// eye orbits at that standing height. 0 = product miniature POV. Set by the splat room
        /// for bedroom QA only.
        /// </summary>
        public float QaStandingLookAtHeightM { get; set; }

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

        /// <summary>Distance from the look-at point to the eye this frame (world units).</summary>
        public float EyeDistance => Mathf.Max(0f, _eyeRadius);

        /// <summary>The character's renderers are hidden because the eye is too close to it.</summary>
        public bool TargetHidden => _hiddenRenderers.Count > 0;

        /// <summary>
        /// The eye distance for this frame: straight to <paramref name="allowed"/> when that is
        /// closer (an obstacle or the box must never be clipped through), otherwise eased back
        /// out over about <paramref name="springBackSec"/>. A negative <paramref name="current"/>
        /// (first frame) jumps to <paramref name="allowed"/>.
        /// </summary>
        public static float NextEyeRadius(
            float current,
            float allowed,
            ref float velocity,
            float springBackSec,
            float deltaTime
        )
        {
            if (current < 0f || allowed <= current || springBackSec <= 0f)
            {
                velocity = 0f;
                return allowed;
            }
            return Mathf.Min(
                allowed,
                Mathf.SmoothDamp(
                    current,
                    allowed,
                    ref velocity,
                    springBackSec,
                    float.PositiveInfinity,
                    deltaTime
                )
            );
        }

        /// <summary>
        /// Unit direction from the look-at point to the eye for an orbit <paramref name="elevationDeg"/>.
        /// Below the look-at point (looking up) the eye would sink into the ground, and pulling it
        /// in along the ray put it inside the character (build 61: 2 cm away at -60 degrees). It
        /// stays at <paramref name="radius"/> instead, as low as the ground allows
        /// (<paramref name="dropToFloor"/> under the look-at point), and only the view tilts up.
        /// </summary>
        public static Vector3 EyeDirection(
            Vector3 forward,
            float elevationDeg,
            float radius,
            float dropToFloor
        )
        {
            var e = elevationDeg * Mathf.Deg2Rad;
            if (e < 0f && radius > 0f)
                e = Mathf.Max(e, -Mathf.Asin(Mathf.Clamp01(dropToFloor / radius)));
            return -forward * Mathf.Cos(e) + Vector3.up * Mathf.Sin(e);
        }

        /// <summary>Whether the character should be hidden with the eye this close to its look-at point.</summary>
        public static bool HidesTarget(float eyeDistance, float hideWithin) =>
            eyeDistance < hideWithin;

        /// <summary>
        /// World Y of the look-at point and the follow rise above it. With a QA standing height
        /// the look-at is that many metres above the tracked floor and the rise is zero (eye at
        /// standing height when pitch is 0); otherwise the product miniature POV (half avatar +
        /// movement.json camera height).
        /// </summary>
        public static void LookAtHeightAndRise(
            float trackedFloorY,
            float halfAvatarWorld,
            float cameraRiseWorld,
            float qaStandingLookAtHeightM,
            out float lookAtY,
            out float rise
        )
        {
            if (qaStandingLookAtHeightM > 0f)
            {
                lookAtY = trackedFloorY + qaStandingLookAtHeightM;
                rise = 0f;
                return;
            }
            lookAtY = trackedFloorY + halfAvatarWorld;
            rise = cameraRiseWorld;
        }

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
            // With no orbit this is exactly focus - yawForward * distance + up * height.
            var distance = scale.ToWorld(_distanceA);
            LookAtHeightAndRise(
                focus.y,
                scale.ToWorld(motor.Config.AvatarHeightA * 0.5f),
                scale.ToWorld(cam.HeightA - motor.Config.AvatarHeightA * 0.5f),
                QaStandingLookAtHeightM,
                out var lookAtY,
                out var rise
            );
            var lookAt = new Vector3(focus.x, lookAtY, focus.z);
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
            var view = -(-forward * Mathf.Cos(e) + Vector3.up * Mathf.Sin(e));
            var floorY = _trackedY + ProvisionalTuning.CameraOrbit.EyeAboveGroundM;
            var toEye = EyeDirection(forward, elevation, radius, Mathf.Max(0f, lookAt.y - floorY));
            _eyeRadius = NextEyeRadius(
                _eyeRadius,
                PulledInRadius(lookAt, toEye, radius, floorY),
                ref _eyeRadiusVelocity,
                ProvisionalTuning.CameraOrbit.SpringBackSec,
                Time.deltaTime
            );
            transform.position = lookAt + toEye * _eyeRadius;
            // The view keeps the asked-for elevation even where the eye could not go there.
            transform.rotation = Quaternion.LookRotation(view, Vector3.up);
            SetTargetHidden(HidesTarget(_eyeRadius, scale.ToWorld(cam.OccluderFadeA)));
        }

        void OnDisable() => SetTargetHidden(false);

        void SetTargetHidden(bool hide)
        {
            if (hide == TargetHidden)
                return;
            if (!hide)
            {
                foreach (var r in _hiddenRenderers)
                {
                    if (r != null)
                        r.enabled = true;
                }
                _hiddenRenderers.Clear();
                return;
            }
            if (target == null)
                return;
            foreach (var r in target.GetComponentsInChildren<Renderer>())
            {
                if (!r.enabled)
                    continue;
                r.enabled = false;
                _hiddenRenderers.Add(r);
            }
        }

        // The eye distance after the camera box, the ground and (optionally) colliders on the way.
        float PulledInRadius(Vector3 lookAt, Vector3 toEye, float radius, float floorY)
        {
            if (_hasBounds)
            {
                // A miniature character's look-at point can sit below the box floor; the box then
                // still bounds x, z and the top (the ground clamp below handles low eyes).
                // Its floor then drops to the eye's own ground limit (it used to stop 2 cm under
                // the look-at point, which pulled a looking-up eye in to a third of its distance).
                var box = _bounds;
                if (lookAt.y <= box.min.y)
                    box.SetMinMax(
                        new Vector3(
                            box.min.x,
                            Mathf.Min(
                                lookAt.y - ProvisionalTuning.CameraOrbit.EyeAboveGroundM,
                                floorY - ProvisionalTuning.CameraOrbit.BoxFloorBelowGroundM
                            ),
                            box.min.z
                        ),
                        box.max
                    );
                radius = Mathf.Min(radius, ExitDistance(box, lookAt, toEye));
            }
            // Looking up from below: the eye never drops under the ground the character stands
            // on (the collision sphere is larger than a miniature character's half height, so
            // the sphere cast alone starts inside the floor and misses it).
            if (toEye.y < 0f)
                radius = Mathf.Min(radius, Mathf.Max(0f, lookAt.y - floorY) / -toEye.y);
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
