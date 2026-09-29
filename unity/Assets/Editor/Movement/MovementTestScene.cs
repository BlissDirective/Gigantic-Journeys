using System;
using System.Linq;
using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Controller;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.EditorTools
{
    /// <summary>
    /// Builds <c>Assets/Scenes/MovementTest.unity</c>, the flat test scene for the M0 capsule
    /// controller (ticket M0-UNITY-03): a metric floor with 1 A distance stripes, the capsule
    /// (TraversalController + touch controls), a fixed follow camera and a sun. Idempotent; run
    /// headless with <c>-executeMethod GiganticJourneys.EditorTools.MovementTestScene.Run</c> or
    /// from the menu Gigantic Journeys/Build Movement Test Scene.
    /// </summary>
    public static class MovementTestScene
    {
        public const string ScenePath = "Assets/Scenes/MovementTest.unity";
        const string MaterialFolder = "Assets/GiganticJourneys/Movement/TestScene";

        [MenuItem("Gigantic Journeys/Build Movement Test Scene")]
        public static void Build()
        {
            var config = MovementConfigLoader.LoadFile(MovementConfigLoader.DefaultPath);
            var scale = MovementScale.Create(
                config,
                ProvisionalTuning.Body.DefaultRealHeightMeters,
                ProvisionalTuning.Environment.DefaultScale
            );
            var a = scale.WorldUnitsPerA;

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var floorMat = Material("Floor", new Color(0.42f, 0.40f, 0.37f));
            var stripeMat = Material("Stripe", new Color(0.18f, 0.20f, 0.24f));
            var capsuleMat = Material("Capsule", new Color(0.95f, 0.45f, 0.15f));

            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1f;
            sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.75f, 0.8f, 0.9f);
            RenderSettings.ambientEquatorColor = new Color(0.55f, 0.55f, 0.55f);
            RenderSettings.ambientGroundColor = new Color(0.3f, 0.28f, 0.25f);

            // A 12 m square floor: a room at 1:12 is ~82 A across.
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Floor";
            floor.transform.localScale = new Vector3(1.2f, 1f, 1.2f);
            floor.GetComponent<MeshRenderer>().sharedMaterial = floorMat;

            // Flush distance stripes every 1 A along +Z (no collider: the floor stays flat).
            var stripes = new GameObject("Distance stripes (1 A)").transform;
            for (var i = 1; i <= 40; i++)
            {
                var s = GameObject.CreatePrimitive(PrimitiveType.Cube);
                s.name = $"{i} A";
                UnityEngine.Object.DestroyImmediate(s.GetComponent<BoxCollider>());
                s.transform.SetParent(stripes, false);
                var wide = i % 5 == 0;
                s.transform.localPosition = new Vector3(0f, 0.0005f, i * a);
                s.transform.localScale = new Vector3(
                    wide ? 20f * a : 6f * a,
                    0.001f,
                    wide ? 0.08f * a : 0.04f * a
                );
                s.GetComponent<MeshRenderer>().sharedMaterial = stripeMat;
            }

            var player = new GameObject("Player (capsule)");
            player.AddComponent<CharacterController>();
            var controller = player.AddComponent<TraversalController>();
            var view = player.AddComponent<TouchControlsView>();
            view.Controller = controller;
            var visual = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            visual.name = "Visual";
            UnityEngine.Object.DestroyImmediate(visual.GetComponent<CapsuleCollider>());
            visual.transform.SetParent(player.transform, false);
            var height = scale.ToWorld(config.AvatarHeightA);
            var diameter = 2f * scale.ToWorld(ProvisionalTuning.Body.CapsuleRadiusA);
            visual.transform.localPosition = Vector3.up * (height * 0.5f);
            visual.transform.localScale = new Vector3(diameter, height * 0.5f, diameter);
            visual.GetComponent<MeshRenderer>().sharedMaterial = capsuleMat;
            var nose = GameObject.CreatePrimitive(PrimitiveType.Cube);
            nose.name = "Facing";
            UnityEngine.Object.DestroyImmediate(nose.GetComponent<BoxCollider>());
            nose.transform.SetParent(player.transform, false);
            nose.transform.localPosition = new Vector3(0f, height * 0.75f, diameter * 0.5f);
            nose.transform.localScale = Vector3.one * (diameter * 0.35f);
            nose.GetComponent<MeshRenderer>().sharedMaterial = stripeMat;

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.01f;
            cam.farClipPlane = 100f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.62f, 0.72f, 0.84f);
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(0f, 1.6f * a, -4f * a);
            camGo.transform.rotation = Quaternion.LookRotation(Vector3.forward, Vector3.up);
            var follow = camGo.AddComponent<FollowCamera>();
            follow.Target = controller;
            controller.CameraTransform = camGo.transform;
            // URP additional camera data is added on first render; nothing else to configure.

            EditorSceneManager.SaveScene(scene, ScenePath);
            AddToBuildSettings();
            AssetDatabase.SaveAssets();
            Debug.Log($"[MovementTestScene] built {ScenePath} (1 A = {a:0.0000} m)");
        }

        static Material Material(string name, Color color)
        {
            if (!AssetDatabase.IsValidFolder(MaterialFolder))
                AssetDatabase.CreateFolder("Assets/GiganticJourneys/Movement", "TestScene");
            var path = $"{MaterialFolder}/{name}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null)
            {
                var shader = Shader.Find("Universal Render Pipeline/Lit");
                mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, path);
            }
            mat.SetColor("_BaseColor", color);
            mat.SetFloat("_Smoothness", 0.2f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static void AddToBuildSettings()
        {
            var scenes = EditorBuildSettings.scenes.ToList();
            if (scenes.Any(s => s.path == ScenePath))
                return;
            scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
        }

        /// <summary>Batchmode entry point; exits non-zero on failure.</summary>
        public static void Run()
        {
            try
            {
                Build();
                EditorApplication.Exit(0);
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                EditorApplication.Exit(1);
            }
        }
    }
}
