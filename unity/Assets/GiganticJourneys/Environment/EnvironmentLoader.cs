using System.Collections.Generic;
using System.IO;
using GaussianSplatting.Runtime;
using GiganticJourneys.Movement;
using GiganticJourneys.Splats;
using UnityEngine;

namespace GiganticJourneys.Environments
{
    /// <summary>
    /// Plays one environment package (M1-GAME-01): loads and checks it
    /// (<see cref="EnvironmentPackage"/>), then builds the scene under this transform: the
    /// splat, the collision mesh, the spawn pose, the summit beacon, the vista sparkles and the
    /// (hidden until selected) route footprints, all in the package's A-unit frame.
    /// <para>Splat and collision mesh: a bundled <see cref="GaussianSplatAsset"/> and
    /// <see cref="Mesh"/> are used when assigned (the spike/dev path). Decoding the package's
    /// <c>.spz</c> / <c>.glb</c> at runtime is not built yet (needs a runtime splat-asset
    /// builder and a glTF importer package); without the bundled assets the loader logs that
    /// once and still places everything else.</para>
    /// </summary>
    public sealed class EnvironmentLoader : MonoBehaviour
    {
        public const string MarkerShaderResource = "GJ/OnTopMarker";
        public static readonly Color BeaconColor = new Color(1f, 0.824f, 0.478f, 0.75f); // accent.amberLight
        public static readonly Color MarkerColor = new Color(0.961f, 0.937f, 0.902f, 0.35f); // paper.cream, faint

        [Tooltip("Directory holding environment_spec.json and the files its assets block names.")]
        public string packageDirectory;

        [Tooltip(
            "Check traversal_graph.movement.config_sha256 against StreamingAssets/movement.json."
        )]
        public bool verifyMovementConfig = true;

        [Tooltip("Load on Start (play mode).")]
        public bool loadOnStart = true;

        [Header("Bundled assets (dev path until runtime .spz/.glb decode lands)")]
        public GaussianSplatAsset splatAsset;
        public SplatRenderSettings splatSettings;
        public Mesh collisionMesh;

        [Header("Goal elements (DESIGN_SYSTEM §1)")]
        [Tooltip("Player setting; on by default (DESIGN_SYSTEM §1 consistency note).")]
        public bool summitBeam = true;
        public float beamWidthA = 1.2f;
        public float beamHeightA = 120f;
        public float sparkleSizeA = 3f;
        public float footprintSpacingA = 2.5f;

        public EnvironmentPackage Package { get; private set; }
        public Transform Spawn { get; private set; }
        public Transform Beacon { get; private set; }
        public Transform RouteRoot { get; private set; }
        public IReadOnlyList<Transform> VistaMarkers => _vistas;
        public GaussianSplatRenderer SplatRenderer { get; private set; }
        public MeshCollider Collision { get; private set; }
        public string SelectedRouteId { get; private set; }

        readonly List<Transform> _vistas = new List<Transform>();
        Transform _root;
        Material _beamMat;
        Material _sparkleMat;
        Material _footMat;
        Mesh _quad;

        void Start()
        {
            if (loadOnStart && Application.isPlaying && !string.IsNullOrEmpty(packageDirectory))
                Load(packageDirectory);
        }

        void OnDestroy()
        {
            Unload();
        }

        /// <summary>The sha256 of the movement.json this build shipped, or null if absent.</summary>
        public static string ShippedMovementSha()
        {
            var path = MovementConfigLoader.DefaultPath;
            return File.Exists(path) ? EnvironmentPackage.Sha256File(path) : null;
        }

        /// <summary>Loads <paramref name="directory"/> and builds the scene (replacing any previous one).</summary>
        public EnvironmentPackage Load(string directory)
        {
            Unload();
            string sha = null;
            if (verifyMovementConfig)
            {
                sha = ShippedMovementSha();
                if (sha == null)
                    throw new EnvironmentPackageException(
                        "StreamingAssets/movement.json missing; cannot verify the package"
                    );
            }
            Package = EnvironmentPackage.Load(directory, sha);
            packageDirectory = directory;
            Build();
            return Package;
        }

        public void Unload()
        {
            if (_root != null)
                DestroyObj(_root.gameObject);
            _root = null;
            _vistas.Clear();
            Spawn = Beacon = RouteRoot = null;
            SplatRenderer = null;
            Collision = null;
            SelectedRouteId = null;
            foreach (var o in new Object[] { _beamMat, _sparkleMat, _footMat, _quad })
            {
                if (o != null)
                    DestroyObj(o);
            }
            _beamMat = _sparkleMat = _footMat = null;
            _quad = null;
            Package = null;
        }

        /// <summary>Shows the footprints of <paramref name="routeId"/>; null hides them (default: off for explorers).</summary>
        public void SelectRoute(string routeId)
        {
            if (RouteRoot == null)
                return;
            for (var i = RouteRoot.childCount - 1; i >= 0; i--)
                DestroyObj(RouteRoot.GetChild(i).gameObject);
            SelectedRouteId = null;
            if (string.IsNullOrEmpty(routeId) || Package.Routes.Find(r => r.Id == routeId) == null)
                return;
            SelectedRouteId = routeId;
            var marks = GoalPlacement.Footprints(
                GoalPlacement.RoutePolyline(Package, routeId),
                footprintSpacingA
            );
            for (var i = 0; i < marks.Count; i++)
            {
                var (pos, rot, left) = marks[i];
                var side = rot * Vector3.right * (left ? -0.25f : 0.25f);
                var f = Marker(
                    $"footprint-{i}",
                    RouteRoot,
                    _footMat,
                    pos + side + Vector3.up * 0.02f
                );
                f.localRotation = rot * Quaternion.Euler(90f, 0f, 0f); // lie flat, toe along the route
                f.localScale = new Vector3(0.45f, 0.8f, 1f);
            }
        }

        /// <summary>Turns the summit beam on or off (player setting).</summary>
        public void SetSummitBeam(bool on)
        {
            summitBeam = on;
            if (Beacon != null)
                Beacon.gameObject.SetActive(on);
        }

        void Build()
        {
            var p = Package;
            _root = new GameObject($"Environment {p.EnvironmentId}").transform;
            _root.SetParent(transform, false);

            var shader = Resources.Load<Shader>(MarkerShaderResource);
            _beamMat = MarkerMaterial(shader, BeaconColor, 0, 1);
            _sparkleMat = MarkerMaterial(shader, BeaconColor, 1, 2);
            _footMat = MarkerMaterial(shader, MarkerColor, 2, 0);
            _quad = BuildQuad();

            BuildSplat(p);
            BuildCollision(p);

            Spawn = new GameObject("Spawn").transform;
            Spawn.SetParent(_root, false);
            Spawn.localPosition = p.SpawnPosition;
            Spawn.localRotation = GoalPlacement.SpawnRotation(p);

            // The beam stands on the summit and rises; the quad's pivot is its bottom edge.
            Beacon = Marker("SummitBeacon", _root, _beamMat, p.SummitPosition);
            Beacon.localScale = new Vector3(beamWidthA, beamHeightA, 1f);
            Beacon.gameObject.SetActive(summitBeam);

            var vistaRoot = new GameObject("Vistas").transform;
            vistaRoot.SetParent(_root, false);
            foreach (var v in p.Vistas)
            {
                var s = Marker(
                    v.Id,
                    vistaRoot,
                    _sparkleMat,
                    v.Position + Vector3.up * (sparkleSizeA * 0.25f)
                );
                s.localScale = new Vector3(sparkleSizeA, sparkleSizeA, 1f);
                _vistas.Add(s);
            }

            RouteRoot = new GameObject("Route").transform;
            RouteRoot.SetParent(_root, false);
        }

        void BuildSplat(EnvironmentPackage p)
        {
            if (splatAsset == null)
            {
                Debug.Log(
                    $"[GJ-ENV] {p.Assets["splat"]}: runtime .spz decode not built yet; assign a bundled GaussianSplatAsset to draw the splat"
                );
                return;
            }
            var go = new GameObject("Splat");
            go.transform.SetParent(_root, false);
            go.SetActive(false); // configure before OnEnable
            SplatRenderer = go.AddComponent<GaussianSplatRenderer>();
            SplatRenderer.m_Asset = splatAsset;
            if (splatSettings != null)
                go.AddComponent<SplatRenderSettingsApplier>().settings = splatSettings;
            go.SetActive(true);
        }

        void BuildCollision(EnvironmentPackage p)
        {
            if (collisionMesh == null)
            {
                Debug.Log(
                    $"[GJ-ENV] {p.Assets["collision_mesh"]}: runtime .glb import not built yet; assign a bundled collision Mesh"
                );
                return;
            }
            var go = new GameObject("Collision");
            go.transform.SetParent(_root, false);
            Collision = go.AddComponent<MeshCollider>();
            Collision.sharedMesh = collisionMesh;
        }

        Transform Marker(string name, Transform parent, Material mat, Vector3 localPos)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.AddComponent<MeshFilter>().sharedMesh = _quad;
            var r = go.AddComponent<MeshRenderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            return go.transform;
        }

        static Material MarkerMaterial(Shader shader, Color color, int shape, int billboard)
        {
            if (shader == null)
                return null;
            var m = new Material(shader) { hideFlags = HideFlags.DontSave };
            m.SetColor("_Color", color);
            m.SetFloat("_Shape", shape);
            m.SetFloat("_Billboard", billboard);
            return m;
        }

        // Unit quad, x in [-0.5, 0.5], y in [0, 1] (pivot at the bottom edge, so the beam
        // stands on the summit), with generous bounds so the billboard never culls early.
        static Mesh BuildQuad()
        {
            var m = new Mesh { name = "GJ marker quad", hideFlags = HideFlags.DontSave };
            m.SetVertices(
                new List<Vector3>
                {
                    new Vector3(-0.5f, 0f, 0f),
                    new Vector3(0.5f, 0f, 0f),
                    new Vector3(0.5f, 1f, 0f),
                    new Vector3(-0.5f, 1f, 0f),
                }
            );
            m.SetUVs(
                0,
                new List<Vector2>
                {
                    new Vector2(0, 0),
                    new Vector2(1, 0),
                    new Vector2(1, 1),
                    new Vector2(0, 1),
                }
            );
            m.SetTriangles(new[] { 0, 2, 1, 0, 3, 2 }, 0);
            m.bounds = new Bounds(new Vector3(0f, 0.5f, 0f), Vector3.one * 2f);
            return m;
        }

        static void DestroyObj(Object o)
        {
            if (Application.isPlaying)
                Destroy(o);
            else
                DestroyImmediate(o);
        }
    }
}
