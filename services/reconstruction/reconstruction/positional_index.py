"""Train-short / test-long positional indices for a many-view reconstructor.

Clean-room reference for the view-index scheme a GJ-owned feed-forward reconstructor
would use, implemented from the *published idea* only (Fast3R's "positional embedding
interpolation", i.e. randomised positional indices; see
design/proposals/external-synthesis-builds.md). No external code, weights, or outputs.

The problem: a phone scan has a variable, often large, number of frames, but we can
only afford to train on a handful of views at a time. If training always numbered its
few views 0, 1, 2, ..., the model would never see the higher index positions and would
have to *extrapolate* at inference -- which fails. The fix is twofold:

1. **Randomised training indices.** With a pool of ``max_index`` positional slots, a
   training sample of ``num_views`` views draws its indices at *random* from the whole
   pool, so across training every slot is exercised even though each batch is small
   ("train short", cover the full range).
2. **Index interpolation at inference.** ``num_views`` views are spread evenly across
   the same ``[0, max_index - 1]`` range -- fractional positions when there are more
   views than slots -- so an arbitrarily long scan still lands *inside* the trained
   range ("test long", never extrapolate).

This module is the deterministic index/embedding math (pure standard library); the
learned network that consumes it is a later, data-gated build.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionalIndexScheme:
    """Assign positional indices (and sinusoidal embeddings) to views.

    ``max_index`` is the size of the positional pool the model is trained to cover;
    ``dim`` is the (even) embedding width.
    """

    max_index: int
    dim: int

    def __post_init__(self) -> None:
        if self.max_index < 2:
            raise ValueError("max_index must be >= 2")
        if self.dim < 2 or self.dim % 2 != 0:
            raise ValueError("dim must be a positive even number")

    def sample_training_indices(self, num_views: int, *, seed: int) -> list[int]:
        """``num_views`` distinct indices drawn from the whole pool, sorted.

        Deterministic for a given ``seed``. Raises if more views than slots are asked
        for (training batches are always "short", so this should not happen).
        """
        if num_views < 1:
            raise ValueError("num_views must be >= 1")
        if num_views > self.max_index:
            raise ValueError(
                f"num_views {num_views} exceeds the positional pool {self.max_index}; "
                "inference_indices handles the test-long case instead"
            )
        rng = random.Random(seed)  # noqa: S311 - deterministic view sampling, not security
        return sorted(rng.sample(range(self.max_index), num_views))

    def inference_indices(self, num_views: int) -> list[float]:
        """``num_views`` positions spread evenly across ``[0, max_index - 1]``.

        For ``num_views > max_index`` the positions are fractional (interpolated) but
        still inside the trained range, so the model never extrapolates.
        """
        if num_views < 1:
            raise ValueError("num_views must be >= 1")
        if num_views == 1:
            return [0.0]
        span = self.max_index - 1
        step = span / (num_views - 1)
        return [round(i * step, 9) for i in range(num_views)]

    def embedding(self, index: float) -> list[float]:
        """Sinusoidal positional embedding of width ``dim`` for a (fractional) index."""
        out: list[float] = []
        half = self.dim // 2
        for k in range(half):
            freq = 1.0 / (10000.0 ** (2.0 * k / self.dim))
            out.append(math.sin(index * freq))
            out.append(math.cos(index * freq))
        return out

    def training_coverage(self, num_views: int, trials: int, *, seed: int) -> float:
        """Fraction of the pool's slots hit across ``trials`` training samples.

        Demonstrates that "short" batches still exercise the whole index range; with
        enough trials this approaches 1.0.
        """
        if trials < 1:
            raise ValueError("trials must be >= 1")
        seen: set[int] = set()
        for t in range(trials):
            seen.update(self.sample_training_indices(num_views, seed=seed + t))
        return len(seen) / self.max_index
