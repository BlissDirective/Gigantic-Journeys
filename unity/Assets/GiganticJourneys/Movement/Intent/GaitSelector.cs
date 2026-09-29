namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// Stick deflection → gait (Bible §3.1): walk &lt; 40 %, jog 40–85 %, run &gt; 85 %, and run
    /// held continuously for 1.5 s becomes sprint. Bands come from <see cref="ProvisionalTuning.Intent"/>.
    /// </summary>
    public sealed class GaitSelector
    {
        float _runHeld;

        public Gait Current { get; private set; }

        public void Reset()
        {
            _runHeld = 0f;
            Current = Gait.Idle;
        }

        /// <summary>
        /// Advances one frame. <paramref name="cap"/> limits the gait (edge balance-walk caps at
        /// walk and crouch at its own speed in M1, Bible §3.1; tests cap at run to time a 5 s run).
        /// </summary>
        public Gait Update(float stickMagnitude, float deltaTime, Gait cap = Gait.Sprint)
        {
            var band = Band(stickMagnitude);
            if (band == Gait.Run)
            {
                _runHeld += deltaTime;
                if (_runHeld >= ProvisionalTuning.Intent.SprintHoldSec)
                    band = Gait.Sprint;
            }
            else
            {
                _runHeld = 0f;
            }
            if (band > cap)
                band = cap;
            Current = band;
            return band;
        }

        /// <summary>The gait band for a deflection, ignoring the sprint hold.</summary>
        public static Gait Band(float stickMagnitude)
        {
            if (stickMagnitude < ProvisionalTuning.Intent.StickDeadzone)
                return Gait.Idle;
            if (stickMagnitude < ProvisionalTuning.Intent.WalkMaxStick)
                return Gait.Walk;
            if (stickMagnitude <= ProvisionalTuning.Intent.JogMaxStick)
                return Gait.Jog;
            return Gait.Run;
        }

        /// <summary>Ground speed for a gait in A/s (movement.json speeds).</summary>
        public static float SpeedA(Gait gait, MovementConfig config)
        {
            switch (gait)
            {
                case Gait.Walk:
                    return config.Speeds.Walk;
                case Gait.Jog:
                    return config.Speeds.Jog;
                case Gait.Run:
                    return config.Speeds.Run;
                case Gait.Sprint:
                    return config.Speeds.Sprint;
                default:
                    return 0f;
            }
        }
    }
}
