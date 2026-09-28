"""Video -> frame-set planning for the open-video corpus (M1-PIPE-01).

The reconstruction pipeline consumes an image set. Corpus clips are videos, so
``modal_app.extract_clip_frames`` turns one into frames, inside Modal, in three
steps this module plans (standard library only, so CI tests it without ffmpeg):

1. **Segments.** Only the clip's ``recommended_segments`` (clip time, visually
   reviewed: no title cards, exteriors or hard cuts) are decoded.
2. **Rate.** ``plan_rate`` picks the target rate so the whole clip lands at or
   under the frame cap (default 300; 400 for long clips), never above
   ``max_fps``. Candidates are decoded at ``oversample`` x that rate.
3. **Sharpness.** ``select_sharpest`` keeps the sharpest candidate of every
   window of ``oversample`` consecutive candidates (variance of the Laplacian,
   computed in the container) and drops windows whose best frame is still far
   blurrier than the clip's median (motion blur, focus hunting).
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

DEFAULT_MAX_FRAMES = 300
LONG_CLIP_MAX_FRAMES = 400
LONG_CLIP_S = 240.0
# 2 fps: at 3 fps a slow orbit gave mean SfM track length ~22 (tabletop pilot,
# 2026-09-28), which only slows bundle adjustment down.
DEFAULT_MAX_FPS = 2.0
DEFAULT_OVERSAMPLE = 3
DEFAULT_LONG_SIDE = 1600
# A window is dropped when its sharpest frame scores below this fraction of the
# clip median (blur is relative: texture-poor scenes score low everywhere).
BLUR_REJECT_FRACTION = 0.3


@dataclass(frozen=True)
class Segment:
    """A usable range of the clip, in clip seconds."""

    start_s: float
    end_s: float

    @property
    def length_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


@dataclass(frozen=True)
class FramePlan:
    """How to sample one clip."""

    segments: tuple[Segment, ...]
    usable_s: float
    max_frames: int
    target_fps: float
    candidate_fps: float
    oversample: int
    long_side: int

    @property
    def expected_frames(self) -> int:
        return int(self.usable_s * self.target_fps)

    def as_dict(self) -> dict:
        return {
            "segments": [[s.start_s, s.end_s] for s in self.segments],
            "usable_s": round(self.usable_s, 2),
            "max_frames": self.max_frames,
            "target_fps": round(self.target_fps, 4),
            "candidate_fps": round(self.candidate_fps, 4),
            "oversample": self.oversample,
            "long_side": self.long_side,
            "expected_frames": self.expected_frames,
        }


def segments_from_meta(meta: dict) -> tuple[Segment, ...]:
    """The clip's ``recommended_segments`` (clip time); the whole clip if absent."""
    rows = meta.get("recommended_segments") or []
    segs = [Segment(float(r["clip_start_s"]), float(r["clip_end_s"])) for r in rows]
    if not segs:
        segs = [Segment(0.0, float(meta["duration_s"]))]
    segs = [s for s in segs if s.length_s > 0.5]
    if not segs:
        raise ValueError(f"{meta.get('id', '?')}: no usable segment")
    return tuple(sorted(segs, key=lambda s: s.start_s))


def plan_rate(
    meta: dict,
    max_frames: int = 0,
    max_fps: float = DEFAULT_MAX_FPS,
    oversample: int = DEFAULT_OVERSAMPLE,
    long_side: int = DEFAULT_LONG_SIDE,
) -> FramePlan:
    """Sampling plan for one clip (``max_frames`` 0 = 300, or 400 for long clips)."""
    segs = segments_from_meta(meta)
    usable = sum(s.length_s for s in segs)
    if max_frames <= 0:
        max_frames = LONG_CLIP_MAX_FRAMES if usable > LONG_CLIP_S else DEFAULT_MAX_FRAMES
    target = min(max_fps, max_frames / usable)
    return FramePlan(
        segments=segs,
        usable_s=usable,
        max_frames=max_frames,
        target_fps=target,
        candidate_fps=target * oversample,
        oversample=oversample,
        long_side=long_side,
    )


def select_sharpest(
    scores: list[list[float]],
    oversample: int = DEFAULT_OVERSAMPLE,
    reject_fraction: float = BLUR_REJECT_FRACTION,
) -> list[tuple[int, int]]:
    """Pick (segment, candidate) indices: the sharpest per window, blurry windows dropped.

    ``scores[s][i]`` is the sharpness of candidate ``i`` of segment ``s``.
    Windows never straddle segments (a cut between them).
    """
    picks: list[tuple[int, int, float]] = []
    for s, seg_scores in enumerate(scores):
        for w in range(0, len(seg_scores), oversample):
            window = seg_scores[w : w + oversample]
            best = max(range(len(window)), key=window.__getitem__)
            picks.append((s, w + best, window[best]))
    if not picks:
        return []
    floor = reject_fraction * median(p[2] for p in picks)
    return [(s, i) for s, i, score in picks if score >= floor]
