#!/usr/bin/env python3
"""Check the App Store icon in a Unity-exported Xcode project (ios-build workflow).

App Store Connect rejects an upload with no 1024x1024 App Store ("ios-marketing")
icon in the asset catalog ("Missing app icon", TestFlight runs 36577265750 and
36760847904), and rejects one with an alpha channel. This finds the AppIcon set
under ``<xcode project dir>``, asserts the 1024 px marketing entry exists and is
1024x1024, and, when that PNG carries alpha, flattens it in place with ``sips``
(macOS) so the upload passes. Without ``sips`` an alpha icon is an error.

Usage: ios_app_icon.py <xcode project dir>
"""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
ALPHA_COLOR_TYPES = {4, 6}  # grey+alpha, RGBA


def png_info(path: Path) -> tuple[int, int, int]:
    """Return (width, height, colour type) from the PNG IHDR chunk."""
    data = path.read_bytes()[:33]
    if len(data) < 33 or data[:8] != PNG_SIG or data[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return width, height, data[25]


def find_marketing_icon(project: Path) -> Path:
    sets = sorted(project.glob("**/Images.xcassets/AppIcon.appiconset/Contents.json"))
    if not sets:
        raise FileNotFoundError(f"no AppIcon.appiconset under {project}")
    contents = sets[0]
    images = json.loads(contents.read_text()).get("images", [])
    for img in images:
        marketing = img.get("idiom") == "ios-marketing"
        single = img.get("idiom") == "universal" and img.get("platform") == "ios"
        if (marketing or single) and img.get("size") == "1024x1024":
            name = img.get("filename")
            if not name:
                raise FileNotFoundError(
                    f"{contents}: the 1024x1024 App Store icon slot has no file"
                    " (assign it in Player Settings > iOS > Icon)"
                )
            path = contents.parent / name
            if not path.is_file():
                raise FileNotFoundError(f"{path} is listed but missing")
            return path
    raise FileNotFoundError(f"{contents}: no 1024x1024 App Store icon entry")


def flatten(path: Path) -> None:
    sips = shutil.which("sips")
    if not sips:
        raise RuntimeError(f"{path} has an alpha channel and sips is unavailable")
    with tempfile.TemporaryDirectory() as tmp:
        jpg = Path(tmp) / "icon.jpg"
        subprocess.run(
            [
                sips,
                "-s",
                "format",
                "jpeg",
                "-s",
                "formatOptions",
                "100",
                str(path),
                "--out",
                str(jpg),
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [sips, "-s", "format", "png", str(jpg), "--out", str(path)],
            check=True,
            capture_output=True,
        )


def check(project: Path) -> Path:
    icon = find_marketing_icon(project)
    width, height, ctype = png_info(icon)
    if (width, height) != (1024, 1024):
        raise ValueError(f"{icon} is {width}x{height}, App Store needs 1024x1024")
    if ctype in ALPHA_COLOR_TYPES:
        flatten(icon)
        width, height, ctype = png_info(icon)
        if ctype in ALPHA_COLOR_TYPES:
            raise ValueError(f"{icon} still has alpha after flattening")
        print(f"::notice::flattened alpha out of {icon.name}")
    return icon


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        icon = check(Path(argv[1]))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"::error::{exc}")
        return 1
    print(f"App Store icon OK: {icon} (1024x1024, opaque)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
