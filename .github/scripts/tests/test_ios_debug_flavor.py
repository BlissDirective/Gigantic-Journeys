"""Tests for the M1-UNITY-01 device-test additions to .github/scripts/ios_debug_flavor.py."""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import json
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve().parents[1] / "ios_debug_flavor.py"
spec = importlib.util.spec_from_file_location("ios_debug_flavor", SCRIPT)
flavor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flavor)

SLUG = "room-x"
EBS = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1045 &1
EditorBuildSettings:
  m_ObjectHideFlags: 0
  serializedVersion: 2
  m_Scenes:
  - enabled: 1
    path: Assets/Scenes/MovementTest.unity
    guid: ddcce6d4c6bd00aeab546991f93496e7
  m_configObjects: {}
"""


def _project(tmp_path: Path) -> Path:
    unity = tmp_path / "unity"
    (unity / "ProjectSettings").mkdir(parents=True)
    (unity / "ProjectSettings" / "EditorBuildSettings.asset").write_text(EBS)
    scene = unity / flavor.DEVICE_TEST_SCENE
    scene.parent.mkdir(parents=True)
    scene.write_text("scene")
    meta = "fileFormatVersion: 2\nguid: 0123456789abcdef0123456789abcdef\n"
    Path(f"{scene}.meta").write_text(meta)
    return unity


def test_add_scene_appends_once_after_existing_scenes(tmp_path):
    unity = _project(tmp_path)
    settings = unity / "ProjectSettings" / "EditorBuildSettings.asset"
    flavor.add_scene(settings, flavor.DEVICE_TEST_SCENE)
    flavor.add_scene(settings, flavor.DEVICE_TEST_SCENE)
    text = settings.read_text()
    assert text.count(flavor.DEVICE_TEST_SCENE) == 1
    assert text.index("MovementTest.unity") < text.index(flavor.DEVICE_TEST_SCENE)
    assert "    guid: 0123456789abcdef0123456789abcdef\n  m_configObjects" in text


def test_committed_build_list_has_no_device_test_scene():
    text = (ROOT / "unity" / "ProjectSettings" / "EditorBuildSettings.asset").read_text()
    assert flavor.DEVICE_TEST_SCENE not in text, "release builds must not ship the SplatRoom scene"
    assert (ROOT / "unity" / f"{flavor.DEVICE_TEST_SCENE}.meta").is_file()


def _package(files: dict[str, bytes]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return gzip.compress(raw.getvalue())


def _manifest(data: bytes) -> dict:
    return {
        "slug": SLUG,
        "resource": f"GJSplatRoom/{SLUG}",
        "splatCount": 3,
        "packageSha256": hashlib.sha256(data).hexdigest(),
        "packageBytes": len(data),
    }


def test_unpack_splat_verifies_and_extracts(tmp_path):
    data = _package({f"{SLUG}.asset": b"a", f"{SLUG}.asset.meta": b"m", f"{SLUG}_pos.bytes": b"p"})
    names = flavor.unpack_splat(data, _manifest(data), tmp_path / "out")
    assert names == [f"{SLUG}.asset", f"{SLUG}.asset.meta", f"{SLUG}_pos.bytes"]
    assert (tmp_path / "out" / f"{SLUG}_pos.bytes").read_bytes() == b"p"


def test_unpack_splat_rejects_hash_mismatch(tmp_path):
    data = _package({f"{SLUG}.asset": b"a"})
    manifest = _manifest(data)
    manifest["packageSha256"] = "0" * 64
    with pytest.raises(ValueError, match="mismatch"):
        flavor.unpack_splat(data, manifest, tmp_path)


@pytest.mark.parametrize("bad", ["../evil.asset", f"sub/{SLUG}.asset", f"{SLUG}.cs", "other.asset"])
def test_unpack_splat_rejects_unexpected_entries(tmp_path, bad):
    data = _package({f"{SLUG}.asset": b"a", bad: b"x"})
    with pytest.raises(ValueError, match="unexpected"):
        flavor.unpack_splat(data, _manifest(data), tmp_path / "out")
    assert not (tmp_path / "evil.asset").exists()


def test_fetch_splat_requires_https(tmp_path, capsys):
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(_manifest(b"")))
    assert flavor.fetch_splat(manifest, tmp_path, "http://example.com/x") == 1
    assert "https" in capsys.readouterr().out


def test_fetch_splat_from_file_unpacks(tmp_path):
    data = _package({f"{SLUG}.asset": b"a", f"{SLUG}_pos.bytes": b"p"})
    pkg = tmp_path / "pkg.tar.gz"
    pkg.write_bytes(data)
    manifest = tmp_path / "m.json"
    manifest.write_text(json.dumps(_manifest(data)))
    assert flavor.fetch_splat(manifest, tmp_path / "out", file=pkg) == 0
    assert (tmp_path / "out" / f"{SLUG}.asset").is_file()


def test_committed_manifest_matches_unity_descriptor():
    manifest = json.loads(
        (ROOT / "unity/Assets/GiganticJourneys/DeviceTest/splat-room.json").read_text()
    )
    assert len(manifest["packageSha256"]) == 64 and manifest["packageBytes"] > 0
    assert manifest["resource"].endswith(manifest["slug"])
    assert "CC BY" in manifest["license"] and manifest["credit"]


@pytest.mark.parametrize(
    ("scene", "splat", "expect_scene", "expect_splat", "rc"),
    [
        (True, True, "present", "present", 0),
        (False, False, "absent", "absent", 0),
        (True, False, "absent", "absent", 1),
        (False, True, "absent", "absent", 1),
        (True, False, "present", "absent", 0),
    ],
)
def test_check_device_test(tmp_path, scene, splat, expect_scene, expect_splat, rc):
    data = tmp_path / "Data"
    data.mkdir()
    blob = b"x"
    if scene:
        blob += flavor.DEVICE_TEST_SCENE.encode()
    if splat:
        blob += f"{SLUG}_pos".encode()
    blob += f"GJSplatRoom/{SLUG}".encode()  # the descriptor alone is not the splat
    (data / "globalgamemanagers").write_bytes(blob)
    assert flavor.check_device_test(tmp_path, expect_scene, expect_splat, SLUG) == rc
