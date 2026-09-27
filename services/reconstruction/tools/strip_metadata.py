#!/usr/bin/env python3
"""Remove GPS, EXIF, XMP, QuickTime location, device and serial metadata from media.

M0-CAPT-01 AT-3 · SECURITY_CHECKLIST §4.1-4.2. Lossless: video is remuxed with
``ffmpeg -c copy`` (no re-encode) and images are rewritten by ExifTool (no
recompression). Every output is then re-verified, and a file that still carries
anything location- or device-identifying is deleted and reported as a failure.

    python services/reconstruction/tools/strip_metadata.py IN [IN ...] --out-dir DIR
    python services/reconstruction/tools/strip_metadata.py --verify FILE [FILE ...]

Video (.mov .mp4 .m4v): keeps the first real video stream only (drops iPhone
timed-metadata tracks, cover art, chapters, and - unless ``--keep-audio`` -
audio, which can carry voices); drops every container and stream tag (``udta``
©xyz, ``meta``/``keys`` com.apple.quicktime.location.ISO6709 / make / model /
software, XMP ``uuid``); zeroes the creation dates; keeps the display rotation
matrix. Verified with ffprobe (no tags beyond the muxer's own) and ExifTool
(``-ee`` so timed metadata is read too).

Images (.jpg .jpeg .heic .heif): ``exiftool -all=``; JPEG keeps only the
Orientation tag and the ICC colour profile (HEIC orientation lives in the
``irot`` box, which is kept). Verified with ExifTool.

Needs ``ffmpeg``/``ffprobe`` (video) and ``exiftool`` (all formats) on PATH.
Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

VERSION = "1.0"
TOOL_ID = f"strip_metadata.py {VERSION}"

VIDEO_EXTS = {".mov": "mov", ".mp4": "mp4", ".m4v": "mp4"}
IMAGE_EXTS = {".jpg", ".jpeg", ".heic", ".heif"}

# Tag names that identify a place, a device, a person or a specific unit.
SENSITIVE_TAG = re.compile(
    r"gps|location|6709|latitude|longitude|altitude|^xyz$|"
    r"^make$|^model$|makernote|serial|^software$|lens|camera(id|serial|owner)|owner|"
    r"artist|author|creator|hostcomputer|usercomment|contentidentifier|"
    r"livephoto|devicename|^device|imageuniqueid|documentid|instanceid",
    re.IGNORECASE,
)
# Groups whose presence alone means metadata survived.
SENSITIVE_GROUP = re.compile(r"^(GPS|XMP|MakerNotes|Apple|Keys|UserData|ItemList)", re.IGNORECASE)
# Groups ExifTool synthesises about the file itself, or that describe colour, not capture.
IGNORED_GROUP = re.compile(r"^(ExifTool|System|File|ICC|ICC_Profile|ICC-.*)$", re.IGNORECASE)
# Composite tags derived from the kept structure (never from stripped metadata).
ALLOWED_COMPOSITE = {"ImageSize", "Megapixels", "AvgBitrate", "Rotation", "Duration"}

# ffprobe tags the muxer writes itself; anything else survived the strip.
ALLOWED_FORMAT_TAGS = {"major_brand", "minor_version", "compatible_brands"}
ALLOWED_STREAM_TAGS = {"language", "handler_name", "vendor_id"}


class StripError(RuntimeError):
    """The file could not be stripped, or metadata survived verification."""


@dataclass
class StripResult:
    source: Path
    output: Path
    kind: str  # "video" | "image"
    location_found: bool  # the SOURCE carried GPS/location (counted, §4.2)
    device_model: str | None  # marketing model read from the source, before stripping
    captured_on: str | None = None  # calendar date read from the source (no time, no zone)
    verified_with: list[str] = field(default_factory=list)
    sha256: str = ""


def _need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise StripError(f"{tool} not found on PATH (install ffmpeg / libimage-exiftool-perl)")
    return path


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    if proc.returncode != 0:
        # Tool stderr can echo tag values; keep only the last line, never the metadata dump.
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:] or ["no output"]
        raise StripError(f"{Path(cmd[0]).name} failed ({proc.returncode}): {tail[0][:200]}")
    return proc.stdout


def tool_versions() -> dict[str, str]:
    out: dict[str, str] = {}
    if shutil.which("exiftool"):
        out["exiftool"] = _run(["exiftool", "-ver"]).strip()
    if shutil.which("ffmpeg"):
        first = _run(["ffmpeg", "-hide_banner", "-version"]).splitlines()[0]
        out["ffmpeg"] = first.split()[2] if len(first.split()) > 2 else first
    return out


def kind_of(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        return "image"
    raise StripError(f"unsupported file type: {path.suffix or '(none)'}")


def exif_tags(path: Path) -> dict[str, object]:
    """All tags ExifTool can read (embedded/timed metadata included), keyed 'Group:Tag'."""
    _need("exiftool")
    out = _run(
        ["exiftool", "-j", "-a", "-G1", "-ee", "-n", "-api", "LargeFileSupport=1", str(path)]
    )
    data = json.loads(out)
    return data[0] if data else {}


def sensitive_exif(tags: dict[str, object]) -> list[str]:
    """Names (never values) of tags that identify a place, device, person or unit."""
    found = []
    for key in tags:
        group, _, name = key.rpartition(":")
        if not group or key == "SourceFile" or IGNORED_GROUP.match(group):
            continue
        if group == "Composite":
            if name not in ALLOWED_COMPOSITE and SENSITIVE_TAG.search(name):
                found.append(key)
            continue
        if SENSITIVE_GROUP.match(group) or SENSITIVE_TAG.search(name):
            found.append(key)
    return sorted(found)


def has_location(tags: dict[str, object]) -> bool:
    return any(re.search(r"gps|location|6709|^xyz$", k.rpartition(":")[2], re.I) for k in tags)


def device_model(tags: dict[str, object]) -> str | None:
    """The marketing model (e.g. 'iPhone 15 Pro') from the source tags, if it is an Apple one."""
    for key, value in tags.items():
        if key.rpartition(":")[2] == "Model" and isinstance(value, str):
            model = value.strip()
            if re.fullmatch(r"(iPhone|iPad)[A-Za-z0-9 ]{0,34}", model):
                return model
    return None


def capture_date(tags: dict[str, object]) -> str | None:
    """YYYY-MM-DD of the capture (local date if the source has one), else None."""
    order = ("CreationDate", "DateTimeOriginal", "CreateDate", "MediaCreateDate")
    for want in order:
        for key, value in tags.items():
            if key.rpartition(":")[2] == want and isinstance(value, str):
                m = re.match(r"(\d{4}):(\d{2}):(\d{2})", value)
                if m and m.group(1) != "0000":
                    return "-".join(m.groups())
    return None


def ffprobe(path: Path) -> dict:
    _need("ffprobe")
    out = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(out)


def sensitive_ffprobe(info: dict) -> list[str]:
    found = [
        f"format:{k}"
        for k in (info.get("format", {}).get("tags") or {})
        if k.lower() not in ALLOWED_FORMAT_TAGS
    ]
    for s in info.get("streams", []):
        for k in s.get("tags") or {}:
            if k.lower() not in ALLOWED_STREAM_TAGS:
                found.append(f"stream{s.get('index')}:{k}")
    if info.get("chapters"):
        found.append("chapters")
    return sorted(found)


def video_info(path: Path) -> tuple[dict, float]:
    """Manifest ``video`` block (sha256 left for the caller) and duration in seconds."""
    info = ffprobe(path)
    streams = info.get("streams", [])
    v = next(
        s
        for s in streams
        if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")
    )
    num, _, den = (v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    rotation = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rotation = int(round(float(sd["rotation"])))
    duration = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    block = {
        "container": VIDEO_EXTS[path.suffix.lower()],
        "codec": v.get("codec_name"),
        "width": int(v.get("width", 0)),
        "height": int(v.get("height", 0)),
        "fps": round(fps, 3),
        "hdr": v.get("color_transfer") in {"arib-std-b67", "smpte2084"},
        "rotation": rotation,
        "audio_kept": any(s.get("codec_type") == "audio" for s in streams),
        "size_bytes": path.stat().st_size,
    }
    return block, duration


def verify_clean(path: Path) -> list[str]:
    """Return the residual sensitive fields (names only); empty means clean."""
    residual = sensitive_exif(exif_tags(path))
    if kind_of(path) == "video":
        residual += sensitive_ffprobe(ffprobe(path))
    return residual


def _strip_video(src: Path, dst: Path, keep_audio: bool) -> None:
    ffmpeg = _need("ffmpeg")
    info = ffprobe(src)
    vcodec = next(
        (
            s.get("codec_name")
            for s in info.get("streams", [])
            if s.get("codec_type") == "video"
            and not (s.get("disposition") or {}).get("attached_pic")
        ),
        None,
    )
    if vcodec is None:
        raise StripError("no video stream")
    cmd = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src)]
    cmd += ["-map", "0:V:0"]
    if keep_audio:
        cmd += ["-map", "0:a:0?"]
    cmd += ["-c", "copy", "-map_metadata", "-1", "-map_metadata:s", "-1", "-map_chapters", "-1"]
    cmd += ["-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact"]
    if vcodec == "hevc":
        cmd += ["-tag:v", "hvc1"]  # Apple players need hvc1
    cmd += ["-movflags", "+faststart", "-f", VIDEO_EXTS[dst.suffix.lower()], str(dst)]
    _run(cmd)


def _strip_image(src: Path, dst: Path) -> None:
    exiftool = _need("exiftool")
    cmd = [exiftool, "-q", "-q", "-all="]
    if src.suffix.lower() in {".jpg", ".jpeg"}:
        cmd += ["-tagsfromfile", "@", "-icc_profile", "-orientation"]
    cmd += ["-o", str(dst), str(src)]
    _run(cmd)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_file(src: Path, dst: Path, *, keep_audio: bool = False) -> StripResult:
    """Strip ``src`` into ``dst`` (never in place), verify, and return what was found.

    Raises StripError (and removes ``dst``) if anything sensitive survives.
    """
    src, dst = Path(src), Path(dst)
    kind = kind_of(src)
    if kind_of(dst) != kind or dst.suffix.lower() != src.suffix.lower():
        raise StripError("output must keep the input's file type")
    if src.resolve() == dst.resolve():
        raise StripError("refusing to strip in place; give a different output path")
    source_tags = exif_tags(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        if kind == "video":
            _strip_video(src, dst, keep_audio)
        else:
            _strip_image(src, dst)
        residual = verify_clean(dst)
        if residual:
            raise StripError(f"metadata survived stripping: {', '.join(residual)}")
    except BaseException:
        if dst.exists():
            dst.unlink()
        raise
    versions = tool_versions()
    verified = [f"exiftool {versions.get('exiftool', '?')}"]
    if kind == "video":
        verified.append(f"ffprobe {versions.get('ffmpeg', '?')}")
    return StripResult(
        source=src,
        output=dst,
        kind=kind,
        location_found=has_location(source_tags),
        device_model=device_model(source_tags),
        captured_on=capture_date(source_tags),
        verified_with=verified,
        sha256=sha256_file(dst),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out-dir", type=Path, help="write stripped copies here (same file names)")
    ap.add_argument("--verify", action="store_true", help="only check files; exit 1 if any leaks")
    ap.add_argument("--keep-audio", action="store_true", help="keep the first audio track")
    args = ap.parse_args(argv)
    bad = 0
    if args.verify:
        for f in args.files:
            residual = verify_clean(f)
            print(f"{'LEAK' if residual else 'clean'}  {f}  {' '.join(residual)}")
            bad += bool(residual)
        return 1 if bad else 0
    if not args.out_dir:
        ap.error("--out-dir is required (files are never stripped in place)")
    for f in args.files:
        try:
            r = strip_file(f, args.out_dir / f.name, keep_audio=args.keep_audio)
        except StripError as exc:
            print(f"FAIL   {f}: {exc}", file=sys.stderr)
            bad += 1
            continue
        loc = "location removed" if r.location_found else "no location in source"
        print(f"clean  {r.output}  ({loc}; verified with {', '.join(r.verified_with)})")
    return 1 if bad else 0


if __name__ == "__main__":
    os.umask(0o077)
    sys.exit(main())
