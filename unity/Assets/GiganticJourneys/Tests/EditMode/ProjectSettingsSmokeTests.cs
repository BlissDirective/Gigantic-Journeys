using System.Linq;
using NUnit.Framework;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.iOS;
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
        public void UrpIsTheDefaultRenderPipeline()
        {
            Assert.IsNotNull(GraphicsSettings.defaultRenderPipeline);
            Assert.AreEqual(
                "UniversalRenderPipelineAsset",
                GraphicsSettings.defaultRenderPipeline.GetType().Name
            );
        }

        // App Store Connect rejects an upload without a 1024 px App Store icon
        // ("Missing app icon", TestFlight runs 36577265750 / 36760847904).
        [Test]
        public void IosAppStoreIconIsAssignedAt1024()
        {
            var icons = PlayerSettings.GetPlatformIcons(
                NamedBuildTarget.iOS,
                iOSPlatformIconKind.Marketing
            );
            Assert.IsNotEmpty(icons, "no iOS marketing icon slot");
            var tex = icons[0].GetTexture();
            Assert.IsNotNull(tex, "iOS App Store (1024 px) icon is not assigned");
            var path = AssetDatabase.GetAssetPath(tex);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.GetSourceTextureWidthAndHeight(out var w, out var h);
            Assert.AreEqual(1024, w, path);
            Assert.AreEqual(1024, h, path);
        }

        [Test]
        public void IosAppIconsAreAllAssigned()
        {
            foreach (var kind in PlayerSettings.GetSupportedIconKinds(NamedBuildTarget.iOS))
            {
                foreach (var icon in PlayerSettings.GetPlatformIcons(NamedBuildTarget.iOS, kind))
                {
                    Assert.IsNotNull(
                        icon.GetTexture(),
                        $"iOS icon {kind} {icon.width}x{icon.height} unassigned"
                    );
                }
            }
        }
    }
}
