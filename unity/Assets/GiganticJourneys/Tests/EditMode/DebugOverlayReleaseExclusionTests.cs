using System;
using System.IO;
using System.Linq;
using GiganticJourneys.DebugTools;
using GiganticJourneys.EditorTools.Build;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Player;
using UnityEditor.Compilation;

namespace GiganticJourneys.Tests
{
    /// <summary>
    /// M0-UNITY-04 AT-2 and SECURITY_CHECKLIST §9.7/§9.8: the debug overlay is
    /// compiled out of release builds. The player scripts are compiled for real
    /// (no build, just the C# player assemblies) with and without the debug
    /// switches, and the overlay assembly and type must be absent from release.
    /// </summary>
    public class DebugOverlayReleaseExclusionTests
    {
        const string OverlayAssembly = "GiganticJourneys.DebugOverlay";
        const string Constraint = "UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG";

        static (BuildTarget target, BuildTargetGroup group) CompileTarget()
        {
            var linux = BuildTarget.StandaloneLinux64;
            if (BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.Standalone, linux))
                return (linux, BuildTargetGroup.Standalone);
            var active = EditorUserBuildSettings.activeBuildTarget;
            return (active, BuildPipeline.GetBuildTargetGroup(active));
        }

        static string[] CompilePlayer(
            ScriptCompilationOptions options,
            string[] extraDefines = null
        )
        {
            var (target, group) = CompileTarget();
            var outDir = Path.Combine(
                Path.GetTempPath(),
                "gj-overlay-exclusion-" + Guid.NewGuid().ToString("N")
            );
            Directory.CreateDirectory(outDir);
            try
            {
                var settings = new ScriptCompilationSettings
                {
                    target = target,
                    group = group,
                    options = options,
                    extraScriptingDefines = extraDefines ?? Array.Empty<string>(),
                };
                var result = PlayerBuildInterface.CompilePlayerScripts(settings, outDir);
                Assert.That(
                    result.assemblies,
                    Is.Not.Empty,
                    "player script compilation produced nothing"
                );
                Assert.That(
                    result.assemblies,
                    Has.Some.StartsWith("GiganticJourneys"),
                    "the game's own runtime assemblies must be in the player"
                );
                if (options == ScriptCompilationOptions.None && extraDefines == null)
                {
                    // No type named DebugOverlay may hide in another player assembly either.
                    foreach (var dll in Directory.GetFiles(outDir, "GiganticJourneys*.dll"))
                    {
                        var text = System.Text.Encoding.ASCII.GetString(File.ReadAllBytes(dll));
                        Assert.That(
                            text.Contains(nameof(DebugOverlay)),
                            Is.False,
                            $"{Path.GetFileName(dll)} references {nameof(DebugOverlay)} in a release build"
                        );
                    }
                }
                return result.assemblies.ToArray();
            }
            finally
            {
                Directory.Delete(outDir, true);
            }
        }

        [Test]
        public void ReleasePlayerScripts_ExcludeDebugOverlayType()
        {
            var assemblies = CompilePlayer(ScriptCompilationOptions.None);
            Assert.That(
                assemblies,
                Has.None.StartsWith(OverlayAssembly),
                "a release (non-development) player must not contain the debug overlay"
            );
        }

        [Test]
        public void DevelopmentPlayerScripts_IncludeDebugOverlay()
        {
            var assemblies = CompilePlayer(ScriptCompilationOptions.DevelopmentBuild);
            Assert.That(assemblies, Has.Some.StartsWith(OverlayAssembly));
        }

        [Test]
        public void GjDebugDefine_ForcesOverlayIntoNonDevelopmentPlayer()
        {
            var assemblies = CompilePlayer(ScriptCompilationOptions.None, new[] { "GJ_DEBUG" });
            Assert.That(assemblies, Has.Some.StartsWith(OverlayAssembly));
        }

        [Test]
        public void OverlayAssembly_HasDebugDefineConstraint()
        {
            var path = CompilationPipeline.GetAssemblyDefinitionFilePathFromAssemblyName(
                OverlayAssembly
            );
            Assert.That(path, Is.Not.Null.And.Not.Empty, "asmdef not found");
            var json = File.ReadAllText(path);
            StringAssert.Contains("\"defineConstraints\"", json);
            StringAssert.Contains(Constraint, json);
            Assert.That(typeof(DebugOverlay).Assembly.GetName().Name, Is.EqualTo(OverlayAssembly));
        }

        [Test]
        public void ReleaseDefines_DoNotForceGjDebug()
        {
            foreach (var target in new[] { NamedBuildTarget.iOS, NamedBuildTarget.Android })
            {
                var defines = PlayerSettings.GetScriptingDefineSymbols(target) ?? "";
                Assert.That(
                    defines.Split(';', ',').Select(d => d.Trim()),
                    Has.No.Member("GJ_DEBUG"),
                    $"{target.TargetName} scripting defines must not ship GJ_DEBUG"
                );
            }
        }

        [Test]
        public void SharePlugin_IsIosOnly_AndExcludedFromReleaseBuilds()
        {
            var importer = (PluginImporter)AssetImporter.GetAtPath(BuildInfoHook.SharePluginPath);
            Assert.That(importer, Is.Not.Null, "GJShareSheet.mm not found");
            Assert.That(importer.GetCompatibleWithPlatform(BuildTarget.iOS), Is.True);
            Assert.That(
                importer.GetCompatibleWithPlatform(BuildTarget.StandaloneLinux64),
                Is.False
            );
            Assert.That(importer.GetCompatibleWithAnyPlatform(), Is.False);
            var was = BuildInfoHook.CurrentBuildIsDebug;
            try
            {
                BuildInfoHook.CurrentBuildIsDebug = false;
                Assert.That(
                    BuildInfoHook.IncludeDebugPlugin(BuildInfoHook.SharePluginPath),
                    Is.False
                );
                BuildInfoHook.CurrentBuildIsDebug = true;
                Assert.That(
                    BuildInfoHook.IncludeDebugPlugin(BuildInfoHook.SharePluginPath),
                    Is.True
                );
            }
            finally
            {
                BuildInfoHook.CurrentBuildIsDebug = was;
            }
        }
    }
}
