namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// Coyote time and jump buffering (Bible §3.3): a jump pressed within <c>jump.coyoteMs</c> of
    /// walking off an edge still fires, and a jump pressed within <c>jump.bufferMs</c> before
    /// landing fires on landing. Assist mode uses <c>assist.coyoteMs</c>. Pure and clock-driven so
    /// it is testable frame by frame (M0-UNITY-03 AT-4).
    /// </summary>
    public sealed class JumpTiming
    {
        const float MsPerSecond = 1000f;

        readonly float _coyoteSec;
        readonly float _bufferSec;

        float _lastGroundedTime = float.NegativeInfinity;
        float _pressTime = float.NegativeInfinity;
        bool _jumpedSinceGrounded;

        public JumpTiming(MovementConfig config, bool assist = false)
        {
            _coyoteSec = (assist ? config.Assist.CoyoteMs : config.Jump.CoyoteMs) / MsPerSecond;
            _bufferSec = config.Jump.BufferMs / MsPerSecond;
        }

        public float CoyoteSeconds => _coyoteSec;
        public float BufferSeconds => _bufferSec;

        /// <summary>
        /// Advances one frame. <paramref name="grounded"/> is the ground state at the start of the
        /// frame. Returns true when the jump fires this frame (the caller launches it).
        /// </summary>
        public bool Tick(float now, bool grounded, bool jumpPressed)
        {
            if (grounded)
            {
                _lastGroundedTime = now;
                _jumpedSinceGrounded = false;
            }
            if (jumpPressed)
                _pressTime = now;

            var buffered = now - _pressTime <= _bufferSec;
            var canJump =
                grounded || (!_jumpedSinceGrounded && now - _lastGroundedTime <= _coyoteSec);
            if (!buffered || !canJump)
                return false;

            _pressTime = float.NegativeInfinity;
            _jumpedSinceGrounded = true;
            return true;
        }

        /// <summary>Forget any pending press and ground history (respawn, teleport).</summary>
        public void Reset()
        {
            _lastGroundedTime = float.NegativeInfinity;
            _pressTime = float.NegativeInfinity;
            _jumpedSinceGrounded = false;
        }
    }
}
