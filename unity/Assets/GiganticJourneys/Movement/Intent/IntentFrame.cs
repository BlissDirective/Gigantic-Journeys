using UnityEngine;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>One frame of player intent, device-independent (Bible §2 Intent layer).</summary>
    public readonly struct IntentFrame
    {
        /// <summary>Stick vector in camera space: x = right, y = forward; magnitude 0..1.</summary>
        public readonly Vector2 Move;

        /// <summary>Jump went down this frame.</summary>
        public readonly bool JumpPressed;

        /// <summary>Jump is held.</summary>
        public readonly bool JumpHeld;

        public IntentFrame(Vector2 move, bool jumpPressed, bool jumpHeld)
        {
            Move = Vector2.ClampMagnitude(move, 1f);
            JumpPressed = jumpPressed;
            JumpHeld = jumpHeld;
        }

        public float Magnitude => Move.magnitude;

        public static readonly IntentFrame None = default;
    }

    /// <summary>A device (gamepad, touch, keyboard, a test script) that produces intent.</summary>
    public interface IIntentSource
    {
        /// <summary>Reads this frame's intent. Called once per frame.</summary>
        IntentFrame Read();
    }

    /// <summary>
    /// Merges every source into one frame (M0-UNITY-03 AT-5: touch and gamepad drive the same
    /// intent layer): the strongest stick wins, and a jump from any source counts.
    /// </summary>
    public sealed class IntentAggregator : IIntentSource
    {
        readonly System.Collections.Generic.List<IIntentSource> _sources =
            new System.Collections.Generic.List<IIntentSource>();

        public int Count => _sources.Count;

        public void Add(IIntentSource source)
        {
            if (source != null && !_sources.Contains(source))
                _sources.Add(source);
        }

        public void Remove(IIntentSource source) => _sources.Remove(source);

        public IntentFrame Read() => Combine(_sources);

        public static IntentFrame Combine(
            System.Collections.Generic.IEnumerable<IIntentSource> sources
        )
        {
            var move = Vector2.zero;
            var pressed = false;
            var held = false;
            foreach (var s in sources)
            {
                var f = s.Read();
                if (f.Move.sqrMagnitude > move.sqrMagnitude)
                    move = f.Move;
                pressed |= f.JumpPressed;
                held |= f.JumpHeld;
            }
            return new IntentFrame(move, pressed, held);
        }
    }
}
