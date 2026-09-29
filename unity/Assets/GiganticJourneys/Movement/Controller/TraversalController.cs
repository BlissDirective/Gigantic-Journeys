using System;
using GiganticJourneys.Movement.Animation;
using GiganticJourneys.Movement.Intent;
using GiganticJourneys.Movement.Procedural;
using GiganticJourneys.Movement.Warping;
using UnityEngine;

namespace GiganticJourneys.Movement.Controller
{
    /// <summary>
    /// Composition root of the five movement layers for the M0 capsule (Bible §2, ticket
    /// M0-UNITY-03): intent (touch + gamepad, merged) → traversal query (verb) → animation
    /// selection / warping / procedural (empty seams in M0) → a CharacterController. Every
    /// movement number comes from movement.json via <see cref="MovementConfigLoader"/>; the capsule
    /// is sized in A and converted to world units with <see cref="MovementScale"/>.
    /// </summary>
    [RequireComponent(typeof(CharacterController))]
    [DisallowMultipleComponent]
    public sealed class TraversalController : MonoBehaviour
    {
        [Tooltip("The character's real-world height in meters (roster data; Bible §1 default).")]
        [SerializeField]
        float avatarRealHeightMeters = ProvisionalTuning.Body.DefaultRealHeightMeters;

        [Tooltip("Environment multiplier: 12 = 1:12 (from the environment spec in M1).")]
        [SerializeField]
        float environmentScale = ProvisionalTuning.Environment.DefaultScale;

        [Tooltip("Assist mode: longer coyote time and a jump bonus (movement.json assist).")]
        [SerializeField]
        bool assist;

        [Tooltip("Orients the stick; defaults to Camera.main.")]
        [SerializeField]
        Transform cameraTransform;

        CharacterController _body;
        GamepadIntentSource _gamepad;
        readonly IntentAggregator _intent = new IntentAggregator();
        readonly IAnimationSelector _animation = new NullAnimationSelector();
        readonly IMotionWarper _warper = new NoMotionWarper();
        readonly IProceduralLayer _procedural = new NoProceduralLayer();

        public LocomotionMotor Motor { get; private set; }
        public MovementConfig Config => Motor?.Config;
        public MovementScale Scale => Motor.Scale;
        public TouchIntentSource Touch { get; } = new TouchIntentSource();
        public IntentAggregator IntentSources => _intent;

        /// <summary>When set, replaces every device (scripted tests, replays).</summary>
        public IIntentSource IntentOverride { get; set; }

        public IntentFrame LastIntent { get; private set; }
        public CharacterController Body => _body;

        public Transform CameraTransform
        {
            get => cameraTransform;
            set => cameraTransform = value;
        }

        void Awake()
        {
            _body = GetComponent<CharacterController>();
            MovementConfig config;
            try
            {
                config = MovementConfigLoader.Current;
            }
            catch (MovementConfigException e)
            {
                Debug.LogError($"[GJ-MOVEMENT] controller disabled: {e.Message}", this);
                enabled = false;
                return;
            }
            Configure(config, avatarRealHeightMeters, environmentScale);
            _gamepad = new GamepadIntentSource();
            _intent.Add(_gamepad);
            _intent.Add(Touch);
        }

        /// <summary>(Re)builds the motor and sizes the capsule from the config.</summary>
        public void Configure(MovementConfig config, float realHeightMeters, float envScale)
        {
            if (config == null)
                throw new ArgumentNullException(nameof(config));
            avatarRealHeightMeters = realHeightMeters;
            environmentScale = envScale;
            var scale = MovementScale.Create(config, realHeightMeters, envScale);
            Motor = new LocomotionMotor(config, scale, assist);
            if (_body == null)
                _body = GetComponent<CharacterController>();
            var height = scale.ToWorld(config.AvatarHeightA);
            var radius = scale.ToWorld(ProvisionalTuning.Body.CapsuleRadiusA);
            _body.enabled = false;
            _body.height = height;
            _body.radius = radius;
            _body.center = Vector3.up * (height * 0.5f);
            _body.stepOffset = scale.ToWorld(config.Verticals.StepUp);
            _body.slopeLimit = config.Slopes.RunMaxDeg;
            _body.skinWidth = radius * ProvisionalTuning.Body.SkinWidthOfRadius;
            _body.minMoveDistance = 0f;
            _body.enabled = true;
        }

        void OnDestroy()
        {
            _gamepad?.Dispose();
            _gamepad = null;
        }

        void Update() => Tick(Time.deltaTime);

        /// <summary>One controller frame (public so tests can drive fixed steps).</summary>
        public void Tick(float deltaTime)
        {
            if (Motor == null || deltaTime <= 0f)
                return;
            var frame = IntentOverride != null ? IntentOverride.Read() : _intent.Read();
            LastIntent = frame;
            var cam =
                cameraTransform != null ? cameraTransform
                : Camera.main != null ? Camera.main.transform
                : null;
            var forward = cam != null ? cam.forward : Vector3.forward;

            var displacementA = Motor.Step(frame, forward, deltaTime);
            _body.Move(displacementA * Motor.Scale.WorldUnitsPerA);
            Motor.AfterMove(_body.isGrounded);

            var facing = Motor.Facing;
            if (facing.sqrMagnitude > 0f)
                transform.rotation = Quaternion.LookRotation(facing, Vector3.up);

            var horizontal = Motor.Velocity;
            horizontal.y = 0f;
            _animation.Select(Motor.Verb, horizontal.magnitude);
            if (!_warper.HasActiveWarp)
                _procedural.Apply(deltaTime);
        }

        /// <summary>Teleports the capsule and resets the motor.</summary>
        public void Teleport(Vector3 position)
        {
            _body.enabled = false;
            transform.position = position;
            _body.enabled = true;
            Motor?.Reset();
        }
    }
}
