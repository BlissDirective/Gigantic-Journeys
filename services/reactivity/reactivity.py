"""Tier-1 reactivity feedback matrix (M3-GAME-01, AUTH #022).

The authoritative, declarative mapping the Unity shader-displacement + particle system consumes:
per scene_graph material how a surface reacts, and per gameplay event what it triggers. Shares the
scene_graph material enum + the traversal_graph verb enum with the audio bank (one source of truth,
many reactions). ``validate_reactivity`` enforces material + verb coverage and well-formedness.
Shader displacement only -- no physics (Tier 2 is research, SPEC §5). stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_MATRIX_PATH = _REPO / "data" / "reactivity" / "reactivity.json"
_SCENE_GRAPH = _REPO / "data" / "schemas" / "environment" / "scene_graph.json"
_TRAVERSAL_GRAPH = _REPO / "data" / "schemas" / "environment" / "traversal_graph.json"


def load_matrix() -> dict:
    return json.loads(_MATRIX_PATH.read_text(encoding="utf-8"))


def scene_graph_materials() -> set[str]:
    schema = json.loads(_SCENE_GRAPH.read_text(encoding="utf-8"))
    return set(schema["$defs"]["surface"]["properties"]["material"]["enum"])


def verb_set() -> set[str]:
    schema = json.loads(_TRAVERSAL_GRAPH.read_text(encoding="utf-8"))
    return set(schema["$defs"]["edge"]["properties"]["verb"]["enum"])


def _num_ok(x: object, lo: float, hi: float) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and lo <= x <= hi


def validate_reactivity(matrix: dict | None = None) -> list[str]:
    """Return a sorted list of problems ([] if the matrix is well-formed and complete)."""
    matrix = matrix if matrix is not None else load_matrix()
    problems: list[str] = []
    disp_kinds = set(matrix.get("displacement_kinds", []))
    part_kinds = set(matrix.get("particle_kinds", []))
    haptics = set(matrix.get("haptic_levels", []))
    shakes = set(matrix.get("shake_levels", []))

    mr = matrix.get("material_response", {})
    missing_mat = sorted(scene_graph_materials() - set(mr))
    if missing_mat:
        problems.append(f"material_response missing scene_graph materials: {missing_mat}")
    for mat, r in mr.items():
        where = f"material {mat}"
        if r.get("displacement") not in disp_kinds:
            problems.append(f"{where}: displacement {r.get('displacement')!r} not a known kind")
        if r.get("particle") not in part_kinds:
            problems.append(f"{where}: particle {r.get('particle')!r} not a known kind")
        if not _num_ok(r.get("stiffness"), 0.0, 1.0):
            problems.append(f"{where}: stiffness must be a number in [0, 1]")

    er = matrix.get("event_reaction", {})
    missing_verb = sorted(verb_set() - set(er))
    if missing_verb:
        problems.append(f"event_reaction missing verbs: {missing_verb}")
    for ev, r in er.items():
        where = f"event {ev}"
        if r.get("particle") not in part_kinds:
            problems.append(f"{where}: particle {r.get('particle')!r} not a known kind")
        if r.get("haptic") not in haptics:
            problems.append(f"{where}: haptic {r.get('haptic')!r} not a known level")
        if r.get("camera_shake") not in shakes:
            problems.append(f"{where}: camera_shake {r.get('camera_shake')!r} not a known level")
        if not isinstance(r.get("displaces"), bool):
            problems.append(f"{where}: displaces must be a bool")

    budget = matrix.get("budget", {})
    if budget.get("fps_floor") != 30:
        problems.append("budget.fps_floor must be 30 (M3 exit target)")
    mc = budget.get("max_concurrent_reactions")
    if not isinstance(mc, int) or isinstance(mc, bool) or mc < 1:
        problems.append("budget.max_concurrent_reactions must be an int >= 1")
    if not _num_ok(matrix.get("scale", {}).get("ref_multiplier"), 1e-6, 1e9):
        problems.append("scale.ref_multiplier must be a positive number")

    return sorted(problems)
