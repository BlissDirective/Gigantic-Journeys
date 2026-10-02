using GiganticJourneys.Movement.Intent;
using GiganticJourneys.Movement.Query;
using UnityEngine;

namespace GiganticJourneys.Movement.Controller
{
    /// <summary>
    /// The M0 capsule's movement model, in A units and free of Unity physics so it can be stepped
    /// in EditMode tests (M0-UNITY-03 AT-3/AT-4). Ground speed is the gait's movement.json speed
    /// (no acceleration curve until motion matching supplies one, M1-MOVE-01); jumps are committed
    /// ballistic arcs solved from jump.* heights and distances under Bible §1 gravity. The caller
    /// applies <see cref="Step"/>'s displacement to a collider and reports the ground back via
    /// <see cref="AfterMove"/>.
    /// </summary>
    public sealed class LocomotionMotor
    {
        readonly GaitSelector _gait;
        readonly JumpTiming _jump;
        readonly VerbRegistry _verbs = new VerbRegistry();
        readonly bool _assist;
        float _time;
        Vector3 _velocity;
        string _activeJump;
        float _activeJumpAirTime;

        public LocomotionMotor(MovementConfig config, MovementScale scale, bool assist = false)
        {
            Config = config;
            Scale = scale;
            _assist = assist;
            _gait = new GaitSelector(config.Intent);
            _jump = new JumpTiming(config, assist);
            _verbs.Register(new LocomotionVerbProvider());
            Grounded = true;
            Facing = Vector3.forward;
            Verb = Verbs.Idle;
        }

        public MovementConfig Config { get; }
        public MovementScale Scale { get; }
        public VerbRegistry Registry => _verbs;
        public JumpTiming JumpTiming => _jump;

        /// <summary>Velocity in A/s (world axes).</summary>
        public Vector3 Velocity => _velocity;
        public bool Grounded { get; private set; }
        public float AirborneSeconds { get; private set; }
        public Gait Gait => _gait.Current;
        public Gait TakeoffGait { get; private set; }
        public string Verb { get; private set; }

        /// <summary>The verb of the last jump launched (standing, running, sprint).</summary>
        public string LastJumpVerb { get; private set; }
        public Vector3 Facing { get; private set; }

        /// <summary>Highest gait allowed (Bible §3.1 caps: balance-walk → walk; M1 sets it per surface).</summary>
        public Gait MaxGait { get; set; } = Gait.Sprint;

        /// <summary>
        /// Advances one frame. <paramref name="cameraForward"/> orients the stick (its y is ignored).
        /// Returns the displacement in A for the frame.
        /// </summary>
        public Vector3 Step(IntentFrame intent, Vector3 cameraForward, float deltaTime)
        {
            _time += deltaTime;
            var gait = _gait.Update(intent.Magnitude, deltaTime, MaxGait);
            var moveDir = WorldDirection(intent.Move, cameraForward);
            var hasMove = gait != Gait.Idle && moveDir.sqrMagnitude > 0f;

            if (Grounded)
            {
                AirborneSeconds = 0f;
                TakeoffGait = gait;
            }
            else
            {
                AirborneSeconds += deltaTime;
            }

            var fired = _jump.Tick(_time, Grounded, intent.JumpPressed);
            if (Grounded && !fired)
                _activeJump = null;
            var g = Scale.GravityA;
            var arc = default(JumpBallistics);
            if (fired)
            {
                LastJumpVerb = LocomotionVerbProvider.JumpVerb(TakeoffGait);
                LocomotionVerbProvider.JumpShape(
                    LastJumpVerb,
                    Config,
                    out var height,
                    out var distance
                );
                if (_assist)
                    height *= 1f + Config.Assist.JumpBonus;
                arc = JumpBallistics.Solve(height, hasMove ? distance : 0f, g);
                _activeJump = LastJumpVerb;
                _activeJumpAirTime = arc.AirTime;
            }
            var context = new VerbContext(
                Grounded,
                AirborneSeconds,
                gait,
                fired,
                TakeoffGait,
                _activeJump,
                _activeJumpAirTime
            );
            Verb = _verbs.Resolve(context, Config);

            if (fired)
            {
                var dir = hasMove ? moveDir : Vector3.zero;
                _velocity = dir * arc.HorizontalSpeed + Vector3.up * arc.VerticalSpeed;
                if (hasMove)
                    Facing = moveDir;
                Grounded = false;
            }
            else if (Grounded)
            {
                var speed = GaitSelector.SpeedA(gait, Config);
                _velocity = hasMove ? moveDir * speed : Vector3.zero;
                if (hasMove)
                    Facing = moveDir;
                // Press into the ground so the collider reports contact every frame.
                _velocity.y = -g * deltaTime;
            }

            if (Grounded)
                return _velocity * deltaTime;

            // Airborne: exact constant-gravity step, no air control (Bible §3.3 committed arcs).
            var displacement =
                _velocity * deltaTime + Vector3.down * (0.5f * g * deltaTime * deltaTime);
            _velocity.y -= g * deltaTime;
            return displacement;
        }

        /// <summary>Reports the collider's ground contact after the move.</summary>
        public void AfterMove(bool grounded)
        {
            if (grounded && !Grounded && _velocity.y > 0f)
                return; // still rising off the ground on the take-off frame
            Grounded = grounded;
            if (grounded && _velocity.y < 0f)
                _velocity.y = 0f;
        }

        /// <summary>Respawn: stop, grounded, forget jump history.</summary>
        public void Reset()
        {
            _velocity = Vector3.zero;
            Grounded = true;
            AirborneSeconds = 0f;
            _gait.Reset();
            _jump.Reset();
            _activeJump = null;
            Verb = Verbs.Idle;
        }

        public static Vector3 WorldDirection(Vector2 stick, Vector3 cameraForward)
        {
            if (stick.sqrMagnitude <= 0f)
                return Vector3.zero;
            var forward = new Vector3(cameraForward.x, 0f, cameraForward.z);
            if (forward.sqrMagnitude <= 0f)
                forward = Vector3.forward;
            forward.Normalize();
            var right = new Vector3(forward.z, 0f, -forward.x);
            return (right * stick.x + forward * stick.y).normalized;
        }
    }
}
