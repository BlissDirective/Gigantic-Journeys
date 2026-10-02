using UnityEngine;

namespace GiganticJourneys.Avatars
{
    /// <summary>
    /// A primitive stand-in for the gj-humanoid-1A visual that follows the
    /// <see cref="AvatarAppearance"/> art contract, so the preset path is testable and playable
    /// before gj-design's rigged mesh lands. About 1 A tall (the character defines the A unit).
    /// No colliders: the movement body is separate and is never changed by appearance.
    /// </summary>
    public static class PlaceholderRig
    {
        /// <summary>Builds <c>Visual</c> under <paramref name="parent"/> and returns it.</summary>
        public static Transform Build(Transform parent)
        {
            var visual = new GameObject("Visual").transform;
            visual.SetParent(parent, false);
            Part(
                "outfit_body",
                PrimitiveType.Capsule,
                visual,
                new Vector3(0f, 0.36f, 0f),
                new Vector3(0.3f, 0.36f, 0.22f)
            );
            Part(
                "skin_head",
                PrimitiveType.Sphere,
                visual,
                new Vector3(0f, 0.84f, 0f),
                new Vector3(0.22f, 0.25f, 0.22f)
            );
            foreach (var style in AvatarParams.HairStyles)
            {
                if (style == "none")
                    continue;
                var (pos, scale) = HairShape(style);
                Part("hair_" + style, PrimitiveType.Sphere, visual, pos, scale);
            }
            Part(
                "glasses_round",
                PrimitiveType.Cylinder,
                visual,
                new Vector3(0f, 0.86f, 0.11f),
                new Vector3(0.17f, 0.005f, 0.05f),
                90f
            );
            Part(
                "glasses_square",
                PrimitiveType.Cube,
                visual,
                new Vector3(0f, 0.86f, 0.115f),
                new Vector3(0.18f, 0.05f, 0.01f)
            );
            Part(
                "glasses_sunglasses",
                PrimitiveType.Cube,
                visual,
                new Vector3(0f, 0.86f, 0.115f),
                new Vector3(0.19f, 0.06f, 0.015f)
            );
            Part(
                "facial_hair_stubble",
                PrimitiveType.Sphere,
                visual,
                new Vector3(0f, 0.77f, 0.06f),
                new Vector3(0.17f, 0.1f, 0.12f)
            );
            Part(
                "facial_hair_mustache",
                PrimitiveType.Cube,
                visual,
                new Vector3(0f, 0.8f, 0.105f),
                new Vector3(0.08f, 0.015f, 0.02f)
            );
            Part(
                "facial_hair_goatee",
                PrimitiveType.Sphere,
                visual,
                new Vector3(0f, 0.74f, 0.09f),
                new Vector3(0.06f, 0.07f, 0.05f)
            );
            Part(
                "facial_hair_full",
                PrimitiveType.Sphere,
                visual,
                new Vector3(0f, 0.76f, 0.05f),
                new Vector3(0.21f, 0.16f, 0.17f)
            );
            Part(
                "headwear_cap",
                PrimitiveType.Cylinder,
                visual,
                new Vector3(0f, 0.97f, 0.02f),
                new Vector3(0.24f, 0.03f, 0.26f)
            );
            Part(
                "headwear_beanie",
                PrimitiveType.Sphere,
                visual,
                new Vector3(0f, 0.95f, 0f),
                new Vector3(0.24f, 0.16f, 0.24f)
            );
            Part(
                "headwear_band",
                PrimitiveType.Cylinder,
                visual,
                new Vector3(0f, 0.92f, 0f),
                new Vector3(0.235f, 0.015f, 0.235f)
            );
            return visual;
        }

        static (Vector3, Vector3) HairShape(string style)
        {
            switch (style)
            {
                case "buzz":
                    return (new Vector3(0f, 0.88f, -0.03f), new Vector3(0.225f, 0.2f, 0.19f));
                case "short":
                    return (new Vector3(0f, 0.9f, -0.035f), new Vector3(0.235f, 0.19f, 0.19f));
                case "long":
                    return (new Vector3(0f, 0.8f, -0.06f), new Vector3(0.25f, 0.36f, 0.17f));
                case "curly":
                    return (new Vector3(0f, 0.91f, -0.04f), new Vector3(0.27f, 0.21f, 0.2f));
                case "afro":
                    return (new Vector3(0f, 0.94f, -0.06f), new Vector3(0.36f, 0.3f, 0.26f));
                case "bun":
                    return (new Vector3(0f, 0.99f, -0.06f), new Vector3(0.1f, 0.1f, 0.1f));
                case "ponytail":
                    return (new Vector3(0f, 0.82f, -0.13f), new Vector3(0.07f, 0.2f, 0.07f));
                case "braids":
                    return (new Vector3(0f, 0.76f, -0.1f), new Vector3(0.2f, 0.32f, 0.08f));
                default: // medium
                    return (new Vector3(0f, 0.88f, -0.045f), new Vector3(0.245f, 0.25f, 0.18f));
            }
        }

        static void Part(
            string name,
            PrimitiveType type,
            Transform parent,
            Vector3 pos,
            Vector3 scale,
            float rollX = 0f
        )
        {
            var go = GameObject.CreatePrimitive(type);
            go.name = name;
            var col = go.GetComponent<Collider>();
            if (col != null)
                Object.DestroyImmediate(col);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.Euler(rollX, 0f, 0f);
            go.transform.localScale = scale;
        }
    }
}
