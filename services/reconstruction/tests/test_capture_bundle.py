"""Capture bundle contract (M1-CAPT-01 AT-1, AT-4).

The golden bundles in services/reconstruction/bundle/fixtures/ are written by the Unity
CaptureBundleWriter (EditMode test CaptureBundleWriterTests.MatchesTheGoldenBundle keeps them
byte-identical to its output), so validating them here ties the C# writer to the schema. The
mutation cases prove each non-schema rule actually fires.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from tools import capture_bundle as cb

jsonschema = pytest.importorskip("jsonschema")

FIXTURES = Path(__file__).resolve().parents[1] / "bundle" / "fixtures"
GOLDEN = sorted(p for p in FIXTURES.iterdir() if p.is_dir())


def test_schema_is_valid_2020_12():
    jsonschema.Draft202012Validator.check_schema(json.loads(cb.SCHEMA.read_text(encoding="utf-8")))


def test_there_are_room_and_tabletop_goldens():
    modes = {json.loads((p / "manifest.json").read_text())["mode"] for p in GOLDEN}
    assert modes == {"room", "tabletop"}


@pytest.mark.parametrize("bundle", GOLDEN, ids=lambda p: p.name)
def test_golden_bundle_from_the_unity_writer_is_valid(bundle):
    assert cb.validate(bundle) == []


@pytest.mark.parametrize("bundle", GOLDEN, ids=lambda p: p.name)
def test_golden_bundle_carries_the_named_contract_contents(bundle):
    m = json.loads((bundle / "manifest.json").read_text())
    first = json.loads((bundle / "frames.jsonl").read_text().splitlines()[0])
    assert len(first["pose"]) == 16  # per-frame ARKit pose
    assert set(m["camera"]["intrinsics"]) == {"fx", "fy", "cx", "cy"}  # intrinsics
    assert m["world"]["gravity"] and m["world"]["metric_scale"] == "arkit-metres"  # up + scale
    assert m["readiness"]["source"] == "gj-app" and 0 <= m["readiness"]["score"] <= 1
    assert m["coverage"]["map"]["painted"]  # coverage map
    assert m["privacy"] == {"metadata_stripped": True, "location_recorded": False}
    assert (m["depth"] is not None) == m["device"]["lidar"]


@pytest.fixture
def bundle(tmp_path):
    src = next(p for p in GOLDEN if "room" in p.name)
    dst = tmp_path / "b"
    shutil.copytree(src, dst)
    return dst


def _edit_manifest(bundle: Path, fn) -> None:
    path = bundle / "manifest.json"
    m = json.loads(path.read_text())
    fn(m)
    path.write_text(json.dumps(m))


def _edit_frames(bundle: Path, fn) -> None:
    path = bundle / "frames.jsonl"
    frames = [json.loads(line) for line in path.read_text().splitlines()]
    fn(frames)
    path.write_text("".join(json.dumps(f) + "\n" for f in frames))


def _errors(bundle: Path) -> str:
    return "\n".join(cb.validate(bundle))


def test_a_location_field_is_rejected(bundle):
    _edit_manifest(bundle, lambda m: m["device"].update(gps={"lat": 1.0}))
    assert "gps" in _errors(bundle)


def test_a_location_field_in_a_frame_is_rejected(bundle):
    _edit_frames(bundle, lambda fs: fs[3].update(location=[41.9, -87.6]))
    assert "location" in _errors(bundle)


def test_a_time_of_day_is_rejected(bundle):
    _edit_manifest(bundle, lambda m: m.update(captured_on="2026-09-29T03:14:15"))
    assert "captured_on" in _errors(bundle)


def test_a_non_rigid_pose_is_rejected(bundle):
    def scale(fs):
        fs[5]["pose"][0] = 2.0

    _edit_frames(bundle, scale)
    assert "orthonormal" in _errors(bundle)


def test_a_reflected_pose_is_rejected(bundle):
    def mirror(fs):
        fs[5]["pose"][0:3] = [-v for v in fs[5]["pose"][0:3]]

    _edit_frames(bundle, mirror)
    assert "reflection" in _errors(bundle)


def test_counts_must_match_the_frames(bundle):
    _edit_manifest(bundle, lambda m: m["frames"].update(count=m["frames"]["count"] + 1))
    assert "frames.count" in _errors(bundle)


def test_accepted_count_must_match(bundle):
    _edit_frames(bundle, lambda fs: fs[0].update(accepted=False))
    assert "frames.accepted" in _errors(bundle)


def test_frame_indices_must_increase(bundle):
    _edit_frames(bundle, lambda fs: fs[4].update(i=fs[3]["i"]))
    assert "does not increase" in _errors(bundle)


def test_passes_must_tile_the_frames(bundle):
    _edit_manifest(
        bundle, lambda m: m["passes"][1].update(first_frame=m["passes"][0]["last_frame"])
    )
    assert "overlap" in _errors(bundle)


def test_coverage_fraction_must_match_the_map(bundle):
    _edit_manifest(bundle, lambda m: m["coverage"].update(fraction=0.99))
    assert "coverage.fraction" in _errors(bundle)


def test_coverage_map_shape_must_match(bundle):
    _edit_manifest(bundle, lambda m: m["coverage"]["map"]["painted"].pop())
    assert "azimuth_bins x elevation_bins" in _errors(bundle)


def test_room_needs_a_view_sphere_map(bundle):
    _edit_manifest(bundle, lambda m: m["coverage"]["map"].update(kind="orbit"))
    assert "view-sphere" in _errors(bundle)


def test_depth_without_lidar_is_rejected(bundle):
    _edit_manifest(bundle, lambda m: m["device"].update(lidar=False))
    assert "LiDAR" in _errors(bundle)


def test_gravity_must_oppose_up(bundle):
    _edit_manifest(bundle, lambda m: m["world"].update(gravity=[0, 1, 0]))
    assert "opposite" in _errors(bundle)


def test_media_mode_requires_video_and_depth_files(bundle):
    errors = cb.validate(bundle, media=True)
    assert any("video.mov missing" in e for e in errors)
    assert any("depth/0.bin missing" in e for e in errors)
    (bundle / "video.mov").write_bytes(b"\0")
    (bundle / "depth").mkdir()
    m = json.loads((bundle / "manifest.json").read_text())
    size = m["depth"]["width"] * m["depth"]["height"] * 2
    for line in (bundle / "frames.jsonl").read_text().splitlines():
        f = json.loads(line)
        if f.get("depth"):
            (bundle / "depth" / f"{f['i']}.bin").write_bytes(b"\0" * size)
    assert cb.validate(bundle, media=True) == []


def test_cli_exit_codes(bundle, capsys):
    assert cb.main([str(bundle)]) == 0
    assert "OK" in capsys.readouterr().out
    _edit_manifest(bundle, lambda m: m.update(mode="garden"))
    assert cb.main([str(bundle)]) == 1


def test_missing_manifest(tmp_path):
    assert cb.validate(tmp_path) == ["manifest.json missing"]
