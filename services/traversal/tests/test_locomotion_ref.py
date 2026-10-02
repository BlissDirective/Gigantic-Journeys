"""Reference-math tests for the movement fluidity/realism pack (#1, #3, #6) — AUTH #043."""

import math

import locomotion_ref as lr
import movement
import pytest

# --- #1 stride/speed warping ---------------------------------------------------------------


def test_natural_speed_matches_cadence_times_stride():
    p = lr.DEFAULT_LOCOMOTION
    assert lr.natural_locomotion_speed(p) == pytest.approx(
        p.refCadence * p.cadenceScale * p.refStrideA
    )


def test_stride_scale_is_one_at_natural_speed():
    assert lr.stride_scale(lr.natural_locomotion_speed()) == pytest.approx(1.0)


def test_stride_scale_clamped_both_ends():
    p = lr.DEFAULT_LOCOMOTION
    assert lr.stride_scale(0.0) == p.strideWarpMin
    assert lr.stride_scale(1_000.0) == p.strideWarpMax


def test_stride_scale_monotonic_non_decreasing():
    speeds = [0.0, 1.2, 2.4, 3.6, 4.5, 10.0]
    scales = [lr.stride_scale(s) for s in speeds]
    assert scales == sorted(scales)


def test_stride_scale_rejects_negative_speed():
    with pytest.raises(ValueError):
        lr.stride_scale(-0.1)


def test_more_real_default_compresses_stride_at_run():
    # the more-miniature-real default (higher cadence) means quick, short steps: at the
    # movement.json run speed the stride compresses below 1.0, within the clamp.
    run = movement.load().speeds.run
    s = lr.stride_scale(run)
    assert lr.DEFAULT_LOCOMOTION.strideWarpMin <= s < 1.0
    # the keep-the-fantasy variant (lower cadence) stretches the stride back up
    assert lr.stride_scale(run, lr.LocomotionParams(cadenceScale=1.5)) > s


# --- #6 snappier accel/decel ---------------------------------------------------------------


def test_approach_speed_converges_without_overshoot():
    cur, target = 0.0, 3.6
    for _ in range(1000):
        nxt = lr.approach_speed(cur, target, 0.016)
        assert nxt <= target + 1e-9  # never overshoots upward
        cur = nxt
        if cur == target:
            break
    assert cur == pytest.approx(target)


def test_approach_speed_noop_on_zero_dt_or_at_target():
    assert lr.approach_speed(2.0, 3.0, 0.0) == 2.0
    assert lr.approach_speed(3.0, 3.0, 0.016) == 3.0


# --- #6 miniature cadence dial -------------------------------------------------------------


def test_physical_ceiling_is_sqrt_scale():
    assert lr.physical_cadence_multiplier(12) == pytest.approx(math.sqrt(12))
    assert lr.physical_cadence_multiplier(1) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        lr.physical_cadence_multiplier(0)


def test_realism_fraction_between_human_and_full():
    frac = lr.realism_fraction(12)  # default cadenceScale 1.5
    assert 0.0 < frac < 1.0
    # at the physical ceiling the dial reads 1.0; at scale 1 there is no miniature effect
    full = lr.LocomotionParams(cadenceScale=math.sqrt(12))
    assert lr.realism_fraction(12, full) == pytest.approx(1.0)
    assert lr.realism_fraction(1) == 0.0


def test_cadence_for_scale_reports_ceiling_and_choice():
    d = lr.cadence_for_scale(12)
    assert d["physical_ceiling"] == pytest.approx(math.sqrt(12))
    assert d["chosen_multiplier"] == pytest.approx(lr.DEFAULT_LOCOMOTION.cadenceScale)
    assert 0.0 < d["realism_fraction"] < 1.0


# --- #3 procedural landing (Bible §5 tiers) ------------------------------------------------


def test_landing_thresholds_come_from_movement_json():
    cfg = movement.load()
    assert lr.landing_tier(cfg.landing.soft - 0.01) == "soft"


def test_landing_tiers_follow_bible_boundaries():
    assert lr.landing_tier(1.0) == "soft"
    assert lr.landing_tier(1.5, moving_forward=True) == "roll"
    assert lr.landing_tier(1.5, moving_forward=False) == "hard"  # neutral stick → hard, not roll
    assert lr.landing_tier(3.0) == "hard"
    assert lr.landing_tier(5.0) == "hard"
    assert lr.landing_tier(5.1) == "recover"


def test_soft_surface_bonus_is_one_tier_gentler():
    assert lr.landing_tier(3.0, "walkable-soft") == "roll"  # hard → roll
    assert lr.landing_tier(6.0, "walkable-soft") == "hard"  # recover → hard
    assert lr.landing_tier(1.0, "walkable-soft") == "soft"  # already gentlest, stays


def test_landing_response_scales_with_tier():
    p = lr.DEFAULT_LANDING
    soft = lr.landing_response(1.0)
    hard = lr.landing_response(4.0)
    assert soft.tier == "soft" and hard.tier == "hard"
    assert soft.absorb_fraction < hard.absorb_fraction
    assert hard.absorb_fraction == pytest.approx(p.maxCrouchFraction)
    assert soft.keeps_speed_fraction == 1.0
    assert lr.landing_response(2.0).keeps_speed_fraction == pytest.approx(0.6)  # roll keeps 60%
    assert hard.keeps_speed_fraction == 0.0


def test_recover_tier_locks_control_longest():
    recover = lr.landing_response(6.0)
    assert recover.tier == "recover"
    assert recover.control_lock_s == lr.RECOVER_LOCK_SEC


def test_landing_response_rejects_negative_fall():
    with pytest.raises(ValueError):
        lr.landing_response(-1.0)


def test_defaults_match_movement_json():
    """The dataclass defaults are the shipped movement.json profile (AUTH #043 lockstep)."""
    assert lr.LocomotionParams.from_movement_config() == lr.DEFAULT_LOCOMOTION
    assert lr.LandingParams.from_movement_config() == lr.DEFAULT_LANDING


def test_more_miniature_real_is_the_default_profile():
    """Owner addendum 2026-10-01 (AUTH #043): gravityScale 0.9, cadenceScale 1.9, accel 0.10."""
    cfg = movement.load()
    assert cfg.gravityScale == pytest.approx(0.9)
    assert cfg.locomotion.cadenceScale == pytest.approx(1.9)
    assert cfg.locomotion.accelTimeSec == pytest.approx(0.10)
