"""Self-hosted reconstruction pipeline (M1-CAPT-03, ADR-0005 / AUTH #030).

Headless orchestration: capture bundle -> SfM (COLMAP/GLOMAP) -> Gaussian-splat
training (gsplat primary, Brush secondary) -> compression (.spz/.sog) ->
collision mesh (Open3D) -> environment package. Pure-stdlib orchestration with
pluggable adapters; heavy tools live in the CUDA container (see Dockerfile).
"""

from __future__ import annotations

from .appearance import AffineColor, AppearanceModel, apply_affine_color
from .arkit_poses import (
    ARKIT_POSES_FILENAME,
    ArkitCapture,
    ArkitFrame,
    ArkitIntrinsics,
    ArkitSeedPoint,
    ArkitSfM,
    colmap_pose,
    parse_arkit_capture,
    write_colmap_model,
)
from .capture_guidance import (
    CoverageModel,
    cell_uncertainty,
    coverage_from_views,
    information_gain,
    next_best_view,
    select_informative_frames,
)
from .compress import CompressError, Compressor, SplatTransformCompressor
from .cost import (
    DAILY_CAP_USD,
    SPIKE_CAP_USD,
    CostLedger,
    ScanCost,
    SpendCapError,
    estimate_usd,
)
from .delivery import CompressionPlan, estimate_bytes, plan_compression
from .depth_normal import edge_aware_log_l1, normal_consistency, normal_tv, pearson_depth_loss
from .depth_prior import DepthPrior, MockDepthPrior, align_scale_shift, apply_scale_shift, to_metric
from .exposure_trajectory import sample_cubic_bspline, sample_linear, slerp
from .fakes import FakeCompressor, FakeMesher, FakeSfM, FakeTrainer
from .feedforward_frontend import (
    FeedForwardReconstructor,
    FeedForwardResult,
    FeedForwardSfM,
    MockFeedForward,
    result_to_capture,
    write_frontend_model,
)
from .licenses import MANIFEST, Component, LicenseError, assert_commercial_safe
from .mesh import Mesher, MeshError, Open3DMesher
from .models import (
    OFFSITE_SOURCES,
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
    require_offsite_source,
)
from .pipeline import ReconstructionRun, run_pipeline
from .positional_index import PositionalIndexScheme
from .render_quality import ns_train_capped_own_args, splatfacto_quality_args
from .sfm import SFM_CHOICES, SFM_SELECTABLE, ColmapSfM, GlomapSfM, SfM, select_sfm
from .submap import loop_closure_candidates, submap_windows
from .tools import ToolNotFoundError, require
from .trainer import (
    BrushTrainer,
    GsplatTrainer,
    Trainer,
    TrainerError,
    recipe_rasterize_mode,
)

__all__ = [
    "ARKIT_POSES_FILENAME",
    "AffineColor",
    "AppearanceModel",
    "CompressionPlan",
    "CoverageModel",
    "cell_uncertainty",
    "coverage_from_views",
    "information_gain",
    "next_best_view",
    "select_informative_frames",
    "DepthPrior",
    "FeedForwardReconstructor",
    "FeedForwardResult",
    "FeedForwardSfM",
    "MockDepthPrior",
    "MockFeedForward",
    "align_scale_shift",
    "apply_affine_color",
    "apply_scale_shift",
    "edge_aware_log_l1",
    "estimate_bytes",
    "loop_closure_candidates",
    "normal_consistency",
    "normal_tv",
    "pearson_depth_loss",
    "plan_compression",
    "result_to_capture",
    "sample_cubic_bspline",
    "sample_linear",
    "slerp",
    "ns_train_capped_own_args",
    "recipe_rasterize_mode",
    "splatfacto_quality_args",
    "submap_windows",
    "to_metric",
    "write_frontend_model",
    "DAILY_CAP_USD",
    "MANIFEST",
    "OFFSITE_SOURCES",
    "SFM_CHOICES",
    "SFM_SELECTABLE",
    "SPIKE_CAP_USD",
    "ArkitCapture",
    "ArkitFrame",
    "ArkitIntrinsics",
    "ArkitSeedPoint",
    "ArkitSfM",
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
    "PositionalIndexScheme",
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
    "colmap_pose",
    "estimate_usd",
    "parse_arkit_capture",
    "read_ply_vertex_count",
    "require",
    "require_offsite_source",
    "run_pipeline",
    "select_sfm",
    "write_colmap_model",
]
