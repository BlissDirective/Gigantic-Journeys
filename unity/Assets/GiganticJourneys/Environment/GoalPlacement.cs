using System.Collections.Generic;
using UnityEngine;

namespace GiganticJourneys.Environments
{
    /// <summary>
    /// Where the non-photo goal elements go (CONTRACT "Placement", DESIGN_SYSTEM §1,
    /// Bible §8). Pure functions over a loaded <see cref="EnvironmentPackage"/>.
    /// </summary>
    public static class GoalPlacement
    {
        /// <summary>
        /// Spawn yaw: <c>facing_deg</c> is measured about +y from +z towards +x, which is
        /// Unity's Euler y (services/scenegraph: atan2(dx, dz)).
        /// </summary>
        public static Quaternion SpawnRotation(EnvironmentPackage p) =>
            Quaternion.Euler(0f, p.SpawnFacingDeg, 0f);

        /// <summary>
        /// The selected route's marker polyline: its beats' edges in order, through the edges'
        /// from/to node positions, with repeated joints collapsed. Empty for an unknown route.
        /// </summary>
        public static List<Vector3> RoutePolyline(EnvironmentPackage p, string routeId)
        {
            var points = new List<Vector3>();
            var route = p.Routes.Find(r => r.Id == routeId);
            if (route == null)
                return points;
            foreach (var beat in route.Beats)
            foreach (var edgeId in beat.EdgeIds)
            {
                var e = p.Edges[edgeId];
                Add(points, p.Nodes[e.From].Position);
                Add(points, p.Nodes[e.To].Position);
            }
            return points;
        }

        /// <summary>
        /// Footprint marks spaced <paramref name="spacing"/> A apart along a polyline (the
        /// locked "faint footprints" treatment): position plus heading, alternating feet.
        /// </summary>
        public static List<(Vector3 position, Quaternion rotation, bool left)> Footprints(
            IReadOnlyList<Vector3> polyline,
            float spacing
        )
        {
            var marks = new List<(Vector3, Quaternion, bool)>();
            if (polyline.Count < 2 || spacing <= 0f)
                return marks;
            var next = 0f; // distance into the current segment of the next mark
            var left = true;
            for (var i = 1; i < polyline.Count; i++)
            {
                var a = polyline[i - 1];
                var seg = polyline[i] - a;
                var len = seg.magnitude;
                if (len < 1e-5f)
                    continue;
                var flat = new Vector3(seg.x, 0f, seg.z);
                var rot =
                    flat.sqrMagnitude > 1e-8f
                        ? Quaternion.LookRotation(flat.normalized, Vector3.up)
                        : Quaternion.identity;
                var d = next;
                for (; d <= len; d += spacing)
                {
                    marks.Add((a + seg * (d / len), rot, left));
                    left = !left;
                }
                next = d - len;
            }
            return marks;
        }

        static void Add(List<Vector3> points, Vector3 p)
        {
            if (points.Count == 0 || (points[points.Count - 1] - p).sqrMagnitude > 1e-8f)
                points.Add(p);
        }
    }
}
