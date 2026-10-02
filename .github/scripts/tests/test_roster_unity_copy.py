"""M1-AVAT-01: the Unity StreamingAssets roster is a byte-identical copy of data/avatar/roster."""

from __future__ import annotations

import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "copy_roster_to_unity.py"
spec = importlib.util.spec_from_file_location("copy_roster_to_unity", SCRIPT)
assert spec and spec.loader
copy_roster = importlib.util.module_from_spec(spec)
spec.loader.exec_module(copy_roster)


def test_unity_roster_copy_is_byte_identical() -> None:
    assert copy_roster.drift() == [], "run python .github/scripts/copy_roster_to_unity.py"


def test_ships_the_manifest_and_all_eight_presets() -> None:
    names = [str(p) for p in copy_roster.files()]
    assert names[0] == "roster.json"
    assert len([n for n in names if n.startswith("presets/")]) == 8
