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

        /// <summary>
        /// Device performance profile for this room (AT-3 on the A15). Applied by the loader on
        /// top of the quality tier: <see cref="renderScale"/> scales the URP render target (the
        /// splat pass's fill rate and overdraw), <see cref="shOrder"/> limits spherical harmonics
        /// (view-dependent colour; also the source of sparkle on faint splats), and the Tier B sort
        /// runs at most every <see cref="sortEveryNthFrame"/> frames and only once the camera has
        /// moved <see cref="resortMoveMeters"/> or turned <see cref="resortAngleDeg"/> since the last
        /// sort. Zero or negative means "keep the tier's value" (renderScale 0 = untouched).
        /// </summary>
        public float renderScale;
        public int shOrder = -1;
        public int sortEveryNthFrame;
        public float resortMoveMeters;
        public float resortAngleDeg;

        /// <summary>
        /// Camera and play-area limits from the training camera coverage
        /// (<c>services/reconstruction/tools/room_limits.py</c>): the splat only holds up from where
        /// the source video looked. The follow camera's eye stays inside the
        /// <see cref="cameraMin"/>..<see cref="cameraMax"/> box (empty = no box), its elevation in
        /// <see cref="orbitMinElevationDeg"/>..<see cref="orbitMaxElevationDeg"/> (both 0 = the
        /// provisional defaults), its pinch zoom in <see cref="orbitMinZoom"/>..<see cref="orbitMaxZoom"/>
        /// (0 = default) and its world view yaw within <see cref="viewYawHalfRangeDeg"/> of
        /// <see cref="viewYawCenterDeg"/> (0 = free). <see cref="occluders"/> are solid boxes (rendered
        /// with the floor material, with colliders) where coverage is thin.
        /// </summary>
        public float[] cameraMin = new float[0];
        public float[] cameraMax = new float[0];
        public float orbitMinElevationDeg;
        public float orbitMaxElevationDeg;
        public float orbitMinZoom;
        public float orbitMaxZoom;
        public float viewYawCenterDeg;
        public float viewYawHalfRangeDeg;
        public Occluder[] occluders = new Occluder[0];

        /// <summary>
        /// Per-room camera mode. <c>"coverage"</c> (default, empty = coverage) applies the
        /// coverage-derived orbit limits above. <c>"free"</c> lets the player look every way:
        /// full 360° yaw and the pitch/zoom range in <see cref="freeOrbit"/>. Both modes keep the
        /// walk area, the camera box, the occluders and camera collision; the coverage values stay
        /// in the config so a room can switch back.
        /// </summary>
        public string cameraMode = CameraModeCoverage;
        public FreeOrbit freeOrbit = new FreeOrbit();

        public const string CameraModeCoverage = "coverage";
        public const string CameraModeFree = "free";

        /// <summary>Orbit range for <see cref="CameraModeFree"/> (elevation of the eye, degrees; zoom multiple).</summary>
        [Serializable]
        public sealed class FreeOrbit
        {
            public float minElevationDeg = -60f;
            public float maxElevationDeg = 80f;
            public float minZoom = 0.5f;
            public float maxZoom = 2.5f;
        }

        public bool IsFreeLook => cameraMode == CameraModeFree;

        /// <summary>A solid box in world space (centre and full size, metres).</summary>
        [Serializable]
        public sealed class Occluder
        {
            public string name;
            public float[] center = new float[3];
            public float[] size = new float[3];

            public Vector3 Center => V3(center, nameof(center));
            public Vector3 Size => V3(size, nameof(size));
        }

        public bool HasCameraBox => cameraMin != null && cameraMin.Length > 0;

        /// <summary>The camera box (only when <see cref="HasCameraBox"/>).</summary>
        public Bounds CameraBox
        {
            get
            {
                var lo = V3(cameraMin, nameof(cameraMin));
                var hi = V3(cameraMax, nameof(cameraMax));
                var b = new Bounds();
                b.SetMinMax(lo, hi);
                return b;
            }
        }

        public bool HasOrbitElevation => orbitMinElevationDeg != 0f || orbitMaxElevationDeg != 0f;
        public bool HasOrbitZoom => orbitMinZoom > 0f || orbitMaxZoom > 0f;

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
            if (renderScale != 0f && !(renderScale >= 0.5f && renderScale <= 1f))
                throw new FormatException("renderScale must be 0 (untouched) or in [0.5, 1]");
            if (shOrder > 3)
                throw new FormatException("shOrder must be at most 3 (-1 = tier)");
            if (resortMoveMeters < 0f || resortAngleDeg < 0f || sortEveryNthFrame < 0)
                throw new FormatException(
                    "sort cadence and resort thresholds must not be negative"
                );
            var sp = Spawn;
            if (sp.x < lo.x || sp.x > hi.x || sp.z < lo.y || sp.z > hi.y)
                throw new FormatException("spawn must lie inside the walkable rectangle");
            ValidateCameraLimits(lo, hi);
        }

        void ValidateCameraLimits(Vector2 walkLo, Vector2 walkHi)
        {
            if (HasCameraBox)
            {
                var box = CameraBox;
                if (!(box.size.x > 0f && box.size.y > 0f && box.size.z > 0f))
                    throw new FormatException("cameraMax must exceed cameraMin on every axis");
                if (
                    walkLo.x < box.min.x
                    || walkHi.x > box.max.x
                    || walkLo.y < box.min.z
                    || walkHi.y > box.max.z
                )
                    throw new FormatException("the camera box must contain the walkable rectangle");
            }
            else if (cameraMax != null && cameraMax.Length > 0)
                throw new FormatException("cameraMax without cameraMin");
            if (
                HasOrbitElevation
                && !(
                    orbitMinElevationDeg < orbitMaxElevationDeg
                    && orbitMinElevationDeg >= -45f
                    && orbitMaxElevationDeg <= 85f
                )
            )
                throw new FormatException(
                    "orbit elevation must be min < max within [-45, 85] degrees (both 0 = default)"
                );
            if (HasOrbitZoom && !(orbitMinZoom > 0f && orbitMinZoom <= 1f && orbitMaxZoom >= 1f))
                throw new FormatException(
                    "orbit zoom must be 0 < min <= 1 <= max (both 0 = default)"
                );
            if (viewYawHalfRangeDeg < 0f || viewYawHalfRangeDeg > 180f)
                throw new FormatException("viewYawHalfRangeDeg must be in [0, 180] (0 = free)");
            if (
                !string.IsNullOrEmpty(cameraMode)
                && cameraMode != CameraModeCoverage
                && cameraMode != CameraModeFree
            )
                throw new FormatException(
                    $"cameraMode must be '{CameraModeCoverage}' or '{CameraModeFree}', not '{cameraMode}'"
                );
            if (IsFreeLook)
            {
                var f = freeOrbit ?? throw new FormatException("cameraMode 'free' needs freeOrbit");
                if (
                    !(
                        f.minElevationDeg < f.maxElevationDeg
                        && f.minElevationDeg >= -80f
                        && f.maxElevationDeg <= 85f
                    )
                )
                    throw new FormatException(
                        "freeOrbit elevation must be min < max within [-80, 85] degrees"
                    );
                if (!(f.minZoom > 0f && f.minZoom <= 1f && f.maxZoom >= 1f))
                    throw new FormatException("freeOrbit zoom must be 0 < min <= 1 <= max");
            }
            foreach (var o in occluders ?? new Occluder[0])
            {
                var size = o.Size;
                _ = o.Center;
                if (!(size.x > 0f && size.y > 0f && size.z > 0f))
                    throw new FormatException($"occluder '{o.name}' needs a positive size");
            }
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
