namespace GiganticJourneys.Movement
{
    /// <summary>What the traversal query knows this frame, handed to every verb provider.</summary>
    public readonly struct VerbContext
    {
        public readonly bool Grounded;
        public readonly float AirborneSeconds;
        public readonly Gait Gait;

        /// <summary>A jump fired this frame (coyote time and the buffer already applied).</summary>
        public readonly bool JumpFired;

        /// <summary>Gait at take-off or on the ground; selects the jump family.</summary>
        public readonly Gait TakeoffGait;

        /// <summary>The committed jump in flight (null when none) and its planned air time, seconds.</summary>
        public readonly string ActiveJump;
        public readonly float ActiveJumpAirTime;

        public VerbContext(
            bool grounded,
            float airborneSeconds,
            Gait gait,
            bool jumpFired,
            Gait takeoffGait,
            string activeJump = null,
            float activeJumpAirTime = 0f
        )
        {
            ActiveJump = activeJump;
            ActiveJumpAirTime = activeJumpAirTime;
            Grounded = grounded;
            AirborneSeconds = airborneSeconds;
            Gait = gait;
            JumpFired = jumpFired;
            TakeoffGait = takeoffGait;
        }
    }

    /// <summary>A provider's claim on the current frame.</summary>
    public readonly struct VerbProposal
    {
        public readonly string Verb;
        public readonly VerbPriority Priority;

        public VerbProposal(string verb, VerbPriority priority)
        {
            Verb = verb;
            Priority = priority;
        }
    }

    /// <summary>
    /// The seam for adding verbs without touching the core (Bible §2, §3.6, §14; ADR-0004):
    /// locomotion, M1 contact verbs and M3 traversal tools each implement this and register with
    /// the traversal query, which picks the highest-priority proposal.
    /// </summary>
    public interface IVerbProvider
    {
        string Id { get; }

        bool TryPropose(in VerbContext context, MovementConfig config, out VerbProposal proposal);
    }
}
