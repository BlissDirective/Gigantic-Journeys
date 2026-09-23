"""Loader for the shared movement tuning contract (``config/movement.json``).

``config/movement.json`` is the single source of truth for movement constants
(Movement Bible §10). This module loads it into typed, frozen dataclasses and
exposes the 85 % reachability margin the deterministic validator uses
(SPEC §3.4, ticket M1-SCEN-05). Dataclass field names mirror the JSON keys 1:1
so the contract is explicit and the loader can reject a missing or unknown key.

Standard library only — no third-party runtime dependency.
"""

import json
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any

MARGIN = 0.85
"""Reachability safety margin: a transition is accepted only up to 85 % of the
maximum (a 15 % margin), per SPEC §3.4 and the Bible §10 validator contract."""

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "movement.json"


class MovementConfigError(ValueError):
    """Raised when movement.json is missing a required key or carries an unknown one."""


def with_margin(value: float) -> float:
    """Return 85 % of ``value`` — the usable reach/distance under the 15 % margin."""
    return MARGIN * value


@dataclass(frozen=True)
class Speeds:
    walk: float
    jog: float
    run: float
    sprint: float
    shimmy: float
    rung: float
    stud: float
    freeClimb: float
    pole: float
    overhang: float


@dataclass(frozen=True)
class Jump:
    standingHeight: float
    standingDistance: float
    runningHeight: float
    runningDistance: float
    sprintDistance: float
    precisionDamping: float
    coyoteMs: float
    bufferMs: float
    ledgeCatchRadius: float


@dataclass(frozen=True)
class Verticals:
    stepUp: float
    hopOver: float
    vault: float
    mantle: float
    vaultMaxDepth: float
    hopMaxDepth: float


@dataclass(frozen=True)
class Landing:
    soft: float
    roll: float
    hard: float
    softSurfaceTierBonus: float


@dataclass(frozen=True)
class Slopes:
    runMaxDeg: float
    slideMinDeg: float
    slideMaxDeg: float


@dataclass(frozen=True)
class Reach:
    ledgeToLedge: float
    holdReach: float
    slipChanceAtMaxReach: float


@dataclass(frozen=True)
class Assist:
    coyoteMs: float
    jumpBonus: float
    slipsOff: bool
    autoGrab: bool


@dataclass(frozen=True)
class Dive:
    minSpeed: float
    distanceA: float
    rollAboveA: float


@dataclass(frozen=True)
class TicTac:
    reboundHeightA: float
    reboundDistanceA: float
    maxChain: float


@dataclass(frozen=True)
class WallRun:
    minWallRunA: float
    maxDurationSec: float
    speed: float
    minEntrySpeed: float
    gravityDampen: float


@dataclass(frozen=True)
class PoleVault:
    plantWindowSec: float
    minRunSpeed: float
    maxGapA: float
    maxHeightA: float


@dataclass(frozen=True)
class Grapple:
    reachA: float
    swingSpeed: float
    swingMaxArcDeg: float
    ascendSpeed: float
    rappelSpeed: float
    deploySec: float
    reelSec: float
    anchorMinLedgeA: float
    snapAssistA: float


@dataclass(frozen=True)
class MovementConfig:
    avatarHeightA: float
    speeds: Speeds
    jump: Jump
    verticals: Verticals
    landing: Landing
    slopes: Slopes
    reach: Reach
    narrowWidthA: float
    crouchHeadroomA: float
    gravityScale: float
    assist: Assist
    dive: Dive
    ticTac: TicTac
    wallRun: WallRun
    poleVault: PoleVault
    grapple: Grapple


def _build(cls: type, data: Any, path: str) -> Any:
    """Strictly build ``cls`` from ``data``; reject missing or unknown keys."""
    if not isinstance(data, dict):
        raise MovementConfigError(f"{path}: expected an object, got {type(data).__name__}")
    field_map = {f.name: f for f in fields(cls)}
    missing = sorted(set(field_map) - set(data))
    unknown = sorted(set(data) - set(field_map))
    if missing:
        raise MovementConfigError(f"{path}: missing key(s) {missing}")
    if unknown:
        raise MovementConfigError(f"{path}: unknown key(s) {unknown}")
    kwargs: dict[str, Any] = {}
    for name, field in field_map.items():
        value = data[name]
        kwargs[name] = (
            _build(field.type, value, f"{path}.{name}") if is_dataclass(field.type) else value
        )
    return cls(**kwargs)


def loads(data: dict[str, Any]) -> MovementConfig:
    """Build a :class:`MovementConfig` from an already-parsed dict."""
    return _build(MovementConfig, data, "movement")


def load(path: str | Path | None = None) -> MovementConfig:
    """Load and validate ``config/movement.json`` (or ``path``) into a config object."""
    target = Path(path) if path is not None else DEFAULT_PATH
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise MovementConfigError(f"cannot read {target}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MovementConfigError(f"{target} is not valid JSON: {exc}") from exc
    return loads(data)
