"""M0-DSGN-01 mockup checks that run in CI without a browser.

- the contrast helpers reproduce WCAG and the Coordinator's DESIGN_SYSTEM §12 measurements;
- the mockup palette equals the locked §2 palette;
- the scrim opacities meet the worst case over any background;
- the committed contrast table (qa/evidence/M0-DSGN-01/contrast.csv) covers every screen, scan and
  surface and has no failures;
- player-facing copy follows the decision-2 vocabulary (never level / map / goal / user).
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
MOCKUPS = HERE.parent
REPO = MOCKUPS.parents[2]
sys.path.insert(0, str(HERE))
import contrast as C  # noqa: E402

CSV = REPO / "qa/evidence/M0-DSGN-01/contrast.csv"
CSS = (MOCKUPS / "mockups.css").read_text(encoding="utf-8")
SCREENS = sorted(p for p in MOCKUPS.glob("*.html") if p.name != "index.html")


def css_var(name: str) -> str:
    m = re.search(rf"--{re.escape(name)}:\s*([^;]+);", CSS)
    assert m, f"--{name} missing from mockups.css"
    return m.group(1).strip()


def test_wcag_reference_values():
    assert C.ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    assert C.ratio((255, 255, 255), (255, 255, 255)) == pytest.approx(1.0)
    assert C.ratio((118, 118, 118), (255, 255, 255)) == pytest.approx(4.54, abs=0.01)


@pytest.mark.parametrize(
    ("fg", "bg", "expected"),
    [
        ("ink.charcoal", "paper.cream", 14.4),
        ("accent.amber", "ink.charcoal", 8.3),
        ("semantic.teal", "paper.cream", 7.2),
        ("text.muted", "surface.charcoal", 4.2),
        ("semantic.sage", "paper.cream", 3.0),
        ("semantic.teal", "ink.charcoal", 2.0),
        ("text.muted", "paper.cream", 2.8),
        ("semantic.terracotta", "paper.cream", 3.7),
    ],
)
def test_reproduces_design_system_field_notes(fg, bg, expected):
    got = C.ratio(C.hex_rgb(C.PALETTE[fg]), C.hex_rgb(C.PALETTE[bg]))
    assert round(got, 1) == expected


def test_derived_muted_tokens_pass_on_their_surfaces():
    on_cream = C.ratio(C.hex_rgb(C.DERIVED["muted-on-cream"]), C.hex_rgb(C.PALETTE["surface.cream"]))
    on_charcoal = C.ratio(C.hex_rgb(C.DERIVED["muted-on-charcoal"]), C.hex_rgb(C.PALETTE["surface.charcoal"]))
    assert on_cream >= 4.5 - 0.05  # §12 quotes 4.5:1 for #63676E on surface.cream
    assert on_charcoal >= 4.5 - 0.05


def test_palette_matches_locked_design_system():
    text = (REPO / "design/DESIGN_SYSTEM.md").read_text(encoding="utf-8")
    locked = dict(re.findall(r"`([a-zA-Z]+\.[a-zA-Z]+)`\s+(#[0-9A-Fa-f]{6})", text))
    for name, hexval in C.PALETTE.items():
        assert locked[name].upper() == hexval
        var = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), name).replace(".", "-")
        assert css_var(var).upper() == hexval, name
    assert css_var("muted-on-cream").upper() == C.DERIVED["muted-on-cream"]
    assert css_var("muted-on-charcoal").upper() == C.DERIVED["muted-on-charcoal"]


def test_scrim_opacities_hold_over_any_background():
    ink, paper = C.hex_rgb(C.PALETTE["ink.charcoal"]), C.hex_rgb(C.PALETTE["paper.cream"])
    text_alpha, disc_alpha = float(css_var("scrim-text")), float(css_var("scrim-disc"))
    assert C.worst_case(paper, ink, text_alpha) >= C.TEXT_MIN
    assert C.worst_case(ink, paper, text_alpha) >= C.TEXT_MIN
    assert C.worst_case(paper, ink, disc_alpha) >= C.ICON_MIN
    assert C.worst_case(ink, paper, disc_alpha) >= C.ICON_MIN
    # the ~60 % disc of §5 is not enough for text: text needs its own, denser scrim
    assert C.min_alpha(paper, ink, C.TEXT_MIN) > disc_alpha


def test_simulation_is_identity_on_greys():
    for kind in C.CVD:
        for g in (0, 128, 255):
            assert all(abs(c - g) < 1.5 for c in C.simulate((g, g, g), kind))


def load_rows():
    with CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_contrast_table_has_no_failures():
    rows = load_rows()
    assert len(rows) > 500
    bad = [r for r in rows if r["pass"] != "yes"]
    assert not bad, bad[:5]
    for r in rows:
        need = 4.5 if r["kind"] == "text" else 3.0
        assert float(r["need"]) == need and float(r["min"]) >= need, r


def test_contrast_table_covers_every_screen_scan_and_surface():
    rows = load_rows()
    seen = {(r["screen"].split(" ")[0], r["scan"], r["surface"]) for r in rows}
    for page in SCREENS:
        name = page.stem
        assert any(s[0] == name for s in seen), f"{name} missing from contrast.csv"
    for name in ("play", "duo-stand", "capture", "create", "results"):
        for scan in ("bright", "dark", "table"):
            for surface in ("glass", "flat"):
                assert (name, scan, surface) in seen, (name, scan, surface)
    assert {r["scrim"] for r in rows if r["scan"] == "dark"} == {"cream"}
    assert {r["scrim"] for r in rows if r["scan"] == "bright"} == {"charcoal"}


FORBIDDEN = re.compile(r"\b(levels?|maps?|goals?|users?)\b", re.I)


@pytest.mark.parametrize("page", SCREENS, ids=lambda p: p.name)
def test_copy_follows_decision_2_vocabulary(page):
    src = page.read_text(encoding="utf-8")
    src = re.sub(r"<!--.*?-->", " ", src, flags=re.S)
    src = re.sub(r"<style>.*?</style>", " ", src, flags=re.S)
    src = re.sub(r"\.map\(", " ", src)
    visible = re.sub(r"<[^>]+>", " ", src)
    aria = " ".join(re.findall(r'aria-label="([^"]*)"', src))
    hits = FORBIDDEN.findall(visible + " " + aria)
    assert not hits, f"{page.name}: {hits}"
