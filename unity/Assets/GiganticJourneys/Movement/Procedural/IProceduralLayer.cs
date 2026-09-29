namespace GiganticJourneys.Movement.Procedural
{
    /// <summary>
    /// Procedural layer seam (Bible §2): foot/hand IK, look-at, lean and Tier 0 feedback triggers.
    /// Empty in M0; Animation Rigging work lands in M1.
    /// </summary>
    public interface IProceduralLayer
    {
        void Apply(float deltaTime);
    }

    public sealed class NoProceduralLayer : IProceduralLayer
    {
        public void Apply(float deltaTime) { }
    }
}
