"""Reference math for the v1 traversal tools (AUTH #021, M3-MOVE-01) — Brain-B side.

Deterministic contracts the Unity tool runtime (Brain A) must match, so the C# tool state machine
never invents its own numbers:

* **Safety-pin grapple** (swing / ascend / rappel) — anchor eligibility, forgiving aim snap, mode
  selection, reach, and the state-machine timing (aim -> deploy/mount -> verb -> auto-unhook ->
  reel -> coil to the back).
* **Matchstick pole-vault** — gap/height feasibility gated by run speed + the plant window.

All constants live in ``config/movement.json`` (``grapple`` / ``poleVault`` blocks); the dataclasses
mirror them and ``from_movement_config`` reads the live file, with a test pinning the defaults.
The reach/feasibility math agrees with the shared affordance library (``affordances.verb_margin``
for the grapple/pole-vault verbs). Standard library only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import movement

_EPS = 1e-9


@dataclass(frozen=True)
class GrappleParams:
    """``movement.json.grapple`` — the safety-pin + twine grapple."""

    reachA: float = 6.0
    swingSpeed: float = 3.0
    swingMaxArcDeg: float = 120.0
    ascendSpeed: float = 0.7
    rappelSpeed: float = 1.0
    deploySec: float = 0.4
    reelSec: float = 0.6
    anchorMinLedgeA: float = 0.1
    snapAssistA: float = 0.3

    @classmethod
    def from_movement_config(cls, cfg: movement.MovementConfig | None = None) -> GrappleParams:
        cfg = cfg if cfg is not None else movement.load()
        return cls(**asdict(cfg.grapple))


@dataclass(frozen=True)
class PoleVaultParams:
    """``movement.json.poleVault`` — the matchstick pole-vault."""

    plantWindowSec: float = 0.25
    minRunSpeed: float = 2.4
    maxGapA: float = 3.0
    maxHeightA: float = 2.0

    @classmethod
    def from_movement_config(cls, cfg: movement.MovementConfig | None = None) -> PoleVaultParams:
        cfg = cfg if cfg is not None else movement.load()
        return cls(**asdict(cfg.poleVault))


DEFAULT_GRAPPLE = GrappleParams()
DEFAULT_POLE_VAULT = PoleVaultParams()

_GRAPPLE_SPEED = {"swing": "swingSpeed", "ascend": "ascendSpeed", "rappel": "rappelSpeed"}


# --- grapple ------------------------------------------------------------------------------


def grapple_span_A(distance_A: float, rise_A: float) -> float:
    """The twine length a shot needs: the larger of the horizontal gap and the vertical change
    (matches ``affordances`` grapple reach)."""
    return max(abs(rise_A), distance_A)


def grapple_in_reach(distance_A: float, rise_A: float, g: GrappleParams = DEFAULT_GRAPPLE) -> bool:
    """True if the anchor is within the twine's ``reachA``."""
    return grapple_span_A(distance_A, rise_A) <= g.reachA


def anchor_eligible(anchor_ledge_A: float, g: GrappleParams = DEFAULT_GRAPPLE) -> bool:
    """A pin needs an anchor ledge of at least ``anchorMinLedgeA`` to mount."""
    return anchor_ledge_A >= g.anchorMinLedgeA


def aim_assisted(aim_error_A: float, g: GrappleParams = DEFAULT_GRAPPLE) -> bool:
    """Forgiving aim (AT-4): a shot within ``snapAssistA`` of a valid anchor snaps to it."""
    return abs(aim_error_A) <= g.snapAssistA


def grapple_mode(distance_A: float, rise_A: float) -> str:
    """Which grapple verb a transition uses: ``rappel`` for a vertical-dominant descent, ``ascend``
    for a vertical-dominant climb, ``swing`` for a lateral gap (the pendulum)."""
    if rise_A < -_EPS and abs(rise_A) >= distance_A:
        return "rappel"
    if rise_A > _EPS and rise_A >= distance_A:
        return "ascend"
    return "swing"


def grapple_traversal_time(
    distance_A: float, rise_A: float, g: GrappleParams = DEFAULT_GRAPPLE
) -> float:
    """Mechanical time for the full state machine: ``deploySec`` + travel (span / the mode's speed)
    + ``reelSec``. Aim is player-paced and not counted. The C# runtime matches this."""
    mode = grapple_mode(distance_A, rise_A)
    speed = getattr(g, _GRAPPLE_SPEED[mode])
    travel = grapple_span_A(distance_A, rise_A) / speed if speed > 0 else 0.0
    return round(g.deploySec + travel + g.reelSec, 4)


def grapple_timeline(
    distance_A: float, rise_A: float, g: GrappleParams = DEFAULT_GRAPPLE
) -> list[dict]:
    """The ordered state-machine phases (AT-1): aim -> deploy/mount -> the grapple verb ->
    auto-unhook -> reel -> coil to the back, with each phase's duration (s). ``aim``, ``unhook``
    and ``coil`` are instantaneous transitions here; ``deploy``/verb/``reel`` carry the timing."""
    mode = grapple_mode(distance_A, rise_A)
    speed = getattr(g, _GRAPPLE_SPEED[mode])
    travel = round(grapple_span_A(distance_A, rise_A) / speed, 4) if speed > 0 else 0.0
    return [
        {"phase": "aim", "duration_s": 0.0},
        {"phase": "deploy", "duration_s": g.deploySec},
        {"phase": mode, "duration_s": travel},
        {"phase": "unhook", "duration_s": 0.0},
        {"phase": "reel", "duration_s": g.reelSec},
        {"phase": "coil", "duration_s": 0.0},
    ]


# --- pole-vault ---------------------------------------------------------------------------


def pole_vault_feasible(
    gap_A: float, height_A: float, run_speed_A_s: float, pv: PoleVaultParams = DEFAULT_POLE_VAULT
) -> bool:
    """A plant clears a gap up to ``maxGapA`` or a height up to ``maxHeightA``, but only at jog+ —
    the run-up must reach ``minRunSpeed`` (the plant window is ``plantWindowSec``)."""
    within = gap_A <= pv.maxGapA and max(height_A, 0.0) <= pv.maxHeightA
    return within and run_speed_A_s >= pv.minRunSpeed
