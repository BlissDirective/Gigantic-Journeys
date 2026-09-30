"""Ranking + anti-gaming (M4-DATA-02, AUTH #026, SPEC §3.7).

A balanced blend (composition option A) of the four-axis community ratings
(fun / interesting / interactive / exciting) and five derived objective signals
(verticality, move variety, reachable volume, completion rate, replay rate), with the
three locked sort tabs — Top this week (time-decay), New (recency), Near your scale
(Room/Tabletop). Every weight comes from ``weights.json`` (telemetry-tunable, never
hard-coded).

Anti-gaming, so a deliberate rate-spam attack cannot materially move a rank (M4 exit):
one rating per account (kept latest), the creator's own rating dropped, a per-device cap
(Sybil farms share few devices), a brigade discount on low-trust rating bursts, account-
age trust weighting, and Bayesian shrinkage toward a prior so a handful of spam ratings
barely move the mean.

Pure standard library. The score is a pure function of its inputs; the DB/telemetry
adapters that supply ratings and play stats are a thin layer added on staging.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

_WEIGHTS = Path(__file__).resolve().parent / "weights.json"
_AXES = ("fun", "interesting", "interactive", "exciting")


def _normalise(d: dict[str, float]) -> dict[str, float]:
    total = sum(v for v in d.values() if isinstance(v, int | float))
    if total <= 0:
        return {k: 0.0 for k in d}
    return {k: (v / total) for k, v in d.items() if isinstance(v, int | float)}


def load_config(path: Path | None = None) -> dict:
    cfg = json.loads((path or _WEIGHTS).read_text(encoding="utf-8"))
    cfg["composition"] = _normalise(cfg["composition"])
    cfg["rating_axes"] = _normalise(cfg["rating_axes"])
    cfg["signals"] = _normalise(cfg["signals"])
    return cfg


@dataclass(frozen=True)
class Rating:
    user_id: str
    device_hash: str
    created_at: datetime
    account_age_days: float = 365.0
    fun: int | None = None
    interesting: int | None = None
    interactive: int | None = None
    exciting: int | None = None

    def axis(self, name: str) -> int | None:
        return getattr(self, name)


@dataclass(frozen=True)
class PlayStats:
    plays: int = 0
    summits: int = 0
    players: int = 0
    replays: int = 0


@dataclass
class Environment:
    environment_id: str
    capture_mode: str  # "room" | "tabletop"
    published_at: datetime
    creator_id: str
    ratings: list[Rating] = field(default_factory=list)
    signals: dict[str, float] | None = None  # precomputed 0..1, else computed from spec
    spec: dict | None = None
    graph: dict | None = None
    play: PlayStats = field(default_factory=PlayStats)


# --- anti-gaming rating aggregation ---


def _trust(rating: Rating, cfg: dict) -> float:
    ag = cfg["anti_gaming"]
    full = ag["full_trust_account_age_days"]
    floor = ag["new_account_trust_floor"]
    return max(floor, min(1.0, rating.account_age_days / full)) if full > 0 else 1.0


def _dedup_latest(ratings: list[Rating]) -> list[Rating]:
    latest: dict[str, Rating] = {}
    for r in ratings:
        cur = latest.get(r.user_id)
        if cur is None or r.created_at > cur.created_at:
            latest[r.user_id] = r
    return list(latest.values())


def _device_capped(ratings: list[Rating], cap: int) -> list[Rating]:
    """Keep at most ``cap`` ratings per device_hash — the most trusted (then earliest),
    deterministically — so a Sybil farm sharing few devices contributes little."""
    by_device: dict[str, list[Rating]] = {}
    for r in ratings:
        by_device.setdefault(r.device_hash, []).append(r)
    kept: list[Rating] = []
    for group in by_device.values():
        group.sort(key=lambda r: (-r.account_age_days, r.created_at.timestamp(), r.user_id))
        kept.extend(group[:cap])
    return kept


def _in_burst(rating: Rating, ratings: list[Rating], cfg: dict) -> bool:
    ag = cfg["anti_gaming"]
    window = timedelta(hours=ag["brigade_burst_window_h"])
    n = sum(1 for o in ratings if abs(o.created_at - rating.created_at) <= window)
    return n >= ag["brigade_burst_min_count"]


def effective_ratings(env: Environment, cfg: dict) -> list[tuple[Rating, float]]:
    """(rating, weight) pairs after dedup, self-rating removal, device cap, trust and the
    brigade discount. Empty when nothing survives."""
    ag = cfg["anti_gaming"]
    pool = [r for r in _dedup_latest(env.ratings) if r.user_id != env.creator_id]
    pool = _device_capped(pool, ag["per_device_cap"])
    out: list[tuple[Rating, float]] = []
    for r in pool:
        w = _trust(r, cfg)
        # a low-trust rating inside a burst is likely brigading -> discount it
        if w < 0.5 and _in_burst(r, pool, cfg):
            w *= ag["brigade_burst_trust_discount"]
        out.append((r, w))
    return out


def rating_component(env: Environment, cfg: dict) -> float:
    """0..1 blended, anti-gamed rating score (Bayesian-shrunk toward the prior)."""
    weighted = effective_ratings(env, cfg)
    prior = cfg["rating_prior"]
    axis_scores: dict[str, float] = {}
    for axis in _AXES:
        num = prior["mean"] * prior["strength"]
        den = float(prior["strength"])
        for r, w in weighted:
            v = r.axis(axis)
            if v is not None:
                num += w * v
                den += w
        shrunk = num / den  # in [1, 5]
        axis_scores[axis] = (shrunk - 1.0) / 4.0  # -> [0, 1]
    return sum(cfg["rating_axes"][a] * axis_scores[a] for a in _AXES)


# --- derived signals ---


def compute_signals(env: Environment, cfg: dict) -> dict[str, float]:
    if env.signals is not None:
        return {k: max(0.0, min(1.0, float(v))) for k, v in env.signals.items()}
    caps = cfg["signal_caps"]
    spec, graph, play = env.spec, env.graph, env.play

    verticality = 0.0
    move_variety = 0.0
    reachable_volume = 0.0
    if spec is not None:
        verticality = min(1.0, max(0.0, spec["summit"]["height_A"]) / caps["verticality_ref_A"])
        if graph is not None:
            verb_of = {e["id"]: e["verb"] for e in graph["edges"]}
            verbs = {
                verb_of[eid]
                for route in spec["routes"]
                for beat in route["beats"]
                for eid in beat["edge_ids"]
                if eid in verb_of
            }
            move_variety = min(1.0, len(verbs) / caps["move_variety_vocab"])
            reachable_volume = _reachable_volume(spec, graph)

    completion_rate = play.summits / play.plays if play.plays else 0.0
    replay_rate = (play.plays - play.players) / play.plays if play.plays else 0.0
    return {
        "verticality": _clamp(verticality),
        "move_variety": _clamp(move_variety),
        "reachable_volume": _clamp(reachable_volume),
        "completion_rate": _clamp(completion_rate),
        "replay_rate": _clamp(replay_rate),
    }


def _reachable_volume(spec: dict, graph: dict) -> float:
    """Proxy for the reachable-volume signal: the bbox of the traversal nodes over the
    environment bbox. (The full signals block is a v1.1 addition; this is the stand-in.)"""
    pts = [n["position"] for n in graph["nodes"]]
    if not pts:
        return 0.0
    span = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    node_vol = max(span[0], 0.1) * max(span[1], 0.1) * max(span[2], 0.1)
    b = spec.get("bounds")
    if not b:
        return 0.0
    env_span = [b["max"][i] - b["min"][i] for i in range(3)]
    env_vol = max(env_span[0], 0.1) * max(env_span[1], 0.1) * max(env_span[2], 0.1)
    return node_vol / env_vol if env_vol > 0 else 0.0


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def signal_component(env: Environment, cfg: dict) -> float:
    signals = compute_signals(env, cfg)
    return sum(cfg["signals"].get(k, 0.0) * signals.get(k, 0.0) for k in cfg["signals"])


# --- blend + feeds ---


def base_score(env: Environment, cfg: dict) -> float:
    comp = cfg["composition"]
    blended = comp["ratings"] * rating_component(env, cfg) + comp["signals"] * signal_component(
        env, cfg
    )
    return blended * cfg["score_scale"]


def _decay(age_days: float, half_life_days: float) -> float:
    return math.exp(-math.log(2) * max(age_days, 0.0) / half_life_days)


def top_week_score(env: Environment, cfg: dict, now: datetime) -> float:
    age_days = (now - env.published_at).total_seconds() / 86400.0
    return base_score(env, cfg) * _decay(age_days, cfg["top_week"]["half_life_days"])


def feed_top_week(envs: list[Environment], cfg: dict, now: datetime) -> list[Environment]:
    return sorted(envs, key=lambda e: (-top_week_score(e, cfg, now), e.environment_id))


def feed_new(envs: list[Environment]) -> list[Environment]:
    return sorted(envs, key=lambda e: (-e.published_at.timestamp(), e.environment_id))


def feed_near_scale(
    envs: list[Environment], mode: str, cfg: dict, now: datetime
) -> list[Environment]:
    scoped = [e for e in envs if e.capture_mode == mode]
    return feed_top_week(scoped, cfg, now)
