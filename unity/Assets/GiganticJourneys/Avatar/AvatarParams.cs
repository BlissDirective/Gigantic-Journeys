using System;
using System.Collections.Generic;
using GiganticJourneys.Movement;

namespace GiganticJourneys.Avatars
{
    /// <summary>Thrown when an avatar_params document breaks its schema.</summary>
    public sealed class AvatarParamsException : Exception
    {
        public AvatarParamsException(string message)
            : base(message) { }
    }

    /// <summary>
    /// One parameter set on the shared base rig (<c>data/schemas/avatar/avatar_params.schema.json</c>
    /// v1.0.0, ADR-0007, AUTH #044). Presets and on-device customs share this representation,
    /// so any character is rig-conformant by construction. Parsed strictly, like the schema
    /// (<c>additionalProperties: false</c> everywhere, every field required, ranges and enums
    /// enforced): a field the schema doesn't know (e.g. biometric data) is rejected, never
    /// ignored. M1-AVAT-01 (preset path) uses it; nothing here captures or derives a likeness.
    /// </summary>
    public sealed class AvatarParams
    {
        public const string SchemaVersion = "1.0.0";
        public const string BaseRig = "gj-humanoid-1A";
        public const int PaletteSteps = 32;

        public static readonly string[] HairStyles =
        {
            "none",
            "buzz",
            "short",
            "medium",
            "long",
            "curly",
            "afro",
            "bun",
            "ponytail",
            "braids",
        };
        public static readonly string[] Glasses = { "none", "round", "square", "sunglasses" };
        public static readonly string[] FacialHair =
        {
            "none",
            "stubble",
            "mustache",
            "goatee",
            "full",
        };
        public static readonly string[] Headwear = { "none", "cap", "beanie", "band" };
        public static readonly string[] Sources = { "preset", "custom_on_device" };
        public static readonly string[] FitQualities = { "low", "medium", "high" };
        public static readonly string[] MaterialTiers = { "standard", "realism-plus" };

        public string Source;
        public string PresetId;
        public string FitQuality;
        public float Height;
        public float Build;
        public float FaceShape;
        public float FaceWidth;
        public float Jaw;
        public float Brow;
        public float Nose;
        public float Eyes;
        public int SkinTone;
        public string HairStyle;
        public int HairColor;
        public string GlassesStyle;
        public string FacialHairStyle;
        public string HeadwearStyle;
        public string Outfit;
        public string MaterialTier;

        public static AvatarParams Parse(string json)
        {
            object root;
            try
            {
                root = StrictJson.Parse(json);
            }
            catch (FormatException e)
            {
                throw new AvatarParamsException(e.Message);
            }
            var o = Obj(root, "avatar_params");
            Keys(
                o,
                "avatar_params",
                new[]
                {
                    "schema_version",
                    "base_rig",
                    "provenance",
                    "body",
                    "face",
                    "skin_tone",
                    "hair",
                    "features",
                    "cosmetic",
                },
                0
            );
            if (Str(o, "schema_version") != SchemaVersion)
                throw new AvatarParamsException($"schema_version must be {SchemaVersion}");
            if (Str(o, "base_rig") != BaseRig)
                throw new AvatarParamsException($"base_rig must be {BaseRig} (one shared rig)");

            var p = new AvatarParams();
            var prov = Obj(o["provenance"], "provenance");
            Keys(prov, "provenance", new[] { "source", "preset_id", "fit_quality" }, 1);
            p.Source = Enum(prov, "source", Sources);
            if (prov.ContainsKey("preset_id"))
                p.PresetId = Slug(prov, "preset_id");
            if (prov.ContainsKey("fit_quality"))
                p.FitQuality = Enum(prov, "fit_quality", FitQualities);
            if (p.Source == "preset" && p.PresetId == null)
                throw new AvatarParamsException("provenance.preset_id is required for a preset");

            var body = Obj(o["body"], "body");
            Keys(body, "body", new[] { "height", "build" }, 2);
            p.Height = Unit(body, "height");
            p.Build = Unit(body, "build");

            var face = Obj(o["face"], "face");
            Keys(face, "face", new[] { "shape", "width", "jaw", "brow", "nose", "eyes" }, 6);
            p.FaceShape = Unit(face, "shape");
            p.FaceWidth = Unit(face, "width");
            p.Jaw = Unit(face, "jaw");
            p.Brow = Unit(face, "brow");
            p.Nose = Unit(face, "nose");
            p.Eyes = Unit(face, "eyes");

            p.SkinTone = Index(o, "skin_tone");

            var hair = Obj(o["hair"], "hair");
            Keys(hair, "hair", new[] { "style", "color" }, 2);
            p.HairStyle = Enum(hair, "style", HairStyles);
            p.HairColor = Index(hair, "color");

            var features = Obj(o["features"], "features");
            Keys(features, "features", new[] { "glasses", "facial_hair", "headwear" }, 3);
            p.GlassesStyle = Enum(features, "glasses", Glasses);
            p.FacialHairStyle = Enum(features, "facial_hair", FacialHair);
            p.HeadwearStyle = Enum(features, "headwear", Headwear);

            var cosmetic = Obj(o["cosmetic"], "cosmetic");
            Keys(cosmetic, "cosmetic", new[] { "outfit", "material_tier" }, 2);
            p.Outfit = Slug(cosmetic, "outfit");
            p.MaterialTier = Enum(cosmetic, "material_tier", MaterialTiers);
            return p;
        }

        // required = how many of the leading names are required (0 = all of them)
        static void Keys(Dictionary<string, object> o, string where, string[] allowed, int required)
        {
            foreach (var k in o.Keys)
            {
                if (Array.IndexOf(allowed, k) < 0)
                    throw new AvatarParamsException(
                        $"{where}: unknown field '{k}' (schema forbids extra fields)"
                    );
            }
            var n = required == 0 ? allowed.Length : required;
            for (var i = 0; i < n; i++)
            {
                if (!o.ContainsKey(allowed[i]))
                    throw new AvatarParamsException($"{where}: missing field '{allowed[i]}'");
            }
        }

        static Dictionary<string, object> Obj(object v, string where) =>
            v as Dictionary<string, object>
            ?? throw new AvatarParamsException($"{where} must be an object");

        static string Str(Dictionary<string, object> o, string k) =>
            o[k] as string ?? throw new AvatarParamsException($"'{k}' must be a string");

        static string Enum(Dictionary<string, object> o, string k, string[] values)
        {
            var s = Str(o, k);
            if (Array.IndexOf(values, s) < 0)
                throw new AvatarParamsException(
                    $"'{k}' must be one of {string.Join(", ", values)}"
                );
            return s;
        }

        static string Slug(Dictionary<string, object> o, string k)
        {
            var s = Str(o, k);
            if (s.Length < 1 || s.Length > 40)
                throw new AvatarParamsException($"'{k}' must be 1-40 characters");
            foreach (var c in s)
            {
                if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '-'))
                    throw new AvatarParamsException($"'{k}' must match ^[a-z0-9-]{{1,40}}$");
            }
            return s;
        }

        static float Unit(Dictionary<string, object> o, string k)
        {
            if (!(o[k] is double d) || d < 0 || d > 1)
                throw new AvatarParamsException($"'{k}' must be a number in [0, 1]");
            return (float)d;
        }

        static int Index(Dictionary<string, object> o, string k)
        {
            if (!(o[k] is double d) || d != Math.Floor(d) || d < 0 || d > PaletteSteps - 1)
                throw new AvatarParamsException(
                    $"'{k}' must be an integer in [0, {PaletteSteps - 1}]"
                );
            return (int)d;
        }
    }
}
