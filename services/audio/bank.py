"""Material x event sound bank (M1-GAME-04, AUTH #022).

The authoritative, declarative feedback-matrix data (Bible §9 extended) the Unity audio engine
consumes: every v1 verb/tool/event -> its mix bus, sound layers, round-robin count, impact scaling,
scale weight, and whether it varies by surface material. ``validate_bank`` also checks coverage
against the frozen traversal_graph verb enum, so every movement verb has a sound. stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_BANK_PATH = _REPO / "data" / "audio" / "sound_bank.json"
_VERB_SCHEMA = _REPO / "data" / "schemas" / "environment" / "traversal_graph.json"

LAYERS = ("transient", "body", "tail")


def load_bank() -> dict:
    return json.loads(_BANK_PATH.read_text(encoding="utf-8"))


def verb_set() -> set[str]:
    """The v1 verb enum from the frozen traversal_graph schema."""
    schema = json.loads(_VERB_SCHEMA.read_text(encoding="utf-8"))
    return set(schema["$defs"]["edge"]["properties"]["verb"]["enum"])


def validate_bank(bank: dict | None = None) -> list[str]:
    """Return a sorted list of problems ([] if the bank is well-formed and complete)."""
    bank = bank if bank is not None else load_bank()
    problems: list[str] = []
    buses = set(bank.get("buses", []))
    weights = set(bank.get("weights", []))
    events = bank.get("events", {})

    for name, e in events.items():
        where = f"event {name}"
        if e.get("bus") not in buses:
            problems.append(f"{where}: bus {e.get('bus')!r} not in {sorted(buses)}")
        if e.get("weight") not in weights:
            problems.append(f"{where}: weight {e.get('weight')!r} not in {sorted(weights)}")
        layers = e.get("layers", [])
        if not layers or any(x not in LAYERS for x in layers):
            problems.append(
                f"{where}: layers {layers} must be a non-empty subset of {list(LAYERS)}"
            )
        rr = e.get("round_robin")
        if not isinstance(rr, int) or rr < 1:
            problems.append(f"{where}: round_robin must be an int >= 1")
        if not isinstance(e.get("impact_scaled"), bool):
            problems.append(f"{where}: impact_scaled must be a bool")
        if not isinstance(e.get("varies_by_material"), bool):
            problems.append(f"{where}: varies_by_material must be a bool")

    missing = sorted(verb_set() - set(events))
    if missing:
        problems.append(f"verbs with no sound: {missing}")

    # locomotion needs enough round-robin variants to avoid machine-gun repetition
    for loco in ("walk", "jog", "run"):
        e = events.get(loco)
        if e and e.get("round_robin", 0) < 4:
            problems.append(f"event {loco}: round_robin {e.get('round_robin')} < 4 (machine-gun)")

    return sorted(problems)
