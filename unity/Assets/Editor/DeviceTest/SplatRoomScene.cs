using System;
using System.IO;
using System.Linq;
using GaussianSplatting.Runtime;
using GiganticJourneys.DeviceTest;
using GiganticJourneys.EditorTools.Splats;
using GiganticJourneys.Movement;
using GiganticJourneys.Movement.Controller;
using GiganticJourneys.Splats;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace GiganticJourneys.EditorTools.DeviceTest
{
    /// <summary>
    /// The internal-debug device-test scene <c>Assets/Scenes/DeviceTest/SplatRoom.unity</c>
    /// (ticket M1-UNITY-01 AT-2/AT-3): the MovementTest character (touch stick, jump, follow
    /// camera) in a reconstructed Gaussian-splat room placed by <c>splat-room.json</c>.
    ///
    /// The scene is deliberately NOT in the committed build list (release builds boot
    /// MovementTest and never contain it); the internal-debug CI lane appends it
    /// (<c>ios_debug_flavor.py add-scene</c>) and fetches the splat into the gitignored
    /// <see cref="ResourcesFolder"/>.
    ///
    /// Batchmode:
    /// <c>-executeMethod GiganticJourneys.EditorTools.DeviceTest.SplatRoomScene.RunBuild</c> (scene),
    /// <c>...RunImport -gjSplatPly &lt;slug&gt;.ply</c> (converts a PLY into the Resources folder, box only),
    /// <c>...RunScreenshot -gjOut &lt;png&gt;</c> (renders the room from the spawn; needs a GPU, e.g. xvfb + Vulkan).
    /// </summary>
    public static class SplatRoomScene
    {
        public const string ScenePath = "Assets/Scenes/DeviceTest/SplatRoom.unity";
        public const string DeviceTestFolder = "Assets/GiganticJourneys/DeviceTest";
        public const string DescriptorPath = DeviceTestFolder + "/splat-room.json";

        /// <summary>Gitignored; filled only by the internal-debug CI lane (or by hand on the box).</summary>
        public const string DownloadFolder = DeviceTestFolder + "/Downloaded";
        public const string ResourcesFolder = DownloadFolder + "/Resources/GJSplatRoom";

        public static SplatRoomDescriptor LoadDescriptor() =>
            SplatRoomDescriptor.Parse(File.ReadAllText(DescriptorPath));

        [MenuItem("Gigantic Journeys/Device Test/Build Splat Room Scene")]
        public static void Build()
        {
            var descriptor = LoadDescriptor();
            var json =
                AssetDatabase.LoadAssetAtPath<TextAsset>(DescriptorPath)
                ?? throw new InvalidOperationException($"{DescriptorPath} is not imported");
            var config = MovementConfigLoader.LoadFile(MovementConfigLoader.DefaultPath);
            var scale = MovementScale.Create(
                config,
                ProvisionalTuning.Body.DefaultRealHeightMeters,
                ProvisionalTuning.Environment.DefaultScale
            );
            var a = scale.WorldUnitsPerA;

            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath) ?? "Assets/Scenes");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.75f, 0.8f, 0.9f);
            RenderSettings.ambientEquatorColor = new Color(0.55f, 0.55f, 0.55f);
            RenderSettings.ambientGroundColor = new Color(0.3f, 0.28f, 0.25f);
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 1f;
            sun.shadows = LightShadows.None; // splats take no shadows; keep the frame cheap
            sun.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            // The splat renderer starts inactive; the loader assigns the asset (when this build
            // has it) and activates it, so a build without the splat still runs cleanly.
            var splatGo = new GameObject("Splat room");
            var renderer = splatGo.AddComponent<GaussianSplatRenderer>();
            SampleSplat.AssignRendererResources(renderer);
            var applier = splatGo.AddComponent<SplatRenderSettingsApplier>();
            applier.settings = SampleSplat.EnsureSettings();
            splatGo.SetActive(false);

            var capsuleMat = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/GiganticJourneys/Movement/TestScene/Capsule.mat"
            );
            var stripeMat = AssetDatabase.LoadAssetAtPath<Material>(
                "Assets/GiganticJourneys/Movement/TestScene/Stripe.mat"
            );
            var player = new GameObject("Player (capsule)");
            player.AddComponent<CharacterController>();
            var controller = player.AddComponent<TraversalController>();
            var view = player.AddComponent<TouchControlsView>();
            view.Controller = controller;
            var height = scale.ToWorld(config.AvatarHeightA);
            var diameter = 2f * scale.ToWorld(ProvisionalTuning.Body.CapsuleRadiusA);
            var visual = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            visual.name = "Visual";
            UnityEngine.Object.DestroyImmediate(visual.GetComponent<CapsuleCollider>());
            visual.transform.SetParent(player.transform, false);
            visual.transform.localPosition = Vector3.up * (height * 0.5f);
            visual.transform.localScale = new Vector3(diameter, height * 0.5f, diameter);
            if (capsuleMat != null)
                visual.GetComponent<MeshRenderer>().sharedMaterial = capsuleMat;
            var nose = GameObject.CreatePrimitive(PrimitiveType.Cube);
            nose.name = "Facing";
            UnityEngine.Object.DestroyImmediate(nose.GetComponent<BoxCollider>());
            nose.transform.SetParent(player.transform, false);
            nose.transform.localPosition = new Vector3(0f, height * 0.75f, diameter * 0.5f);
            nose.transform.localScale = Vector3.one * (diameter * 0.35f);
            if (stripeMat != null)
                nose.GetComponent<MeshRenderer>().sharedMaterial = stripeMat;
            player.transform.SetPositionAndRotation(
                descriptor.Spawn,
                Quaternion.Euler(0f, descriptor.spawnYawDeg, 0f)
            );

            var camGo = new GameObject("Main Camera") { tag = "MainCamera" };
            var cam = camGo.AddComponent<Camera>();
            cam.nearClipPlane = 0.01f;
            cam.farClipPlane = 100f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.11f, 0.09f, 0.07f); // warm dark: pruned gaps read as shadow
            // AT-3: the splat pass is an unsafe render-graph pass, so MSAA/HDR camera targets get
            // stored and reloaded around it every frame (4x MSAA HDR at 2532x1170 on the A15).
            // The splats bring their own soft edges; the capsule can do without MSAA here.
            cam.allowMSAA = false;
            cam.allowHDR = false;
            camGo.AddComponent<AudioListener>();
            PlaceFollowCamera(camGo.transform, player.transform, a);
            var follow = camGo.AddComponent<FollowCamera>();
            follow.Target = controller;
            controller.CameraTransform = camGo.transform;

            // A plain dark floor under the splats: pruning removed the floaters that used to fake
            // the floor at grazing angles, so this fills those gaps and grounds the character.
            var floor = GameObject.CreatePrimitive(PrimitiveType.Quad);
            floor.name = "Floor (visual)";
            UnityEngine.Object.DestroyImmediate(floor.GetComponent<MeshCollider>());
            var walkLo = descriptor.WalkMin;
            var walkHi = descriptor.WalkMax;
            var mid = (walkLo + walkHi) * 0.5f;
            floor.transform.SetPositionAndRotation(
                new Vector3(mid.x, FloorVisualDepth, mid.y),
                Quaternion.Euler(90f, 0f, 0f)
            );
            floor.transform.localScale = new Vector3(
                walkHi.x - walkLo.x + 2f,
                walkHi.y - walkLo.y + 2f,
                1f
            );
            var floorRenderer = floor.GetComponent<MeshRenderer>();
            floorRenderer.sharedMaterial = FloorMaterial();
            floorRenderer.shadowCastingMode = ShadowCastingMode.Off;

            var loader = new GameObject("Splat room loader").AddComponent<SplatRoomLoader>();
            loader.descriptorJson = json;
            loader.splatRenderer = renderer;
            loader.player = player.transform;

            EditorSceneManager.SaveScene(scene, ScenePath);
            AssetDatabase.SaveAssets();
            Debug.Log(
                $"[SplatRoomScene] built {ScenePath} for {descriptor.slug} (1 A = {a:0.0000} m)"
            );
        }

        /// <summary>
        /// The visual floor sits below the walkable y = 0 so the reconstructed floor splats (which
        /// scatter a little around the fitted plane) stay in front of it; it only shows through gaps.
        /// </summary>
        public const float FloorVisualDepth = -0.25f;

        public const string FloorMaterialPath = "Assets/GiganticJourneys/DeviceTest/RoomFloor.mat";

        static Material FloorMaterial()
        {
            var mat = AssetDatabase.LoadAssetAtPath<Material>(FloorMaterialPath);
            if (mat != null)
                return mat;
            mat = new Material(
                Shader.Find("Universal Render Pipeline/Lit")
                    ?? throw new InvalidOperationException("URP Lit shader not found")
            )
            {
                name = "RoomFloor",
            };
            mat.SetColor("_BaseColor", new Color(0.16f, 0.13f, 0.1f));
            mat.SetFloat("_Smoothness", 0f);
            AssetDatabase.CreateAsset(mat, FloorMaterialPath);
            return mat;
        }

        static void PlaceFollowCamera(Transform cam, Transform player, float a)
        {
            var back = player.rotation * Vector3.back;
            cam.position = player.position + back * (4f * a) + Vector3.up * (1.6f * a);
            cam.rotation = Quaternion.LookRotation(
                player.position
                    + Vector3.up * (0.8f * a)
                    - cam.position
                    + player.forward * (4f * a),
                Vector3.up
            );
        }

        /// <summary>Converts a 3DGS PLY (named &lt;slug&gt;.ply) into <see cref="ResourcesFolder"/>.</summary>
        public static GaussianSplatAsset Import(string plyPath)
        {
            var descriptor = LoadDescriptor();
            var expected = Path.GetFileName(descriptor.resource);
            if (Path.GetFileNameWithoutExtension(plyPath) != expected)
                throw new ArgumentException(
                    $"PLY must be named {expected}.ply to match {DescriptorPath}"
                );
            EnsureFolder(ResourcesFolder);
            var asset = SampleSplat.ConvertPly(plyPath, ResourcesFolder);
            if (asset == null)
                throw new InvalidOperationException("conversion produced no asset");
            if (asset.splatCount != descriptor.splatCount)
                throw new InvalidOperationException(
                    $"{asset.splatCount} splats, descriptor says {descriptor.splatCount}"
                );
            Debug.Log(
                $"[SplatRoomScene] imported {asset.splatCount} splats into {ResourcesFolder}"
            );
            return asset;
        }

        static void EnsureFolder(string path)
        {
            var parts = path.Split('/');
            var cur = parts[0];
            for (var i = 1; i < parts.Length; i++)
            {
                var next = cur + "/" + parts[i];
                if (!AssetDatabase.IsValidFolder(next))
                    AssetDatabase.CreateFolder(cur, parts[i]);
                cur = next;
            }
        }

        /// <summary>
        /// Renders the room in edit mode at the iPhone's aspect (19.5:9): the follow camera at the
        /// spawn, the follow camera mid-hall facing the side wall, and a high overview, side by
        /// side, into <paramref name="outPng"/>. Returns the splat coverage
        /// (fraction of pixels that differ from a splat-off baseline) of the follow view.
        /// </summary>
        public static float Screenshot(string outPng, int width = 780, int height = 360)
        {
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null)
                throw new InvalidOperationException(
                    "no graphics device; run under xvfb with -force-vulkan"
                );
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            var descriptor = LoadDescriptor();
            var asset =
                AssetDatabase.LoadAssetAtPath<GaussianSplatAsset>(
                    $"{ResourcesFolder}/{Path.GetFileName(descriptor.resource)}.asset"
                ) ?? throw new InvalidOperationException($"no splat asset under {ResourcesFolder}");
            var loader = UnityEngine.Object.FindFirstObjectByType<SplatRoomLoader>();
            var r = loader.splatRenderer;
            r.transform.SetLocalPositionAndRotation(descriptor.Position, descriptor.Rotation);
            r.transform.localScale = descriptor.Scale;
            r.m_Asset = asset;
            r.gameObject.SetActive(true);
            var cam = Camera.main;
            var player = loader.player;
            var a = MovementScale
                .Create(
                    MovementConfigLoader.LoadFile(MovementConfigLoader.DefaultPath),
                    ProvisionalTuning.Body.DefaultRealHeightMeters,
                    ProvisionalTuning.Environment.DefaultScale
                )
                .WorldUnitsPerA;

            PlaceFollowCamera(cam.transform, player, a);
            cam.fieldOfView = 60f;
            r.enabled = false;
            var baseline = Render(cam, width, height);
            r.enabled = true;
            Render(cam, width, height); // primes the sort
            var follow = Render(cam, width, height);
            var coverage = Coverage(follow, baseline);

            // Device-like second view: mid-hall, turned toward the side wall and columns.
            var spawnPos = player.position;
            var spawnRot = player.rotation;
            player.SetPositionAndRotation(
                new Vector3(0.8f, spawnPos.y, 1.5f),
                Quaternion.Euler(0f, 90f, 0f)
            );
            PlaceFollowCamera(cam.transform, player, a);
            Render(cam, width, height);
            var side = Render(cam, width, height);
            player.SetPositionAndRotation(spawnPos, spawnRot);

            // Overview: above and behind the spawn, looking down the room.
            var back = player.rotation * Vector3.back;
            cam.transform.position = player.position + back * 1.5f + Vector3.up * 1.6f;
            cam.transform.rotation = Quaternion.LookRotation(
                player.position + player.forward * 4f - cam.transform.position,
                Vector3.up
            );
            Render(cam, width, height);
            var overview = Render(cam, width, height);

            var sheet = new Texture2D(width * 3, height, TextureFormat.RGB24, false);
            sheet.SetPixels(0, 0, width, height, follow.GetPixels());
            sheet.SetPixels(width, 0, width, height, side.GetPixels());
            sheet.SetPixels(width * 2, 0, width, height, overview.GetPixels());
            sheet.Apply();
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPng)) ?? ".");
            File.WriteAllBytes(outPng, sheet.EncodeToPNG());
            foreach (var t in new[] { baseline, follow, side, overview, sheet })
                UnityEngine.Object.DestroyImmediate(t);
            Debug.Log(
                $"[SplatRoomScene] screenshot {outPng}: follow-view splat coverage {coverage:P1} on {SystemInfo.graphicsDeviceType}"
            );
            return coverage;
        }

        static float Coverage(Texture2D a, Texture2D b)
        {
            var pa = a.GetPixels32();
            var pb = b.GetPixels32();
            var changed = 0;
            for (var i = 0; i < pa.Length; i++)
            {
                if (
                    Math.Abs(pa[i].r - pb[i].r)
                        + Math.Abs(pa[i].g - pb[i].g)
                        + Math.Abs(pa[i].b - pb[i].b)
                    > 24
                )
                    changed++;
            }
            return (float)changed / pa.Length;
        }

        static Texture2D Render(Camera cam, int width, int height)
        {
            var rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            var tex = new Texture2D(width, height, TextureFormat.RGB24, false);
            var prevTarget = cam.targetTexture;
            var prevActive = RenderTexture.active;
            try
            {
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                tex.Apply();
            }
            finally
            {
                cam.targetTexture = prevTarget;
                RenderTexture.active = prevActive;
                rt.Release();
                UnityEngine.Object.DestroyImmediate(rt);
            }
            return tex;
        }

        static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            var i = Array.IndexOf(args, name);
            return i >= 0 && i + 1 < args.Length ? args[i + 1] : null;
        }

        static void Batch(Action body)
        {
            var code = 0;
            try
            {
                body();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
                code = 1;
            }
            EditorApplication.Exit(code);
        }

        public static void RunBuild() => Batch(Build);

        public static void RunImport() =>
            Batch(() =>
                Import(
                    Arg("-gjSplatPly") ?? throw new ArgumentException("-gjSplatPly <path> required")
                )
            );

        public static void RunScreenshot() =>
            Batch(() =>
            {
                var coverage = Screenshot(Arg("-gjOut") ?? "Temp/splat-check.png");
                if (coverage < 0.05f)
                    throw new InvalidOperationException(
                        $"splat covers only {coverage:P1} of the follow view"
                    );
            });

        /// <summary>True when the committed build list contains the device-test scene (it must not).</summary>
        public static bool InCommittedBuildList() =>
            EditorBuildSettings.scenes.Any(s => s.path == ScenePath);
    }
}
