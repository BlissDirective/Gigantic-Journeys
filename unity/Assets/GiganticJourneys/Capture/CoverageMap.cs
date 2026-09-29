using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace GiganticJourneys.Capture
{
    /// <summary>
    /// What the capture has seen, as an azimuth x elevation grid (the data behind the coverage wash,
    /// the percentage in the ring, Done at 60 %, and the missed-corner arrow; DESIGN_SYSTEM §6).
    /// <para><b>Room</b> (view sphere): each accepted frame paints the bin of its viewing direction,
    /// which rewards looking at every wall, the floor under furniture and the tops of shelves.</para>
    /// <para><b>Tabletop</b> (orbit): each accepted frame paints the bin of the camera's position
    /// around the build, seen from the build centre. The centre is the least-squares point closest to
    /// all viewing rays (the player keeps the build centred), so it needs no tap to place.</para>
    /// The on-device AR wash (painting real surfaces from the ARKit mesh) is the platform layer's
    /// job; this grid is its platform-neutral twin and what the bundle records.
    /// </summary>
    public sealed class CoverageMap
    {
        private const float CentreMoveRepaint = 0.05f;
        private const float FallbackCentreDistance = 0.5f;

        private readonly int[,] _hits;
        private readonly List<Vector3> _orbitPositions = new List<Vector3>();

        // Normal equations for the closest point to all rays: sum(I - d d^T) c = sum(I - d d^T) p.
        private float _a00,
            _a01,
            _a02,
            _a11,
            _a12,
            _a22;
        private Vector3 _b;
        private int _rays;
        private Vector3 _paintedCentre;
        private bool _hasPaintedCentre;
        private Vector3 _fallbackCentre;

        /// <summary>Creates an empty map for the mode.</summary>
        public CoverageMap(CaptureMode mode)
        {
            Mode = mode;
            bool room = mode == CaptureMode.Room;
            AzimuthBins = room
                ? CaptureTuning.Coverage.RoomAzimuthBins
                : CaptureTuning.Coverage.OrbitAzimuthBins;
            ElevationBins = room
                ? CaptureTuning.Coverage.RoomElevationBins
                : CaptureTuning.Coverage.OrbitElevationBins;
            ElevationMinDeg = room
                ? CaptureTuning.Coverage.RoomElevationMinDeg
                : CaptureTuning.Coverage.OrbitElevationMinDeg;
            ElevationMaxDeg = room
                ? CaptureTuning.Coverage.RoomElevationMaxDeg
                : CaptureTuning.Coverage.OrbitElevationMaxDeg;
            _hits = new int[ElevationBins, AzimuthBins];
        }

        /// <summary>The capture mode.</summary>
        public CaptureMode Mode { get; }

        /// <summary>Azimuth bins (columns).</summary>
        public int AzimuthBins { get; }

        /// <summary>Elevation bins (rows, low to high).</summary>
        public int ElevationBins { get; }

        /// <summary>Lowest elevation mapped (deg).</summary>
        public float ElevationMinDeg { get; }

        /// <summary>Highest elevation mapped (deg).</summary>
        public float ElevationMaxDeg { get; }

        /// <summary>"view-sphere" (room) or "orbit" (tabletop), as recorded in the bundle.</summary>
        public string Kind => Mode == CaptureMode.Room ? "view-sphere" : "orbit";

        /// <summary>Tabletop only: the estimated build centre (world space).</summary>
        public Vector3 OrbitCentre => _rays >= 2 && TrySolveCentre(out var c) ? c : _fallbackCentre;

        /// <summary>True when the bin has enough accepted frames to count as painted.</summary>
        public bool IsPainted(int elevation, int azimuth) =>
            _hits[elevation, azimuth] >= CaptureTuning.Coverage.FramesToPaint;

        /// <summary>Painted share of all bins, 0–1.</summary>
        public float Fraction
        {
            get
            {
                int painted = 0;
                for (int e = 0; e < ElevationBins; e++)
                {
                    for (int a = 0; a < AzimuthBins; a++)
                    {
                        if (IsPainted(e, a))
                        {
                            painted++;
                        }
                    }
                }

                return (float)painted / (ElevationBins * AzimuthBins);
            }
        }

        /// <summary>Paints the bin for an accepted frame (blurred or untracked frames must not be added).</summary>
        public void Add(in CaptureFrame frame)
        {
            if (Mode == CaptureMode.Room)
            {
                Paint(frame.Forward);
                return;
            }

            if (_rays == 0)
            {
                _fallbackCentre = frame.Position + frame.Forward * FallbackCentreDistance;
            }

            AccumulateRay(frame.Position, frame.Forward);
            _orbitPositions.Add(frame.Position);
            Vector3 centre = OrbitCentre;
            if (!_hasPaintedCentre || (centre - _paintedCentre).magnitude > CentreMoveRepaint)
            {
                RepaintOrbit(centre);
            }
            else
            {
                Paint(frame.Position - centre);
            }
        }

        /// <summary>
        /// The largest connected unpainted region (azimuth wraps around), for the missed-corner arrow:
        /// its size in bins and the world-space direction to point at (room: a viewing direction;
        /// tabletop: from the build centre towards the unseen side). False when everything is painted.
        /// </summary>
        public bool TryGetMissedCorner(out Vector3 direction, out int size)
        {
            direction = Vector3.zero;
            size = 0;
            var seen = new bool[ElevationBins, AzimuthBins];
            var stack = new Stack<(int e, int a)>();
            for (int e0 = 0; e0 < ElevationBins; e0++)
            {
                for (int a0 = 0; a0 < AzimuthBins; a0++)
                {
                    if (seen[e0, a0] || IsPainted(e0, a0))
                    {
                        continue;
                    }

                    int count = 0;
                    Vector3 sum = Vector3.zero;
                    stack.Push((e0, a0));
                    seen[e0, a0] = true;
                    while (stack.Count > 0)
                    {
                        var (e, a) = stack.Pop();
                        count++;
                        sum += BinDirection(e, a);
                        Visit(e, (a + 1) % AzimuthBins, seen, stack);
                        Visit(e, (a + AzimuthBins - 1) % AzimuthBins, seen, stack);
                        Visit(e + 1, a, seen, stack);
                        Visit(e - 1, a, seen, stack);
                    }

                    if (count > size)
                    {
                        size = count;
                        direction =
                            sum.sqrMagnitude > 1e-8f ? sum.normalized : BinDirection(e0, a0);
                    }
                }
            }

            return size > 0;
        }

        /// <summary>One string per elevation row (low to high), '1' painted / '0' not, as in the bundle.</summary>
        public string[] PaintedRows()
        {
            var rows = new string[ElevationBins];
            var sb = new StringBuilder(AzimuthBins);
            for (int e = 0; e < ElevationBins; e++)
            {
                sb.Clear();
                for (int a = 0; a < AzimuthBins; a++)
                {
                    sb.Append(IsPainted(e, a) ? '1' : '0');
                }

                rows[e] = sb.ToString();
            }

            return rows;
        }

        /// <summary>Unit direction at the centre of a bin (azimuth 0 = +Z, clockwise towards +X seen from above).</summary>
        public Vector3 BinDirection(int elevation, int azimuth)
        {
            float azDeg = (azimuth + 0.5f) * 360f / AzimuthBins;
            float elDeg =
                ElevationMinDeg
                + (elevation + 0.5f) * (ElevationMaxDeg - ElevationMinDeg) / ElevationBins;
            float az = azDeg * Mathf.Deg2Rad;
            float el = elDeg * Mathf.Deg2Rad;
            return new Vector3(
                Mathf.Cos(el) * Mathf.Sin(az),
                Mathf.Sin(el),
                Mathf.Cos(el) * Mathf.Cos(az)
            );
        }

        private void Visit(int e, int a, bool[,] seen, Stack<(int e, int a)> stack)
        {
            if (e < 0 || e >= ElevationBins || seen[e, a] || IsPainted(e, a))
            {
                return;
            }

            seen[e, a] = true;
            stack.Push((e, a));
        }

        private void Paint(Vector3 direction)
        {
            if (direction.sqrMagnitude < 1e-8f)
            {
                return;
            }

            Vector3 d = direction.normalized;
            float elDeg = Mathf.Asin(Mathf.Clamp(d.y, -1f, 1f)) * Mathf.Rad2Deg;
            if (elDeg < ElevationMinDeg || elDeg > ElevationMaxDeg)
            {
                return;
            }

            float azDeg = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
            if (azDeg < 0f)
            {
                azDeg += 360f;
            }

            int a = Mathf.Min((int)(azDeg / 360f * AzimuthBins), AzimuthBins - 1);
            int e = Mathf.Min(
                (int)(
                    (elDeg - ElevationMinDeg) / (ElevationMaxDeg - ElevationMinDeg) * ElevationBins
                ),
                ElevationBins - 1
            );
            _hits[e, a]++;
        }

        private void RepaintOrbit(Vector3 centre)
        {
            System.Array.Clear(_hits, 0, _hits.Length);
            foreach (var p in _orbitPositions)
            {
                Paint(p - centre);
            }

            _paintedCentre = centre;
            _hasPaintedCentre = true;
        }

        private void AccumulateRay(Vector3 p, Vector3 d)
        {
            // M = I - d d^T (symmetric)
            float m00 = 1f - d.x * d.x,
                m01 = -d.x * d.y,
                m02 = -d.x * d.z;
            float m11 = 1f - d.y * d.y,
                m12 = -d.y * d.z,
                m22 = 1f - d.z * d.z;
            _a00 += m00;
            _a01 += m01;
            _a02 += m02;
            _a11 += m11;
            _a12 += m12;
            _a22 += m22;
            _b += new Vector3(
                m00 * p.x + m01 * p.y + m02 * p.z,
                m01 * p.x + m11 * p.y + m12 * p.z,
                m02 * p.x + m12 * p.y + m22 * p.z
            );
            _rays++;
        }

        private bool TrySolveCentre(out Vector3 centre)
        {
            // Cramer's rule on the symmetric 3x3 system.
            float det =
                _a00 * (_a11 * _a22 - _a12 * _a12)
                - _a01 * (_a01 * _a22 - _a12 * _a02)
                + _a02 * (_a01 * _a12 - _a11 * _a02);
            // Near-parallel rays (the player has not moved around the build yet) are ill-conditioned.
            if (Mathf.Abs(det) < 1e-3f * _rays * _rays * _rays)
            {
                centre = default;
                return false;
            }

            float inv = 1f / det;
            centre = new Vector3(
                inv
                    * (
                        _b.x * (_a11 * _a22 - _a12 * _a12)
                        - _a01 * (_b.y * _a22 - _a12 * _b.z)
                        + _a02 * (_b.y * _a12 - _a11 * _b.z)
                    ),
                inv
                    * (
                        _a00 * (_b.y * _a22 - _a12 * _b.z)
                        - _b.x * (_a01 * _a22 - _a12 * _a02)
                        + _a02 * (_a01 * _b.z - _b.y * _a02)
                    ),
                inv
                    * (
                        _a00 * (_a11 * _b.z - _b.y * _a12)
                        - _a01 * (_a01 * _b.z - _b.y * _a02)
                        + _b.x * (_a01 * _a12 - _a11 * _a02)
                    )
            );
            return true;
        }
    }
}
