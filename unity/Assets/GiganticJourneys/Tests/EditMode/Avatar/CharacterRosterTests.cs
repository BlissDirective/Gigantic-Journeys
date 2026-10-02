using System.IO;
using System.Linq;
using GiganticJourneys.Avatars;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.UIElements;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// Ticket M1-AVAT-01 (preset path): the shipped roster loads and validates, avatar_params
    /// is parsed as strictly as its schema, the parameters apply to the visual only (the movement
    /// body is untouched, AT-1), and the picker uses "your character" copy.
    /// </summary>
    public class CharacterRosterTests
    {
        const string Valid =
            "{\"schema_version\":\"1.0.0\",\"base_rig\":\"gj-humanoid-1A\","
            + "\"provenance\":{\"source\":\"preset\",\"preset_id\":\"roster-ava-01\"},"
            + "\"body\":{\"height\":0.5,\"build\":0.45},"
            + "\"face\":{\"shape\":0.5,\"width\":0.5,\"jaw\":0.45,\"brow\":0.5,\"nose\":0.5,\"eyes\":0.55},"
            + "\"skin_tone\":15,\"hair\":{\"style\":\"medium\",\"color\":10},"
            + "\"features\":{\"glasses\":\"none\",\"facial_hair\":\"none\",\"headwear\":\"none\"},"
            + "\"cosmetic\":{\"outfit\":\"explorer-amber\",\"material_tier\":\"standard\"}}";

        static string RepoRoster =>
            Path.GetFullPath(Path.Combine(Application.dataPath, "../../data/avatar/roster"));

        [Test]
        public void ShippedRosterHasEightValidPresetsOnTheSharedRig()
        {
            var roster = CharacterRoster.Load();
            Assert.AreEqual(8, roster.Presets.Count);
            Assert.GreaterOrEqual(roster.Presets.Count, roster.Floor);
            Assert.AreEqual(8, roster.Presets.Select(p => p.PresetId).Distinct().Count());
            Assert.AreEqual(
                8,
                roster.Presets.Select(p => p.HeroColor).Distinct().Count(),
                "a distinct hero colour each"
            );
            foreach (var p in roster.Presets)
            {
                Assert.AreEqual("preset", p.Params.Source);
                Assert.AreEqual(p.PresetId, p.Params.PresetId);
            }
        }

        [Test]
        public void ShippedRosterIsByteIdenticalToTheRepoData()
        {
            Assume.That(Directory.Exists(RepoRoster), "repo checkout not present");
            var shipped = CharacterRoster.DefaultDirectory;
            foreach (
                var src in Directory.GetFiles(RepoRoster, "*.json", SearchOption.AllDirectories)
            )
            {
                var rel = src.Substring(RepoRoster.Length + 1);
                if (rel.StartsWith("tests"))
                    continue;
                CollectionAssert.AreEqual(
                    File.ReadAllBytes(src),
                    File.ReadAllBytes(Path.Combine(shipped, rel)),
                    $"{rel}: run python .github/scripts/copy_roster_to_unity.py"
                );
            }
        }

        [Test]
        public void ParsesAValidParameterSet()
        {
            var p = AvatarParams.Parse(Valid);
            Assert.AreEqual("roster-ava-01", p.PresetId);
            Assert.AreEqual(0.45f, p.Build);
            Assert.AreEqual(15, p.SkinTone);
            Assert.AreEqual("medium", p.HairStyle);
        }

        [TestCase("\"build\":0.45", "\"build\":1.2", "[0, 1]")]
        [TestCase("\"skin_tone\":15", "\"skin_tone\":32", "integer in [0, 31]")]
        [TestCase("\"skin_tone\":15", "\"skin_tone\":1.5", "integer")]
        [TestCase("\"style\":\"medium\"", "\"style\":\"mohawk\"", "must be one of")]
        [TestCase(
            "\"base_rig\":\"gj-humanoid-1A\"",
            "\"base_rig\":\"other-rig\"",
            "one shared rig"
        )]
        [TestCase("\"schema_version\":\"1.0.0\"", "\"schema_version\":\"2.0.0\"", "schema_version")]
        [TestCase(",\"preset_id\":\"roster-ava-01\"", "", "preset_id is required")]
        [TestCase(
            "\"eyes\":0.55}",
            "\"eyes\":0.55,\"landmarks\":[1,2,3]}",
            "unknown field 'landmarks'"
        )]
        [TestCase(
            "\"skin_tone\":15,",
            "\"skin_tone\":15,\"face_embedding\":[0.1],",
            "unknown field 'face_embedding'"
        )]
        [TestCase("\"outfit\":\"explorer-amber\"", "\"outfit\":\"Explorer Amber\"", "^[a-z0-9-]")]
        [TestCase(",\"jaw\":0.45", "", "missing field 'jaw'")]
        public void RejectsWhatTheSchemaRejects(string from, string to, string because)
        {
            StringAssert.Contains(from, Valid);
            var e = Assert.Throws<AvatarParamsException>(() =>
                AvatarParams.Parse(Valid.Replace(from, to))
            );
            StringAssert.Contains(because, e.Message);
        }

        [Test]
        public void SchemaFixturesAgree()
        {
            var fixtures = Path.GetFullPath(
                Path.Combine(Application.dataPath, "../../data/schemas/avatar/fixtures")
            );
            Assume.That(Directory.Exists(fixtures), "repo checkout not present");
            Assert.DoesNotThrow(() =>
                AvatarParams.Parse(
                    File.ReadAllText(Path.Combine(fixtures, "valid/custom_avatar.json"))
                )
            );
            foreach (var bad in new[] { "avatar_biometric_field.json", "avatar_out_of_range.json" })
                Assert.Throws<AvatarParamsException>(
                    () =>
                        AvatarParams.Parse(
                            File.ReadAllText(Path.Combine(fixtures, "invalid", bad))
                        ),
                    bad
                );
        }

        [Test]
        public void AppearanceChangesTheVisualOnlyNeverTheMovementBody()
        {
            var rig = new GameObject("gj-humanoid-1A");
            try
            {
                var body = rig.AddComponent<CapsuleCollider>();
                body.height = 1f;
                body.radius = 0.2f;
                PlaceholderRig.Build(rig.transform);
                var look = rig.AddComponent<AvatarAppearance>();
                var roster = CharacterRoster.Load();
                foreach (var preset in roster.Presets)
                {
                    look.Apply(preset.Params, preset.HeroColor);
                    Assert.AreEqual(Vector3.one, rig.transform.localScale, "rig root never scales");
                    Assert.AreEqual(1f, body.height);
                    Assert.AreEqual(0.2f, body.radius);
                    Assert.AreEqual(
                        AvatarAppearance.ScaleFor(preset.Params),
                        look.visual.localScale
                    );
                    AssertOneVariant(look.visual, "hair_", preset.Params.HairStyle);
                    AssertOneVariant(look.visual, "glasses_", preset.Params.GlassesStyle);
                    AssertOneVariant(look.visual, "facial_hair_", preset.Params.FacialHairStyle);
                    AssertOneVariant(look.visual, "headwear_", preset.Params.HeadwearStyle);
                    var mpb = new MaterialPropertyBlock();
                    look.visual.Find("outfit_body").GetComponent<Renderer>().GetPropertyBlock(mpb);
                    Assert.AreEqual(preset.HeroColor, mpb.GetColor("_BaseColor"));
                    look.visual.Find("skin_head").GetComponent<Renderer>().GetPropertyBlock(mpb);
                    Assert.AreEqual(
                        AvatarAppearance.SkinColor(preset.Params.SkinTone),
                        mpb.GetColor("_BaseColor")
                    );
                }
                Assert.AreEqual(
                    0,
                    rig.GetComponentsInChildren<Collider>().Length - 1,
                    "the placeholder adds no colliders"
                );
            }
            finally
            {
                Object.DestroyImmediate(rig);
            }
        }

        [Test]
        public void ScaleStaysWithinTheRigTolerance()
        {
            var p = AvatarParams.Parse(Valid);
            p.Height = 1f;
            p.Build = 0f;
            var s = AvatarAppearance.ScaleFor(p);
            Assert.AreEqual(1f + AvatarAppearance.HeightRange, s.y, 1e-6);
            Assert.AreEqual(1f - AvatarAppearance.BuildRange, s.x, 1e-6);
        }

        [Test]
        public void PalettesSpanLightToDeep()
        {
            Assert.Greater(
                AvatarAppearance.SkinColor(0).grayscale,
                AvatarAppearance.SkinColor(31).grayscale + 0.4f
            );
            Assert.Greater(
                AvatarAppearance.HairColor(0).grayscale,
                AvatarAppearance.HairColor(31).grayscale + 0.4f
            );
        }

        [Test]
        public void PickerSaysYourCharacterAndRemembersTheChoice()
        {
            PlayerPrefs.DeleteKey(CharacterSelectView.PrefsKey);
            var go = new GameObject("picker");
            var rig = new GameObject("rig");
            try
            {
                PlaceholderRig.Build(rig.transform);
                var view = go.AddComponent<CharacterSelectView>();
                view.preview = rig.AddComponent<AvatarAppearance>();
                view.Show();
                Assert.AreEqual(8, view.Cards.Count);
                Assert.AreEqual("roster-ava-01", view.SelectedPresetId, "first preset by default");
                var texts = view.Root.Query<TextElement>().ToList().Select(t => t.text).ToList();
                CollectionAssert.Contains(texts, "Choose your character");
                Assert.IsFalse(
                    texts.Any(t => t.ToLowerInvariant().Contains("avatar")),
                    "'avatar' is only for the custom-create flow"
                );
                Assert.IsTrue(
                    view.Cards.All(c => c.style.height.value.value >= 48f),
                    "48 px minimum target"
                );

                view.Select("roster-ava-05");
                Assert.AreEqual("roster-ava-05", view.preview.Applied.PresetId);
                Assert.AreEqual(
                    Visibility.Visible,
                    view.Cards[4].Q<Label>("check").style.visibility.value
                );
                Assert.AreEqual(
                    Visibility.Hidden,
                    view.Cards[0].Q<Label>("check").style.visibility.value
                );
                CharacterRoster.Preset confirmed = null;
                view.Confirmed += p => confirmed = p;
                view.Confirm();
                Assert.AreEqual("roster-ava-05", confirmed.PresetId);
                Assert.AreEqual(
                    "roster-ava-05",
                    PlayerPrefs.GetString(CharacterSelectView.PrefsKey)
                );
                Assert.AreEqual(
                    "roster-ava-05",
                    CharacterSelectView.RememberedOrDefault(view.Roster)
                );
            }
            finally
            {
                PlayerPrefs.DeleteKey(CharacterSelectView.PrefsKey);
                Object.DestroyImmediate(go);
                Object.DestroyImmediate(rig);
            }
        }

        static void AssertOneVariant(Transform visual, string prefix, string selected)
        {
            var active = visual
                .GetComponentsInChildren<Transform>(true)
                .Where(t => t.name.StartsWith(prefix) && t.gameObject.activeSelf)
                .Select(t => t.name)
                .ToList();
            if (selected == "none")
                Assert.IsEmpty(active, prefix);
            else
                CollectionAssert.AreEqual(new[] { prefix + selected }, active);
        }
    }
}
