"""FisherRF clean-room capture guidance: coverage uncertainty + information-gain selection."""

import pytest
from reconstruction.capture_guidance import (
    CoverageModel,
    cell_uncertainty,
    coverage_from_views,
    information_gain,
    next_best_view,
    select_informative_frames,
)

# A four-wall room; views cover disjoint or overlapping wall sets.
CELLS = ["w1", "w2", "w3", "w4"]
VIEWS = {"vA": {"w1", "w2"}, "vB": {"w3", "w4"}, "vC": {"w1", "w2"}}  # vC duplicates vA


def test_cell_uncertainty_decreases_with_observation():
    assert cell_uncertainty(0) == 1.0
    assert cell_uncertainty(1) == 0.5
    assert cell_uncertainty(3) == pytest.approx(0.25)
    with pytest.raises(ValueError):
        cell_uncertainty(-1)


def test_model_observe_and_total():
    m = CoverageModel(CELLS)
    assert m.total_uncertainty() == pytest.approx(4.0)  # 4 cells x 1.0
    m.observe(["w1", "w2"])
    assert m.uncertainty("w1") == 0.5
    assert m.total_uncertainty() == pytest.approx(0.5 + 0.5 + 1.0 + 1.0)
    with pytest.raises(ValueError):
        CoverageModel([])


def test_information_gain_rewards_unseen_and_decreases():
    m = CoverageModel(CELLS)
    assert information_gain(m, VIEWS["vA"]) == pytest.approx(1.0)  # 2 unseen cells x 0.5
    m.observe(VIEWS["vA"])
    assert information_gain(m, VIEWS["vA"]) == pytest.approx(2 * (0.5 - 1 / 3), abs=1e-6)


def test_next_best_view_picks_most_uncertain_coverage():
    m = CoverageModel(CELLS)
    vid, gain = next_best_view(m, VIEWS)
    assert vid == "vA" and gain == pytest.approx(1.0)  # tie on gain -> lowest id
    m.observe(VIEWS["vA"])
    # now vB (two unseen) beats vC (two already-seen)
    assert next_best_view(m, {"vB": VIEWS["vB"], "vC": VIEWS["vC"]})[0] == "vB"
    with pytest.raises(ValueError):
        next_best_view(m, {})


def test_select_prefers_disjoint_coverage_and_caps_k():
    picks = select_informative_frames(VIEWS, 2)
    assert picks == ["vA", "vB"]  # disjoint pair beats the redundant vC
    assert select_informative_frames(VIEWS, 2) == picks  # deterministic
    assert select_informative_frames(VIEWS, 0) == []


def test_coverage_gaps_flags_unseen_walls():
    m = coverage_from_views(CELLS, [{"w1", "w2"}, {"w1", "w2"}])  # w1,w2 seen twice
    assert m.coverage_gaps(threshold=0.5) == ["w3", "w4"]  # only the unseen walls remain
