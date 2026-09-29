"""Planar-patch segmentation of the cleaned collision mesh (M1-SCEN-02, step 1).

The reconstruction gives one connected, watertight triangle mesh. Before surfaces
can be classified (desk top, book stack, wall, ledge...) the mesh has to be split
into planar patches. This is a deterministic region-grow: starting from each unused
triangle, neighbours join the patch while their normal stays within a tolerance of
the seed normal and they stay close to the seed plane. Pure standard library.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from . import geometry as g
from .mesh import Mesh, Vec3


@dataclass
class Patch:
    """A planar group of triangles from the collision mesh."""

    tri_indices: list[int]
    normal: Vec3  # area-weighted unit normal
    centroid: Vec3  # area-weighted centroid
    area: float
    _mesh: Mesh = field(repr=False)

    @property
    def triangle_count(self) -> int:
        return len(self.tri_indices)

    def vertex_ids(self) -> set[int]:
        ids: set[int] = set()
        for ti in self.tri_indices:
            ids.update(self._mesh.triangles[ti])
        return ids

    def bounds(self) -> tuple[Vec3, Vec3]:
        """Axis-aligned (min, max) over the patch vertices."""
        xs, ys, zs = [], [], []
        for vid in self.vertex_ids():
            x, y, z = self._mesh.vertices[vid]
            xs.append(x)
            ys.append(y)
            zs.append(z)
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _adjacency(mesh: Mesh) -> dict[tuple[int, int], list[int]]:
    """Undirected edge -> triangle indices sharing it."""
    adj: dict[tuple[int, int], list[int]] = {}
    for ti, (a, b, c) in enumerate(mesh.triangles):
        for u, v in ((a, b), (b, c), (c, a)):
            key = (u, v) if u < v else (v, u)
            adj.setdefault(key, []).append(ti)
    return adj


def _neighbours(mesh: Mesh, adj: dict[tuple[int, int], list[int]], ti: int) -> list[int]:
    a, b, c = mesh.triangles[ti]
    out: list[int] = []
    for u, v in ((a, b), (b, c), (c, a)):
        key = (u, v) if u < v else (v, u)
        out.extend(t for t in adj[key] if t != ti)
    return out


def segment_planar(
    mesh: Mesh,
    normal_tol_deg: float = 25.0,
    coplanar_tol: float = 0.12,
    min_area: float = 0.0,
) -> list[Patch]:
    """Segment ``mesh`` into planar patches.

    A neighbour triangle joins the current patch when its normal is within
    ``normal_tol_deg`` of the seed triangle's normal and its centroid is within
    ``coplanar_tol`` (perpendicular distance) of the seed plane. Coordinates are in
    whatever units the mesh is in, so ``coplanar_tol`` is in those units (the scene
    builder segments in A units). Patches are returned largest-area first, with the
    seed triangle index breaking ties, so the result is deterministic.
    """
    tris = mesh.triangles
    verts = mesh.vertices
    tnormal: list[Vec3] = []
    tcentroid: list[Vec3] = []
    tarea: list[float] = []
    for a, b, c in tris:
        v0, v1, v2 = verts[a], verts[b], verts[c]
        tnormal.append(g.tri_normal(v0, v1, v2))
        tcentroid.append(g.tri_centroid(v0, v1, v2))
        tarea.append(g.tri_area(v0, v1, v2))

    adj = _adjacency(mesh)
    visited = [False] * len(tris)
    patches: list[Patch] = []

    for seed in range(len(tris)):
        if visited[seed] or tarea[seed] == 0.0:
            visited[seed] = True  # skip degenerate triangles as their own patch
            continue
        seed_n = tnormal[seed]
        seed_p = tcentroid[seed]
        members: list[int] = []
        queue: deque[int] = deque([seed])
        visited[seed] = True
        while queue:
            ti = queue.popleft()
            members.append(ti)
            for nb in sorted(_neighbours(mesh, adj, ti)):
                if visited[nb] or tarea[nb] == 0.0:
                    continue
                if g.angle_deg(tnormal[nb], seed_n) > normal_tol_deg:
                    continue
                if abs(g.dot(g.sub(tcentroid[nb], seed_p), seed_n)) > coplanar_tol:
                    continue
                visited[nb] = True
                queue.append(nb)

        area = sum(tarea[t] for t in members)
        if area < min_area:
            continue
        # Area-weighted normal + centroid over the patch.
        nx = ny = nz = cx = cy = cz = 0.0
        for t in members:
            w = tarea[t]
            n, cen = tnormal[t], tcentroid[t]
            nx += n[0] * w
            ny += n[1] * w
            nz += n[2] * w
            cx += cen[0] * w
            cy += cen[1] * w
            cz += cen[2] * w
        normal = g.normalize((nx, ny, nz)) if area > 0 else seed_n
        centroid = (cx / area, cy / area, cz / area)
        patches.append(
            Patch(
                tri_indices=sorted(members),
                normal=normal,
                centroid=centroid,
                area=area,
                _mesh=mesh,
            )
        )

    patches.sort(key=lambda p: (-p.area, p.tri_indices[0]))
    return patches
