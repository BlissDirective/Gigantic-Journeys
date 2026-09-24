"""Splat compression adapters (PLY -> SPZ/SOG via splat-transform).

The real adapter runs ``splat-transform`` (MIT) inside the container; importing
this module never requires it. Tests use ``fakes.FakeCompressor``.
"""

from __future__ import annotations

import subprocess  # noqa: S404 - orchestrating trusted CLI tools by fixed argv
from pathlib import Path
from typing import Protocol

from .models import CompressedSplat, ReconstructionConfig, ReconstructionError, SplatModel
from .tools import require


class CompressError(ReconstructionError):
    """Raised when compression fails to produce output."""


class Compressor(Protocol):
    """Compress an uncompressed splat for delivery."""

    def compress(
        self, model: SplatModel, work_dir: Path, config: ReconstructionConfig
    ) -> CompressedSplat: ...


class SplatTransformCompressor:
    """playcanvas/splat-transform (MIT): PLY -> .spz (~10x) or .sog (~20x)."""

    def compress(
        self, model: SplatModel, work_dir: Path, config: ReconstructionConfig
    ) -> CompressedSplat:
        tool = require("splat-transform")
        out = work_dir / f"{model.scan_id}.{config.compress_format.value}"
        subprocess.run([tool, str(model.ply_path), str(out)], check=True)
        if not out.exists():
            raise CompressError(f"compressed output not produced: {out}")
        return CompressedSplat(
            scan_id=model.scan_id,
            path=out,
            fmt=config.compress_format,
            size_bytes=out.stat().st_size,
            splat_count=model.splat_count,
        )
