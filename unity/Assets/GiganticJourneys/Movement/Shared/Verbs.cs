namespace GiganticJourneys.Movement
{
    /// <summary>Locomotion gait chosen from stick deflection (Bible §3.1).</summary>
    public enum Gait
    {
        Idle,
        Walk,
        Jog,
        Run,
        Sprint,
    }

    /// <summary>
    /// Verb identifiers. Strings (not an enum) so verb providers added later — contact verbs in
    /// M1, traversal tools in M3 (AUTH #021) — register new verbs without editing the core.
    /// </summary>
    public static class Verbs
    {
        public const string Idle = "idle";
        public const string Walk = "walk";
        public const string Jog = "jog";
        public const string Run = "run";
        public const string Sprint = "sprint";
        public const string StandingJump = "standing-jump";
        public const string RunningJump = "running-jump";
        public const string SprintJump = "sprint-jump";
        public const string Airborne = "airborne";
        public const string Fall = "fall";
    }

    /// <summary>Resolution order between providers; later members win ties (Bible §3.5 priority).</summary>
    public enum VerbPriority
    {
        Locomotion,
        Contact,
        Tool,
    }
}
