"""Submap windowing + loop-closure scheduling for a full-video feed-forward pass.

capture-render-quality-v1 (external-synthesis-builds.md). A single feed-forward pass cannot
hold a 3-4 minute (hundreds-of-frames) capture in GPU memory with global consistency.
VGGT-SLAM (BSD-2) solves this by cutting the video into overlapping submaps, globally
aligning them, and closing loops when the sweep revisits a spot. This module is the
GPU-free scheduling core of that pattern: deterministic submap windows over the frame
sequence, and loop-closure candidate detection from per-submap descriptors (the retrieval
model that produces descriptors is Operator; the windowing + candidate logic is here).

Standard library only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence


def submap_windows(num_frames: int, window: int, stride: int) -> list[tuple[int, int]]:
    """Overlapping ``[start, end)`` windows covering all frames.

    ``window`` is the frames per submap, ``stride`` how far the window advances (``stride <
    window`` gives overlap, which is what keeps neighbouring submaps alignable). The final
    window is clamped so the last frames are always covered.
    """
    if num_frames < 1:
        raise ValueError("num_frames must be >= 1")
    if window < 1 or stride < 1:
        raise ValueError("window and stride must be >= 1")
    if window >= num_frames:
        return [(0, num_frames)]
    out: list[tuple[int, int]] = []
    start = 0
    while True:
        end = min(start + window, num_frames)
        out.append((start, end))
        if end >= num_frames:
            break
        start += stride
    # Ensure the tail is covered by a full-width final window.
    if out[-1][1] < num_frames:
        out.append((num_frames - window, num_frames))
    return out


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def loop_closure_candidates(
    descriptors: Sequence[Sequence[float]], *, threshold: float = 0.9, min_gap: int = 2
) -> list[tuple[int, int]]:
    """Submap pairs ``(i, j)`` whose descriptors are similar enough to be a loop closure.

    ``min_gap`` skips temporally-adjacent submaps (they always overlap). Pairs are returned
    with ``i < j``, best (most similar) first, deterministically.
    """
    if min_gap < 1:
        raise ValueError("min_gap must be >= 1")
    scored: list[tuple[float, int, int]] = []
    n = len(descriptors)
    for i in range(n):
        for j in range(i + min_gap, n):
            sim = _cosine(descriptors[i], descriptors[j])
            if sim >= threshold:
                scored.append((sim, i, j))
    scored.sort(key=lambda s: (-s[0], s[1], s[2]))
    return [(i, j) for _, i, j in scored]
