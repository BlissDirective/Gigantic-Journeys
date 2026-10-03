using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine.Rendering;

namespace GiganticJourneys.Tests
{
    public class ProjectSettingsSmokeTests
    {
        [Test]
        public void IosBundleIdIsTheStoreId()
        {
            Assert.AreEqual(
                ProjectIdentity.BundleId,
                PlayerSettings.GetApplicationIdentifier(NamedBuildTarget.iOS)
            );
        }

        [Test]
        public void IosUsesMetalOnlyAndIl2Cpp()
        {
            CollectionAssert.AreEqual(
                new[] { GraphicsDeviceType.Metal },
                PlayerSettings.GetGraphicsAPIs(BuildTarget.iOS)
            );
            Assert.AreEqual(
                ScriptingImplementation.IL2CPP,
                PlayerSettings.GetScriptingBackend(NamedBuildTarget.iOS)
            );
        }

        [Test]
        public void BootSceneIsFirstEnabledBuildScene()
        {
            var first = EditorBuildSettings.scenes.FirstOrDefault(s => s.enabled);
            Assert.IsNotNull(first, "EditorBuildSettings has no enabled scene");
            Assert.AreEqual(ProjectIdentity.BootScenePath, first.path);
        }

        [Test]
        public void BootSceneIsThePlayableMovementTestScene()
        {
            Assert.AreEqual(
                GiganticJourneys.EditorTools.MovementTestScene.ScenePath,
                ProjectIdentity.BootScenePath
            );
            Assert.IsTrue(
                File.Exists(ProjectIdentity.BootScenePath),
                ProjectIdentity.BootScenePath
            );
            Assert.AreEqual(ProjectIdentity.BootScenePath, EditorBuildSettings.scenes[0].path);
            Assert.IsTrue(EditorBuildSettings.scenes[0].enabled);
        }

        [Test]
        public void UrpIsTheDefaultRenderPipeline()
        {
            Assert.IsNotNull(GraphicsSettings.defaultRenderPipeline);
            Assert.AreEqual(
                "UniversalRenderPipelineAsset",
                GraphicsSettings.defaultRenderPipeline.GetType().Name
            );
        }

        // App Store Connect rejects an upload without a 1024 px App Store icon
        // ("Missing app icon", TestFlight runs 36577265750 / 36760847904). Read from
        // ProjectSettings.asset directly: the unity-tests image has no iOS module, so the
        // UnityEditor.iOS icon-kind API is unavailable there.
        static (int width, int kind, string guid)[] IosIcons()
        {
            var yaml = File.ReadAllText("ProjectSettings/ProjectSettings.asset");
            var block = Regex.Match(
                yaml,
                @"m_BuildTargetPlatformIcons:\s*\n\s*- m_BuildTarget: iPhone\n(?<b>(?:\s{4,}.*\n)+)"
            );
            Assert.IsTrue(block.Success, "no iPhone icon block in ProjectSettings.asset");
            return Regex
                .Matches(
                    block.Groups["b"].Value,
                    @"- m_Textures:\s*\n\s*- \{fileID: (?<fid>-?\d+)(?:, guid: (?<guid>[0-9a-f]+))?[^}]*\}\s*\n\s*m_Width: (?<w>\d+)\s*\n\s*m_Height: \d+\s*\n\s*m_Kind: (?<k>\d+)"
                )
                .Cast<Match>()
                .Select(m =>
                    (
                        int.Parse(m.Groups["w"].Value),
                        int.Parse(m.Groups["k"].Value),
                        m.Groups["guid"].Value
                    )
                )
                .ToArray();
        }

        [Test]
        public void IosAppStoreIconIsAssignedAt1024()
        {
            // m_Kind 4 = iOSPlatformIconKind.Marketing (the App Store icon).
            var marketing = IosIcons().Where(i => i.kind == 4 && i.width == 1024).ToArray();
            Assert.AreEqual(1, marketing.Length, "no iOS App Store (1024 px) icon slot");
            var path = AssetDatabase.GUIDToAssetPath(marketing[0].guid);
            Assert.IsNotEmpty(path, "iOS App Store (1024 px) icon is not assigned");
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.GetSourceTextureWidthAndHeight(out var w, out var h);
            Assert.AreEqual(1024, w, path);
            Assert.AreEqual(1024, h, path);
            Assert.IsFalse(
                importer.DoesSourceTextureHaveAlpha(),
                $"{path}: the App Store icon must be opaque"
            );
        }

        [Test]
        public void IosAppIconsAreAllAssigned()
        {
            var icons = IosIcons();
            Assert.Greater(icons.Length, 10, "iOS icon slots missing");
            foreach (var (width, kind, guid) in icons)
            {
                Assert.IsNotEmpty(
                    AssetDatabase.GUIDToAssetPath(guid),
                    $"iOS icon kind {kind} {width}px unassigned"
                );
            }
        }
    }
}
