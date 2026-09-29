using UnityEngine;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// A floating virtual stick: the first touch in its zone sets the origin, dragging deflects it
    /// up to <c>radius</c> pixels (DESIGN_SYSTEM decision 5: floating stick anywhere in the left third).
    /// Screen space, pixels, y up.
    /// </summary>
    public sealed class FloatingStick
    {
        public bool Active { get; private set; }
        public int TouchId { get; private set; } = -1;
        public Vector2 Origin { get; private set; }
        public Vector2 Position { get; private set; }

        /// <summary>Deflection, magnitude 0..1.</summary>
        public Vector2 Value { get; private set; }

        public void Begin(int touchId, Vector2 screenPosition)
        {
            Active = true;
            TouchId = touchId;
            Origin = screenPosition;
            Position = screenPosition;
            Value = Vector2.zero;
        }

        public void Drag(Vector2 screenPosition, float radiusPixels)
        {
            if (!Active || radiusPixels <= 0f)
                return;
            Position = screenPosition;
            Value = Vector2.ClampMagnitude((screenPosition - Origin) / radiusPixels, 1f);
        }

        public void End()
        {
            Active = false;
            TouchId = -1;
            Value = Vector2.zero;
        }
    }

    /// <summary>Where the touch controls sit for a given screen (pixels, y up).</summary>
    public readonly struct TouchLayout
    {
        public readonly Rect StickZone;
        public readonly Vector2 JumpCenter;
        public readonly float JumpRadius;
        public readonly float StickRadius;

        public TouchLayout(Rect safeArea, float pixelsPerPoint)
        {
            StickZone = new Rect(
                safeArea.xMin,
                safeArea.yMin,
                safeArea.width * ProvisionalTuning.Touch.StickZoneWidthFraction,
                safeArea.height
            );
            JumpRadius = ProvisionalTuning.Touch.JumpPadPt * pixelsPerPoint * 0.5f;
            var inset = ProvisionalTuning.Touch.JumpPadInsetPt * pixelsPerPoint;
            JumpCenter = new Vector2(
                safeArea.xMax - inset - JumpRadius,
                safeArea.yMin + inset + JumpRadius
            );
            StickRadius = ProvisionalTuning.Touch.StickRadiusPt * pixelsPerPoint;
        }

        public bool InStickZone(Vector2 p) => StickZone.Contains(p);

        public bool OnJumpPad(Vector2 p) =>
            (p - JumpCenter).sqrMagnitude <= JumpRadius * JumpRadius;

        /// <summary>iOS screen scale from density: round(dpi / 163), clamped 1..3 (1 when unknown).</summary>
        public static float PixelsPerPoint(float dpi)
        {
            if (dpi <= 0f || float.IsNaN(dpi) || float.IsInfinity(dpi))
                return 1f;
            return Mathf.Clamp(
                Mathf.Round(dpi / ProvisionalTuning.Touch.PointsReferenceDpi),
                1f,
                ProvisionalTuning.Touch.MaxPixelsPerPoint
            );
        }
    }
}
