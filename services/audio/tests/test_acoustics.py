"""M1-GAME-04 scale-aware acoustics (AUTH #022): Sabine reverb + scale pitch/gain."""

import json
import math
from pathlib import Path

import acoustics

REPO = Path(__file__).resolve().parents[3]
FIX = REPO / "data" / "schemas" / "environment" / "fixtures" / "valid"


def test_reverb_follows_sabine_when_unclamped():
    p = acoustics.reverb_profile(50.0, 80.0, 0.15)
    expected = acoustics.TUNING["sabine_k"] * 50.0 / (80.0 * 0.15)
    assert math.isclose(p.rt60_s, round(expected, 4), rel_tol=1e-3)
    assert 0.0 <= p.wet <= 1.0
    assert p.hf_damping == 0.15


def test_bigger_room_rings_longer():
    small = acoustics.reverb_profile(8.0, 24.0, 0.15)
    big = acoustics.reverb_profile(800.0, 520.0, 0.15)
    assert big.rt60_s > small.rt60_s
    assert big.wet >= small.wet


def test_more_absorptive_is_deader():
    live = acoustics.reverb_profile(100.0, 120.0, 0.03)  # tile / metal
    dead = acoustics.reverb_profile(100.0, 120.0, 0.45)  # curtain / carpet
    assert live.rt60_s > dead.rt60_s


def test_rt60_is_clamped():
    rc = acoustics.TUNING["rt60_clamp_s"]
    tiny = acoustics.reverb_profile(0.5, 40.0, 0.6)
    huge = acoustics.reverb_profile(5000.0, 200.0, 0.02)
    assert tiny.rt60_s == rc["min"]
    assert huge.rt60_s == rc["max"]


def _room(dim_a, material, mult=12, m_per_a=0.1458):
    return {
        "scale": {"multiplier": mult, "metres_per_A": m_per_a},
        "bounds": {"min": [0, 0, 0], "max": [dim_a, dim_a, dim_a]},
        "surfaces": [{"id": "s", "material": material, "area_A2": dim_a * dim_a}],
    }


def test_small_dead_room_vs_large_live_room():
    # AT-2: reverb audibly differs between a small dead room and a large live one.
    dead = acoustics.reverb_from_scene_graph(_room(10, "carpet-rug"))
    live = acoustics.reverb_from_scene_graph(_room(60, "tile-stone"))
    assert live.rt60_s > dead.rt60_s


def test_reverb_from_desk_fixture_is_sane_and_deterministic():
    doc = json.loads((FIX / "scene_graph.desk-tabletop.json").read_text(encoding="utf-8"))
    a = acoustics.reverb_from_scene_graph(doc)
    b = acoustics.reverb_from_scene_graph(doc)
    rc = acoustics.TUNING["rt60_clamp_s"]
    assert a == b
    assert rc["min"] <= a.rt60_s <= rc["max"]
    assert 0.0 <= a.wet <= 1.0


def test_scale_pitch_tinier_world_pitches_up_and_weight_resists():
    ref = acoustics.TUNING["scale"]["ref_multiplier"]
    at_ref = acoustics.scale_pitch_semitones(ref, "light")
    tinier = acoustics.scale_pitch_semitones(ref * 2, "light")
    bigger = acoustics.scale_pitch_semitones(ref / 2, "light")
    assert at_ref == 0.0
    assert tinier > 0.0 > bigger
    heavy = acoustics.scale_pitch_semitones(ref * 2, "heavy")
    assert 0.0 < heavy < tinier  # a heavy event resists the up-shift so booms stay big


def test_scale_pitch_and_gain_are_clamped():
    sc = acoustics.TUNING["scale"]
    assert acoustics.scale_pitch_semitones(10000, "light") == sc["pitch_clamp_semitones"]["max"]
    assert acoustics.scale_gain_db(10000) == sc["gain_clamp_db"]["min"]


def test_gain_moves_with_scale():
    ref = acoustics.TUNING["scale"]["ref_multiplier"]
    assert acoustics.scale_gain_db(ref) == 0.0
    assert acoustics.scale_gain_db(ref * 4) < 0.0  # tinier world is a touch quieter
