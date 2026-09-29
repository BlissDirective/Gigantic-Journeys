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

    /// <summary>
    /// Where the touch controls sit for a given screen (pixels, y up), after the player's
    /// <see cref="ControlCustomization"/>: button size, left-handed mirror, dragged jump-pad position.
    /// </summary>
    public readonly struct TouchLayout
    {
        public readonly Rect SafeArea;
        public readonly Rect StickZone;
        public readonly Vector2 JumpCenter;
        public readonly float JumpRadius;
        public readonly float StickRadius;
        public readonly bool LeftHanded;

        public TouchLayout(Rect safeArea, float pixelsPerPoint)
            : this(safeArea, pixelsPerPoint, null) { }

        public TouchLayout(Rect safeArea, float pixelsPerPoint, ControlCustomization customization)
        {
            var c = (customization ?? ControlCustomization.Default).Clamped();
            SafeArea = safeArea;
            LeftHanded = c.leftHanded;
            var zoneWidth = safeArea.width * ProvisionalTuning.Touch.StickZoneWidthFraction;
            StickZone = new Rect(
                c.leftHanded ? safeArea.xMax - zoneWidth : safeArea.xMin,
                safeArea.yMin,
                zoneWidth,
                safeArea.height
            );
            JumpRadius = c.buttonSizePt * pixelsPerPoint * 0.5f;
            var inset = ProvisionalTuning.Touch.JumpPadInsetPt * pixelsPerPoint;
            // Default anchor: low-right (low-left when mirrored), inset from the safe-area corner.
            var towardCentre = c.leftHanded ? 1f : -1f;
            var anchorX = c.leftHanded
                ? safeArea.xMin + inset + JumpRadius
                : safeArea.xMax - inset - JumpRadius;
            var x = anchorX + towardCentre * c.jumpOffsetPt.x * pixelsPerPoint;
            var y = safeArea.yMin + inset + JumpRadius + c.jumpOffsetPt.y * pixelsPerPoint;
            // Keep the whole pad inside the safe area and out of the stick zone.
            var minX = c.leftHanded ? safeArea.xMin + JumpRadius : StickZone.xMax + JumpRadius;
            var maxX = c.leftHanded ? StickZone.xMin - JumpRadius : safeArea.xMax - JumpRadius;
            JumpCenter = new Vector2(
                minX <= maxX ? Mathf.Clamp(x, minX, maxX) : (minX + maxX) * 0.5f,
                Mathf.Clamp(
                    y,
                    safeArea.yMin + JumpRadius,
                    Mathf.Max(safeArea.yMin + JumpRadius, safeArea.yMax - JumpRadius)
                )
            );
            StickRadius = ProvisionalTuning.Touch.StickRadiusPt * pixelsPerPoint;
        }

        /// <summary>True when the screen geometry differs (fold, unfold, Split View, rotation).</summary>
        public bool GeometryDiffers(TouchLayout other) => SafeArea != other.SafeArea;

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
