#!/usr/bin/env python3
"""Copy the preset character roster into Unity StreamingAssets, byte-identically.

``data/avatar/roster/roster.json`` and ``data/avatar/roster/presets/*.json`` (the canonical
preset data, M1-AVAT-05) are what the Unity selection screen loads (M1-AVAT-01). The copy at
``unity/Assets/StreamingAssets/avatar/roster/`` is never hand-edited: run this after any
change to the roster. ``--check`` exits 1 when the copy has drifted (pytest runs it in CI).

Usage: ``python .github/scripts/copy_roster_to_unity.py [--check]``
"""

from __future__ import annotations

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "avatar" / "roster"
DST = ROOT / "unity" / "Assets" / "StreamingAssets" / "avatar" / "roster"


def files() -> list[pathlib.Path]:
    """Roster files to ship, relative to the roster directory."""
    return [pathlib.Path("roster.json")] + sorted(
        p.relative_to(SRC) for p in (SRC / "presets").glob("*.json")
    )


def drift() -> list[str]:
    """Problems with the Unity copy (empty when byte-identical, with no extra json)."""
    problems = []
    wanted = set(files())
    for rel in sorted(wanted):
        dst = DST / rel
        if not dst.is_file():
            problems.append(f"missing {rel}")
        elif dst.read_bytes() != (SRC / rel).read_bytes():
            problems.append(f"differs {rel}")
    if DST.is_dir():
        for extra in sorted(p.relative_to(DST) for p in DST.rglob("*.json")):
            if extra not in wanted:
                problems.append(f"extra {extra}")
    return problems


def main(argv: list[str]) -> int:
    if "--check" in argv:
        problems = drift()
        for p in problems:
            print(f"roster copy: {p}")
        return 1 if problems else 0
    for rel in files():
        (DST / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SRC / rel, DST / rel)
    print(f"copied {len(files())} roster files -> {DST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
