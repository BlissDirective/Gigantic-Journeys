"""Feed-forward reconstruction front-end: metric point maps + poses -> splat init.

capture-render-quality-v1 (external-synthesis-builds.md). The commercial-safe way to
replace the brittle COLMAP SIFT + GLOMAP stage is a feed-forward transformer that regresses
dense metric point maps + poses in one pass: **MapAnything** (facebook/map-anything-apache,
Apache-2.0) which can be *conditioned on known intrinsics/poses* -- so we feed it GJ's ARKit
metric poses to lock scale -- or **VGGT-1B-Commercial** (custom commercial licence, counsel).

This module is the port + the bridge, both GPU-free: a ``FeedForwardReconstructor`` Protocol,
a deterministic ``MockFeedForward`` for tests, and ``write_frontend_model`` which turns the
model's output into the exact COLMAP model the trainer reads -- reusing ``arkit_poses``'s
writer and gating seed points by confidence (the feed-forward analogue of the scene-graph
confidence gate). The model inference itself is cloud-GPU (Operator). Standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .arkit_poses import (
    ArkitCapture,
    ArkitFrame,
    ArkitIntrinsics,
    ArkitSeedPoint,
    write_colmap_model,
)

Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class FFFrame:
    """One view the front-end solved: image name, intrinsics, metric cam->world (16, row-major)."""

    name: str
    intrinsics: ArkitIntrinsics
    cam_to_world: tuple[float, ...]


@dataclass(frozen=True)
class FFPoint:
    """A predicted 3D point with a per-point confidence in [0, 1]."""

    xyz: Vec3
    rgb: tuple[int, int, int] = (128, 128, 128)
    confidence: float = 1.0


@dataclass(frozen=True)
class FeedForwardResult:
    """Dense metric reconstruction from a feed-forward pass."""

    frames: list[FFFrame]
    points: list[FFPoint] = field(default_factory=list)
    metric: bool = False  # True when the output is in real metres
    conditioned_on_arkit: bool = False  # True when ARKit poses/intrinsics were fed in


class FeedForwardReconstructor(Protocol):
    """A model: frames -> poses + a dense point map (optionally ARKit-conditioned)."""

    name: str

    def reconstruct(
        self,
        frame_names: list[str],
        intrinsics: ArkitIntrinsics,
        *,
        prior_poses: list[tuple[float, ...]] | None = None,
    ) -> FeedForwardResult: ...


def result_to_capture(result: FeedForwardResult, *, confidence_floor: float = 0.0) -> ArkitCapture:
    """Convert a feed-forward result into an ``ArkitCapture``, dropping low-confidence points."""
    frames = [ArkitFrame(f.name, f.intrinsics, f.cam_to_world) for f in result.frames]
    points = [
        ArkitSeedPoint(xyz=p.xyz, rgb=p.rgb)
        for p in result.points
        if p.confidence >= confidence_floor
    ]
    return ArkitCapture(frames=frames, points=points)


def write_frontend_model(
    result: FeedForwardResult, model_dir: Path, *, confidence_floor: float = 0.0
) -> int:
    """Write the COLMAP model the trainer reads; returns the seed-point count kept."""
    capture = result_to_capture(result, confidence_floor=confidence_floor)
    write_colmap_model(capture, model_dir)
    return len(capture.points)


def _identity_pose(i: int) -> tuple[float, ...]:
    # A camera stepping along +x, looking down -z (a trivial deterministic fallback pose).
    return (1, 0, 0, float(i), 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


class MockFeedForward:
    """Deterministic stand-in for a real feed-forward model (tests / dry runs; no GPU)."""

    name = "mock-feedforward"

    def reconstruct(
        self,
        frame_names: list[str],
        intrinsics: ArkitIntrinsics,
        *,
        prior_poses: list[tuple[float, ...]] | None = None,
    ) -> FeedForwardResult:
        frames: list[FFFrame] = []
        for i, name in enumerate(frame_names):
            c2w = prior_poses[i] if prior_poses is not None else _identity_pose(i)
            frames.append(FFFrame(name, intrinsics, tuple(float(x) for x in c2w)))
        # A tiny seed cloud with mixed confidence, so gating is exercised.
        points = [
            FFPoint((0.0, 0.0, -1.0), (210, 190, 170), 0.92),
            FFPoint((0.4, 0.1, -1.2), (120, 120, 120), 0.80),
            FFPoint((0.9, 0.0, -1.0), (90, 90, 90), 0.25),  # low-confidence -> gated out
        ]
        conditioned = prior_poses is not None
        return FeedForwardResult(
            frames=frames, points=points, metric=conditioned, conditioned_on_arkit=conditioned
        )
