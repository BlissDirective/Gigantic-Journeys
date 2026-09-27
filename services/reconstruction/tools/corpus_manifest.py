"""Corpus manifest rows: build, check and validate (M0-CAPT-01 AT-2).

``services/reconstruction/corpus/manifest.json`` is validated against
``manifest.schema.json`` (jsonschema, provided by CI) plus rules a schema cannot
express: unique ids, id prefix equals mode, storage path matches id, and no
coordinates, street addresses, e-mail addresses or phone numbers in free text.

    python services/reconstruction/tools/corpus_manifest.py            # validate
    python services/reconstruction/tools/corpus_manifest.py --summary  # M0-OWNER-01 counts
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parents[1] / "corpus"
MANIFEST = CORPUS_DIR / "manifest.json"
SCHEMA = CORPUS_DIR / "manifest.schema.json"
ROOM_CLASSES = ("couch", "coffee_table", "dining_chair", "bookshelf")

# Free text must never carry a place or a person.
_PII = {
    "coordinates": re.compile(r"[-+]?\d{1,3}\.\d{3,}\s*[,; ]\s*[-+]?\d{1,3}\.\d{3,}"),
    "street address": re.compile(
        r"\b\d{1,6}\s+(?:[A-Za-z0-9.'-]+\s+){0,4}"
        r"(street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|court|ct|way|place|pl|"
        r"terrace|parkway|pkwy|highway|hwy|circle|cir)\b",
        re.IGNORECASE,
    ),
    "postal code": re.compile(r"\b\d{5}(?:-\d{4})?\b|\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b"),
    "e-mail": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "phone number": re.compile(r"\+?\d[\d ().-]{8,}\d"),
    "url": re.compile(r"https?://|www\.", re.IGNORECASE),
}


def pii_findings(text: str) -> list[str]:
    return [label for label, rx in _PII.items() if rx.search(text or "")]


def _texts(row: dict) -> list[tuple[str, str]]:
    out = [
        ("notes", row.get("notes", "")),
        ("coverage.summary", row.get("coverage", {}).get("summary", "")),
    ]
    out += [
        (f"intake.warnings[{i}]", w)
        for i, w in enumerate(row.get("intake", {}).get("warnings", []))
    ]
    return out


def check_rules(manifest: dict) -> list[str]:
    """Cross-row and privacy rules beyond the JSON schema."""
    errors: list[str] = []
    seen: set[str] = set()
    for row in manifest.get("captures", []):
        cid = row.get("id", "?")
        if cid in seen:
            errors.append(f"{cid}: duplicate id")
        seen.add(cid)
        if not str(cid).startswith(f"{row.get('mode')}-"):
            errors.append(f"{cid}: id prefix must equal mode")
        path = row.get("storage", {}).get("path", "")
        if path and not re.fullmatch(
            rf"/corpus/{re.escape(cid)}/{re.escape(cid)}\.(mov|mp4)", path
        ):
            errors.append(f"{cid}: storage.path must be /corpus/{cid}/{cid}.<ext>")
        container = row.get("video", {}).get("container")
        if path and container and not path.endswith(f".{container}"):
            errors.append(f"{cid}: storage.path extension must match video.container")
        for field, text in _texts(row):
            for label in pii_findings(text):
                errors.append(f"{cid}: {field} looks like it contains a {label}")
    return errors


def validate(manifest: dict, schema: dict | None = None) -> list[str]:
    import jsonschema  # CI pins jsonschema==4.26.0; imported lazily for the Modal container

    schema = schema or json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))
    ]
    return errors + check_rules(manifest)


def next_id(mode: str, taken: set[str]) -> str:
    n = 1
    while f"{mode}-{n:02d}" in taken:
        n += 1
    return f"{mode}-{n:02d}"


def quality_warnings(mode: str, video: dict, duration_s: float, lighting: str) -> list[str]:
    """Plain-language flags against the capture guide (corpus/README.md)."""
    w: list[str] = []
    long_side = max(video.get("width", 0), video.get("height", 0))
    if long_side and long_side < 3840:
        w.append(
            f"not 4K ({video['width']}x{video['height']}): likely re-compressed by the iPhone "
            "picker; re-upload with Options > Current, or check Settings > Camera > Record Video"
        )
    if video.get("codec") == "h264":
        w.append("H.264, expected HEVC: possibly transcoded on upload")
    fps = video.get("fps") or 0
    if fps and abs(fps - 30) > 1:
        w.append(f"{fps:g} fps, guide asks for 30 fps")
    if video.get("hdr"):
        w.append(
            "HDR (HLG/Dolby Vision) video: turn off Settings > Camera > Record Video > HDR Video"
        )
    if mode == "room":
        if duration_s > 180:
            w.append(f"{duration_s:.0f} s is over the 3 min room maximum")
        elif duration_s < 45:
            w.append(f"{duration_s:.0f} s is short for a room (90 s ideal)")
    else:
        if duration_s > 90:
            w.append(f"{duration_s:.0f} s is long for a tabletop (30-60 s)")
        elif duration_s < 20:
            w.append(f"{duration_s:.0f} s is short for a tabletop (30-60 s)")
    if lighting == "dim":
        w.append("dim light: expect a weaker reconstruction")
    return w


def build_row(
    *,
    capture_id: str,
    owner: dict,
    video: dict,
    duration_s: float,
    device_model: str | None,
    captured_on: str | None,
    received_on: str,
    strip_tool: str,
    verified_with: list[str],
    location_found: bool,
) -> dict:
    mode = owner["mode"]
    flags = owner.get("objects", {})
    objects = {k: bool(flags.get(k, False)) for k in ROOM_CLASSES} if mode == "room" else {}
    if mode == "tabletop":
        objects["lego"] = bool(flags.get("lego", False))
    note = owner.get("note", "") or ""
    if pii_findings(note):
        note = "[note removed at intake: looked like it contained personal data]"
    passes = 2
    summary = (
        "camera-app capture; chest-height arc + low/high pass per the guide (not measured)"
        if mode == "room"
        else "camera-app capture; low + high orbit per the guide (not measured)"
    )
    return {
        "id": capture_id,
        "mode": mode,
        "source": "iphone-camera-app",
        "captured_on": captured_on,
        "device": {"model": device_model, "lidar": None},
        "duration_s": round(float(duration_s), 2),
        "lighting": owner["lighting"],
        "objects": objects,
        "readiness": {"score": None, "source": "not-measured"},
        "coverage": {"summary": summary, "fraction": None, "passes": passes},
        "video": video,
        "storage": {"path": f"/corpus/{capture_id}/{capture_id}.{video['container']}"},
        "privacy": {
            "metadata_stripped": True,
            "strip_tool": strip_tool,
            "verified_with": verified_with,
            "location_found_on_intake": bool(location_found),
            "owner_confirmed_clear": bool(owner.get("privacy_ok")),
        },
        "intake": {
            "received_on": received_on,
            "warnings": quality_warnings(mode, video, duration_s, owner["lighting"]),
        },
        "notes": note[:300],
    }


def summary(manifest: dict) -> dict:
    rows = manifest.get("captures", [])
    rooms = [r for r in rows if r["mode"] == "room"]
    tables = [r for r in rows if r["mode"] == "tabletop"]
    return {
        "rooms": len(rooms),
        "tabletops": len(tables),
        "rooms_with_all_bible_classes": sum(
            all(r["objects"].get(k) for k in ROOM_CLASSES) for r in rooms
        ),
        "lego_tabletops": sum(bool(r["objects"].get("lego")) for r in tables),
        "owner_confirmed_clear": sum(r["privacy"]["owner_confirmed_clear"] for r in rows),
        "location_found_on_intake": sum(r["privacy"]["location_found_on_intake"] for r in rows),
        "with_warnings": sum(bool(r.get("intake", {}).get("warnings")) for r in rows),
        "M0-OWNER-01_target": "10 rooms (>=3 with all four classes), 5 tabletops (>=2 Lego)",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("manifest", nargs="?", type=Path, default=MANIFEST)
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = validate(manifest)
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if args.summary:
        print(json.dumps(summary(manifest), indent=2))
    if not errors:
        print(f"OK {args.manifest.name}: {len(manifest.get('captures', []))} capture(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
