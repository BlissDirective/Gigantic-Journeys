namespace GiganticJourneys.Movement.Animation
{
    /// <summary>
    /// Animation-selection layer seam (Bible §2): given the resolved verb and the predicted
    /// trajectory, pick the pose/clip. M0 has no animation (a capsule), so the controller uses
    /// <see cref="NullAnimationSelector"/>; M1-MOVE-01 decides motion matching vs blend trees.
    /// </summary>
    public interface IAnimationSelector
    {
        void Select(string verb, float speedA);
    }

    /// <summary>The M0 capsule: nothing to animate. Records the last verb for debugging.</summary>
    public sealed class NullAnimationSelector : IAnimationSelector
    {
        public string LastVerb { get; private set; }

        public void Select(string verb, float speedA) => LastVerb = verb;
    }
}
