"""Tests for .github/scripts/ios_app_icon.py (TestFlight "Missing app icon" guard)."""

from __future__ import annotations

import importlib.util
import json
import struct
import zlib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "ios_app_icon.py"
spec = importlib.util.spec_from_file_location("ios_app_icon", SCRIPT)
ios_app_icon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ios_app_icon)


def _png(path: Path, w: int, h: int, ctype: int) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0)
    path.write_bytes(
        ios_app_icon.PNG_SIG
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(b""))
        + chunk(b"IEND", b"")
    )


def _project(tmp_path: Path, entry: dict, png: tuple[int, int, int] | None) -> Path:
    icons = tmp_path / "Unity-iPhone" / "Images.xcassets" / "AppIcon.appiconset"
    icons.mkdir(parents=True)
    (icons / "Contents.json").write_text(json.dumps({"images": [entry]}))
    if png and entry.get("filename"):
        _png(icons / entry["filename"], *png)
    return tmp_path


MARKETING = {
    "idiom": "ios-marketing",
    "size": "1024x1024",
    "scale": "1x",
    "filename": "Icon-1024.png",
}


def test_opaque_1024_marketing_icon_passes(tmp_path):
    proj = _project(tmp_path, MARKETING, (1024, 1024, 2))
    assert ios_app_icon.check(proj).name == "Icon-1024.png"
    assert ios_app_icon.main(["x", str(proj)]) == 0


def test_single_size_universal_icon_passes(tmp_path):
    entry = {
        "idiom": "universal",
        "platform": "ios",
        "size": "1024x1024",
        "filename": "AppIcon.png",
    }
    assert ios_app_icon.check(_project(tmp_path, entry, (1024, 1024, 2))).name == "AppIcon.png"


def test_unassigned_slot_fails(tmp_path):
    entry = {k: v for k, v in MARKETING.items() if k != "filename"}
    with pytest.raises(FileNotFoundError, match="no file"):
        ios_app_icon.check(_project(tmp_path, entry, None))


def test_missing_appiconset_fails(tmp_path):
    assert ios_app_icon.main(["x", str(tmp_path)]) == 1


def test_wrong_size_fails(tmp_path):
    with pytest.raises(ValueError, match="512x512"):
        ios_app_icon.check(_project(tmp_path, MARKETING, (512, 512, 2)))


def test_alpha_without_sips_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(ios_app_icon.shutil, "which", lambda _: None)
    with pytest.raises(RuntimeError, match="alpha"):
        ios_app_icon.check(_project(tmp_path, MARKETING, (1024, 1024, 6)))
