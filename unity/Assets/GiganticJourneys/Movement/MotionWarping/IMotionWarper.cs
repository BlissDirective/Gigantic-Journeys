namespace GiganticJourneys.Movement.Warping
{
    /// <summary>
    /// Motion-warping layer seam (Bible §2): stretches contact clips so hands and feet land on the
    /// real edge. Empty in M0 (no contact verbs); M1 contact verbs implement it (ADR-0004).
    /// </summary>
    public interface IMotionWarper
    {
        bool HasActiveWarp { get; }
    }

    public sealed class NoMotionWarper : IMotionWarper
    {
        public bool HasActiveWarp => false;
    }
}
