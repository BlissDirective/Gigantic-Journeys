"""No-GPU reference adapters for tests and a local dry run.

They produce deterministic, tiny artifacts so the full pipeline can be
exercised without COLMAP/gsplat/Open3D. Never used inside the container.
"""

from __future__ import annotations

from pathlib import Path

from .models import (
    CameraPoses,
    CollisionMesh,
    CompressedSplat,
    MiB,
    ReconstructionConfig,
    ScanInput,
    SplatModel,
)


class FakeSfM:
    """Return deterministic poses without running SfM."""

    def run(self, scan: ScanInput, work_dir: Path) -> CameraPoses:
        sparse = work_dir / "sparse" / "0"
        sparse.mkdir(parents=True, exist_ok=True)
        return CameraPoses(
            scan_id=scan.scan_id,
            sparse_dir=sparse,
            registered_images=scan.image_count,
        )


class FakeTrainer:
    """Write a header-only PLY declaring ``splat_count`` vertices."""

    def __init__(self, splat_count: int | None = None) -> None:
        self._splat_count = splat_count

    def train(self, poses: CameraPoses, work_dir: Path, config: ReconstructionConfig) -> SplatModel:
        n = self._splat_count if self._splat_count is not None else config.splat_budget
        ply = work_dir / f"{poses.scan_id}.ply"
        ply.write_text(f"ply\nformat ascii 1.0\nelement vertex {n}\nend_header\n")
        return SplatModel(scan_id=poses.scan_id, ply_path=ply, splat_count=n)


class FakeCompressor:
    """Report a chosen compressed size without writing a large file."""

    def __init__(self, size_bytes: int = 60 * MiB) -> None:
        self._size_bytes = size_bytes

    def compress(
        self, model: SplatModel, work_dir: Path, config: ReconstructionConfig
    ) -> CompressedSplat:
        out = work_dir / f"{model.scan_id}.{config.compress_format.value}"
        out.write_bytes(b"fake-compressed-splat")
        return CompressedSplat(
            scan_id=model.scan_id,
            path=out,
            fmt=config.compress_format,
            size_bytes=self._size_bytes,
            splat_count=model.splat_count,
        )


class FakeMesher:
    """Write a stub mesh and report a chosen triangle count."""

    def __init__(self, triangle_count: int = 50_000) -> None:
        self._triangle_count = triangle_count

    def derive(self, model: SplatModel, work_dir: Path) -> CollisionMesh:
        out = work_dir / f"{model.scan_id}.obj"
        out.write_text("# fake collision mesh\n")
        return CollisionMesh(
            scan_id=model.scan_id,
            path=out,
            triangle_count=self._triangle_count,
            size_bytes=out.stat().st_size,
        )
