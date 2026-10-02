using System;
using UnityEngine;

namespace GiganticJourneys.Avatars
{
    /// <summary>
    /// Applies an <see cref="AvatarParams"/> to the shared base rig (gj-humanoid-1A,
    /// M1-AVAT-01 AT-1). Only the <b>visual</b> changes. The movement body (collider, motor,
    /// socket and IK targets) is never touched, so every character moves identically.
    /// <para>Art contract for the rig (gj-design delivers the final art; the placeholder in
    /// <see cref="PlaceholderRig"/> follows the same contract):</para>
    /// <list type="bullet">
    /// <item><c>Visual</c> child: scaled by body height/build within ±6% / ±12%.</item>
    /// <item>Blend shapes <c>face_shape, face_width, jaw, brow, nose, eyes</c> (0-100) on any
    /// SkinnedMeshRenderer under Visual.</item>
    /// <item>Renderers tagged by name prefix: <c>skin</c>, <c>hair</c>, <c>outfit</c>, which get the
    /// skin palette, hair palette and outfit/hero colour (MaterialPropertyBlock, no material copies).</item>
    /// <item>Variant children <c>hair_&lt;style&gt;</c>, <c>glasses_&lt;style&gt;</c>,
    /// <c>facial_hair_&lt;style&gt;</c>, <c>headwear_&lt;style&gt;</c>: exactly the selected one
    /// is active ("none" hides the slot).</item>
    /// </list>
    /// </summary>
    public sealed class AvatarAppearance : MonoBehaviour
    {
        public const float HeightRange = 0.06f;
        public const float BuildRange = 0.12f;
        public static readonly string[] FaceBlendShapes =
        {
            "face_shape",
            "face_width",
            "jaw",
            "brow",
            "nose",
            "eyes",
        };

        static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        static readonly int ColorId = Shader.PropertyToID("_Color");

        [Tooltip("The visual root (defaults to the child named 'Visual').")]
        public Transform visual;

        public AvatarParams Applied { get; private set; }
        public Color OutfitColor { get; private set; }

        Vector3 _baseScale = Vector3.one;
        bool _captured;
        MaterialPropertyBlock _mpb;

        /// <summary>Provisional 32-step skin ramp (light to deep); gj-design owns the final palette.</summary>
        public static Color SkinColor(int index) =>
            Ramp(
                index,
                new Color(0.98f, 0.87f, 0.78f),
                new Color(0.85f, 0.65f, 0.50f),
                new Color(0.24f, 0.15f, 0.11f)
            );

        /// <summary>Provisional 32-step hair ramp (platinum to black); gj-design owns the final palette.</summary>
        public static Color HairColor(int index) =>
            Ramp(
                index,
                new Color(0.93f, 0.86f, 0.70f),
                new Color(0.45f, 0.27f, 0.14f),
                new Color(0.06f, 0.05f, 0.05f)
            );

        /// <summary>Visual scale factors for a parameter set (x/z from build, y from height).</summary>
        public static Vector3 ScaleFor(AvatarParams p) =>
            new Vector3(
                1f + (p.Build - 0.5f) * 2f * BuildRange,
                1f + (p.Height - 0.5f) * 2f * HeightRange,
                1f + (p.Build - 0.5f) * 2f * BuildRange
            );

        public void Apply(AvatarParams p, Color outfitColor)
        {
            if (p == null)
                throw new ArgumentNullException(nameof(p));
            if (visual == null)
                visual = transform.Find("Visual");
            if (visual == null)
                throw new InvalidOperationException(
                    "rig has no 'Visual' child (gj-humanoid-1A art contract)"
                );
            if (!_captured)
            {
                _baseScale = visual.localScale;
                _captured = true;
            }
            visual.localScale = Vector3.Scale(_baseScale, ScaleFor(p));

            var weights = new[] { p.FaceShape, p.FaceWidth, p.Jaw, p.Brow, p.Nose, p.Eyes };
            foreach (var smr in visual.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var mesh = smr.sharedMesh;
                if (mesh == null)
                    continue;
                for (var i = 0; i < FaceBlendShapes.Length; i++)
                {
                    var idx = mesh.GetBlendShapeIndex(FaceBlendShapes[i]);
                    if (idx >= 0)
                        smr.SetBlendShapeWeight(idx, weights[i] * 100f);
                }
            }

            Variant("hair_", p.HairStyle);
            Variant("glasses_", p.GlassesStyle);
            Variant("facial_hair_", p.FacialHairStyle);
            Variant("headwear_", p.HeadwearStyle);

            _mpb ??= new MaterialPropertyBlock();
            OutfitColor = outfitColor;
            foreach (var r in visual.GetComponentsInChildren<Renderer>(true))
            {
                var n = r.gameObject.name;
                Color? c =
                    n.StartsWith("skin", StringComparison.Ordinal) ? SkinColor(p.SkinTone)
                    : n.StartsWith("hair", StringComparison.Ordinal)
                    || n.StartsWith("facial_hair", StringComparison.Ordinal)
                        ? HairColor(p.HairColor)
                    : n.StartsWith("outfit", StringComparison.Ordinal) ? outfitColor
                    : (Color?)null;
                if (c == null)
                    continue;
                r.GetPropertyBlock(_mpb);
                _mpb.SetColor(BaseColorId, c.Value);
                _mpb.SetColor(ColorId, c.Value);
                r.SetPropertyBlock(_mpb);
            }
            Applied = p;
        }

        void Variant(string prefix, string selected)
        {
            foreach (var t in visual.GetComponentsInChildren<Transform>(true))
            {
                var n = t.gameObject.name;
                if (!n.StartsWith(prefix, StringComparison.Ordinal))
                    continue;
                // "hair_" must not claim "facial_hair_*"; prefixes are matched at the start only.
                t.gameObject.SetActive(n == prefix + selected);
            }
        }

        static Color Ramp(int index, Color a, Color b, Color c)
        {
            var t = Mathf.Clamp01(index / (float)(AvatarParams.PaletteSteps - 1));
            return t < 0.5f ? Color.Lerp(a, b, t * 2f) : Color.Lerp(b, c, (t - 0.5f) * 2f);
        }
    }
}
