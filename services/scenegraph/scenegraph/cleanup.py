"""Traversal-quality mesh cleanup (M1-SCEN-01): floater removal, hole fill, and a
ceiling cap, turning the reconstruction's collision OBJ into a watertight mesh the
character cannot fall out of.

The reconstruction stage (services/reconstruction Open3DMesher) already removes
statistical outliers, small clusters and decimates. This stage owns the *gameplay*
bar: (1) drop any remaining disconnected floaters, (2) fill the small holes
reconstruction leaves in walls/floor so the character can't fall through, and
(3) cap the open top of an inside-out room scan. Large intentional openings
(doorways, windows) are left alone unless `fill_all_holes` is set.

Pure standard library: it runs on the already-decimated OBJ with no Open3D/numpy,
so it is deterministic, fast, and testable on synthetic meshes.
"""

from __future__ import annotations

from dataclasses import dataclass

from .mesh import Mesh, Tri, Vec3

_AXIS = {"x": 0, "y": 1, "z": 2}


@dataclass(frozen=True)
class CleanupConfig:
    # A connected component smaller than this fraction of all triangles is a
    # floater and is removed (the largest component is always kept).
    min_component_fraction: float = 0.02
    # A boundary loop with at most this many edges is a "small hole" -> filled.
    max_hole_edges: int = 40
    # Which axis is up (room scans: the ceiling is the max along this axis).
    up_axis: str = "y"
    # A boundary loop whose centroid sits within this top fraction of the up-range
    # is treated as the ceiling opening and filled regardless of size.
    ceiling_band: float = 0.15
    # Fill every boundary loop (fully watertight), ignoring size/ceiling rules.
    fill_all_holes: bool = False

    def __post_init__(self) -> None:
        if self.up_axis not in _AXIS:
            raise ValueError(f"up_axis must be x/y/z, got {self.up_axis!r}")
        if not 0.0 <= self.ceiling_band <= 1.0:
            raise ValueError("ceiling_band must be in [0, 1]")


@dataclass
class CleanupStats:
    input_triangles: int = 0
    input_vertices: int = 0
    components: int = 0
    floater_triangles_removed: int = 0
    degenerate_removed: int = 0
    boundary_loops: int = 0
    holes_filled: int = 0
    ceiling_capped: int = 0
    triangles_added: int = 0
    output_triangles: int = 0
    output_vertices: int = 0
    watertight: bool = False
    remaining_boundary_edges: int = 0

    def as_dict(self) -> dict:
        return dict(self.__dict__)


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def _drop_degenerate(triangles: list[Tri]) -> tuple[list[Tri], int]:
    out = [t for t in triangles if t[0] != t[1] and t[1] != t[2] and t[0] != t[2]]
    return out, len(triangles) - len(out)


def _reindex(vertices: list[Vec3], triangles: list[Tri]) -> Mesh:
    """Keep only referenced vertices, remapping triangle indices."""
    used = sorted({i for t in triangles for i in t})
    remap = {old: new for new, old in enumerate(used)}
    return Mesh(
        [vertices[i] for i in used],
        [(remap[a], remap[b], remap[c]) for a, b, c in triangles],
    )


def remove_floaters(mesh: Mesh, min_fraction: float) -> tuple[Mesh, int, int]:
    """Drop connected components below min_fraction of all triangles; always keep
    the largest. Returns (mesh, component_count, triangles_removed)."""
    uf = _UnionFind(mesh.vertex_count)
    for a, b, c in mesh.triangles:
        uf.union(a, b)
        uf.union(b, c)
    comps: dict[int, list[Tri]] = {}
    for t in mesh.triangles:
        comps.setdefault(uf.find(t[0]), []).append(t)
    if not comps:
        return mesh, 0, 0
    total = mesh.triangle_count
    largest = max(comps.values(), key=len)
    threshold = min_fraction * total
    kept: list[Tri] = []
    for tris in comps.values():
        if tris is largest or len(tris) >= threshold:
            kept.extend(tris)
    removed = total - len(kept)
    return _reindex(mesh.vertices, kept), len(comps), removed


def boundary_loops(mesh: Mesh) -> list[list[int]]:
    """Ordered vertex loops along the mesh boundary (edges used by one triangle)."""
    adj: dict[int, list[int]] = {}
    for u, v in mesh.boundary_edges():
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, []).append(u)
    loops: list[list[int]] = []
    visited: set[int] = set()
    for start in adj:
        if start in visited:
            continue
        loop = [start]
        visited.add(start)
        prev, cur = -1, start
        while True:
            nxt = None
            for n in adj[cur]:
                if n == prev:
                    continue
                if n not in visited:
                    nxt = n
                    break
            if nxt is None:
                break  # loop closes (its neighbours are all visited) or dead-ends
            loop.append(nxt)
            visited.add(nxt)
            prev, cur = cur, nxt
        if len(loop) >= 3:
            loops.append(loop)
    return loops


def _fan_fill(vertices: list[Vec3], loop: list[int]) -> tuple[Vec3, list[Tri]]:
    """A centroid vertex + a triangle fan closing the loop. Winding is arbitrary
    (a collision mesh collides on both sides)."""
    cx = sum(vertices[i][0] for i in loop) / len(loop)
    cy = sum(vertices[i][1] for i in loop) / len(loop)
    cz = sum(vertices[i][2] for i in loop) / len(loop)
    centroid_index = len(vertices)
    tris = [(centroid_index, loop[k], loop[(k + 1) % len(loop)]) for k in range(len(loop))]
    return (cx, cy, cz), tris


def fill_holes(mesh: Mesh, config: CleanupConfig) -> tuple[Mesh, int, int]:
    """Fill small holes + the ceiling opening. Returns (mesh, holes_filled,
    ceiling_capped)."""
    loops = boundary_loops(mesh)
    if not loops:
        return mesh, 0, 0
    axis = _AXIS[config.up_axis]
    ups = [v[axis] for v in mesh.vertices]
    up_min, up_max = min(ups), max(ups)
    up_span = up_max - up_min
    ceiling_cut = up_max - config.ceiling_band * up_span if up_span > 0 else up_max

    vertices = list(mesh.vertices)
    triangles = list(mesh.triangles)
    holes_filled = 0
    ceiling_capped = 0
    for loop in loops:
        centroid_up = sum(mesh.vertices[i][axis] for i in loop) / len(loop)
        is_ceiling = up_span > 0 and centroid_up >= ceiling_cut
        small = len(loop) <= config.max_hole_edges
        if not (config.fill_all_holes or small or is_ceiling):
            continue
        centroid, tris = _fan_fill(vertices, loop)
        vertices.append(centroid)
        triangles.extend(tris)
        if is_ceiling and not small:
            ceiling_capped += 1
        else:
            holes_filled += 1
    return Mesh(vertices, triangles), holes_filled, ceiling_capped


def clean_mesh(mesh: Mesh, config: CleanupConfig | None = None) -> tuple[Mesh, CleanupStats]:
    """Floater removal -> degenerate drop -> hole fill + ceiling cap. Returns the
    cleaned mesh and per-step stats."""
    config = config or CleanupConfig()
    stats = CleanupStats(input_triangles=mesh.triangle_count, input_vertices=mesh.vertex_count)

    tris, degen = _drop_degenerate(mesh.triangles)
    stats.degenerate_removed = degen
    mesh = _reindex(mesh.vertices, tris) if degen else Mesh(list(mesh.vertices), tris)

    mesh, comp_count, removed = remove_floaters(mesh, config.min_component_fraction)
    stats.components = comp_count
    stats.floater_triangles_removed = removed

    stats.boundary_loops = len(boundary_loops(mesh))
    before = mesh.triangle_count
    mesh, holes, ceiling = fill_holes(mesh, config)
    stats.holes_filled = holes
    stats.ceiling_capped = ceiling
    stats.triangles_added = mesh.triangle_count - before

    stats.output_triangles = mesh.triangle_count
    stats.output_vertices = mesh.vertex_count
    stats.remaining_boundary_edges = len(mesh.boundary_edges())
    stats.watertight = mesh.is_watertight()
    return mesh, stats
