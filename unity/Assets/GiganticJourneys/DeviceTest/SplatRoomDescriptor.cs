using System;
using System.Globalization;
using UnityEngine;

namespace GiganticJourneys.DeviceTest
{
    /// <summary>
    /// The device-test splat room (ticket M1-UNITY-01 AT-2/AT-3): which reconstructed room the
    /// internal-debug build loads, how it is placed, and where the character may walk.
    ///
    /// The committed descriptor (<c>splat-room.json</c>) carries only placement numbers, the
    /// credit line and the integrity hash. The splat itself never enters git (the repo hygiene
    /// check bans scan files, and this repository is public): the internal-debug CI lane fetches
    /// the converted asset from the private staging bucket through a short-lived signed URL,
    /// verifies <see cref="PackageSha256"/>, and unpacks it into a gitignored Resources folder
    /// (see <c>.github/scripts/ios_debug_flavor.py fetch-splat</c>). Release builds never contain it.
    /// </summary>
    [Serializable]
    public sealed class SplatRoomDescriptor
    {
        public string slug;
        public string displayName;

        /// <summary>Resources path of the converted GaussianSplatAsset (no extension).</summary>
        public string resource;
        public int splatCount;
        public string credit;
        public string license;
        public string packageObject;
        public string packageSha256;
        public long packageBytes;

        /// <summary>Splat-local to world: position, rotation (x, y, z, w) and scale (a negative z un-mirrors right-handed capture data).</summary>
        public float[] position = new float[3];
        public float[] rotation = { 0f, 0f, 0f, 1f };
        public float[] scale = { 1f, 1f, 1f };

        /// <summary>Walkable floor rectangle in world XZ (the floor is world y = 0).</summary>
        public float[] walkMin = { -1f, -1f };
        public float[] walkMax = { 1f, 1f };
        public float[] spawn = new float[3];
        public float spawnYawDeg;

        public string PackageSha256 => packageSha256;

        public Vector3 Position => V3(position, nameof(position));
        public Quaternion Rotation
        {
            get
            {
                Require(rotation, 4, nameof(rotation));
                return new Quaternion(
                    rotation[0],
                    rotation[1],
                    rotation[2],
                    rotation[3]
                ).normalized;
            }
        }
        public Vector3 Scale => V3(scale, nameof(scale));
        public Vector3 Spawn => V3(spawn, nameof(spawn));
        public Vector2 WalkMin => V2(walkMin, nameof(walkMin));
        public Vector2 WalkMax => V2(walkMax, nameof(walkMax));

        /// <summary>Splat-local to world matrix.</summary>
        public Matrix4x4 LocalToWorld => Matrix4x4.TRS(Position, Rotation, Scale);

        public static SplatRoomDescriptor Parse(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
                throw new FormatException("splat room descriptor is empty");
            var d = JsonUtility.FromJson<SplatRoomDescriptor>(json);
            d.Validate();
            return d;
        }

        /// <summary>Throws <see cref="FormatException"/> when a field is missing or out of range.</summary>
        public void Validate()
        {
            if (string.IsNullOrEmpty(slug) || string.IsNullOrEmpty(resource))
                throw new FormatException("splat room descriptor needs slug and resource");
            if (string.IsNullOrEmpty(credit) || string.IsNullOrEmpty(license))
                throw new FormatException(
                    "splat room descriptor needs the credit line and license (OPEN_VIDEO_ATTRIBUTION.md)"
                );
            if (splatCount <= 0)
                throw new FormatException("splatCount must be positive");
            if (string.IsNullOrEmpty(packageSha256) || packageSha256.Length != 64)
                throw new FormatException("packageSha256 must be a 64-character hex SHA-256");
            var s = Scale;
            if (Mathf.Abs(s.x) < 1e-4f || Mathf.Abs(s.y) < 1e-4f || Mathf.Abs(s.z) < 1e-4f)
                throw new FormatException("scale components must be non-zero");
            _ = Position;
            _ = Rotation;
            _ = Spawn;
            var lo = WalkMin;
            var hi = WalkMax;
            if (!(hi.x > lo.x && hi.y > lo.y))
                throw new FormatException("walkMax must exceed walkMin");
            var sp = Spawn;
            if (sp.x < lo.x || sp.x > hi.x || sp.z < lo.y || sp.z > hi.y)
                throw new FormatException("spawn must lie inside the walkable rectangle");
        }

        /// <summary>"780,004" style count for the on-screen label.</summary>
        public static string FormatCount(int n) => n.ToString("N0", CultureInfo.InvariantCulture);

        static Vector3 V3(float[] a, string name)
        {
            Require(a, 3, name);
            return new Vector3(a[0], a[1], a[2]);
        }

        static Vector2 V2(float[] a, string name)
        {
            Require(a, 2, name);
            return new Vector2(a[0], a[1]);
        }

        static void Require(float[] a, int n, string name)
        {
            if (a == null || a.Length != n)
                throw new FormatException($"{name} needs {n} numbers");
            foreach (var f in a)
            {
                if (float.IsNaN(f) || float.IsInfinity(f))
                    throw new FormatException($"{name} has a non-finite number");
            }
        }
    }
}
