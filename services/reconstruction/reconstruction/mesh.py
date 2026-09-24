"""Collision-mesh derivation (Open3D).

The real adapter imports Open3D (MIT) lazily and runs in the container;
importing this module never requires it. Tests use ``fakes.FakeMesher``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import CollisionMesh, ReconstructionError, SplatModel


class MeshError(ReconstructionError):
    """Raised when mesh derivation fails or Open3D is missing."""


class Mesher(Protocol):
    """Derive a low-poly collision mesh for gameplay physics."""

    def derive(self, model: SplatModel, work_dir: Path) -> CollisionMesh: ...


class Open3DMesher:
    """Poisson surface reconstruction from splat centers (Open3D, MIT).

    Produces a watertight low-poly collision mesh. Open3D is imported lazily so
    this module imports without it outside the container.
    """

    def derive(self, model: SplatModel, work_dir: Path) -> CollisionMesh:
        try:
            import open3d as o3d
        except ImportError as exc:
            raise MeshError("open3d not installed; run in the container") from exc

        pcd = o3d.io.read_point_cloud(str(model.ply_path))
        pcd.estimate_normals()
        mesh, _ = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
        out = work_dir / f"{model.scan_id}.obj"
        o3d.io.write_triangle_mesh(str(out), mesh)
        return CollisionMesh(
            scan_id=model.scan_id,
            path=out,
            triangle_count=len(mesh.triangles),
            size_bytes=out.stat().st_size,
        )
