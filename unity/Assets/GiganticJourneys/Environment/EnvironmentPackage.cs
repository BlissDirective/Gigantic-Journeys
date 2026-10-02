using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using GiganticJourneys.Movement;
using UnityEngine;

namespace GiganticJourneys.Environments
{
    /// <summary>Thrown when an environment package fails a loader check (M1-GAME-01).</summary>
    public sealed class EnvironmentPackageException : Exception
    {
        public EnvironmentPackageException(string message)
            : base(message) { }
    }

    /// <summary>
    /// One reconstructed environment package, parsed and checked per
    /// <c>services/packages/CONTRACT.md</c> (reference: <c>services/packages/package.py</c>):
    /// the <c>environment_spec.json</c> manifest, the scene and traversal graphs it names, and
    /// the binary assets' presence. Positions are environment-local A units, +y up,
    /// left-handed: Unity's own frame, consumed with no conversion.
    /// </summary>
    public sealed class EnvironmentPackage
    {
        public const string ManifestName = "environment_spec.json";
        public const string SchemaVersion = "1.0.0";
        static readonly string[] AssetKeys =
        {
            "splat",
            "collision_mesh",
            "scene_graph",
            "traversal_graph",
            "thumbnail",
        };

        public sealed class Node
        {
            public string Id;
            public string SurfaceId;
            public Vector3 Position;
            public string Kind;
            public bool Plantable;
        }

        public sealed class Edge
        {
            public string Id;
            public string From;
            public string To;
            public string Verb;
            public string Tier;
        }

        public sealed class Beat
        {
            public int Index;
            public string Role;
            public List<string> EdgeIds = new List<string>();
        }

        public sealed class Route
        {
            public string Id;
            public int Rank;
            public string RelativeDifficulty;
            public List<Beat> Beats = new List<Beat>();
        }

        public sealed class Vista
        {
            public string Id;
            public string NodeId;
            public Vector3 Position;
            public Vector3 LookAt;
            public string AccessTier;
        }

        public sealed class SurfaceMesh
        {
            public string SurfaceId;
            public int Submesh;
            public int TriangleStart;
            public int TriangleCount;
        }

        public string Directory { get; private set; }
        public string EnvironmentId { get; private set; }
        public string CaptureMode { get; private set; }

        /// <summary>Package-relative asset names from the manifest's <c>assets</c> block.</summary>
        public IReadOnlyDictionary<string, string> Assets => _assets;

        public string SpawnNodeId { get; private set; }
        public Vector3 SpawnPosition { get; private set; }
        public float SpawnFacingDeg { get; private set; }
        public string SummitNodeId { get; private set; }
        public Vector3 SummitPosition { get; private set; }
        public bool SummitTruePeak { get; private set; }
        public float SummitHeightA { get; private set; }
        public string MovementConfigSha256 { get; private set; }
        public Bounds SceneBounds { get; private set; }

        public readonly List<Route> Routes = new List<Route>();
        public readonly List<Vista> Vistas = new List<Vista>();
        public readonly Dictionary<string, Node> Nodes = new Dictionary<string, Node>();
        public readonly Dictionary<string, Edge> Edges = new Dictionary<string, Edge>();
        public readonly List<SurfaceMesh> SurfaceMeshes = new List<SurfaceMesh>();

        readonly Dictionary<string, string> _assets = new Dictionary<string, string>();

        /// <summary>Absolute path of an asset named in the manifest (e.g. "splat").</summary>
        public string AssetPath(string key) => Path.Combine(Directory, _assets[key]);

        /// <summary>SHA-256 (lowercase hex) of a file's bytes, as services/traversal/graph.py.</summary>
        public static string Sha256File(string path)
        {
            using var sha = SHA256.Create();
            var hash = sha.ComputeHash(File.ReadAllBytes(path));
            return BitConverter.ToString(hash).Replace("-", string.Empty).ToLowerInvariant();
        }

        /// <summary>
        /// Loads and checks the package in <paramref name="directory"/>. When
        /// <paramref name="movementConfigSha256"/> is given the traversal graph must have been
        /// generated against that exact movement.json (CONTRACT step 3).
        /// </summary>
        public static EnvironmentPackage Load(string directory, string movementConfigSha256 = null)
        {
            var p = new EnvironmentPackage { Directory = directory };
            var manifestPath = Path.Combine(directory, ManifestName);
            if (!File.Exists(manifestPath))
                throw new EnvironmentPackageException($"{ManifestName} missing in {directory}");
            var spec = ReadDoc(manifestPath);
            p.EnvironmentId = Str(spec, "environment_id");
            p.CaptureMode = Str(spec, "capture_mode");

            var assets = Obj(spec, "assets");
            foreach (var key in AssetKeys)
            {
                var name = Str(assets, key);
                if (!IsPackageRelative(name))
                    throw new EnvironmentPackageException(
                        $"assets.{key} '{name}' is not a package-relative file name"
                    );
                if (!File.Exists(Path.Combine(directory, name)))
                    throw new EnvironmentPackageException(
                        $"assets.{key} '{name}' missing from the package"
                    );
                p._assets[key] = name;
            }

            var spawn = Obj(spec, "spawn");
            p.SpawnNodeId = Str(spawn, "node_id");
            p.SpawnPosition = Vec(spawn, "position");
            p.SpawnFacingDeg = Num(spawn, "facing_deg");
            var summit = Obj(spec, "summit");
            p.SummitNodeId = Str(summit, "node_id");
            p.SummitPosition = Vec(summit, "position");
            p.SummitHeightA = Num(summit, "height_A");
            p.SummitTruePeak = (bool)Get(summit, "true_peak");

            foreach (var r in Arr(spec, "routes"))
            {
                var ro = AsObj(r, "routes[]");
                var route = new Route
                {
                    Id = Str(ro, "id"),
                    Rank = (int)Num(ro, "rank"),
                    RelativeDifficulty = Str(ro, "relative_difficulty"),
                };
                foreach (var b in Arr(ro, "beats"))
                {
                    var bo = AsObj(b, "beats[]");
                    var beat = new Beat { Index = (int)Num(bo, "index"), Role = Str(bo, "role") };
                    foreach (var e in Arr(bo, "edge_ids"))
                        beat.EdgeIds.Add((string)e);
                    route.Beats.Add(beat);
                }
                p.Routes.Add(route);
            }
            foreach (var v in Arr(spec, "vistas"))
            {
                var vo = AsObj(v, "vistas[]");
                p.Vistas.Add(
                    new Vista
                    {
                        Id = Str(vo, "id"),
                        NodeId = Str(vo, "node_id"),
                        Position = Vec(vo, "position"),
                        LookAt = Vec(vo, "look_at"),
                        AccessTier = Str(vo, "access_tier"),
                    }
                );
            }

            var scene = ReadDoc(p.AssetPath("scene_graph"));
            var traversal = ReadDoc(p.AssetPath("traversal_graph"));
            foreach (
                var (doc, label) in new[] { (scene, "scene_graph"), (traversal, "traversal_graph") }
            )
            {
                if (Str(doc, "environment_id") != p.EnvironmentId)
                    throw new EnvironmentPackageException(
                        $"{label}.environment_id differs from the manifest"
                    );
            }
            var frame = Obj(scene, "frame");
            if (
                Str(frame, "units") != "A"
                || Str(frame, "up") != "+y"
                || Str(frame, "handedness") != "left"
            )
                throw new EnvironmentPackageException(
                    "scene_graph.frame must be A units, +y up, left-handed"
                );
            var bounds = Obj(scene, "bounds");
            var bmin = Vec(bounds, "min");
            var bmax = Vec(bounds, "max");
            var sceneBounds = new Bounds();
            sceneBounds.SetMinMax(bmin, bmax);
            p.SceneBounds = sceneBounds;
            foreach (var s in Arr(scene, "surfaces"))
            {
                var so = AsObj(s, "surfaces[]");
                if (!so.TryGetValue("mesh", out var m) || m == null)
                    continue;
                var mo = AsObj(m, "surface.mesh");
                p.SurfaceMeshes.Add(
                    new SurfaceMesh
                    {
                        SurfaceId = Str(so, "id"),
                        Submesh = (int)Num(mo, "submesh"),
                        TriangleStart = (int)Num(mo, "triangle_start"),
                        TriangleCount = (int)Num(mo, "triangle_count"),
                    }
                );
            }

            p.MovementConfigSha256 = Str(Obj(traversal, "movement"), "config_sha256");
            if (
                movementConfigSha256 != null
                && !string.Equals(
                    p.MovementConfigSha256,
                    movementConfigSha256,
                    StringComparison.OrdinalIgnoreCase
                )
            )
                throw new EnvironmentPackageException(
                    "traversal_graph.movement.config_sha256 does not match the shipped movement.json "
                        + "(the controller and the graph must agree; regenerate the package)"
                );
            foreach (var n in Arr(traversal, "nodes"))
            {
                var no = AsObj(n, "nodes[]");
                var node = new Node
                {
                    Id = Str(no, "id"),
                    SurfaceId = Str(no, "surface_id"),
                    Position = Vec(no, "position"),
                    Kind = Str(no, "kind"),
                    Plantable = (bool)Get(no, "plantable"),
                };
                p.Nodes[node.Id] = node;
            }
            foreach (var e in Arr(traversal, "edges"))
            {
                var eo = AsObj(e, "edges[]");
                var edge = new Edge
                {
                    Id = Str(eo, "id"),
                    From = Str(eo, "from"),
                    To = Str(eo, "to"),
                    Verb = Str(eo, "verb"),
                    Tier = Str(eo, "tier"),
                };
                if (!p.Nodes.ContainsKey(edge.From) || !p.Nodes.ContainsKey(edge.To))
                    throw new EnvironmentPackageException(
                        $"edge {edge.Id} references an unknown node"
                    );
                p.Edges[edge.Id] = edge;
            }

            p.CrossCheck();
            return p;
        }

        void CrossCheck()
        {
            if (!Nodes.ContainsKey(SpawnNodeId))
                throw new EnvironmentPackageException(
                    $"spawn.node_id {SpawnNodeId} is not a traversal node"
                );
            if (!Nodes.ContainsKey(SummitNodeId))
                throw new EnvironmentPackageException(
                    $"summit.node_id {SummitNodeId} is not a traversal node"
                );
            foreach (var r in Routes)
            foreach (var b in r.Beats)
            foreach (var id in b.EdgeIds)
            {
                if (!Edges.ContainsKey(id))
                    throw new EnvironmentPackageException(
                        $"route {r.Id} beat {b.Index} names unknown edge {id}"
                    );
            }
            foreach (var v in Vistas)
            {
                if (!Nodes.ContainsKey(v.NodeId))
                    throw new EnvironmentPackageException(
                        $"vista {v.Id} node {v.NodeId} is not a traversal node"
                    );
            }
            if (Vistas.Count > 3)
                throw new EnvironmentPackageException("at most 3 vistas (DESIGN_SYSTEM §1)");
        }

        /// <summary>A bare file name: no directory part, no traversal, no scheme or drive.</summary>
        public static bool IsPackageRelative(string name)
        {
            if (string.IsNullOrWhiteSpace(name))
                return false;
            if (name.IndexOfAny(new[] { '/', '\\', ':' }) >= 0)
                return false;
            return name != "." && name != ".." && !name.StartsWith(".", StringComparison.Ordinal);
        }

        // --- JSON access (StrictJson dictionaries; errors name the field) ---
        static Dictionary<string, object> ReadDoc(string path)
        {
            object root;
            try
            {
                root = StrictJson.Parse(File.ReadAllText(path));
            }
            catch (FormatException e)
            {
                throw new EnvironmentPackageException($"{Path.GetFileName(path)}: {e.Message}");
            }
            var doc = AsObj(root, Path.GetFileName(path));
            if (Str(doc, "schema_version") != SchemaVersion)
                throw new EnvironmentPackageException(
                    $"{Path.GetFileName(path)}: schema_version must be {SchemaVersion}"
                );
            return doc;
        }

        static object Get(Dictionary<string, object> o, string key) =>
            o.TryGetValue(key, out var v)
                ? v
                : throw new EnvironmentPackageException($"missing key '{key}'");

        static Dictionary<string, object> AsObj(object v, string what) =>
            v as Dictionary<string, object>
            ?? throw new EnvironmentPackageException($"{what} must be an object");

        static Dictionary<string, object> Obj(Dictionary<string, object> o, string key) =>
            AsObj(Get(o, key), key);

        static List<object> Arr(Dictionary<string, object> o, string key) =>
            Get(o, key) as List<object>
            ?? throw new EnvironmentPackageException($"'{key}' must be an array");

        static string Str(Dictionary<string, object> o, string key) =>
            Get(o, key) as string
            ?? throw new EnvironmentPackageException($"'{key}' must be a string");

        static float Num(Dictionary<string, object> o, string key) =>
            Get(o, key) is double d
                ? (float)d
                : throw new EnvironmentPackageException($"'{key}' must be a number");

        static Vector3 Vec(Dictionary<string, object> o, string key)
        {
            var a = Arr(o, key);
            if (a.Count != 3 || !(a[0] is double x) || !(a[1] is double y) || !(a[2] is double z))
                throw new EnvironmentPackageException(
                    string.Format(CultureInfo.InvariantCulture, "'{0}' must be [x, y, z]", key)
                );
            return new Vector3((float)x, (float)y, (float)z);
        }
    }
}
