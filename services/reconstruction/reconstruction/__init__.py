"""Self-hosted reconstruction pipeline (M1-CAPT-03, ADR-0005 / AUTH #030).

Headless orchestration: capture bundle -> SfM (COLMAP/GLOMAP) -> Gaussian-splat
training (gsplat primary, Brush secondary) -> compression (.spz/.sog) ->
collision mesh (Open3D) -> environment package. Pure-stdlib orchestration with
pluggable adapters; heavy tools live in the CUDA container (see Dockerfile).
"""

from __future__ import annotations

from .compress import CompressError, Compressor, SplatTransformCompressor
from .cost import (
    DAILY_CAP_USD,
    SPIKE_CAP_USD,
    CostLedger,
    ScanCost,
    SpendCapError,
    estimate_usd,
)
from .fakes import FakeCompressor, FakeMesher, FakeSfM, FakeTrainer
from .licenses import MANIFEST, Component, LicenseError, assert_commercial_safe
from .mesh import Mesher, MeshError, Open3DMesher
from .models import (
    CameraPoses,
    CollisionMesh,
    CompressedSplat,
    EnvironmentPackage,
    Format,
    ReconstructionConfig,
    ReconstructionError,
    ScanInput,
    Source,
    SplatModel,
    read_ply_vertex_count,
)
from .pipeline import ReconstructionRun, run_pipeline
from .sfm import ColmapSfM, GlomapSfM, SfM
from .tools import ToolNotFoundError, require
from .trainer import BrushTrainer, GsplatTrainer, Trainer, TrainerError

__all__ = [
    "DAILY_CAP_USD",
    "MANIFEST",
    "SPIKE_CAP_USD",
    "BrushTrainer",
    "CameraPoses",
    "CollisionMesh",
    "ColmapSfM",
    "Component",
    "CompressError",
    "CompressedSplat",
    "Compressor",
    "CostLedger",
    "EnvironmentPackage",
    "FakeCompressor",
    "FakeMesher",
    "FakeSfM",
    "FakeTrainer",
    "Format",
    "GlomapSfM",
    "GsplatTrainer",
    "LicenseError",
    "MeshError",
    "Mesher",
    "Open3DMesher",
    "ReconstructionConfig",
    "ReconstructionError",
    "ReconstructionRun",
    "ScanCost",
    "ScanInput",
    "SfM",
    "Source",
    "SpendCapError",
    "SplatModel",
    "SplatTransformCompressor",
    "ToolNotFoundError",
    "Trainer",
    "TrainerError",
    "assert_commercial_safe",
    "estimate_usd",
    "read_ply_vertex_count",
    "require",
    "run_pipeline",
]
