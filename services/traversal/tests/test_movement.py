"""Tests for the movement.json loader (ticket M0-MOVE-01, AT-3)."""

import dataclasses
import json
import pathlib

import movement
import pytest

CONFIG = pathlib.Path(movement.__file__).resolve().parents[2] / "config" / "movement.json"


def _valid_dict() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_load_real_config_spot_checks() -> None:
    cfg = movement.load()
    assert cfg.avatarHeightA == 1.0
    assert cfg.speeds.run == 3.6
    assert cfg.jump.coyoteMs == 100
    assert cfg.verticals.mantle == 1.4
    assert cfg.grapple.reachA == 6.0
    assert cfg.wallRun.minEntrySpeed == 3.0
    assert cfg.assist.slipsOff is True
    assert cfg.assist.autoGrab is True


def test_with_margin() -> None:
    assert movement.MARGIN == 0.85
    assert movement.with_margin(6.0) == pytest.approx(5.1)
    assert movement.with_margin(1.0) == pytest.approx(0.85)
    assert movement.with_margin(0.0) == pytest.approx(0.0)


def test_missing_key_raises() -> None:
    data = _valid_dict()
    del data["grapple"]
    with pytest.raises(movement.MovementConfigError, match="missing key"):
        movement.loads(data)


def test_missing_nested_key_raises() -> None:
    data = _valid_dict()
    del data["speeds"]["run"]
    with pytest.raises(movement.MovementConfigError, match="speeds"):
        movement.loads(data)


def test_unknown_key_raises() -> None:
    data = _valid_dict()
    data["speeds"]["teleport"] = 99.0
    with pytest.raises(movement.MovementConfigError, match="unknown key"):
        movement.loads(data)


def test_frozen_config_is_immutable() -> None:
    cfg = movement.load()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.avatarHeightA = 2.0


def test_flatten_matches_shared_fixture() -> None:
    """C#/Python agreement (M0-MOVE-01 AT-4): the Unity test reads the same fixture."""
    expected = json.loads(movement.FIXTURE.read_text(encoding="utf-8"))
    flat = movement.flatten(movement.load())
    assert flat == expected, "regenerate: python services/traversal/movement.py --write-fixture"
    assert len(flat) == len(_valid_dict_paths(_valid_dict()))


def _valid_dict_paths(data: dict, prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            paths += _valid_dict_paths(value, f"{prefix}{key}.")
        else:
            paths.append(f"{prefix}{key}")
    return paths
