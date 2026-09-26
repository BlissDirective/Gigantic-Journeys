"""Collision-mesh derivation (Open3D).

The real adapter imports Open3D (MIT) and numpy lazily and runs in the
container; importing this module never requires them. Tests use
``fakes.FakeMesher``; the filtering rules live in ``splat_ops.MeshFilter``.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Protocol

from .models import CollisionMesh, ReconstructionError, SplatModel
from .splat_ops import MeshFilter


class MeshError(ReconstructionError):
    """Raised when mesh derivation fails or Open3D is missing."""


class Mesher(Protocol):
    """Derive a low-poly collision mesh for gameplay physics."""

    def derive(self, model: SplatModel, work_dir: Path) -> CollisionMesh: ...


def read_splat_ply(path: Path):
    """The vertex table of a binary little-endian float PLY as a numpy record array."""
    import numpy as np

    with path.open("rb") as fh:
        if fh.readline().strip() != b"ply":
            raise MeshError(f"not a PLY file: {path}")
        names: list[str] = []
        count = 0
        while True:
            line = fh.readline()
            if not line:
                raise MeshError(f"truncated PLY header: {path}")
            parts = line.split()
            if parts[:1] == [b"format"] and parts[1] != b"binary_little_endian":
                raise MeshError(f"unsupported PLY format {parts[1]!r}: {path}")
            if parts[:2] == [b"element", b"vertex"]:
                count = int(parts[2])
            elif parts[:1] == [b"property"]:
                if parts[1] != b"float":
                    raise MeshError(f"unsupported PLY property type {parts[1]!r}: {path}")
                names.append(parts[2].decode())
            elif parts[:1] == [b"end_header"]:
                break
        dtype = np.dtype([(n, "<f4") for n in names])
        return np.fromfile(fh, dtype=dtype, count=count)


def scene_bounds(xyz, rules: MeshFilter):
    """Robust scene box (numpy): percentile box, optionally over dense cells only."""
    import numpy as np

    p = rules.bounds_percentile
    lo = np.percentile(xyz, p, axis=0)
    hi = np.percentile(xyz, 100.0 - p, axis=0)
    if rules.bounds_mode == "dense":
        inside = ((xyz >= lo) & (xyz <= hi)).all(axis=1)
        pts = xyz[inside]
        cell = np.maximum((hi - lo) / rules.bounds_grid, 1e-9)
        idx = np.minimum(((pts - lo) / cell).astype(np.int64), rules.bounds_grid - 1)
        flat = (idx[:, 0] * rules.bounds_grid + idx[:, 1]) * rules.bounds_grid + idx[:, 2]
        _, inverse, counts = np.unique(flat, return_inverse=True, return_counts=True)
        dense = counts[inverse] >= rules.dense_cell_fraction * counts.mean()
        if dense.sum() >= 100:
            pts = pts[dense]
            lo = np.percentile(pts, p, axis=0)
            hi = np.percentile(pts, 100.0 - p, axis=0)
    pad = (hi - lo) * rules.bounds_margin
    return lo - pad, hi + pad


class Open3DMesher:
    """Poisson surface reconstruction from *cleaned* splat centers (Open3D, MIT).

    Meshing every splat center made the mesh size swing 3.8-46 MB run to run
    on one config: far-away / faint / huge splats pulled Poisson's octree out
    to the stray points and it filled the void with surface. Cleaning first
    (``MeshFilter``): opacity filter -> robust scene box crop -> huge-splat
    filter -> statistical outlier removal -> voxel downsample; then Poisson ->
    drop low-density vertices -> crop to the box -> drop small pieces ->
    quadric decimation to ``target_triangles``. Normals are oriented toward the
    scene origin, which nerfstudio's dataparser centers on the cameras (inside
    the room for an indoor capture), so Poisson sees one consistent side.
    Per-step counts land in ``CollisionMesh.stats`` (cost sheet ``mesh``).
    """

    def __init__(self, rules: MeshFilter | None = None) -> None:
        self.rules = rules or MeshFilter()

    def derive(self, model: SplatModel, work_dir: Path) -> CollisionMesh:
        try:
            import numpy as np
            import open3d as o3d
        except ImportError as exc:
            raise MeshError("open3d/numpy not installed; run in the container") from exc

        r = self.rules
        started = time.monotonic()
        v = read_splat_ply(model.ply_path)
        xyz = np.stack([v["x"], v["y"], v["z"]], axis=1).astype(np.float64)
        stats: dict = {"splats": int(len(xyz))}

        keep = np.isfinite(xyz).all(axis=1)
        if "opacity" in v.dtype.names:
            keep &= v["opacity"] >= r.min_opacity_logit
        stats["after_opacity"] = int(keep.sum())
        if not keep.any():
            raise MeshError("no splats pass the opacity filter")

        lo, hi = scene_bounds(xyz[keep], r)
        keep &= ((xyz >= lo) & (xyz <= hi)).all(axis=1)
        stats["after_bounds"] = int(keep.sum())
        diagonal = float(np.linalg.norm(hi - lo))
        stats["bounds"] = {"min": lo.round(3).tolist(), "max": hi.round(3).tolist()}

        if all(f"scale_{i}" in v.dtype.names for i in range(3)):
            largest = np.exp(np.max(np.stack([v[f"scale_{i}"] for i in range(3)], axis=1), axis=1))
            keep &= largest <= r.max_scale_fraction * diagonal
        stats["after_scale"] = int(keep.sum())

        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(xyz[keep]))
        pcd, _ = pcd.remove_statistical_outlier(r.outlier_neighbors, r.outlier_std)
        stats["after_outliers"] = len(pcd.points)
        pcd = pcd.voxel_down_sample(diagonal * r.voxel_fraction)
        stats["meshed_points"] = len(pcd.points)
        if len(pcd.points) < 100:
            raise MeshError(f"too few points left to mesh ({len(pcd.points)})")

        pcd.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(knn=30))
        pcd.orient_normals_towards_camera_location(np.zeros(3))
        mesh, density = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=r.poisson_depth
        )
        density = np.asarray(density)
        mesh.remove_vertices_by_mask(density < np.quantile(density, r.density_quantile))
        mesh = mesh.crop(o3d.geometry.AxisAlignedBoundingBox(lo, hi))
        stats["poisson_triangles"] = len(mesh.triangles)

        clusters, sizes, _ = mesh.cluster_connected_triangles()
        clusters, sizes = np.asarray(clusters), np.asarray(sizes)
        small = sizes[clusters] < r.min_cluster_fraction * max(len(clusters), 1)
        mesh.remove_triangles_by_mask(small)
        mesh.remove_unreferenced_vertices()
        stats["clusters_kept"] = int((sizes >= r.min_cluster_fraction * len(clusters)).sum())
        if len(mesh.triangles) > r.target_triangles:
            mesh = mesh.simplify_quadric_decimation(r.target_triangles)
        mesh.remove_degenerate_triangles()
        mesh.remove_unreferenced_vertices()
        if len(mesh.triangles) == 0:
            raise MeshError("collision mesh is empty after cleaning")

        out = work_dir / f"{model.scan_id}.obj"
        o3d.io.write_triangle_mesh(str(out), mesh, write_vertex_normals=False)
        stats["vertices"] = len(mesh.vertices)
        stats["mesh_s"] = round(time.monotonic() - started, 2)
        return CollisionMesh(
            scan_id=model.scan_id,
            path=out,
            triangle_count=len(mesh.triangles),
            size_bytes=out.stat().st_size,
            stats=stats,
        )
