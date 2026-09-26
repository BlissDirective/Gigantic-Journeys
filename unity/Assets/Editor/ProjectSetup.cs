using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace GiganticJourneys.EditorTools
{
    /// <summary>
    /// Idempotent project configuration (unity/README.md, ticket M0-UNITY-01):
    /// identity, iOS Metal + IL2CPP, one URP pipeline asset per quality tier,
    /// the boot scene and EditorBuildSettings. Run headless with
    /// <c>-batchmode -nographics -quit -executeMethod GiganticJourneys.EditorTools.ProjectSetup.Run</c>
    /// or from the menu Gigantic Journeys/Apply Project Setup.
    /// </summary>
    public static class ProjectSetup
    {
        const string SettingsFolder = "Assets/Settings";

        // Quality tiers, lowest first. Index 2 (High) is the iOS default;
        // runtime tier selection for older iPhones is later gameplay work.
        static readonly Tier[] Tiers =
        {
            new Tier("Low", 0.75f, 1, 25f, false, 1),
            new Tier("Medium", 0.9f, 2, 40f, true, 2),
            new Tier("High", 1f, 4, 60f, true, 4),
        };

        [MenuItem("Gigantic Journeys/Apply Project Setup")]
        public static void Apply()
        {
            ApplyIdentity();
            var assets = EnsurePipelineAssets();
            ApplyQualityTiers(assets);
            GraphicsSettings.defaultRenderPipeline = assets[assets.Length - 1];
            EnsureBootScene();
            AssetDatabase.SaveAssets();
            Debug.Log("[ProjectSetup] applied: identity, iOS Metal/IL2CPP, URP tiers, boot scene");
        }

        /// <summary>Batchmode entry point; exits non-zero on failure.</summary>
        public static void Run()
        {
            try
            {
                Apply();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                EditorApplication.Exit(1);
            }
        }

        static void ApplyIdentity()
        {
            PlayerSettings.companyName = ProjectIdentity.CompanyName;
            PlayerSettings.productName = ProjectIdentity.ProductName;
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, ProjectIdentity.BundleId);
            PlayerSettings.SetApplicationIdentifier(
                NamedBuildTarget.Android,
                ProjectIdentity.BundleId
            );

            // iOS: the v1 ship target (AUTH #003).
            PlayerSettings.SetScriptingBackend(
                NamedBuildTarget.iOS,
                ScriptingImplementation.IL2CPP
            );
            // Metal is the only iOS graphics API in Unity 6. Unity normalizes iOS to
            // "automatic" whenever iOS is the active target, so keep it automatic
            // (resolves to Metal only; the EditMode smoke test asserts this).
            PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.iOS, true);
            PlayerSettings.stripEngineCode = true;

            // Android: buildable on demand, not shipped in v1.
            PlayerSettings.SetScriptingBackend(
                NamedBuildTarget.Android,
                ScriptingImplementation.IL2CPP
            );
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;

            // Input System package only (activeInputHandler: 0 old, 1 new, 2 both).
            var player = new SerializedObject(
                AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]
            );
            var handler = player.FindProperty("activeInputHandler");
            if (handler != null && handler.intValue != 1)
            {
                handler.intValue = 1;
                player.ApplyModifiedPropertiesWithoutUndo();
            }
        }

        static UniversalRenderPipelineAsset[] EnsurePipelineAssets()
        {
            if (!AssetDatabase.IsValidFolder(SettingsFolder))
            {
                AssetDatabase.CreateFolder("Assets", "Settings");
            }

            var postProcess = AssetDatabase.LoadAssetAtPath<PostProcessData>(
                "Packages/com.unity.render-pipelines.universal/Runtime/Data/PostProcessData.asset"
            );

            var result = new UniversalRenderPipelineAsset[Tiers.Length];
            for (var i = 0; i < Tiers.Length; i++)
            {
                var tier = Tiers[i];
                var rendererPath = $"{SettingsFolder}/URP-{tier.Name}-Renderer.asset";
                var pipelinePath = $"{SettingsFolder}/URP-{tier.Name}.asset";

                var renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rendererPath);
                if (renderer == null)
                {
                    renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
                    AssetDatabase.CreateAsset(renderer, rendererPath);
                }
                if (renderer.postProcessData == null && postProcess != null)
                {
                    renderer.postProcessData = postProcess;
                    EditorUtility.SetDirty(renderer);
                }

                var pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(
                    pipelinePath
                );
                if (pipeline == null)
                {
                    pipeline = UniversalRenderPipelineAsset.Create(renderer);
                    AssetDatabase.CreateAsset(pipeline, pipelinePath);
                }
                pipeline.renderScale = tier.RenderScale;
                pipeline.msaaSampleCount = tier.Msaa;
                pipeline.shadowDistance = tier.ShadowDistance;
                pipeline.supportsHDR = tier.Hdr;
                pipeline.shadowCascadeCount = tier.ShadowCascades;
                EditorUtility.SetDirty(pipeline);
                result[i] = pipeline;
            }
            AssetDatabase.SaveAssets();
            return result;
        }

        static void ApplyQualityTiers(UniversalRenderPipelineAsset[] assets)
        {
            var quality = new SerializedObject(
                AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/QualitySettings.asset")[0]
            );
            var levels = quality.FindProperty("m_QualitySettings");
            var wanted = Tiers.Select(t => t.Name).ToArray();

            // Keep only the Low/Medium/High levels, in that order.
            for (var i = levels.arraySize - 1; i >= 0; i--)
            {
                var name = levels
                    .GetArrayElementAtIndex(i)
                    .FindPropertyRelative("name")
                    .stringValue;
                if (!wanted.Contains(name))
                {
                    levels.DeleteArrayElementAtIndex(i);
                }
            }
            for (var i = 0; i < wanted.Length; i++)
            {
                var found = -1;
                for (var j = 0; j < levels.arraySize; j++)
                {
                    var n = levels.GetArrayElementAtIndex(j).FindPropertyRelative("name");
                    if (n.stringValue == wanted[i])
                    {
                        found = j;
                    }
                }
                if (found < 0)
                {
                    levels.InsertArrayElementAtIndex(levels.arraySize);
                    found = levels.arraySize - 1;
                    levels.GetArrayElementAtIndex(found).FindPropertyRelative("name").stringValue =
                        wanted[i];
                }
                if (found != i)
                {
                    levels.MoveArrayElement(found, i);
                }
                levels
                    .GetArrayElementAtIndex(i)
                    .FindPropertyRelative("customRenderPipeline")
                    .objectReferenceValue = assets[i];
            }

            var top = wanted.Length - 1;
            var perPlatform = quality.FindProperty("m_PerPlatformDefaultQuality");
            for (var i = 0; i < perPlatform.arraySize; i++)
            {
                var entry = perPlatform.GetArrayElementAtIndex(i);
                entry.FindPropertyRelative("second").intValue = top;
            }
            quality.FindProperty("m_CurrentQuality").intValue = top;
            quality.ApplyModifiedPropertiesWithoutUndo();
        }

        static void EnsureBootScene()
        {
            var path = ProjectIdentity.BootScenePath;
            if (!File.Exists(path))
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                var scene = EditorSceneManager.NewScene(
                    NewSceneSetup.DefaultGameObjects,
                    NewSceneMode.Single
                );
                if (!EditorSceneManager.SaveScene(scene, path))
                {
                    throw new InvalidOperationException($"could not save {path}");
                }
                AssetDatabase.Refresh();
            }

            var others = EditorBuildSettings.scenes.Where(s => s.path != path);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(path, true) }
                .Concat(others)
                .ToArray();
        }

        readonly struct Tier
        {
            public readonly string Name;
            public readonly float RenderScale;
            public readonly int Msaa;
            public readonly float ShadowDistance;
            public readonly bool Hdr;
            public readonly int ShadowCascades;

            public Tier(
                string name,
                float renderScale,
                int msaa,
                float shadowDistance,
                bool hdr,
                int shadowCascades
            )
            {
                Name = name;
                RenderScale = renderScale;
                Msaa = msaa;
                ShadowDistance = shadowDistance;
                Hdr = hdr;
                ShadowCascades = shadowCascades;
            }
        }
    }
}
