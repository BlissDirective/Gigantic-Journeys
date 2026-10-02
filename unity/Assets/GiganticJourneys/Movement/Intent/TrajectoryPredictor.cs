using UnityEngine;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// Predicts where the avatar will be over the next <c>intent.trajectorySec</c> seconds
    /// (movement.json, Bible §2 Intent layer). M0: constant ground velocity, or a ballistic arc when airborne;
    /// motion matching (M1-MOVE-01) consumes the same samples.
    /// </summary>
    public static class TrajectoryPredictor
    {
        public static void Predict(
            Vector3 position,
            Vector3 velocity,
            float gravity,
            bool grounded,
            float horizonSec,
            Vector3[] samples
        )
        {
            if (samples == null || samples.Length == 0)
                return;
            var step = horizonSec / samples.Length;
            for (var i = 0; i < samples.Length; i++)
            {
                var t = step * (i + 1);
                var p = position + velocity * t;
                if (!grounded)
                    p.y -= 0.5f * gravity * t * t;
                samples[i] = p;
            }
        }
    }
}
