using UnityEngine;

namespace GiganticJourneys.Movement.Controller
{
    /// <summary>
    /// Fixed follow camera for M0 (Bible §8 subset; orbit, collision and per-verb rules are M1):
    /// distance 4A, height 1.6A, look-ahead 0.8A in the travel direction, +0.5A and +4° FOV at
    /// run/sprint, and no vertical follow for the first 0.2 s of a jump. The yaw stays where the
    /// scene placed the camera. Numbers from <see cref="ProvisionalTuning.Camera"/> (pending the
    /// movement.json camera section, DESIGN_SYSTEM decision 5).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public sealed class FollowCamera : MonoBehaviour
    {
        [SerializeField]
        TraversalController target;

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

        void Awake()
        {
            _camera = GetComponent<Camera>();
            var f = transform.forward;
            _yawForward = new Vector3(f.x, 0f, f.z);
            if (_yawForward.sqrMagnitude <= 0f)
                _yawForward = Vector3.forward;
            _yawForward.Normalize();
            _camera.fieldOfView = ProvisionalTuning.Camera.BaseVerticalFovDeg;
        }

        void LateUpdate()
        {
            if (target == null || target.Motor == null)
                return;
            var motor = target.Motor;
            var scale = motor.Scale;
            var pos = target.transform.position;
            var running = motor.Gait == Gait.Run || motor.Gait == Gait.Sprint;
            var blend = ProvisionalTuning.Camera.BlendSec;

            if (!_initialized)
            {
                _trackedY = pos.y;
                _distanceA = ProvisionalTuning.Camera.FollowDistanceA;
                _lookAhead = Vector3.zero;
                _initialized = true;
            }

            var holdY =
                !motor.Grounded
                && motor.AirborneSeconds < ProvisionalTuning.Camera.JumpVerticalHoldSec;
            if (!holdY)
                _trackedY = Mathf.SmoothDamp(_trackedY, pos.y, ref _trackedYVelocity, blend);

            var wantDistance =
                ProvisionalTuning.Camera.FollowDistanceA
                + (running ? ProvisionalTuning.Camera.RunDistanceBonusA : 0f);
            _distanceA = Mathf.SmoothDamp(_distanceA, wantDistance, ref _distanceVelocity, blend);
            var wantFov = running ? ProvisionalTuning.Camera.RunFovBonusDeg : 0f;
            _fovBonus = Mathf.SmoothDamp(_fovBonus, wantFov, ref _fovVelocity, blend);
            _camera.fieldOfView = ProvisionalTuning.Camera.BaseVerticalFovDeg + _fovBonus;

            var travel = motor.Velocity;
            travel.y = 0f;
            var wantAhead =
                travel.sqrMagnitude > 0f
                    ? travel.normalized * scale.ToWorld(ProvisionalTuning.Camera.LookAheadA)
                    : Vector3.zero;
            _lookAhead = Vector3.SmoothDamp(_lookAhead, wantAhead, ref _lookAheadVelocity, blend);

            var focus = new Vector3(pos.x, _trackedY, pos.z) + _lookAhead;
            var eye =
                focus
                - _yawForward * scale.ToWorld(_distanceA)
                + Vector3.up * scale.ToWorld(ProvisionalTuning.Camera.HeightA);
            transform.position = eye;
            var lookAt = focus + Vector3.up * scale.ToWorld(motor.Config.AvatarHeightA * 0.5f);
            transform.rotation = Quaternion.LookRotation(lookAt - eye, Vector3.up);
        }
    }
}
