using System.Collections.Generic;
using UnityEngine;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>One touch as the orbit gesture sees it (screen pixels, y up).</summary>
    public readonly struct OrbitTouch
    {
        public readonly int Id;
        public readonly Vector2 Start;
        public readonly Vector2 Position;
        public readonly bool InProgress;

        public OrbitTouch(int id, Vector2 start, Vector2 position, bool inProgress)
        {
            Id = id;
            Start = start;
            Position = position;
            InProgress = inProgress;
        }
    }

    /// <summary>Camera input produced by <see cref="CameraOrbitGesture"/> for one frame.</summary>
    public readonly struct OrbitDelta
    {
        public readonly float YawDeg;
        public readonly float PitchDeg;

        /// <summary>Multiplier for the follow distance (1 = unchanged; below 1 zooms in).</summary>
        public readonly float Zoom;

        public OrbitDelta(float yawDeg, float pitchDeg, float zoom)
        {
            YawDeg = yawDeg;
            PitchDeg = pitchDeg;
            Zoom = zoom;
        }

        public static readonly OrbitDelta None = new OrbitDelta(0f, 0f, 1f);
    }

    /// <summary>
    /// Touch camera orbit (Bible §8, M1): a one-finger drag that starts outside the stick zone
    /// and off the jump pad turns the follow camera (yaw and pitch), and two such fingers pinch
    /// to zoom. It never takes a stick or jump touch, ignores taps (a drag must leave a small
    /// deadzone first, so overlay buttons don't turn the view), and steps aside for the debug
    /// overlay's three-finger tap: every touch that was down while three or more were down is
    /// ignored until it lifts. Pure logic; <c>FollowCamera</c> feeds it the touchscreen.
    /// </summary>
    public sealed class CameraOrbitGesture
    {
        readonly Dictionary<int, Vector2> _last = new Dictionary<int, Vector2>();
        readonly HashSet<int> _orbiting = new HashSet<int>();
        readonly HashSet<int> _blocked = new HashSet<int>();
        readonly List<OrbitTouch> _candidates = new List<OrbitTouch>();
        readonly HashSet<int> _seen = new HashSet<int>();

        /// <summary>True while a finger is turning the camera.</summary>
        public bool Orbiting => _orbiting.Count > 0;

        public OrbitDelta Update(
            IReadOnlyList<OrbitTouch> touches,
            TouchLayout layout,
            float pixelsPerPoint
        )
        {
            var ppp = pixelsPerPoint > 0f ? pixelsPerPoint : 1f;
            var down = 0;
            foreach (var t in touches)
            {
                if (t.InProgress)
                    down++;
            }
            _seen.Clear();
            foreach (var t in touches)
            {
                if (t.InProgress)
                    _seen.Add(t.Id);
            }
            _blocked.RemoveWhere(id => !_seen.Contains(id));
            if (down >= ProvisionalTuning.CameraOrbit.OverlayTapFingers)
            {
                foreach (var id in _seen)
                    _blocked.Add(id);
            }

            _candidates.Clear();
            foreach (var t in touches)
            {
                if (!t.InProgress || _blocked.Contains(t.Id))
                    continue;
                if (layout.InStickZone(t.Start) || layout.OnJumpPad(t.Start))
                    continue;
                _candidates.Add(t);
            }

            var delta = OrbitDelta.None;
            if (_candidates.Count == 1)
            {
                var t = _candidates[0];
                if (!_orbiting.Contains(t.Id))
                {
                    var moved = (t.Position - t.Start).magnitude / ppp;
                    if (moved >= ProvisionalTuning.CameraOrbit.DeadzonePt)
                    {
                        _orbiting.Add(t.Id);
                        _last[t.Id] = t.Position;
                    }
                }
                else if (_last.TryGetValue(t.Id, out var prev))
                {
                    var d = (t.Position - prev) / ppp;
                    delta = new OrbitDelta(
                        d.x * ProvisionalTuning.CameraOrbit.YawDegPerPt,
                        -d.y * ProvisionalTuning.CameraOrbit.PitchDegPerPt,
                        1f
                    );
                }
            }
            else if (_candidates.Count == 2)
            {
                var a = _candidates[0];
                var b = _candidates[1];
                if (_last.TryGetValue(a.Id, out var pa) && _last.TryGetValue(b.Id, out var pb))
                {
                    var before = (pa - pb).magnitude;
                    var now = (a.Position - b.Position).magnitude;
                    if (before > 1f && now > 1f)
                        delta = new OrbitDelta(0f, 0f, before / now);
                }
                _orbiting.Add(a.Id);
                _orbiting.Add(b.Id);
            }

            _orbiting.RemoveWhere(id => !Has(_candidates, id));
            var stale = new List<int>();
            foreach (var id in _last.Keys)
            {
                if (!Has(_candidates, id))
                    stale.Add(id);
            }
            foreach (var id in stale)
                _last.Remove(id);
            foreach (var t in _candidates)
            {
                if (_orbiting.Contains(t.Id))
                    _last[t.Id] = t.Position;
            }
            return delta;
        }

        public void Reset()
        {
            _last.Clear();
            _orbiting.Clear();
            _blocked.Clear();
        }

        static bool Has(List<OrbitTouch> list, int id)
        {
            foreach (var t in list)
            {
                if (t.Id == id)
                    return true;
            }
            return false;
        }
    }
}
