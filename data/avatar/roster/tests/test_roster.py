"""v1 preset-roster data tests (AUTH #044 / #024): the 8 curated avatar_params + manifest.

The roster is the Brain-B / data half of M1-AVAT-01: each preset is a schema-valid ``avatar_params``
on the shared rig (so it is rig-conformant by construction), and the set satisfies the AUTH #024
inclusive casting matrix with CVD-safe hero colors. The Unity selection UI (gj-gameplay) consumes
this data; the final art and any player-facing names are gj-design's.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROSTER = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
PRESETS = ROSTER / "presets"
AVATAR_SCHEMA_DIR = REPO / "data" / "schemas" / "avatar"
sys.path.insert(0, str(AVATAR_SCHEMA_DIR))

import validate_avatar  # noqa: E402

# Okabe-Ito CVD-safe qualitative palette (7 chromatic) + a neutral grey for the 8th.
# https://jfly.uni-koeln.de/color/ — distinguishable under deuteran/protan/tritan vision.
OKABE_ITO_CHROMATIC = {
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
}
CVD_SAFE = OKABE_ITO_CHROMATIC | {"#999999"}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def manifest() -> dict:
    return load(ROSTER / "roster.json")


def preset_files() -> list[Path]:
    return sorted(PRESETS.glob("*.json"))


def _rel_luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def test_every_preset_is_schema_valid_and_non_biometric():
    files = preset_files()
    assert len(files) == 8, "expect 8 launch presets"
    for p in files:
        doc = load(p)
        assert validate_avatar.validate(doc, "avatar_params") == [], p.name
        assert validate_avatar.forbidden_keys(doc) == [], p.name
        assert doc["base_rig"] == "gj-humanoid-1A", p.name
        assert doc["provenance"]["source"] == "preset", p.name


def test_manifest_matches_preset_files():
    m = manifest()
    assert m["base_rig"] == "gj-humanoid-1A"
    entries = m["presets"]
    assert len(entries) == 8
    assert m.get("floor", 6) <= len(entries)
    ids_manifest = [e["preset_id"] for e in entries]
    assert len(set(ids_manifest)) == 8, "preset_ids unique"
    for e in entries:
        f = ROSTER / e["file"]
        assert f.exists(), e["file"]
        assert load(f)["provenance"]["preset_id"] == e["preset_id"], e["preset_id"]
    ids_disk = {load(p)["provenance"]["preset_id"] for p in preset_files()}
    assert ids_disk == set(ids_manifest)


def test_casting_matrix_is_inclusive():
    # AUTH #024: spread across body type, apparent gender presentation, skin tone, apparent age,
    # floor of 6. Numeric axes come from the preset files; categorical axes from the manifest.
    docs = [load(p) for p in preset_files()]
    m = manifest()

    skin = {d["skin_tone"] for d in docs}
    assert len(skin) >= 6, "skin-tone variety"
    assert min(skin) <= 7 and max(skin) >= 24, "skin tone spans the ramp"

    heights = [d["body"]["height"] for d in docs]
    builds = [d["body"]["build"] for d in docs]
    assert max(heights) - min(heights) >= 0.35, "height spread"
    assert max(builds) - min(builds) >= 0.35, "build spread"

    assert len({d["hair"]["style"] for d in docs}) >= 6, "hair-style variety"

    gender = {e["gender_presentation"] for e in m["presets"]}
    assert {"masculine", "feminine"} <= gender and len(gender) >= 3, "gender spread"

    age = {e["apparent_age"] for e in m["presets"]}
    assert {"young-adult", "mature"} <= age, "apparent-age spread"


def test_hero_colors_are_distinct_and_cvd_safe():
    heroes = [e["hero_color"].upper() for e in manifest()["presets"]]
    assert len(set(heroes)) == 8, "hero colors distinct"
    assert set(heroes) <= {c.upper() for c in CVD_SAFE}, "from the CVD-safe palette"
    assert {c.upper() for c in OKABE_ITO_CHROMATIC} <= set(heroes), "full Okabe-Ito chromatic set"
    lum = [_rel_luminance(h) for h in heroes]
    assert max(lum) - min(lum) >= 0.4, "luminance spread for silhouette readability"
