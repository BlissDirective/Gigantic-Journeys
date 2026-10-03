"""Scale-aware acoustics reference (M1-GAME-04, AUTH #022).

Deterministic reference the Unity/C# audio engine mirrors. Two signature computations:

- ``reverb_profile`` / ``reverb_from_scene_graph``: a parametric room reverb (RT60 via Sabine,
  wet mix, HF damping) derived from the reconstructed room's volume + its surface materials (both
  in the frozen scene_graph), so a big tiled room rings and a small carpeted one is dead.
- ``scale_pitch_semitones`` / ``scale_gain_db``: how an event's pitch and level shift with the
  environment scale multiplier (scene_graph.scale.multiplier), so Lego clicks stay tiny and floor
  booms stay big.

All tuning lives in ``data/audio/acoustics.json`` (the C# engine reads the same file). stdlib only.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_TUNING_PATH = _REPO / "data" / "audio" / "acoustics.json"

TUNING: dict = json.loads(_TUNING_PATH.read_text(encoding="utf-8"))
ABSORPTION: dict[str, float] = TUNING["material_absorption"]


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def absorption_of(material: str) -> float:
    """Mid-band Sabine absorption for a scene_graph material (falls back to 'unknown')."""
    return ABSORPTION.get(material, ABSORPTION["unknown"])


@dataclass(frozen=True)
class ReverbProfile:
    rt60_s: float
    wet: float
    hf_damping: float  # 0..1; higher = duller (more high frequencies absorbed)


def reverb_profile(
    volume_m3: float, boundary_area_m2: float, avg_absorption: float
) -> ReverbProfile:
    """Parametric reverb from room geometry + average absorption.

    RT60 = k * V / (S * a_avg) (Sabine); wet grows with RT60; damping grows with absorption.
    All outputs are clamped to the playable range in ``acoustics.json``.
    """
    k = TUNING["sabine_k"]
    rc = TUNING["rt60_clamp_s"]
    a_avg = _clamp(avg_absorption, 0.01, 1.0)
    total_absorption = max(boundary_area_m2 * a_avg, 1e-6)  # sabins (m^2)
    rt60 = _clamp(k * max(volume_m3, 0.0) / total_absorption, rc["min"], rc["max"])
    w = TUNING["wet"]
    span = max(w["rt60_full_s"] - rc["min"], 1e-6)
    frac = _clamp((rt60 - rc["min"]) / span, 0.0, 1.0)
    wet = w["min"] + frac * (w["max"] - w["min"])
    return ReverbProfile(round(rt60, 4), round(wet, 4), round(a_avg, 4))


def avg_absorption_of_surfaces(surfaces: list[dict]) -> float:
    """Area-weighted mean absorption over classified surfaces (by area_A2 and material)."""
    num = 0.0
    den = 0.0
    for s in surfaces:
        area = float(s.get("area_A2", 0.0) or 0.0)
        if area <= 0.0:
            continue
        num += area * absorption_of(s.get("material", "unknown"))
        den += area
    return num / den if den > 0 else absorption_of("unknown")


def reverb_from_scene_graph(doc: dict) -> ReverbProfile:
    """Compute a room reverb from a scene_graph document (frozen schema)."""
    m_per_a = float(doc["scale"]["metres_per_A"])
    lo, hi = doc["bounds"]["min"], doc["bounds"]["max"]
    lx = abs(hi[0] - lo[0]) * m_per_a
    ly = abs(hi[1] - lo[1]) * m_per_a
    lz = abs(hi[2] - lo[2]) * m_per_a
    volume_m3 = lx * ly * lz
    boundary_area_m2 = 2.0 * (lx * ly + lx * lz + ly * lz)
    a_avg = avg_absorption_of_surfaces(doc.get("surfaces", []))
    return reverb_profile(volume_m3, boundary_area_m2, a_avg)


def _octave_scale(multiplier: float) -> float:
    ref = TUNING["scale"]["ref_multiplier"]
    return math.log2(max(multiplier, 1e-6) / ref)


def scale_pitch_semitones(multiplier: float, weight: str = "medium") -> float:
    """Pitch shift (semitones) for an event at this scale. A tinier world (bigger multiplier)
    pitches up; heavier events resist the shift so booms stay big."""
    sc = TUNING["scale"]
    base = sc["pitch_semitones_per_octave"] * _octave_scale(multiplier)
    factor = sc["weight_pitch_factor"].get(weight, sc["weight_pitch_factor"]["medium"])
    pc = sc["pitch_clamp_semitones"]
    return round(_clamp(base * factor, pc["min"], pc["max"]), 4)


def scale_gain_db(multiplier: float) -> float:
    """Level trim (dB) for the scale: a tinier world is a touch quieter / closer-miked."""
    sc = TUNING["scale"]
    gc = sc["gain_clamp_db"]
    base = sc["gain_db_per_octave"] * _octave_scale(multiplier)
    return round(_clamp(base, gc["min"], gc["max"]), 4)
