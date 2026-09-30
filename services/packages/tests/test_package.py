"""Environment-package format + reference validator (M1-GAME-01 loader prep)."""

import json
from pathlib import Path

import package
import pytest

REPO = Path(__file__).resolve().parents[3]
FIX = REPO / "data" / "schemas" / "environment" / "fixtures" / "valid"
GOLDEN = REPO / "unity" / "Assets" / "GiganticJourneys" / "Tests" / "Environments" / "desk-tabletop"

STUB = {
    "splat": b"SPZ placeholder (presence-only stub; real corpus package replaces this).\n",
    "collision_mesh": b"glB placeholder (presence-only stub; real corpus package replaces this).\n",
    "thumbnail": b"WEBP placeholder (presence-only stub; real corpus package replaces this).\n",
}


def _triple():
    return (
        json.loads((FIX / "scene_graph.desk-tabletop.json").read_text(encoding="utf-8")),
        json.loads((FIX / "traversal_graph.desk-tabletop.json").read_text(encoding="utf-8")),
        json.loads((FIX / "environment_spec.desk-tabletop.json").read_text(encoding="utf-8")),
    )


def test_reference_validate_clean_on_frozen_triple(tmp_path):
    scene, graph, spec = _triple()
    pkg = package.assemble(scene, graph, spec, STUB, tmp_path / "pkg")
    assert package.validate(pkg) == []


def test_committed_golden_package_validates():
    assert GOLDEN.is_dir(), "the committed golden package should exist for the Unity loader test"
    assert package.validate(GOLDEN) == []


def test_golden_matches_frozen_fixtures():
    # drift guard: the committed golden's docs are the frozen fixtures (renamed per assets)
    assert json.loads((GOLDEN / "environment_spec.json").read_text()) == _triple()[2]
    assert json.loads((GOLDEN / "scene_graph.json").read_text()) == _triple()[0]
    assert json.loads((GOLDEN / "traversal_graph.json").read_text()) == _triple()[1]


def test_missing_binary_asset_is_reported(tmp_path):
    scene, graph, spec = _triple()
    pkg = package.assemble(scene, graph, spec, STUB, tmp_path / "pkg")
    (pkg / spec["assets"]["splat"]).unlink()
    problems = package.validate(pkg)
    assert any("splat" in p for p in problems)


def test_missing_manifest_is_reported(tmp_path):
    (tmp_path / "empty").mkdir()
    problems = package.validate(tmp_path / "empty")
    assert problems and "environment_spec.json" in problems[0]


def test_inconsistent_triple_is_reported(tmp_path):
    scene, graph, spec = _triple()
    spec = dict(spec)
    spec["scale_multiplier"] = spec["scale_multiplier"] + 1  # now disagrees with scene_graph
    pkg = package.assemble(scene, graph, spec, STUB, tmp_path / "pkg")
    problems = package.validate(pkg)
    assert any("consistency" in p and "scale_multiplier" in p for p in problems)


def test_assemble_rejects_missing_asset_bytes(tmp_path):
    scene, graph, spec = _triple()
    with pytest.raises(package.PackageError):
        package.assemble(scene, graph, spec, {"splat": b"x"}, tmp_path / "pkg")
