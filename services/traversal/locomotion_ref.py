"""Reference math for the movement fluidity/realism pack (AUTH #043) — Brain-B side.

Deterministic contracts the Unity runtime (Brain A) must match:

* **#1 stride/speed warping** → :func:`stride_scale` (kill foot-sliding at any speed).
* **#3 procedural landing/weight** → :func:`landing_response` (Bible §5 tiers → absorption).
* **#6 miniature realism** → :func:`cadence_for_scale` / :func:`realism_fraction`.

The tuning constants live in ``config/movement.json`` (``locomotion`` / ``landingResponse``
blocks, landed with the AUTH #043 lockstep + the C# ``MovementConfig`` migration). The dataclass
defaults mirror those values so callers without a config still get the shipped profile;
:meth:`LocomotionParams.from_movement_config` / :meth:`LandingParams.from_movement_config` read the
live file, and a test pins the defaults to it. Landing-tier *thresholds* (soft/roll/hard) are read
from ``movement.json.landing``.

Standard library only.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

import movement


@dataclass(frozen=True)
class LocomotionParams:
    """``movement.json.locomotion`` block (#1, #6). Values are the "more miniature-real"
    defaults (Owner 2026-10-01); the "keep the fantasy" variant lowers ``cadenceScale`` to 1.5 and
    raises the accel time to 0.14."""

    refStrideA: float = 0.9
    refCadence: float = 2.6
    cadenceScale: float = 1.9
    accelTimeSec: float = 0.10
    decelTimeSec: float = 0.10
    strideWarpMin: float = 0.6
    strideWarpMax: float = 1.8
    footPlantLockRadiusA: float = 0.05

    @classmethod
    def from_movement_config(cls, cfg: movement.MovementConfig | None = None) -> LocomotionParams:
        """Build from ``movement.json.locomotion`` (loads ``config/movement.json`` by default)."""
        cfg = cfg if cfg is not None else movement.load()
        return cls(**asdict(cfg.locomotion))


@dataclass(frozen=True)
class LandingParams:
    """``movement.json.landingResponse`` block (#3). Absorption/camera scale with the
    Bible §5 tier; the tier *thresholds* themselves come from ``movement.json.landing``."""

    absorbTimeSec: float = 0.12
    recoverTimeSec: float = 0.22
    maxCrouchFraction: float = 0.35
    camDipA: float = 0.15
    softSurfaceExtra: float = 0.5
    controlLockSec: dict[str, float] = field(
        default_factory=lambda: {"soft": 0.0, "roll": 0.15, "hard": 0.3}
    )

    @classmethod
    def from_movement_config(cls, cfg: movement.MovementConfig | None = None) -> LandingParams:
        """Build from ``movement.json.landingResponse`` (loads the live file by default)."""
        cfg = cfg if cfg is not None else movement.load()
        return cls(**asdict(cfg.landingResponse))


DEFAULT_LOCOMOTION = LocomotionParams()
DEFAULT_LANDING = LandingParams()

# Bible §5: a >5A fall is "recover" — ragdoll 0.4 s + get-up 1.2 s (time penalty, no v1 damage).
RECOVER_LOCK_SEC = 1.6
# Forward speed kept per landing tier (Bible §5): soft keeps all, roll keeps 60%, hard/recover zero.
_KEEPS_SPEED = {"soft": 1.0, "roll": 0.6, "hard": 0.0, "recover": 0.0}
# Absorption + camera-dip strength per tier, as a fraction of the configured maxima.
_TIER_STRENGTH = {"soft": 0.4, "roll": 0.7, "hard": 1.0, "recover": 1.0}
# Gentlest → harshest, for the walkable-soft "tier -1" bonus (Bible §5).
_TIER_ORDER = ("soft", "roll", "hard", "recover")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# --- #1 / #6 locomotion -------------------------------------------------------------------


def natural_locomotion_speed(p: LocomotionParams = DEFAULT_LOCOMOTION) -> float:
    """Ground speed (A/s) the base locomotion clip covers at its authored cadence × stride,
    including the #6 ``cadenceScale``. Stride warping stretches the clip around this speed."""
    return p.refCadence * p.cadenceScale * p.refStrideA


def stride_scale(ground_speed_A_s: float, p: LocomotionParams = DEFAULT_LOCOMOTION) -> float:
    """#1 — stride-warp ratio for the current ground speed, clamped to
    ``[strideWarpMin, strideWarpMax]``. ``1.0`` plays the clip at its natural stride, ``>1``
    stretches, ``<1`` compresses; the C# locks a planted foot within ``footPlantLockRadiusA`` so a
    contact never slides. Monotonic non-decreasing in speed."""
    if ground_speed_A_s < 0:
        raise ValueError("ground_speed_A_s must be >= 0")
    natural = natural_locomotion_speed(p)
    raw = ground_speed_A_s / natural if natural > 0 else p.strideWarpMax
    return _clamp(raw, p.strideWarpMin, p.strideWarpMax)


def approach_speed(
    current: float, target: float, dt: float, p: LocomotionParams = DEFAULT_LOCOMOTION
) -> float:
    """#6 — snappier accel/decel reference: move ``current`` toward ``target`` at a constant rate
    that would cover a full natural-speed change in ``accelTimeSec`` (speeding up) or
    ``decelTimeSec`` (slowing), never overshooting. The C# locomotion smoothing matches this."""
    if dt <= 0:
        return current
    tau = p.accelTimeSec if abs(target) >= abs(current) else p.decelTimeSec
    if tau <= 0:
        return target
    step = (natural_locomotion_speed(p) / tau) * dt
    if abs(target - current) <= step:
        return target
    return current + math.copysign(step, target - current)


def physical_cadence_multiplier(scale: float) -> float:
    """The step-rate multiplier that *full* miniature realism implies: a pendulum/step period
    scales with √length, so a 1:``scale`` body steps √``scale``× faster than a human. This is the
    realism ceiling (≈3.46× at 1:12) — documented, rarely shipped whole."""
    if scale <= 0:
        raise ValueError("scale must be > 0")
    return math.sqrt(scale)


def effective_cadence(p: LocomotionParams = DEFAULT_LOCOMOTION) -> float:
    """The step rate the game actually uses (steps/s) = ``refCadence × cadenceScale``."""
    return p.refCadence * p.cadenceScale


def cadence_for_scale(scale: float, p: LocomotionParams = DEFAULT_LOCOMOTION) -> dict[str, float]:
    """#6 — the miniature cadence dial for ``scale`` (e.g. 12 for 1:12): the chosen multiplier,
    the physical ceiling, and where the chosen value sits between human (0.0) and full (1.0)."""
    return {
        "chosen_multiplier": p.cadenceScale,
        "effective_cadence": effective_cadence(p),
        "physical_ceiling": physical_cadence_multiplier(scale),
        "realism_fraction": realism_fraction(scale, p),
    }


def realism_fraction(scale: float, p: LocomotionParams = DEFAULT_LOCOMOTION) -> float:
    """Where ``cadenceScale`` sits on the human (0.0) → full-miniature (1.0) dial for ``scale``.
    0.0 when the ceiling is 1 (scale 1)."""
    ceiling = physical_cadence_multiplier(scale)
    if ceiling <= 1.0:
        return 0.0
    return (p.cadenceScale - 1.0) / (ceiling - 1.0)


# --- #3 procedural landing / weight -------------------------------------------------------


@dataclass(frozen=True)
class LandingResponse:
    """What the C# landing system plays: the Bible §5 tier plus the procedural weight it drives."""

    tier: str
    absorb_fraction: float  # body compression as a fraction of avatar height
    cam_dip_A: float  # camera dip distance (A)
    control_lock_s: float  # how long before full control returns
    keeps_speed_fraction: float  # forward speed retained through the landing


def _landing_thresholds() -> tuple[float, float, float]:
    cfg = movement.load()
    return (cfg.landing.soft, cfg.landing.roll, cfg.landing.hard)


def landing_tier(
    fall_A: float,
    surface_class: str = "walkable-hard",
    moving_forward: bool = True,
    thresholds: tuple[float, float, float] | None = None,
) -> str:
    """Bible §5 landing tier for a fall of ``fall_A`` A. ``roll`` needs forward motion (neutral →
    ``hard``); landing on ``walkable-soft`` is one tier gentler (the cushion bonus)."""
    soft, roll, hard = thresholds if thresholds is not None else _landing_thresholds()
    if fall_A < soft:
        tier = "soft"
    elif fall_A < roll:
        tier = "roll" if moving_forward else "hard"
    elif fall_A <= hard:
        tier = "hard"
    else:
        tier = "recover"
    if surface_class == "walkable-soft":
        tier = _TIER_ORDER[max(0, _TIER_ORDER.index(tier) - 1)]
    return tier


def landing_response(
    fall_A: float,
    surface_class: str = "walkable-hard",
    moving_forward: bool = True,
    p: LandingParams = DEFAULT_LANDING,
    thresholds: tuple[float, float, float] | None = None,
) -> LandingResponse:
    """#3 — the procedural landing response for a fall: tier (Bible §5) → absorption, camera dip,
    control-lock, and retained speed. Absorption/camera scale with the tier's strength."""
    if fall_A < 0:
        raise ValueError("fall_A must be >= 0")
    tier = landing_tier(fall_A, surface_class, moving_forward, thresholds)
    strength = _TIER_STRENGTH[tier]
    lock = RECOVER_LOCK_SEC if tier == "recover" else p.controlLockSec[tier]
    return LandingResponse(
        tier=tier,
        absorb_fraction=p.maxCrouchFraction * strength,
        cam_dip_A=p.camDipA * strength,
        control_lock_s=lock,
        keeps_speed_fraction=_KEEPS_SPEED[tier],
    )
