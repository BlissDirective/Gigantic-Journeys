using System.Linq;
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
        public void UrpIsTheDefaultRenderPipeline()
        {
            Assert.IsNotNull(GraphicsSettings.defaultRenderPipeline);
            Assert.AreEqual(
                "UniversalRenderPipelineAsset",
                GraphicsSettings.defaultRenderPipeline.GetType().Name
            );
        }
    }
}
