"""Capture bundle validator (M1-CAPT-01 AT-1, AT-4; the capture → reconstruction contract).

A bundle is the directory the app writes after a guided capture:

    <bundle>/manifest.json   validated against bundle/capture_bundle.schema.json
    <bundle>/frames.jsonl    one frame per line ($defs/frame)
    <bundle>/video.mov|mp4   the stripped video (checked with --media)
    <bundle>/depth/<i>.bin   LiDAR depth, float16 little-endian metres (with --media)

On top of the schema, this checks what a schema cannot express: the frame count, the
accepted count and the tracking fraction agree with frames.jsonl; frame indices and times
increase; every pose is a rigid camera-to-world transform; passes tile the frames; the
coverage map has the declared shape and matches the fraction; depth is present exactly
when the device has LiDAR; and no key anywhere looks like location or identity data.

    python services/reconstruction/tools/capture_bundle.py <bundle-dir> [--media]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / "bundle" / "capture_bundle.schema.json"

# Keys that would carry a place or a person; the schema already forbids unknown keys,
# this is the belt to its braces (SECURITY_CHECKLIST §4.4).
FORBIDDEN_KEY_PARTS = (
    "gps",
    "location",
    "latitude",
    "longitude",
    "altitude",
    "address",
    "exif",
    "serial",
    "device_name",
    "email",
    "user",
)
# Contract keys that contain a forbidden word but carry none of that data.
ALLOWED_KEYS = frozenset({"location_recorded"})
ROTATION_TOLERANCE = 1e-3
FRACTION_TOLERANCE = 0.01


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _schema_errors(instance: object, schema: dict, where: str) -> list[str]:
    import jsonschema  # CI pins jsonschema==4.26.0

    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{where}{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def forbidden_keys(node: object, path: str = "") -> list[str]:
    """Paths of dict keys that look like location or identity fields."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}/{key}"
            if key not in ALLOWED_KEYS and any(
                part in str(key).lower() for part in FORBIDDEN_KEY_PARTS
            ):
                found.append(here)
            found += forbidden_keys(value, here)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += forbidden_keys(value, f"{path}[{i}]")
    return found


def pose_errors(pose: list[float]) -> list[str]:
    """A camera-to-world pose must be finite, rigid (orthonormal, det +1), last row 0 0 0 1."""
    if len(pose) != 16 or not all(math.isfinite(v) for v in pose):
        return ["pose must be 16 finite numbers"]
    # column-major: element (row r, col c) is pose[c * 4 + r]
    m = [[pose[c * 4 + r] for c in range(4)] for r in range(4)]
    errors = []
    if any(abs(m[3][c] - (1.0 if c == 3 else 0.0)) > ROTATION_TOLERANCE for c in range(4)):
        errors.append("pose last row must be 0 0 0 1 (column-major 4x4)")
    for a in range(3):
        for b in range(3):
            dot = sum(m[r][a] * m[r][b] for r in range(3))
            if abs(dot - (1.0 if a == b else 0.0)) > ROTATION_TOLERANCE:
                errors.append("pose rotation is not orthonormal")
                return errors
    det = (
        m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
    )
    if det < 0:
        errors.append("pose rotation is a reflection (det < 0)")
    return errors


def _read_frames(path: Path) -> tuple[list[dict], list[str]]:
    frames, errors = [], []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            frames.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"frames.jsonl:{n}: not JSON ({exc.msg})")
    return frames, errors


def validate(bundle: Path, media: bool = False) -> list[str]:
    """All contract violations for the bundle directory (empty list = valid)."""
    bundle = Path(bundle)
    manifest_path = bundle / "manifest.json"
    if not manifest_path.is_file():
        return ["manifest.json missing"]
    schema = _schema()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = _schema_errors(manifest, schema, "manifest.json:")
    errors += [
        f"manifest.json:{p}: looks like location/identity data" for p in forbidden_keys(manifest)
    ]
    if errors:
        return errors  # later checks assume a well-formed manifest

    frames_path = bundle / manifest["frames"]["file"]
    if not frames_path.is_file():
        return errors + ["frames.jsonl missing"]
    frames, parse_errors = _read_frames(frames_path)
    errors += parse_errors
    frame_schema = {"$defs": schema["$defs"], "$ref": "#/$defs/frame"}
    for n, frame in enumerate(frames, start=1):
        errors += _schema_errors(frame, frame_schema, f"frames.jsonl:{n}:")
        errors += [
            f"frames.jsonl:{n}:{p}: looks like location/identity data"
            for p in forbidden_keys(frame)
        ]
        if isinstance(frame.get("pose"), list):
            errors += [f"frames.jsonl:{n}: {e}" for e in pose_errors(frame["pose"])]
    if errors:
        return errors

    declared = manifest["frames"]
    if declared["count"] != len(frames):
        errors.append(
            f"frames.count is {declared['count']} but frames.jsonl has {len(frames)} lines"
        )
    accepted = sum(1 for f in frames if f["accepted"])
    if declared["accepted"] != accepted:
        errors.append(
            f"frames.accepted is {declared['accepted']} but {accepted} frames are accepted"
        )
    normal = sum(1 for f in frames if f["tracking"] == "normal") / len(frames)
    if abs(declared["tracking_normal_fraction"] - normal) > FRACTION_TOLERANCE:
        errors.append(
            f"frames.tracking_normal_fraction {declared['tracking_normal_fraction']}"
            f" != {normal:.3f}"
        )
    for prev, cur in zip(frames, frames[1:], strict=False):
        if cur["i"] <= prev["i"]:
            errors.append(f"frame index {cur['i']} does not increase")
        if cur["t"] < prev["t"]:
            errors.append(f"frame {cur['i']}: time goes backwards")
    if frames and frames[-1]["i"] >= manifest["video"]["frame_count"]:
        errors.append("a frame index is beyond video.frame_count")

    indices = [f["i"] for f in frames]
    passes = manifest["passes"]
    if passes[0]["reason"] != "start":
        errors.append("the first pass must have reason 'start'")
    if passes[0]["first_frame"] != indices[0] or passes[-1]["last_frame"] != indices[-1]:
        errors.append("passes must start at the first frame and end at the last")
    for a, b in zip(passes, passes[1:], strict=False):
        if b["first_frame"] <= a["last_frame"]:
            errors.append("passes overlap or are out of order")
    for p in passes:
        if p["last_frame"] < p["first_frame"]:
            errors.append("a pass ends before it starts")
    if len(passes) != manifest["coverage"]["passes"]:
        errors.append("coverage.passes must equal the number of passes")

    cmap = manifest["coverage"]["map"]
    rows = cmap["painted"]
    if len(rows) != cmap["elevation_bins"] or any(len(r) != cmap["azimuth_bins"] for r in rows):
        errors.append("coverage.map.painted does not match azimuth_bins x elevation_bins")
    else:
        painted = sum(r.count("1") for r in rows) / (cmap["azimuth_bins"] * cmap["elevation_bins"])
        if abs(painted - manifest["coverage"]["fraction"]) > FRACTION_TOLERANCE:
            errors.append(
                f"coverage.fraction {manifest['coverage']['fraction']}"
                f" != painted share {painted:.3f}"
            )
    expected_kind = "view-sphere" if manifest["mode"] == "room" else "orbit"
    if cmap["kind"] != expected_kind:
        errors.append(f"coverage.map.kind must be '{expected_kind}' for mode '{manifest['mode']}'")
    if cmap["elevation_max_deg"] <= cmap["elevation_min_deg"]:
        errors.append("coverage.map elevation range is empty")
    if (
        abs(manifest["readiness"]["components"]["coverage"] - manifest["coverage"]["fraction"])
        > FRACTION_TOLERANCE
    ):
        errors.append("readiness.components.coverage must equal coverage.fraction")

    depth = manifest["depth"]
    with_depth = [f["i"] for f in frames if f.get("depth")]
    if not manifest["device"]["lidar"] and (depth is not None or with_depth):
        errors.append("depth present on a device without LiDAR")
    if depth is not None and depth["count"] != len(with_depth):
        errors.append(f"depth.count is {depth['count']} but {len(with_depth)} frames carry depth")
    if depth is None and with_depth:
        errors.append("frames carry depth but manifest.depth is null")

    up, gravity = manifest["world"]["up"], manifest["world"]["gravity"]
    for name, v in (("world.up", up), ("world.gravity", gravity)):
        if abs(math.sqrt(sum(c * c for c in v)) - 1.0) > 0.01:
            errors.append(f"{name} must be a unit vector")
    if sum(a * b for a, b in zip(up, gravity, strict=True)) > -0.9:
        errors.append("world.gravity must point roughly opposite world.up")

    if media:
        video = bundle / manifest["video"]["file"]
        if not video.is_file():
            errors.append(f"{manifest['video']['file']} missing")
        if depth is not None:
            size = depth["width"] * depth["height"] * 2
            for i in with_depth:
                f = bundle / depth["dir"] / f"{i}.bin"
                if not f.is_file():
                    errors.append(f"depth/{i}.bin missing")
                elif f.stat().st_size != size:
                    errors.append(f"depth/{i}.bin is {f.stat().st_size} bytes, expected {size}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--media", action="store_true", help="also require the video and depth files"
    )
    args = parser.parse_args(argv)
    errors = validate(args.bundle, media=args.media)
    for e in errors:
        print(f"capture_bundle: {e}")
    if not errors:
        print(f"capture_bundle: {args.bundle} OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
