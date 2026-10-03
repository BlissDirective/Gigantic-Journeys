"""M1-GAME-04 AudioMixer/bus config (AUTH #022): buses match the bank, ducking + budget valid."""

import copy

import bank
import mixer


def test_shipped_mixer_is_valid():
    assert mixer.validate_mixer() == []


def test_mixer_buses_match_the_sound_bank():
    assert set(mixer.load_mixer()["buses"]) == set(bank.load_bank()["buses"])


def test_non_diegetic_buses_are_dry():
    buses = mixer.load_mixer()["buses"]
    for name in ("ui", "music"):
        assert buses[name]["reverb_send"] is False


def test_priorities_are_unique():
    pr = [b["priority"] for b in mixer.load_mixer()["buses"].values()]
    assert len(set(pr)) == len(pr)


def test_a_ui_cue_ducks_action_so_a_warning_reads():
    ducks = mixer.load_mixer()["ducking"]
    assert any(
        d["trigger"] == "ui" and "movement" in d["targets"] and d["duck_db"] < 0 for d in ducks
    )


def test_validator_catches_bus_mismatch():
    m = copy.deepcopy(mixer.load_mixer())
    m["buses"].pop("tools")
    assert any("bank buses" in p for p in mixer.validate_mixer(m))


def test_validator_catches_a_positive_duck_and_bad_target():
    m = copy.deepcopy(mixer.load_mixer())
    m["ducking"].append(
        {
            "name": "bad",
            "trigger": "ui",
            "targets": ["nope"],
            "duck_db": 3.0,
            "attack_ms": 10,
            "release_ms": 100,
        }
    )
    probs = mixer.validate_mixer(m)
    assert any("bad" in p and "not a bus" in p for p in probs)
    assert any("bad" in p and "duck_db must be negative" in p for p in probs)


def test_validator_catches_reverb_on_music():
    m = copy.deepcopy(mixer.load_mixer())
    m["buses"]["music"]["reverb_send"] = True
    assert any("non-diegetic" in p for p in mixer.validate_mixer(m))


def test_load_is_deterministic():
    assert mixer.load_mixer() == mixer.load_mixer()
