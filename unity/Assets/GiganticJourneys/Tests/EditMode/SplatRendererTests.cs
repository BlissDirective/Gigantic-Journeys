using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using GaussianSplatting.Runtime;
using GiganticJourneys.EditorTools;
using GiganticJourneys.EditorTools.Splats;
using GiganticJourneys.Splats;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace GiganticJourneys.Tests
{
    /// <summary>Ticket M0-UNITY-02: the pinned splat renderer, its URP wiring and the sample.</summary>
    public class SplatRendererTests
    {
        const string PackageName = "org.nesnausk.gaussian-splatting";

        [Test]
        public void RendererPackageIsPinnedToACommitSha()
        {
            var manifest = File.ReadAllText("Packages/manifest.json");
            var m = Regex.Match(manifest, $"\"{Regex.Escape(PackageName)}\"\\s*:\\s*\"([^\"]+)\"");
            Assert.IsTrue(m.Success, $"{PackageName} missing from Packages/manifest.json");
            StringAssert.IsMatch(
                "^https://github\\.com/aras-p/UnityGaussianSplatting\\.git\\?path=/package#[0-9a-f]{40}$",
                m.Groups[1].Value,
                "the renderer must be a git URL pinned to a full commit SHA (SECURITY_CHECKLIST 7.1)"
            );
        }

        [Test]
        public void RendererPackageLicenseIsMit()
        {
            var info = UnityEditor.PackageManager.PackageInfo.FindForAssetPath(
                $"Packages/{PackageName}/package.json"
            );
            Assert.IsNotNull(info, "renderer package not resolved");
            var license = Path.Combine(info.resolvedPath, "LICENSE.md");
            Assert.IsTrue(File.Exists(license), "renderer LICENSE.md missing");
            StringAssert.StartsWith("MIT License", File.ReadAllText(license).TrimStart());
        }

        [Test]
        public void EveryUrpRendererHasTheSplatFeature()
        {
            var renderers = AssetDatabase
                .FindAssets("t:UniversalRendererData", new[] { "Assets/Settings" })
                .Select(g =>
                    AssetDatabase.LoadAssetAtPath<UniversalRendererData>(
                        AssetDatabase.GUIDToAssetPath(g)
                    )
                )
                .ToArray();
            Assert.AreEqual(3, renderers.Length, "expected one URP renderer per quality tier");
            foreach (var r in renderers)
                Assert.IsTrue(
                    r.rendererFeatures.Any(f =>
                        f != null
                        && f.GetType().FullName == ProjectSetup.SplatFeatureType
                        && f.isActive
                    ),
                    $"{r.name} lacks an active {ProjectSetup.SplatFeatureType}"
                );
        }

        [Test]
        public void SampleSplatIsSmallAndLoadable()
        {
            var asset = AssetDatabase.LoadAssetAtPath<GaussianSplatAsset>(SampleSplat.AssetPath);
            Assert.IsNotNull(asset, $"{SampleSplat.AssetPath} missing");
            Assert.Greater(asset.splatCount, 10000);
            Assert.IsNotNull(asset.posData);
            Assert.IsNotNull(asset.colorData);
            var bytes = Directory
                .GetFiles(SampleSplat.Folder, SampleSplat.SampleName + "*")
                .Where(f => !f.EndsWith(".meta"))
                .Sum(f => new FileInfo(f).Length);
            Assert.LessOrEqual(
                bytes,
                10L * 1024 * 1024,
                "sample splat must be at most 10 MB (AT-2)"
            );
        }

        [Test]
        public void SampleSceneReferencesTheSampleAndSettings()
        {
            Assert.IsTrue(File.Exists(SampleSplat.ScenePath), $"{SampleSplat.ScenePath} missing");
            var deps = AssetDatabase.GetDependencies(SampleSplat.ScenePath, false);
            CollectionAssert.Contains(deps, SampleSplat.AssetPath);
            CollectionAssert.Contains(deps, SampleSplat.SettingsPath);
        }

        [Test]
        public void LodSettingsCoverEveryQualityTier()
        {
            var settings = AssetDatabase.LoadAssetAtPath<SplatRenderSettings>(
                SampleSplat.SettingsPath
            );
            Assert.IsNotNull(settings, $"{SampleSplat.SettingsPath} missing");
            Assert.AreEqual(QualitySettings.names.Length, settings.tiers.Length);
            foreach (var t in settings.tiers)
            {
                Assert.That(t.shOrder, Is.InRange(0, 3));
                Assert.GreaterOrEqual(t.sortEveryNthFrame, 1);
                Assert.Greater(t.maxSplats, 0);
            }
        }
    }
}
