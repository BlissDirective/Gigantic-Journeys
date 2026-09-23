#!/usr/bin/env python3
"""Copy config/movement.json to the Unity StreamingAssets path, byte-identically.

The Unity copy at ``unity/Assets/StreamingAssets/movement.json`` is never
hand-edited. Run this after any AUTH-approved change to ``config/movement.json``
(which changes together with Movement Bible §10). CI (``governance.yml``, job
``movement-sync``) fails if the two files are not byte-identical.

Usage: ``python .github/scripts/copy_movement_to_unity.py``
"""

from __future__ import annotations

import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "config" / "movement.json"
DST = ROOT / "unity" / "Assets" / "StreamingAssets" / "movement.json"


def main() -> None:
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC, DST)
    print(f"copied {SRC.relative_to(ROOT)} -> {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
