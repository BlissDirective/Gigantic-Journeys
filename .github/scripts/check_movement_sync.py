#!/usr/bin/env python3
"""config/movement.json is the single source of truth for movement constants.

Checks (governance.yml, job movement-sync):
  1. config/movement.json parses.
  2. It equals the JSON block in design/MOVEMENT_BIBLE.md §10 (they change together under one
     AUTH REQUEST of type design-change; Bible header rule for Sections 3, 5, 10).
  3. If unity/Assets/StreamingAssets/movement.json exists it is byte-identical (copied, never
     hand-edited).
  4. If config/movement.schema.json exists, the constants validate against it.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "movement.json"
BIBLE = ROOT / "design" / "MOVEMENT_BIBLE.md"
UNITY_COPY = ROOT / "unity" / "Assets" / "StreamingAssets" / "movement.json"
SCHEMA = ROOT / "config" / "movement.schema.json"
BIBLE_BLOCK = re.compile(r"## 10\. Tuning constants.*?```json\n(.*?)```", re.S)


def main() -> int:
    errors: list[str] = []
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"::error file=config/movement.json::does not parse: {exc}")
        return 1

    match = BIBLE_BLOCK.search(BIBLE.read_text(encoding="utf-8"))
    if not match:
        errors.append("could not find the §10 JSON block in design/MOVEMENT_BIBLE.md")
    else:
        try:
            if json.loads(match.group(1)) != config:
                errors.append(
                    "config/movement.json differs from design/MOVEMENT_BIBLE.md §10; "
                    "they change together under one AUTH (design-change)"
                )
        except json.JSONDecodeError as exc:
            errors.append(f"Movement Bible §10 JSON does not parse: {exc}")

    if UNITY_COPY.exists():
        if UNITY_COPY.read_bytes() != CONFIG.read_bytes():
            errors.append(
                "unity/Assets/StreamingAssets/movement.json is not byte-identical to "
                "config/movement.json (copy it; never hand-edit the Unity copy)"
            )
    else:
        print("note: no Unity copy yet (M0-MOVE-01 adds the StreamingAssets copy)")

    if SCHEMA.exists():
        try:
            import jsonschema

            jsonschema.validate(config, json.loads(SCHEMA.read_text(encoding="utf-8")))
        except ImportError:
            print("note: jsonschema not installed; skipping schema validation")
        except (json.JSONDecodeError, jsonschema.ValidationError, jsonschema.SchemaError) as exc:
            errors.append(f"movement.json fails config/movement.schema.json: {exc}")

    for err in errors:
        print(f"::error::{err}")
    if not errors:
        print("movement-sync: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
