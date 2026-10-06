"""Information-gain capture guidance (FisherRF method, clean-room).

capture-render-quality-v1 (external-synthesis-builds.md). FisherRF uses the Fisher
information of a radiance field to score how much a view would *teach* the model (with no
ground truth), giving next-best-view selection and a per-pixel uncertainty map. FisherRF's
own code is non-commercial (built on Inria 3DGS), so this is a **clean-room reimplementation
of the published idea** on GJ's own stack -- no FisherRF/Inria code, weights, or outputs.

The exact Fisher information needs the differentiable renderer's Hessian (GPU, Operator).
This module is the deterministic, GPU-free planner that drives the two shippable capture-UX
wins: it represents the scene as cells (e.g. scene-graph surfaces or a voxel grid), treats a
cell's uncertainty as a decreasing function of how often it has been observed (the
information proxy the renderer's Fisher diagonal later refines), and uses the same
submodular information-gain score for:

  * **next-best-view / "you missed this wall"** coverage coaching during capture, and
  * **informative-frame selection** -- pick a small, high-coverage subset of a ≤4-min
    video's frames so SfM / training sees less redundant data and the capture stays short.

A "view" is given as the set of cell ids it observes (visibility is scene geometry the
Operator computes; the planner takes the cell sets as its contract). Standard library only;
deterministic.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence


def cell_uncertainty(count: int) -> float:
    """Uncertainty of a cell observed ``count`` times: 1/(1+count), decreasing to 0."""
    if count < 0:
        raise ValueError("count must be >= 0")
    return 1.0 / (1.0 + count)


class CoverageModel:
    """Per-cell observation counts and the uncertainty derived from them."""

    def __init__(self, cells: Iterable[str]) -> None:
        self.counts: dict[str, int] = {c: 0 for c in cells}
        if not self.counts:
            raise ValueError("CoverageModel needs at least one cell")

    def copy(self) -> CoverageModel:
        m = CoverageModel(self.counts.keys())
        m.counts = dict(self.counts)
        return m

    def observe(self, cell_ids: Iterable[str]) -> None:
        for c in cell_ids:
            if c in self.counts:
                self.counts[c] += 1

    def uncertainty(self, cell: str) -> float:
        return cell_uncertainty(self.counts[cell])

    def total_uncertainty(self) -> float:
        return sum(cell_uncertainty(c) for c in self.counts.values())

    def coverage_gaps(self, threshold: float = 0.5) -> list[str]:
        """Cells still at or above ``threshold`` uncertainty, worst (least-seen) first."""
        gaps = [(self.counts[c], c) for c in self.counts if self.uncertainty(c) >= threshold]
        gaps.sort(key=lambda kc: (kc[0], kc[1]))
        return [c for _, c in gaps]


def information_gain(model: CoverageModel, view_cells: Iterable[str]) -> float:
    """Total-uncertainty reduction if ``view_cells`` were observed once more.

    For a cell seen ``c`` times the marginal gain is 1/(1+c) - 1/(2+c); unseen cells give
    the most, so the score rewards views that cover under-observed regions (submodular).
    """
    gain = 0.0
    seen: set[str] = set()
    for cell in view_cells:
        if cell in model.counts and cell not in seen:
            c = model.counts[cell]
            gain += cell_uncertainty(c) - cell_uncertainty(c + 1)
            seen.add(cell)
    return gain


def next_best_view(
    model: CoverageModel, candidates: Mapping[str, Iterable[str]]
) -> tuple[str, float]:
    """The candidate view with the largest information gain, as ``(view_id, gain)``.

    Ties break on the view id, so the result is deterministic.
    """
    if not candidates:
        raise ValueError("need at least one candidate view")
    best_id: str | None = None
    best_gain = -1.0
    for vid in sorted(candidates):
        gain = information_gain(model, candidates[vid])
        if gain > best_gain:
            best_gain, best_id = gain, vid
    assert best_id is not None
    return best_id, best_gain


def select_informative_frames(
    views: Mapping[str, Iterable[str]],
    k: int,
    *,
    seed: CoverageModel | None = None,
    min_gain: float = 1e-9,
) -> list[str]:
    """Greedily pick up to ``k`` views that maximise cumulative coverage (submodular).

    Starts from ``seed`` (a partial capture) or an empty model over the union of all cells,
    repeatedly adding the highest-marginal-gain view, until ``k`` are chosen or no view adds
    more than ``min_gain``. Returns the chosen view ids in selection order; deterministic.
    """
    if k <= 0:
        return []
    view_sets = {vid: set(cells) for vid, cells in views.items()}
    if seed is not None:
        model = seed.copy()
    else:
        universe = set().union(*view_sets.values()) if view_sets else set()
        if not universe:
            return []
        model = CoverageModel(universe)
    chosen: list[str] = []
    remaining = set(view_sets)
    while remaining and len(chosen) < k:
        pick, gain = next_best_view(model, {vid: view_sets[vid] for vid in remaining})
        if gain <= min_gain:
            break
        chosen.append(pick)
        model.observe(view_sets[pick])
        remaining.discard(pick)
    return chosen


def coverage_from_views(
    cells: Sequence[str], observed_views: Iterable[Iterable[str]]
) -> CoverageModel:
    """Build a CoverageModel over ``cells`` and apply the already-captured ``observed_views``."""
    model = CoverageModel(cells)
    for view in observed_views:
        model.observe(view)
    return model
