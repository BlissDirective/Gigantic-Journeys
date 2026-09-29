#!/usr/bin/env python3
"""Render the M0-DSGN-01 mockups and measure text/icon contrast on the stand-in scans (AT-2).

For every screen, state, scan and surface variant this script
  1. loads the page in headless Chrome and reads the measurement export (``#gj-measure``): each text and
     icon element, its foreground colour, and the nearest painted surface (colour, opacity, glass or flat);
  2. renders the same page with ``hidescrim=1`` (what lies under each scrim) at 1 pt = 1 px;
  3. composites the scrim over those pixels (blurred first for glass, like ``backdrop-filter``) and
     computes the WCAG ratio per pixel inside the element box; the row keeps the minimum and the 5th
     percentile. Text passes at >= 4.5:1 and icons at >= 3:1 on the minimum.

Usage: python render.py [--out DIR] [--csv PATH] [--only SCREEN] [--scan bright=FRAME.png ...]
Needs google-chrome and Pillow (not needed in CI; the committed CSV is checked by the pytest suite).
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOCKUPS = HERE.parent
REPO = MOCKUPS.parents[2]
sys.path.insert(0, str(HERE))
import contrast as C  # noqa: E402

SCANS = ("bright", "dark", "table")
IMAGES: dict[str, str] = {}  # scan -> image URL, set by --scan (real test scans replace the CSS stand-ins)
SURFACES = ("glass", "flat")
LAND, PORT, DUO = (852, 393), (393, 852), (1016, 720)
# screen file, size, states, over the scan (True) or an opaque shell (False), extra query
MATRIX = [
    ("play.html", LAND, ("run", "action", "pressed", "penalty"), True, ""),
    ("play.html", LAND, ("action",), True, "hc=1"),
    ("duo-stand.html", DUO, ("default",), True, ""),
    ("capture.html", PORT, ("pre", "recording", "fast", "lowlight", "long", "missed"), True, "mode=room"),
    ("capture.html", PORT, ("pre", "missed"), True, "mode=tabletop"),
    ("create.html", LAND, ("progress", "failed", "queued"), True, ""),
    ("results.html", LAND, ("results", "store", "loss"), True, ""),
    ("settings.html", PORT, ("controls",), True, ""),
    ("browse.html", PORT, ("grid", "back", "report", "rate", "scale"), False, ""),
    ("consent.html", PORT, ("age", "under13", "privacy", "learn"), False, ""),
    ("settings.html", PORT, ("access",), False, ""),
    ("state-colors.html", (760, 420), ("default",), False, ""),
]
CHROME = [
    "google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
    "--hide-scrollbars", "--virtual-time-budget=1500",
]  # fmt: skip


def url(page: str, query: str) -> str:
    return f"file://{MOCKUPS / page}?{query}"


def dump_measure(page: str, query: str) -> dict:
    out = subprocess.run([*CHROME, "--dump-dom", url(page, query)], capture_output=True, text=True, check=True)
    m = re.search(r'<pre id="gj-measure"[^>]*>(.*?)</pre>', out.stdout, re.S)
    if not m:
        raise RuntimeError(f"no measurement export in {page}?{query}")
    return json.loads(html.unescape(m.group(1)))


def screenshot(page: str, query: str, size: tuple[int, int], path: Path, scale: int = 1) -> Path:
    cmd = [*CHROME, f"--force-device-scale-factor={scale}", f"--window-size={size[0]},{size[1]}"]
    subprocess.run([*cmd, f"--screenshot={path}", url(page, query)], capture_output=True, check=True)
    return path


def measure_item(item: dict, under, under_blur) -> tuple[float, float, str, float]:
    fg = item["fg"][:3]
    bg = item["bg"]
    if bg is None:  # text drawn straight on the scan: measure against the raw pixels
        img, color, alpha, desc = under, None, 0.0, "scan (no surface)"
    else:
        color, alpha = bg[:3], bg[3]
        desc = C.rgb_hex(color) + (f" @ {alpha:.2f}" if alpha < 1 else "")
        if alpha >= 0.999:
            r = C.ratio(fg, color)
            return r, r, desc, alpha
        img = under_blur if item["glass"] else under
        desc += " glass" if item["glass"] else " flat"
    x, y, w, h = item["rect"]
    box = (max(0, int(x)), max(0, int(y)), min(img.width, int(x + w + 0.999)), min(img.height, int(y + h + 0.999)))
    crop = img.crop(box)
    flat = getattr(crop, "get_flattened_data", crop.getdata)
    px = list(flat()) or [(0, 0, 0)]
    ratios = sorted(C.ratio(fg, p if color is None else C.over(color, alpha, p)) for p in px)
    return ratios[0], ratios[len(ratios) // 20], desc, alpha


def run_case(args) -> list[dict]:
    from PIL import Image, ImageFilter

    page, size, state, scan, surface, extra, tmp = args
    q = f"state={state}&bg={scan}&surface={surface}" + (f"&{extra}" if extra else "")
    if scan in IMAGES:
        q += f"&img={IMAGES[scan]}"
    data = dump_measure(page, q)
    stem = f"{page[:-5]}-{state}-{scan}-{surface}" + (f"-{extra.replace('=', '')}" if extra else "")
    under = Image.open(screenshot(page, q + "&hidescrim=1", size, tmp / f"{stem}-under.png")).convert("RGB")
    under_blur = under.filter(ImageFilter.GaussianBlur(20))
    rows = []
    for it in data["items"]:
        mn, p5, desc, alpha = measure_item(it, under, under_blur)
        need = C.TEXT_MIN if it["kind"] == "text" else C.ICON_MIN
        rows.append({
            "screen": page[:-5] + (f" ({extra})" if extra else ""), "state": state, "scan": scan, "surface": surface,
            "scrim": data["scrim"], "item": it["id"], "kind": it["kind"], "fg": C.rgb_hex(it["fg"]),
            "on": desc, "min": f"{mn:.2f}", "p5": f"{p5:.2f}", "need": f"{need:.1f}", "pass": "yes" if mn >= need else "NO",
        })  # fmt: skip
    for t in data["targets"]:
        if not t["ok"]:
            rows.append({
                "screen": page[:-5], "state": state, "scan": scan, "surface": surface, "scrim": data["scrim"],
                "item": f"TARGET {t['name']} {t['w']}x{t['h']}", "kind": "target", "fg": "", "on": "",
                "min": str(min(t["w"], t["h"])), "p5": "", "need": str(t["min"]), "pass": "NO",
            })  # fmt: skip
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="/tmp/gj-mockups")
    ap.add_argument("--csv", default=str(REPO / "qa/evidence/M0-DSGN-01/contrast.csv"))
    ap.add_argument("--only", default="")
    ap.add_argument("--scan", action="append", default=[], help="bright|dark|table=/path/to/frame.png (repeatable)")
    args = ap.parse_args()
    for spec in args.scan:
        name, path = spec.split("=", 1)
        IMAGES[name] = Path(path).resolve().as_uri()
    tmp = Path(args.out)
    tmp.mkdir(parents=True, exist_ok=True)
    cases = []
    for page, size, states, over_scan, extra in MATRIX:
        if args.only and not page.startswith(args.only):
            continue
        for state in states:
            for scan in SCANS if over_scan else ("bright",):
                for surface in SURFACES:
                    cases.append((page, size, state, scan, surface, extra, tmp))
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = [r for rs in pool.map(run_case, cases) for r in rs]
    with open(args.csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    fails = [r for r in rows if r["pass"] != "yes"]
    print(f"{len(cases)} renders, {len(rows)} measurements, {len(fails)} failures -> {args.csv}")
    for r in fails[:60]:
        print(f"  FAIL {r['screen']} {r['state']} {r['scan']} {r['surface']}: {r['item']} {r['min']} < {r['need']} ({r['on']})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
