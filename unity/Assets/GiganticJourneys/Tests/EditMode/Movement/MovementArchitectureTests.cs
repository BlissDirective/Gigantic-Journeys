using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using GiganticJourneys.Movement;
using NUnit.Framework;
using UnityEngine;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// The five-layer movement architecture (Bible §2; M0-UNITY-03 AT-1) and the no-hard-coded-
    /// constants rule (AT-7).
    /// </summary>
    public class MovementArchitectureTests
    {
        /// <summary>Bottom to top. Each assembly may reference only assemblies before it.</summary>
        static readonly string[] Layers =
        {
            "GJ.Movement.Shared",
            "GJ.Intent",
            "GJ.TraversalQuery",
            "GJ.AnimationSelection",
            "GJ.MotionWarping",
            "GJ.Procedural",
            "GJ.Movement.Controller",
        };

        static string MovementRoot =>
            Path.Combine(Application.dataPath, "GiganticJourneys", "Movement");

        static Dictionary<string, List<string>> ReadAsmdefs()
        {
            var result = new Dictionary<string, List<string>>();
            foreach (
                var file in Directory.GetFiles(
                    MovementRoot,
                    "*.asmdef",
                    SearchOption.AllDirectories
                )
            )
            {
                var json = (Dictionary<string, object>)StrictJson.Parse(File.ReadAllText(file));
                var refs = ((List<object>)json["references"]).Cast<string>().ToList();
                result[(string)json["name"]] = refs;
            }
            return result;
        }

        [Test]
        public void AllLayerAssembliesExist()
        {
            var asmdefs = ReadAsmdefs();
            Assert.That(asmdefs.Keys, Is.EquivalentTo(Layers));
        }

        [Test]
        public void AsmdefReferences_PointOnlyDownward()
        {
            var asmdefs = ReadAsmdefs();
            for (var i = 0; i < Layers.Length; i++)
            {
                foreach (var r in asmdefs[Layers[i]])
                {
                    var j = Array.IndexOf(Layers, r);
                    if (j < 0)
                    {
                        Assert.That(
                            r.StartsWith("GJ.", StringComparison.Ordinal)
                                || r.StartsWith("GiganticJourneys", StringComparison.Ordinal),
                            Is.False,
                            $"{Layers[i]} references project assembly {r} outside the movement stack"
                        );
                        continue;
                    }
                    Assert.That(
                        j,
                        Is.LessThan(i),
                        $"{Layers[i]} must not reference {r} (upward or sideways)"
                    );
                }
            }
            Assert.That(asmdefs["GJ.Movement.Shared"], Is.Empty, "Shared depends on nothing");
        }

        [Test]
        public void CompiledAssemblies_PointOnlyDownward()
        {
            var loaded = AppDomain
                .CurrentDomain.GetAssemblies()
                .ToDictionary(a => a.GetName().Name, a => a);
            for (var i = 0; i < Layers.Length; i++)
            {
                Assert.That(loaded.ContainsKey(Layers[i]), $"{Layers[i]} compiled");
                foreach (var r in loaded[Layers[i]].GetReferencedAssemblies())
                {
                    var j = Array.IndexOf(Layers, r.Name);
                    if (j >= 0)
                        Assert.That(j, Is.LessThan(i), $"{Layers[i]} uses {r.Name}");
                }
            }
        }

        [Test]
        public void SharedAssembly_HoldsTheContractTypes()
        {
            var shared = typeof(MovementConfig).Assembly;
            Assert.That(shared.GetName().Name, Is.EqualTo("GJ.Movement.Shared"));
            Assert.That(typeof(IVerbProvider).Assembly, Is.EqualTo(shared));
            Assert.That(typeof(MoveClip).Assembly, Is.EqualTo(shared));
            Assert.That(typeof(ScriptableObject).IsAssignableFrom(typeof(MoveClip)), Is.True);
        }

        // AT-7: numbers in movement code come from MovementConfig (or, pending the intent/camera
        // AUTH, the single ProvisionalTuning file). Allowed literals are pure math.
        static readonly HashSet<string> Allowed = new HashSet<string>
        {
            "0",
            "1",
            "2",
            "0.5",
            "1000",
        };

        static readonly string[] Exempt =
        {
            "ProvisionalTuning.cs", // the one pending-AUTH constants file
            "StrictJson.cs", // a JSON parser, no tuning
            "MovementScale.cs", // 9.81 standard gravity, Bible §1
            "TouchControlsView.cs", // placeholder UI styling until design tokens (M0-DSGN-02)
        };

        static readonly Regex Number = new Regex(@"(?<![\w.])(\d+\.\d+|\d+)(?:[fFdDmM])?(?![\w.])");
        static readonly Regex Comment = new Regex(
            @"//.*?$|/\*.*?\*/",
            RegexOptions.Singleline | RegexOptions.Multiline
        );
        static readonly Regex Str = new Regex("\"(?:\\\\.|[^\"\\\\])*\"");

        [Test]
        public void NoMovementOrCameraLiteral_OutsideTheConfig()
        {
            var offenders = new List<string>();
            foreach (
                var file in Directory.GetFiles(MovementRoot, "*.cs", SearchOption.AllDirectories)
            )
            {
                if (Exempt.Contains(Path.GetFileName(file)))
                    continue;
                var code = Str.Replace(Comment.Replace(File.ReadAllText(file), ""), "\"\"");
                foreach (Match m in Number.Matches(code))
                {
                    if (!Allowed.Contains(m.Groups[1].Value))
                        offenders.Add($"{Path.GetFileName(file)}: {m.Value}");
                }
            }
            Assert.That(
                offenders,
                Is.Empty,
                "tuning literals belong in movement.json: " + string.Join(", ", offenders)
            );
        }
    }
}
