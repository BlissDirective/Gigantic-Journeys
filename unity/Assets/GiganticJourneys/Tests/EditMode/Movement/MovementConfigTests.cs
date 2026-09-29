using System.Collections.Generic;
using System.IO;
using GiganticJourneys.Movement;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>MovementConfig loads movement.json strictly (M0-UNITY-03 AT-2; M0-MOVE-01 AT-4).</summary>
    public class MovementConfigTests
    {
        static string ShippedPath => MovementConfigLoader.DefaultPath;

        static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));

        static string ShippedText => File.ReadAllText(ShippedPath);

        [Test]
        public void ShippedFile_LoadsIntoTypedFields()
        {
            var c = MovementConfigLoader.LoadFile(ShippedPath);
            Assert.That(c.AvatarHeightA, Is.EqualTo(1f));
            Assert.That(c.Speeds.Walk, Is.EqualTo(1.2f));
            Assert.That(c.Speeds.Sprint, Is.EqualTo(4.5f));
            Assert.That(c.Jump.StandingHeight, Is.EqualTo(1.1f));
            Assert.That(c.Jump.RunningDistance, Is.EqualTo(2.4f));
            Assert.That(c.Jump.CoyoteMs, Is.EqualTo(100f));
            Assert.That(c.Jump.BufferMs, Is.EqualTo(120f));
            Assert.That(c.Assist.SlipsOff, Is.True);
            Assert.That(c.Grapple.SnapAssistA, Is.EqualTo(0.3f));
            Assert.That(c.GravityScale, Is.EqualTo(0.8f));
        }

        [Test]
        public void StartupConfig_IsTheShippedFile()
        {
            var c = MovementConfigLoader.Current;
            Assert.That(c, Is.Not.Null);
            Assert.That(c.Values, Is.EqualTo(MovementConfigLoader.LoadFile(ShippedPath).Values));
        }

        [Test]
        public void EveryJsonLeaf_IsReadIntoATypedField()
        {
            var c = MovementConfig.Parse(ShippedText);
            var leaves = new List<string>();
            CollectLeaves((Dictionary<string, object>)StrictJson.Parse(ShippedText), "", leaves);
            Assert.That(c.Values.Keys, Is.EquivalentTo(leaves));
        }

        static void CollectLeaves(Dictionary<string, object> d, string prefix, List<string> into)
        {
            foreach (var kv in d)
            {
                if (kv.Value is Dictionary<string, object> child)
                    CollectLeaves(child, prefix + kv.Key + ".", into);
                else
                    into.Add(prefix + kv.Key);
            }
        }

        [Test]
        public void CSharpAndPython_AgreeOnEveryConstant_SharedFixture()
        {
            var fixturePath = Path.Combine(
                RepoRoot,
                "services",
                "traversal",
                "tests",
                "fixtures",
                "movement_expected.json"
            );
            Assert.That(File.Exists(fixturePath), fixturePath);
            var expected =
                (Dictionary<string, object>)StrictJson.Parse(File.ReadAllText(fixturePath));
            var actual = MovementConfigLoader.LoadFile(ShippedPath).Values;
            Assert.That(actual.Keys, Is.EquivalentTo(expected.Keys));
            foreach (var kv in expected)
            {
                if (kv.Value is bool b)
                    Assert.That(actual[kv.Key], Is.EqualTo(b), kv.Key);
                else
                    Assert.That((double)actual[kv.Key], Is.EqualTo((double)kv.Value), kv.Key);
            }
        }

        [Test]
        public void MissingKey_IsAHardError_NamingThePath()
        {
            var text = ShippedText.Replace("\"coyoteMs\": 100, ", "");
            Assert.That(text, Is.Not.EqualTo(ShippedText), "fixture edit applied");
            var e = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(text));
            StringAssert.Contains("missing required key 'jump.coyoteMs'", e.Message);
        }

        [Test]
        public void MissingSection_IsAHardError()
        {
            var text = ShippedText.Replace("\"gravityScale\": 0.8,", "");
            var e = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(text));
            StringAssert.Contains("'gravityScale'", e.Message);
        }

        [Test]
        public void ExtraKey_IsAHardError_NamingThePath()
        {
            var text = ShippedText.Replace("\"walk\": 1.2,", "\"walk\": 1.2, \"fly\": 9.0,");
            var e = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(text));
            StringAssert.Contains("unknown key 'speeds.fly'", e.Message);
        }

        [Test]
        public void ExtraTopLevelKey_IsAHardError()
        {
            var text = ShippedText.Replace(
                "\"avatarHeightA\": 1.0,",
                "\"avatarHeightA\": 1.0, \"camera\": {},"
            );
            var e = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(text));
            StringAssert.Contains("unknown key 'camera'", e.Message);
        }

        [Test]
        public void WrongType_IsAHardError()
        {
            var text = ShippedText.Replace("\"run\": 3.6", "\"run\": \"fast\"");
            var e = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(text));
            StringAssert.Contains("'speeds.run' must be a number", e.Message);
        }

        [Test]
        public void DuplicateKey_AndMalformedJson_AreHardErrors()
        {
            var dup = ShippedText.Replace("\"walk\": 1.2,", "\"walk\": 1.2, \"walk\": 1.3,");
            var e1 = Assert.Throws<MovementConfigException>(() => MovementConfig.Parse(dup));
            StringAssert.Contains("duplicate key 'walk'", e1.Message);
            var e2 = Assert.Throws<MovementConfigException>(() =>
                MovementConfig.Parse("{\"a\": }")
            );
            StringAssert.Contains("not valid JSON", e2.Message);
        }

        [Test]
        public void MissingFile_IsAHardError()
        {
            var e = Assert.Throws<MovementConfigException>(() =>
                MovementConfigLoader.LoadFile(
                    Path.Combine(Application.temporaryCachePath, "no-such-movement.json")
                )
            );
            StringAssert.Contains("cannot read", e.Message);
        }

        [Test]
        public void StrictJson_ParsesStandardValues()
        {
            var v =
                (Dictionary<string, object>)
                    StrictJson.Parse("{\"a\":[1,-2.5e1,true,null,\"x\\n\\u0041\"]}");
            var list = (List<object>)v["a"];
            Assert.That(list[0], Is.EqualTo(1d));
            Assert.That(list[1], Is.EqualTo(-25d));
            Assert.That(list[2], Is.EqualTo(true));
            Assert.That(list[3], Is.Null);
            Assert.That(list[4], Is.EqualTo("x\nA"));
        }
    }
}
