"""Audio-source generation recipe (M1-GAME-04 / AUTH #022, AT-4) -- vendor-agnostic.

Turns ``data/audio/sound_bank.json`` into a concrete, provider-neutral generation plan: one spec
per bank event (carrying the scene_graph materials for the events that vary by material), each with
a text prompt, a clip count, loop/one-shot handling and the post-process the clip needs.
``build_manifest`` reproduces ``data/audio/source_manifest.json`` so the plan can't drift from the
bank, and it closes the ``qa/audio-sources.md`` gap by saying exactly what to generate (or find as
CC0 foley) for every event.

The prompt shapes -- short-decay object impacts, and a world-ambience loop left raw to keep its
seamless boundary -- are adapted from the MIT-licensed image-blaster project
(``.claude/skills/image-blast-sfx``). The generator itself is a port (:class:`AudioProvider`):
:class:`DryRunProvider` needs no account and no spend; a real provider (ElevenLabs via FAL is the
natural candidate) plugs in behind the same interface and is gated on a spend/account AUTH
(CLAUDE.md) -- this module makes no network call and holds no key. Standard library only.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

_REPO = Path(__file__).resolve().parents[2]
_BANK_PATH = _REPO / "data" / "audio" / "sound_bank.json"
_SCENE_GRAPH = _REPO / "data" / "schemas" / "environment" / "scene_graph.json"
_MANIFEST_PATH = _REPO / "data" / "audio" / "source_manifest.json"

# Sustained beds that loop; everything else is a one-shot (sustained contacts like slide/wall-run
# are round-robin one-shots the engine can loop, not pre-looped clips).
LOOP_EVENTS = frozenset({"ambience-bed", "music-ambient-bed", "music-shrink-theme"})

# ElevenLabs text-to-SFX (via FAL) would map a request as text=prompt,
# duration_seconds=duration_s (clamped to this range), loop=loop, with `count` calls for
# round-robin variants. Adding that provider needs an account + key + a spend AUTH.
ELEVENLABS_DURATION_RANGE = (0.5, 22.0)

_WEIGHT_SECONDS = {"light": 0.6, "medium": 1.0, "heavy": 1.5}
_BUS_LUFS = {"ui": -14.0, "music": -18.0}  # others default below
_DEFAULT_LUFS = -16.0

# Readable phrase per event for the prompt; a miss falls back to the de-prefixed event name.
_PHRASE = {
    "walk": "footstep, walking gait",
    "jog": "footstep, jogging gait",
    "run": "footstep, running gait",
    "land-soft": "soft landing",
    "land-hard": "hard landing",
    "land-roll": "rolling landing",
    "land-heavy": "heavy landing",
}
_EVENT_PREFIXES = ("grapple-", "polevault-", "react-", "ui-", "sting-", "music-", "land-")


def load_bank() -> dict:
    return json.loads(_BANK_PATH.read_text(encoding="utf-8"))


def scene_graph_materials() -> list[str]:
    """The concrete scene_graph materials (the frozen enum minus ``unknown``)."""
    schema = json.loads(_SCENE_GRAPH.read_text(encoding="utf-8"))
    enum = schema["$defs"]["surface"]["properties"]["material"]["enum"]
    return [m for m in enum if m != "unknown"]


@dataclass(frozen=True)
class PostProcess:
    """How a generated clip is cleaned. Loops are left raw to preserve their seamless boundary;
    one-shots are silence-trimmed and loudness-normalised (the image-blaster SFX recipe)."""

    leave_raw: bool
    trim_silence: bool
    normalize: bool
    target_lufs: float | None


@dataclass(frozen=True)
class GenerationRequest:
    """One concrete clip-family to generate (``count`` round-robin variants)."""

    id: str
    event: str
    material: str | None
    prompt: str
    kind: str
    loop: bool
    count: int
    duration_s: float
    bus: str
    weight: str
    post_process: PostProcess


@dataclass(frozen=True)
class GenerationSpec:
    """A bank event's generation plan; expands to one request per material (or one if fixed)."""

    event: str
    bus: str
    kind: str
    weight: str
    loop: bool
    count: int
    duration_s: float
    materials: tuple[str, ...] | None
    prompt_template: str
    post_process: PostProcess

    def expand(self) -> list[GenerationRequest]:
        if self.materials:
            return [
                GenerationRequest(
                    id=f"{self.event}__{m}",
                    event=self.event,
                    material=m,
                    prompt=self.prompt_template.replace("{material}", m),
                    kind=self.kind,
                    loop=self.loop,
                    count=self.count,
                    duration_s=self.duration_s,
                    bus=self.bus,
                    weight=self.weight,
                    post_process=self.post_process,
                )
                for m in self.materials
            ]
        return [
            GenerationRequest(
                id=self.event,
                event=self.event,
                material=None,
                prompt=self.prompt_template,
                kind=self.kind,
                loop=self.loop,
                count=self.count,
                duration_s=self.duration_s,
                bus=self.bus,
                weight=self.weight,
                post_process=self.post_process,
            )
        ]


def _kind(event: str, bus: str) -> str:
    if event in LOOP_EVENTS:
        return "world-ambience"
    if bus == "ui":
        return "ui-cue"
    if bus == "music":
        return "music-sting"
    if bus == "world":
        return "reaction"
    return "object-impact"  # movement + tools one-shots


def _duration(weight: str, layers: list[str], loop: bool) -> float:
    if loop:
        return 10.0
    d = _WEIGHT_SECONDS.get(weight, 1.0)
    if "tail" in layers:
        d += 0.5
    lo, hi = ELEVENLABS_DURATION_RANGE
    return round(min(max(d, lo), hi), 2)


def _post_process(loop: bool, bus: str) -> PostProcess:
    if loop:
        return PostProcess(leave_raw=True, trim_silence=False, normalize=False, target_lufs=None)
    return PostProcess(
        leave_raw=False,
        trim_silence=True,
        normalize=True,
        target_lufs=_BUS_LUFS.get(bus, _DEFAULT_LUFS),
    )


def _phrase(event: str) -> str:
    if event in _PHRASE:
        return _PHRASE[event]
    name = event
    for p in _EVENT_PREFIXES:
        if name.startswith(p):
            name = name[len(p) :]
            break
    return name.replace("-", " ")


def build_prompt(event: str, bus: str, weight: str, loop: bool, material: str | None = None) -> str:
    """Compose the text prompt. ``material`` may be ``"{material}"`` to leave a fill slot."""
    phrase = _phrase(event)
    surface = f" on {material}" if material else ""
    if loop:
        space = f"{material} " if material else ""
        return f"ambient loop, 1:12 miniature room tone, {space}space, no music or voices"
    if bus == "ui":
        return f"clean UI {phrase} cue, short, neutral, no music, no voices"
    if bus == "music":
        return f"short musical sting, {phrase}, orchestral-lite, no voices"
    if bus == "world":
        return f"character reaction foley, {phrase}{surface}, short-decay, miniature scale"
    return (
        f"impact one-shot, short-decay, 1:12 miniature scale, {weight} {phrase}{surface}, "
        f"no music, no voices"
    )


def build_manifest(
    bank: dict | None = None, materials: list[str] | None = None
) -> list[GenerationSpec]:
    """One :class:`GenerationSpec` per bank event, sorted by event name (deterministic)."""
    bank = bank if bank is not None else load_bank()
    materials = materials if materials is not None else scene_graph_materials()
    specs: list[GenerationSpec] = []
    for name in sorted(bank.get("events", {})):
        e = bank["events"][name]
        bus = e["bus"]
        weight = e["weight"]
        loop = name in LOOP_EVENTS
        vbm = bool(e.get("varies_by_material"))
        mats = tuple(materials) if vbm else None
        template = build_prompt(name, bus, weight, loop, "{material}" if vbm else None)
        specs.append(
            GenerationSpec(
                event=name,
                bus=bus,
                kind=_kind(name, bus),
                weight=weight,
                loop=loop,
                count=int(e["round_robin"]),
                duration_s=_duration(weight, e.get("layers", []), loop),
                materials=mats,
                prompt_template=template,
                post_process=_post_process(loop, bus),
            )
        )
    return specs


def validate_manifest(specs: list[GenerationSpec], bank: dict | None = None) -> list[str]:
    """Return a sorted list of problems ([] if the plan covers the bank and is well-formed)."""
    bank = bank if bank is not None else load_bank()
    problems: list[str] = []
    events = bank.get("events", {})
    by_event = {s.event: s for s in specs}

    missing = sorted(set(events) - set(by_event))
    if missing:
        problems.append(f"events with no generation spec: {missing}")
    extra = sorted(set(by_event) - set(events))
    if extra:
        problems.append(f"specs for unknown events: {extra}")

    for name, s in sorted(by_event.items()):
        e = events.get(name)
        if e is None:
            continue
        where = f"spec {name}"
        if s.count != e["round_robin"]:
            problems.append(f"{where}: count {s.count} != round_robin {e['round_robin']}")
        vbm = bool(e.get("varies_by_material"))
        if vbm and not s.materials:
            problems.append(f"{where}: varies_by_material but no materials")
        if not vbm and s.materials:
            problems.append(f"{where}: fixed event should not carry materials")
        if s.materials and "{material}" not in s.prompt_template:
            problems.append(f"{where}: material-varying prompt has no {{material}} slot")
        if s.loop and not s.post_process.leave_raw:
            problems.append(f"{where}: loop must leave the clip raw (seamless boundary)")
        if not s.loop and s.post_process.leave_raw:
            problems.append(f"{where}: one-shot should be trimmed/normalised, not raw")
    return sorted(problems)


def ffmpeg_filters(pp: PostProcess) -> list[str]:
    """The deterministic ffmpeg ``-af`` filter chain for a clip's post-process (the recipe).

    A loop is left raw (no filters). A one-shot trims leading/trailing near-silence from both ends
    and loudness-normalises to the target LUFS."""
    if pp.leave_raw:
        return []
    chain: list[str] = []
    if pp.trim_silence:
        trim = (
            "silenceremove=start_periods=1:start_silence=0.02:start_threshold=-50dB:detection=peak"
        )
        chain.append(f"{trim},areverse,{trim},areverse")
    if pp.normalize and pp.target_lufs is not None:
        chain.append(f"loudnorm=I={pp.target_lufs}:TP=-1.5:LRA=11")
    return chain


def _spec_to_dict(s: GenerationSpec) -> dict:
    return {
        "bus": s.bus,
        "kind": s.kind,
        "weight": s.weight,
        "loop": s.loop,
        "count": s.count,
        "duration_s": s.duration_s,
        "materials": list(s.materials) if s.materials else None,
        "prompt_template": s.prompt_template,
        "post_process": asdict(s.post_process),
    }


def manifest_dict(specs: list[GenerationSpec] | None = None) -> dict:
    specs = specs if specs is not None else build_manifest()
    return {
        "_note": (
            "Audio-source generation plan (M1-GAME-04 / AUTH #022). Generated by "
            "services/audio/sources.py:build_manifest from data/audio/sound_bank.json; do not hand "
            "edit. One entry per bank event; material-varying events expand over `materials` with "
            "the {material} slot filled. `count` = round-robin variants. Loops are left raw; "
            "one-shots are trimmed + loudness-normalised (see post_process / ffmpeg_filters). "
            "Clips may be CC0 foley or provider-generated; a generation provider (e.g. ElevenLabs "
            "via FAL) needs a spend/account AUTH. Provenance per clip: qa/audio-sources.md."
        ),
        "materials": scene_graph_materials(),
        "events": {s.event: _spec_to_dict(s) for s in specs},
    }


def write_manifest() -> dict:
    """Regenerate data/audio/source_manifest.json from the bank. Returns the written dict."""
    data = manifest_dict()
    _MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


class AudioProvider(Protocol):
    """Port for a text-to-SFX backend. A real one needs a spend/account AUTH; none ships here."""

    name: str

    def generate(self, request: GenerationRequest) -> list[bytes]: ...


@dataclass
class DryRunProvider:
    """A no-spend provider: records the requests it was asked to generate, returns no audio."""

    name: str = "dry-run"
    requested: list[str] = field(default_factory=list)

    def generate(self, request: GenerationRequest) -> list[bytes]:
        self.requested.append(request.id)
        return []


if __name__ == "__main__":  # pragma: no cover - manual regeneration
    write_manifest()
    print(f"wrote {_MANIFEST_PATH.relative_to(_REPO)}")
