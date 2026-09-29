using UnityEngine;

namespace GiganticJourneys.Movement
{
    /// <summary>
    /// A tagged animation clip for one verb (Bible §2, §11). Stub for M0-UNITY-03: the capsule
    /// has no animation; M1-MOVE-01 fills the clip database and M1 contact verbs add warp targets.
    /// </summary>
    [CreateAssetMenu(menuName = "Gigantic Journeys/Movement/Move Clip", fileName = "MoveClip")]
    public sealed class MoveClip : ScriptableObject
    {
        [Tooltip("Verb id from GiganticJourneys.Movement.Verbs (or a provider's own id).")]
        public string verb;

        public AnimationClip clip;

        [Tooltip(
            "Contact clip stretched by the motion-warping layer so hands/feet land on the real edge."
        )]
        public bool warped;
    }
}
