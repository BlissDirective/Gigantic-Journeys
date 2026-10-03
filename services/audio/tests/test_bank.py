"""M1-GAME-04 sound bank (AUTH #022): coverage of every verb + well-formedness."""

import copy

import bank


def test_shipped_bank_is_valid_and_complete():
    assert bank.validate_bank() == []


def test_every_v1_verb_has_a_sound():
    events = set(bank.load_bank()["events"])
    assert bank.verb_set() <= events


def test_buses_and_weights_are_declared():
    b = bank.load_bank()
    buses, weights = set(b["buses"]), set(b["weights"])
    for name, e in b["events"].items():
        assert e["bus"] in buses, name
        assert e["weight"] in weights, name


def test_validator_catches_a_missing_verb():
    b = copy.deepcopy(bank.load_bank())
    b["events"].pop("wall-run")
    probs = bank.validate_bank(b)
    assert any("wall-run" in p and "no sound" in p for p in probs)


def test_validator_catches_a_bad_bus_and_low_round_robin():
    b = copy.deepcopy(bank.load_bank())
    b["events"]["walk"]["bus"] = "nope"
    b["events"]["run"]["round_robin"] = 1
    probs = bank.validate_bank(b)
    assert any("walk" in p and "bus" in p for p in probs)
    assert any("run" in p and "machine-gun" in p for p in probs)


def test_load_is_deterministic():
    assert bank.load_bank() == bank.load_bank()
