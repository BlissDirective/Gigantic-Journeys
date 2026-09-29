#!/usr/bin/env python3
"""Build the M0-DSGN-01 evidence PNGs (qa/evidence/M0-DSGN-01/) from the mockups.

Each PNG is a labelled contact sheet of headless-Chrome renders (device scale 2, or 1 for wide sheets),
kept under the 2 MB evidence limit (qa/VISUAL_QA.md). Needs google-chrome and Pillow.
Usage: python evidence.py [--out qa/evidence/M0-DSGN-01]
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render import DUO, LAND, PORT, REPO, screenshot  # noqa: E402

MAX = 2 * 1024 * 1024
SHEETS = [
    # name, columns, scale, [(page, query, size, label)]
    ("01-play-hud-three-scans", 1, 2, [("play.html", f"state=action&bg={b}", LAND, f"Play HUD + controls, action available, glass, {b} scan (auto scrim)") for b in ("bright", "dark", "table")]),
    ("02-play-annotated-safe-zones", 1, 2, [("play.html", "state=action&bg=bright&annot=1", LAND, "Touch targets (magenta), safe area (yellow), 16 pt control inset (green), HUD band top 8 % (cyan); iPhone 15 Pro landscape")]),
    ("03-play-glass-flat-contrast", 1, 2, [("play.html", f"state=action&bg=bright&{v}", LAND, lab) for v, lab in (("surface=glass", "Glass (default)"), ("surface=flat", "Flat twin (Reduce Transparency)"), ("hc=1", "Increase Contrast (scrims 90 %, thicker outlines)"))]),
    ("04-play-states", 1, 2, [("play.html", f"state={s}&bg=table", LAND, lab) for s, lab in (("run", "Running: no contextual action"), ("pressed", "Jump pressed: the only amber fill"), ("penalty", "Time penalty: small +0:04 beside the timer"), ("controller", "Controller connected: touch controls hidden"))]),
    ("05-duo-stand-annotated", 1, 2, [("duo-stand.html", "bg=bright&annot=1", DUO, "iPhone Duo stand mode: photograph above the fold, every control below (inner display points assumed)")]),
    ("06-capture-room-states", 6, 1, [("capture.html", f"mode=room&state={s}&bg=bright", PORT, s) for s in ("pre", "recording", "fast", "lowlight", "long", "missed")]),
    ("07-capture-tabletop-dark", 3, 1, [("capture.html", f"mode=tabletop&state={s}&bg=dark{x}", PORT, lab) for s, x, lab in (("pre", "", "tabletop: mode toggle"), ("recording", "&hatch=1", "recording, hatch coverage"), ("missed", "", "missed corner"))]),
    ("08-capture-annotated", 2, 2, [("capture.html", f"mode=room&state={s}&bg=bright&annot=1", PORT, s) for s in ("pre", "missed")]),
    ("09-create-wait-states", 1, 2, [("create.html", f"state={s}&bg=table", LAND, lab) for s, lab in (("progress", "Reconstruction wait: four-stage bar, estimate, what's happening"), ("failed", "Failure: kind, specific, actionable"), ("queued", "Daily cap: queued, never an error"))]),
    ("10-browse-states", 5, 1, [("browse.html", f"state={s}", PORT, s) for s in ("grid", "scale", "back", "report", "rate")]),
    ("11-browse-annotated", 2, 2, [("browse.html", f"state={s}&annot=1", PORT, s) for s in ("grid", "rate")]),
    ("12-results-store-loss", 1, 2, [("results.html", f"state={s}&bg=dark", LAND, lab) for s, lab in (("results", "Results: Share primary"), ("store", "Below the fold, after a summit only"), ("loss", "Loss: Keep going, nothing else"))]),
    ("13-consent-age-gate", 4, 1, [("consent.html", f"state={s}&annot=1", PORT, s) for s in ("age", "under13", "privacy", "learn")]),
    ("14-settings-accessibility-controls", 2, 2, [("settings.html", f"state={s}&bg=bright", PORT, s) for s in ("access", "controls")]),
    ("15-state-colours-cvd", 2, 1, [("state-colors.html", f"cvd={c}" if c else "", (760, 420), c or "typical") for c in ("", "deuteranopia", "protanopia", "tritanopia")]),
    ("16-deuteranopia-screens", 2, 1, [
        ("play.html", "state=pressed&bg=bright&cvd=deuteranopia", LAND, "play, jump pressed"),
        ("create.html", "state=progress&bg=dark&cvd=deuteranopia", LAND, "create wait on cream scrim"),
        ("capture.html", "mode=room&state=fast&bg=bright&cvd=deuteranopia", PORT, "capture: too fast (solid wash)"),
        ("capture.html", "mode=room&state=fast&bg=bright&hatch=1&cvd=deuteranopia", PORT, "capture: too fast (hatch wash)")]),
    ("17-glass-vs-flat", 2, 1, [(p, f"state={s}&bg={b}&surface={v}", sz, f"{p[:-5]} {s} {v}") for p, s, b, sz in (("create.html", "progress", "table", LAND), ("results.html", "results", "bright", LAND)) for v in ("glass", "flat")]),
]  # fmt: skip


def label(img, text: str):
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
    bar = Image.new("RGB", (img.width, 36), (40, 40, 40))
    ImageDraw.Draw(bar).text((10, 6), text, fill=(255, 255, 255), font=font)
    out = Image.new("RGB", (img.width, img.height + 36), (40, 40, 40))
    out.paste(bar, (0, 0))
    out.paste(img, (0, 36))
    return out


def build(name: str, cols: int, scale: int, items, tmp: Path, out: Path) -> Path:
    from PIL import Image

    tiles = []
    for i, (page, query, size, text) in enumerate(items):
        p = screenshot(page, query, size, tmp / f"{name}-{i}.png", scale=scale)
        tiles.append(label(Image.open(p).convert("RGB"), text))
    rows = [tiles[i : i + cols] for i in range(0, len(tiles), cols)]
    width = max(sum(t.width for t in r) + 8 * (len(r) - 1) for r in rows)
    height = sum(max(t.height for t in r) for r in rows) + 8 * (len(rows) - 1)
    sheet = Image.new("RGB", (width, height), (85, 85, 85))
    y = 0
    for r in rows:
        x = 0
        for t in r:
            sheet.paste(t, (x, y))
            x += t.width + 8
        y += max(t.height for t in r) + 8
    dest = out / f"{name}.png"
    sheet.save(dest, optimize=True)
    if dest.stat().st_size > MAX:
        sheet.quantize(colors=256, dither=Image.Dither.NONE).save(dest, optimize=True)
    while dest.stat().st_size > MAX:
        sheet = sheet.resize((sheet.width * 4 // 5, sheet.height * 4 // 5))
        sheet.quantize(colors=256, dither=Image.Dither.NONE).save(dest, optimize=True)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(REPO / "qa/evidence/M0-DSGN-01"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        for name, cols, scale, items in SHEETS:
            d = build(name, cols, scale, items, Path(t), out)
            print(f"{d.name}: {d.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
