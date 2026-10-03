#!/usr/bin/env python3
"""data/audio/ is the single source of truth for the v1 audio contract (M1-GAME-04, AUTH #022).

Checks (governance.yml, job audio-sync):
  1. acoustics.json, sound_bank.json, mixer.json all parse.
  2. The contract is internally consistent: the sound bank validates (every verb covered,
     well-formed); the mixer validates (buses match the bank, ducking + budget sane); the
     acoustics table covers every scene_graph material.
  3. If a Unity mirror unity/Assets/StreamingAssets/audio/<f>.json exists it is byte-identical
     (copied, never hand-edited). None yet is fine (the C# audio engine has not landed).
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUDIO = ROOT / "data" / "audio"
UNITY_AUDIO = ROOT / "unity" / "Assets" / "StreamingAssets" / "audio"
SCENE_GRAPH_SCHEMA = ROOT / "data" / "schemas" / "environment" / "scene_graph.json"
FILES = ("acoustics.json", "sound_bank.json", "mixer.json")


def main() -> int:
    errors: list[str] = []

    # 1. all three parse
    for name in FILES:
        try:
            json.loads((AUDIO / name).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"::error file=data/audio/{name}::does not parse: {exc}")
            return 1

    # 2. internal consistency (reuse the reference validators)
    sys.path.insert(0, str(ROOT / "services" / "audio"))
    try:
        import bank
        import mixer

        errors += [f"sound_bank: {p}" for p in bank.validate_bank()]
        errors += [f"mixer: {p}" for p in mixer.validate_mixer()]
    except ImportError as exc:
        errors.append(f"could not import the services/audio validators: {exc}")

    # acoustics must cover every scene_graph material
    try:
        acoustics = json.loads((AUDIO / "acoustics.json").read_text(encoding="utf-8"))
        schema = json.loads(SCENE_GRAPH_SCHEMA.read_text(encoding="utf-8"))
        materials = set(schema["$defs"]["surface"]["properties"]["material"]["enum"])
        missing = sorted(materials - set(acoustics.get("material_absorption", {})))
        if missing:
            errors.append(f"acoustics.json material_absorption missing materials: {missing}")
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"could not check acoustics material coverage: {exc}")

    # 3. Unity mirror byte-identity (lenient until the engine lands)
    if not any((UNITY_AUDIO / n).exists() for n in FILES):
        print("note: no Unity audio mirror yet (the C# audio engine adds StreamingAssets/audio/)")
    else:
        for name in FILES:
            mirror = UNITY_AUDIO / name
            if not mirror.exists():
                errors.append(
                    f"partial Unity audio mirror: StreamingAssets/audio/{name} is missing "
                    "(mirror all three audio files together)"
                )
            elif mirror.read_bytes() != (AUDIO / name).read_bytes():
                errors.append(
                    f"unity/Assets/StreamingAssets/audio/{name} is not byte-identical to "
                    f"data/audio/{name} (copy it; never hand-edit the Unity copy)"
                )

    for err in errors:
        print(f"::error::{err}")
    if not errors:
        print("audio-sync: OK")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
