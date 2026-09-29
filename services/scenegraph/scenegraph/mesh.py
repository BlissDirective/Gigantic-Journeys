"""Minimal triangle-mesh type + Wavefront OBJ I/O, standard library only.

The scene-graph stage runs on the reconstruction's collision mesh (an OBJ written
by services/reconstruction Open3DMesher). That mesh is already outlier-cleaned and
decimated to a few thousand triangles, so a pure-Python representation is fast
enough and needs no Open3D/numpy — the whole stage runs anywhere, GPU-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

Vec3 = tuple[float, float, float]
Tri = tuple[int, int, int]


class MeshError(Exception):
    """Raised on malformed mesh input."""


@dataclass
class Mesh:
    """A triangle mesh: vertices and 0-based triangle indices."""

    vertices: list[Vec3]
    triangles: list[Tri]

    @property
    def triangle_count(self) -> int:
        return len(self.triangles)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    def edges(self) -> dict[tuple[int, int], int]:
        """Undirected edge -> number of triangles that use it."""
        counts: dict[tuple[int, int], int] = {}
        for a, b, c in self.triangles:
            for u, v in ((a, b), (b, c), (c, a)):
                key = (u, v) if u < v else (v, u)
                counts[key] = counts.get(key, 0) + 1
        return counts

    def boundary_edges(self) -> list[tuple[int, int]]:
        """Edges used by exactly one triangle (a mesh boundary / hole rim)."""
        return [e for e, n in self.edges().items() if n == 1]

    def is_watertight(self) -> bool:
        """Watertight = every edge is shared by exactly two triangles."""
        return self.triangle_count > 0 and all(n == 2 for n in self.edges().values())


def _face_index(token: str, nverts: int) -> int:
    """Parse one OBJ face token ('v', 'v/vt', 'v//vn', 'v/vt/vn'); 1-based, or
    negative = relative to the current vertex count. Returns a 0-based index."""
    raw = token.split("/", 1)[0]
    i = int(raw)
    if i > 0:
        return i - 1
    if i < 0:
        return nverts + i
    raise MeshError("OBJ face index 0 is invalid")


def read_obj(path: Path) -> Mesh:
    """Read an OBJ into a triangle mesh. Polygons are fan-triangulated; normals,
    texture coords, groups and materials are ignored."""
    vertices: list[Vec3] = []
    triangles: list[Tri] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "v":
            if len(parts) < 4:
                raise MeshError(f"{path}:{lineno}: vertex needs 3 coordinates")
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "f":
            if len(parts) < 4:
                raise MeshError(f"{path}:{lineno}: face needs at least 3 vertices")
            idx = [_face_index(tok, len(vertices)) for tok in parts[1:]]
            for k in range(1, len(idx) - 1):  # fan triangulation
                triangles.append((idx[0], idx[k], idx[k + 1]))
    if not vertices:
        raise MeshError(f"{path}: no vertices")
    return Mesh(vertices, triangles)


def write_obj(mesh: Mesh, path: Path) -> None:
    """Write a triangle mesh as OBJ (1-based indices), deterministically."""
    lines = [f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in mesh.vertices]
    lines += [f"f {a + 1} {b + 1} {c + 1}" for a, b, c in mesh.triangles]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
