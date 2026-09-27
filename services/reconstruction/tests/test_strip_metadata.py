"""strip_metadata.py removes GPS / EXIF / XMP / QuickTime location + device tags (M0-CAPT-01 AT-3).

Every fixture is generated here (FFmpeg / heif-enc) and gets SYNTHETIC GPS, make,
model, software and serial injected with ExifTool - never real media
(SECURITY_CHECKLIST §4.3 / §6.5). CI installs the tools and sets
GJ_REQUIRE_MEDIA_TOOLS=1 so a missing tool fails instead of skipping.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from tools import strip_metadata as sm

TOOLS = ("ffmpeg", "ffprobe", "exiftool", "heif-enc")
MISSING = [t for t in TOOLS if not shutil.which(t)]
if MISSING and os.environ.get("GJ_REQUIRE_MEDIA_TOOLS") == "1":
    raise RuntimeError(f"media tools required in CI but missing: {MISSING}")
needs_tools = pytest.mark.skipif(bool(MISSING), reason=f"missing media tools: {MISSING}")

LAT, LON = "37.7749", "-122.4194"  # synthetic (a public landmark), never a real capture
GPS_TAGS = [
    f"-GPSLatitude={LAT}",
    "-GPSLatitudeRef=N",
    f"-GPSLongitude={LON[1:]}",
    "-GPSLongitudeRef=W",
    f"-XMP:GPSLatitude={LAT}",
    f"-XMP:GPSLongitude={LON}",
    "-Make=Apple",
    "-Model=iPhone 15 Pro",
    "-Software=18.0",
    "-SerialNumber=SYNTHETIC123",
]


def run(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def exif(path: Path) -> dict:
    return json.loads(run("exiftool", "-j", "-a", "-G1", "-ee", "-n", str(path)))[0]


def assert_no_location_or_device(path: Path) -> None:
    tags = exif(path)
    leaked = [
        k
        for k in tags
        if any(
            w in k.lower()
            for w in ("gps", "location", "6709", "make", "model", "serial", "software", "xmp")
        )
    ]
    assert leaked == [], leaked
    assert sm.verify_clean(path) == []


def make_video(tmp: Path, name: str, rotation: int = 90, audio: bool = True) -> Path:
    out = tmp / name
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]
    cmd += ["-f", "lavfi", "-i", "testsrc2=size=320x240:rate=30"]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440"]
    cmd += ["-t", "1", "-c:v", "libx265", "-x265-params", "log-level=none", "-tag:v", "hvc1"]
    if audio:
        cmd += ["-c:a", "aac"]
    cmd += ["-movflags", "use_metadata_tags"]
    # iPhone-style QuickTime `keys` atoms: com.apple.quicktime.location.ISO6709 etc.
    cmd += ["-metadata", "com.apple.quicktime.location.ISO6709=+37.7749-122.4194+010.000/"]
    cmd += ["-metadata", "com.apple.quicktime.make=Apple"]
    cmd += ["-metadata", "com.apple.quicktime.model=iPhone 15 Pro"]
    cmd += ["-metadata", "com.apple.quicktime.software=18.0"]
    cmd += ["-metadata", "com.apple.quicktime.creationdate=2026-09-20T10:00:00-0500"]
    cmd += [str(out)]
    run(*cmd)
    # plus the classic udta ©xyz location, UserData make/model, an XMP packet, and the
    # display rotation of a portrait iPhone video (track matrix)
    run(
        "exiftool", "-q", "-overwrite_original", f"-Rotation={rotation}",
        f"-UserData:GPSCoordinates={LAT}, {LON}, 10", "-UserData:Make=Apple",
        "-UserData:Model=iPhone 15 Pro", f"-XMP:GPSLatitude={LAT}", f"-XMP:GPSLongitude={LON}",
        "-XMP:SerialNumber=SYNTHETIC123", str(out),
    )  # fmt: skip
    return out


def make_image(tmp: Path, name: str) -> Path:
    png = tmp / "src.png"
    run(
        "ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
        "testsrc2=size=64x48", "-frames:v", "1", str(png),
    )  # fmt: skip
    out = tmp / name
    if out.suffix.lower() in {".heic", ".heif"}:
        run("heif-enc", "-q", "50", str(png), "-o", str(out))
    else:
        run("ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(png), str(out))
    run("exiftool", "-q", "-overwrite_original", *GPS_TAGS, "-Orientation#=6", str(out))
    return out


def stream_hash(path: Path) -> str:
    return run(
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-map", "0:v:0",
        "-c", "copy", "-f", "streamhash", "-hash", "sha256", "-",
    )  # fmt: skip


# ------------------------------------------------------------------ video
@needs_tools
@pytest.mark.parametrize("name", ["capture.MOV", "capture.mp4"])
def test_strips_location_atoms_and_device_tags_from_mov_and_mp4(tmp_path, name):
    src = make_video(tmp_path, name)
    before = exif(src)
    assert any("GPS" in k for k in before), "fixture must carry synthetic GPS"
    assert sm.verify_clean(src), "the verifier must flag the unstripped fixture"

    res = sm.strip_file(src, tmp_path / "out" / name)

    assert res.location_found is True
    assert res.device_model == "iPhone 15 Pro"
    assert res.captured_on == "2026-09-20"
    assert_no_location_or_device(res.output)
    assert json.loads(
        run("ffprobe", "-v", "error", "-show_format", "-of", "json", str(res.output))
    )["format"].get("tags", {}).keys() <= {"major_brand", "minor_version", "compatible_brands"}


@needs_tools
def test_video_is_remuxed_not_reencoded_and_keeps_rotation(tmp_path):
    src = make_video(tmp_path, "capture.mov", rotation=90)
    res = sm.strip_file(src, tmp_path / "out" / "capture.mov")
    assert stream_hash(src) == stream_hash(res.output)  # identical HEVC packets
    video, duration = sm.video_info(res.output)
    assert video["codec"] == "hevc" and video["rotation"] in (90, -90, 270, -270)
    assert (video["width"], video["height"]) == (320, 240)
    assert video["fps"] == pytest.approx(30, abs=0.1)
    assert duration == pytest.approx(1.0, abs=0.2)
    assert run(
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
        "stream=codec_tag_string", "-of", "default=nw=1:nk=1", str(res.output),
    ).strip() == "hvc1"  # fmt: skip


@needs_tools
def test_audio_dropped_by_default_and_kept_on_request(tmp_path):
    src = make_video(tmp_path, "capture.mov")
    silent, _ = sm.video_info(sm.strip_file(src, tmp_path / "a" / "capture.mov").output)
    kept = sm.strip_file(src, tmp_path / "b" / "capture.mov", keep_audio=True)
    assert silent["audio_kept"] is False
    assert sm.video_info(kept.output)[0]["audio_kept"] is True
    assert_no_location_or_device(kept.output)


# ------------------------------------------------------------------ images
@needs_tools
def test_strips_exif_gps_xmp_from_jpeg_and_keeps_orientation(tmp_path):
    src = make_image(tmp_path, "photo.jpg")
    assert any("GPS" in k for k in exif(src))
    res = sm.strip_file(src, tmp_path / "out" / "photo.jpg")
    assert res.location_found and res.device_model == "iPhone 15 Pro"
    assert_no_location_or_device(res.output)
    assert exif(res.output).get("IFD0:Orientation") == 6


@needs_tools
def test_strips_exif_gps_xmp_from_heic(tmp_path):
    src = make_image(tmp_path, "photo.heic")
    assert any("GPS" in k for k in exif(src))
    res = sm.strip_file(src, tmp_path / "out" / "photo.heic")
    assert res.location_found
    assert_no_location_or_device(res.output)
    assert not any(k.startswith(("IFD0:", "ExifIFD:", "GPS:")) for k in exif(res.output))


# ------------------------------------------------------------------ safety
@needs_tools
def test_refuses_in_place_and_type_changes(tmp_path):
    src = make_image(tmp_path, "photo.jpg")
    with pytest.raises(sm.StripError, match="in place"):
        sm.strip_file(src, src)
    with pytest.raises(sm.StripError, match="file type"):
        sm.strip_file(src, tmp_path / "photo.heic")


def test_rejects_unsupported_types(tmp_path):
    with pytest.raises(sm.StripError, match="unsupported"):
        sm.kind_of(tmp_path / "notes.txt")


@needs_tools
def test_cli_strips_to_out_dir_and_verify_mode_flags_leaks(tmp_path, capsys):
    src = make_image(tmp_path, "photo.jpg")
    assert sm.main(["--verify", str(src)]) == 1
    assert sm.main([str(src), "--out-dir", str(tmp_path / "clean")]) == 0
    assert sm.main(["--verify", str(tmp_path / "clean" / "photo.jpg")]) == 0
    out = capsys.readouterr().out
    assert LAT not in out and "SYNTHETIC" not in out  # names only, never values


def test_sensitive_exif_flags_names_not_values():
    tags = {
        "SourceFile": "x",
        "File:FileName": "x",
        "Keys:GPSCoordinates": "1 2",
        "UserData:Make": "Apple",
        "XMP-exif:Anything": "x",
        "Track1:MatrixStructure": "0 1 0",
        "Composite:Rotation": 90,
        "Composite:GPSPosition": "1 2",
        "ICC_Profile:DeviceModel": "display",
        "QuickTime:Duration": 1.0,
    }
    assert sm.sensitive_exif(tags) == [
        "Composite:GPSPosition",
        "Keys:GPSCoordinates",
        "UserData:Make",
        "XMP-exif:Anything",
    ]
    assert sm.has_location(tags)
    assert not sm.has_location({"QuickTime:Duration": 1})


def test_sensitive_ffprobe_allows_only_muxer_tags():
    clean = {
        "format": {"tags": {"major_brand": "qt  "}},
        "streams": [{"index": 0, "tags": {"handler_name": "VideoHandler", "vendor_id": "FFMP"}}],
    }
    assert sm.sensitive_ffprobe(clean) == []
    dirty = {
        "format": {"tags": {"location": "+37-122/"}},
        "streams": [{"index": 0, "tags": {"encoder": "x"}}],
    }
    assert sm.sensitive_ffprobe(dirty) == ["format:location", "stream0:encoder"]


def test_capture_date_is_date_only():
    assert sm.capture_date({"Keys:CreationDate": "2026:09:20 10:00:00-05:00"}) == "2026-09-20"
    assert sm.capture_date({"QuickTime:CreateDate": "0000:00:00 00:00:00"}) is None
    assert sm.device_model({"IFD0:Model": "iPhone 15 Pro"}) == "iPhone 15 Pro"
    assert sm.device_model({"IFD0:Model": "Canon EOS"}) is None
