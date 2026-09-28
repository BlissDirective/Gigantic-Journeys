namespace GiganticJourneys.DebugTools
{
    /// <summary>
    /// Detects the overlay's three-finger tap from the number of touches in
    /// progress each frame (ticket M0-UNITY-04). A tap fires once when three or
    /// more fingers are down together, provided the first finger landed no more
    /// than <see cref="MaxGatherSeconds"/> earlier and the gesture is not
    /// already a long hold. The detector re-arms when every finger lifts, so a
    /// held gesture toggles only once.
    /// </summary>
    public sealed class ThreeFingerTapDetector
    {
        public const int Fingers = 3;
        public const float MaxGatherSeconds = 0.5f;

        bool _armed = true;
        bool _gathering;
        float _firstDown;

        /// <summary>Feed the current touch count; returns true on the frame the tap fires.</summary>
        public bool Update(int touchesInProgress, float time)
        {
            if (touchesInProgress <= 0)
            {
                _armed = true;
                _gathering = false;
                return false;
            }
            if (!_gathering)
            {
                _gathering = true;
                _firstDown = time;
            }
            if (_armed && touchesInProgress >= Fingers)
            {
                _armed = false;
                return time - _firstDown <= MaxGatherSeconds;
            }
            return false;
        }
    }
}
