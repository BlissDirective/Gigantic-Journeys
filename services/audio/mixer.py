"""AudioMixer / bus config reference (M1-GAME-04, AUTH #022).

The Unity AudioMixer graph + static mix as data: a master, the five category buses (matching the
sound bank's buses), a scale-aware reverb send bus (fed by the diegetic buses, driven by
services/audio/acoustics), sidechain ducking rules, and the mobile voice budget. ``validate_mixer``
cross-checks the buses against data/audio/sound_bank.json so every event's bus has a mixer strip.
The C# audio engine mirrors this file. stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_MIXER_PATH = _REPO / "data" / "audio" / "mixer.json"
_BANK_PATH = _REPO / "data" / "audio" / "sound_bank.json"

GAIN_MIN_DB = -60.0
GAIN_MAX_DB = 6.0
VOICE_CAP = 64  # mobile polyphony ceiling
DRY_BUSES = ("ui", "music")  # non-diegetic: no room reverb (diegetic-first design)


def load_mixer() -> dict:
    return json.loads(_MIXER_PATH.read_text(encoding="utf-8"))


def _bank_buses() -> set[str]:
    return set(json.loads(_BANK_PATH.read_text(encoding="utf-8")).get("buses", []))


def _is_num(x: object) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_mixer(mixer: dict | None = None, bank_buses: set[str] | None = None) -> list[str]:
    """Return a sorted list of problems ([] if the mixer is well-formed and consistent)."""
    mixer = mixer if mixer is not None else load_mixer()
    bank_buses = bank_buses if bank_buses is not None else _bank_buses()
    problems: list[str] = []
    buses = mixer.get("buses", {})
    names = set(buses)

    if names != bank_buses:
        problems.append(
            f"mixer buses {sorted(names)} != bank buses "
            f"(missing={sorted(bank_buses - names)} extra={sorted(names - bank_buses)})"
        )

    def _gain_ok(g: object, where: str) -> None:
        if not _is_num(g) or not (GAIN_MIN_DB <= g <= GAIN_MAX_DB):
            problems.append(f"{where}: gain_db {g} out of [{GAIN_MIN_DB}, {GAIN_MAX_DB}]")

    _gain_ok(mixer.get("master", {}).get("gain_db"), "master")
    _gain_ok(mixer.get("reverb_bus", {}).get("gain_db"), "reverb_bus")

    priorities = []
    for name, b in buses.items():
        where = f"bus {name}"
        _gain_ok(b.get("gain_db"), where)
        if not isinstance(b.get("reverb_send"), bool):
            problems.append(f"{where}: reverb_send must be a bool")
        mv = b.get("max_voices")
        if not isinstance(mv, int) or isinstance(mv, bool) or not (1 <= mv <= VOICE_CAP):
            problems.append(f"{where}: max_voices must be an int in [1, {VOICE_CAP}]")
        priorities.append(b.get("priority"))
        if name in DRY_BUSES and b.get("reverb_send"):
            problems.append(f"{where}: non-diegetic bus must have reverb_send=false")

    if any(not isinstance(p, int) or isinstance(p, bool) for p in priorities) or len(
        set(priorities)
    ) != len(priorities):
        problems.append(f"bus priorities must be unique integers: {priorities}")

    for d in mixer.get("ducking", []):
        nm = d.get("name", "?")
        if d.get("trigger") not in names:
            problems.append(f"duck {nm}: trigger {d.get('trigger')!r} not a bus")
        for t in d.get("targets", []):
            if t not in names:
                problems.append(f"duck {nm}: target {t!r} not a bus")
            if t == d.get("trigger"):
                problems.append(f"duck {nm}: target equals trigger {t!r}")
        if not (_is_num(d.get("duck_db")) and d["duck_db"] < 0):
            problems.append(f"duck {nm}: duck_db must be negative (a cut)")
        for key in ("attack_ms", "release_ms"):
            if not (_is_num(d.get(key)) and d[key] >= 0):
                problems.append(f"duck {nm}: {key} must be >= 0")

    vb = mixer.get("voice_budget", {}).get("total_max")
    if not isinstance(vb, int) or isinstance(vb, bool) or not (1 <= vb <= VOICE_CAP):
        problems.append(f"voice_budget.total_max must be an int in [1, {VOICE_CAP}]")
    else:
        biggest = max((b.get("max_voices", 0) for b in buses.values()), default=0)
        if vb < biggest:
            problems.append(f"voice_budget.total_max {vb} < largest bus max_voices {biggest}")

    return sorted(problems)
