using System;
using UnityEngine;

namespace GiganticJourneys.Movement.Intent
{
    /// <summary>
    /// The player's touch-control customization (DESIGN_SYSTEM decision 5, "Customization": Settings ›
    /// Controls with drag-to-reposition, a 56–96 pt size slider, a left-handed mirror, an opacity
    /// slider, and Reset). Pure data: <see cref="TouchLayout"/> applies it, <see cref="ControlCustomizationStore"/>
    /// persists it. The size applies to the buttons (the jump pad, later the contextual action); the
    /// floating stick keeps its own travel radius.
    /// </summary>
    [Serializable]
    public sealed class ControlCustomization
    {
        public const int CurrentVersion = 1;
        public const float MinSizePt = ProvisionalTuning.Touch.ButtonSizeMinPt;
        public const float MaxSizePt = ProvisionalTuning.Touch.ButtonSizeMaxPt;
        public const float MinOpacity = ProvisionalTuning.Touch.OpacityMin;
        public const float MaxOpacity = 1f;

        /// <summary>Idle opacity of the controls (the locked scrim discs are ~60 %).</summary>
        public const float DefaultOpacity = ProvisionalTuning.Touch.OpacityDefault;

        /// <summary>How far a dragged control may move from its default anchor, points.</summary>
        public const float MaxOffsetPt = ProvisionalTuning.Touch.DragOffsetMaxPt;

        public int version = CurrentVersion;

        /// <summary>Jump-pad diameter, points (56–96).</summary>
        public float buttonSizePt = ProvisionalTuning.Touch.JumpPadPt;

        /// <summary>Idle opacity, 0.2–1; a pressed control is always fully opaque.</summary>
        public float opacity = DefaultOpacity;

        /// <summary>Mirror the layout: stick zone on the right third, jump pad low-left.</summary>
        public bool leftHanded;

        /// <summary>
        /// Drag offset of the jump pad from its default anchor, points. x points toward the screen
        /// centre (so the same offset works mirrored), y points up.
        /// </summary>
        public Vector2 jumpOffsetPt;

        public static ControlCustomization Default => new ControlCustomization();

        public bool IsDefault => Equals(Default);

        /// <summary>A copy with every field inside its range; NaN or infinite values fall back to the default.</summary>
        public ControlCustomization Clamped()
        {
            return new ControlCustomization
            {
                version = CurrentVersion,
                buttonSizePt = Mathf.Clamp(
                    Finite(buttonSizePt, ProvisionalTuning.Touch.JumpPadPt),
                    MinSizePt,
                    MaxSizePt
                ),
                opacity = Mathf.Clamp(Finite(opacity, DefaultOpacity), MinOpacity, MaxOpacity),
                leftHanded = leftHanded,
                jumpOffsetPt = new Vector2(
                    Mathf.Clamp(Finite(jumpOffsetPt.x, 0f), -MaxOffsetPt, MaxOffsetPt),
                    Mathf.Clamp(Finite(jumpOffsetPt.y, 0f), -MaxOffsetPt, MaxOffsetPt)
                ),
            };
        }

        public string ToJson() => JsonUtility.ToJson(Clamped());

        /// <summary>
        /// Parses a stored customization. Empty, malformed, or newer-version data returns the
        /// default (a Settings reset is always a safe outcome); values are clamped.
        /// </summary>
        public static ControlCustomization FromJson(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
                return Default;
            try
            {
                var c = JsonUtility.FromJson<ControlCustomization>(json);
                if (c == null || c.version < 1 || c.version > CurrentVersion)
                    return Default;
                return c.Clamped();
            }
            catch (ArgumentException)
            {
                return Default;
            }
        }

        public override bool Equals(object obj) =>
            obj is ControlCustomization o
            && Mathf.Approximately(buttonSizePt, o.buttonSizePt)
            && Mathf.Approximately(opacity, o.opacity)
            && leftHanded == o.leftHanded
            && Mathf.Approximately(jumpOffsetPt.x, o.jumpOffsetPt.x)
            && Mathf.Approximately(jumpOffsetPt.y, o.jumpOffsetPt.y);

        public override int GetHashCode() => HashCode.Combine(buttonSizePt, opacity, leftHanded);

        static float Finite(float v, float fallback) =>
            float.IsNaN(v) || float.IsInfinity(v) ? fallback : v;
    }

    /// <summary>
    /// Persists <see cref="ControlCustomization"/> in PlayerPrefs (a UI preference, no personal data).
    /// </summary>
    public static class ControlCustomizationStore
    {
        public const string DefaultKey = "gj.controls.v1";

        public static ControlCustomization Load(string key = DefaultKey) =>
            ControlCustomization.FromJson(PlayerPrefs.GetString(key, string.Empty));

        public static void Save(ControlCustomization customization, string key = DefaultKey)
        {
            PlayerPrefs.SetString(key, (customization ?? ControlCustomization.Default).ToJson());
            PlayerPrefs.Save();
        }

        /// <summary>Settings › Controls › Reset.</summary>
        public static ControlCustomization Reset(string key = DefaultKey)
        {
            PlayerPrefs.DeleteKey(key);
            PlayerPrefs.Save();
            return ControlCustomization.Default;
        }
    }
}
