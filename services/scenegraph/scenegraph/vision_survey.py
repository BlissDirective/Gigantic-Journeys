"""Vision-pass survey contract + reference (M1-SCEN-02 material/semantic, M3-GAME-01 objects).

The self-hosted vision pass (SPEC §3.3 — it runs on our own infrastructure and never sends a
user's scan off-site) turns the reconstruction's own renders into a *literal scene survey*: a
flat, observational record of the room (materials, lighting, ambience) and its separable objects.
Two consumers read the survey, both keyed to the frozen ``data/schemas/environment`` enums:

* **M1-SCEN-02** — :class:`SurveyVisionLabeler` implements the ``classify.VisionLabeler`` port, so
  a survey adds the Bible §9 ``material`` and a coarse ``semantic`` label (and an optional finer
  class override) to each planar patch of the collision mesh, replacing ``GeometricStub``.
* **M3-GAME-01** — :func:`segmented_objects` returns the *dynamic* objects (the ones a player
  could move) with a normalised material, so Tier-1 reactivity keys off the same material labels.

The *prompt design* — a literal survey in observational language, one material + evidence per
object, the "could a human lift or push it?" separability test, and never a compound asset — is
adapted from the MIT-licensed image-blaster project (``neilsonnn/image-blaster``,
``.claude/skills/image-blast-uncover``). The model is ours; this module normalises the model's
free-text output onto the frozen scene-graph enums and checks it. Standard library only.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from .classify import VisionLabel
from .segment import Patch

# Bible §9 feedback-matrix materials — the frozen scene_graph.material enum.
MATERIALS = (
    "wood",
    "tile-stone",
    "carpet-rug",
    "fabric-cushion",
    "lego-plastic",
    "paper-cardboard",
    "metal",
    "glass",
    "plant",
    "curtain",
    "unknown",
)

# Bible §4 surface classes — the frozen scene_graph.class enum (for a class override).
SURFACE_CLASSES = (
    "walkable-hard",
    "walkable-soft",
    "walkable-narrow",
    "ledge",
    "rung",
    "stud",
    "textured-vertical",
    "pole",
    "overhang",
    "slope",
    "wall-smooth",
    "soft-hanging",
    "void",
    "hazard-none",
)

# Free-text material -> enum. First group whose keyword appears (as a word or substring) wins, so
# the more specific groups come first. A miss falls back to "unknown" (never a wrong guess).
_MATERIAL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("glass", ("glass", "mirror", "window", "windowpane", "acrylic-pane")),
    ("metal", ("metal", "steel", "aluminium", "aluminum", "iron", "chrome", "brass")),
    ("curtain", ("curtain", "drape", "drapery", "blind")),
    ("carpet-rug", ("carpet", "rug")),
    (
        "fabric-cushion",
        (
            "fabric",
            "cushion",
            "upholster",
            "pillow",
            "sofa",
            "couch",
            "cloth",
            "textile",
            "bedding",
            "duvet",
            "blanket",
        ),
    ),
    ("paper-cardboard", ("paper", "cardboard", "carton", "book", "box", "magazine")),
    ("lego-plastic", ("lego", "plastic", "abs", "acrylic", "vinyl", "resin")),
    ("plant", ("plant", "foliage", "leaf", "leaves", "fern", "flower", "shrub", "moss")),
    (
        "tile-stone",
        (
            "tile",
            "stone",
            "ceramic",
            "marble",
            "granite",
            "concrete",
            "porcelain",
            "slate",
            "brick",
        ),
    ),
    ("wood", ("wood", "timber", "oak", "pine", "plank", "bamboo", "mdf", "plywood")),
)

# Coarse semantics that are built-in scene surfaces, never movable objects (image-blaster rule:
# "do not extract scene-surface elements or built-in parts of the environment").
ARCHITECTURAL_SEMANTICS = frozenset(
    {
        "floor",
        "flooring",
        "wall",
        "ceiling",
        "window",
        "door",
        "doorway",
        "stairs",
        "staircase",
        "column",
        "pillar",
        "beam",
        "railing",
        "fixture",
        "built-in",
        "rug",
        "carpet",
        "countertop",
        "worktop",
    }
)

_DYNAMIC = "dynamic"
_STATIC = "static"
_REJECT = "reject"


def normalize_material(text: str | None) -> str:
    """Map a vision model's free-text material to the scene_graph enum; "unknown" on a miss.

    Keywords match whole word tokens (equal, or a prefix so "upholster" catches "upholstered")
    rather than raw substrings, so e.g. "corrugated" does not match "rug"."""
    if not text:
        return "unknown"
    t = text.strip().lower()
    if t in MATERIALS:
        return t
    tokens = [tok for tok in re.split(r"[^a-z]+", t) if tok]
    for material, keywords in _MATERIAL_KEYWORDS:
        if any(tok == kw or tok.startswith(kw) for tok in tokens for kw in keywords):
            return material
    return "unknown"


def normalize_semantic(text: str | None) -> str | None:
    """Coerce a coarse label to the scene_graph ``semantic`` pattern ``^[a-z][a-z-]{1,31}$``.

    Lowercase, turn separators into hyphens, drop anything else, collapse and trim hyphens, and
    truncate to 32 characters. Returns ``None`` when nothing usable remains (never free text)."""
    if not text:
        return None
    out: list[str] = []
    for ch in text.strip().lower():
        if "a" <= ch <= "z":
            out.append(ch)
        elif ch in " _-/":
            out.append("-")
    collapsed = "-".join(part for part in "".join(out).split("-") if part)
    collapsed = collapsed[:32]
    if len(collapsed) < 2 or not ("a" <= collapsed[0] <= "z"):
        return None
    return collapsed


@dataclass(frozen=True)
class SurveySurface:
    """A static scene surface the model located and labelled (feeds M1-SCEN-02 patch labels)."""

    id: str
    material: str
    centroid: tuple[float, float, float]
    semantic: str | None = None
    class_override: str | None = None
    confidence: float | None = None


@dataclass(frozen=True)
class SurveyObject:
    """A candidate object. Separability decides whether it is a dynamic, movable object."""

    id: str
    name: str
    description: str = ""
    materials: tuple[str, ...] = ()
    semantic: str | None = None
    liftable: bool = False
    pushable: bool = False
    architectural: bool = False
    compound: bool = False
    count_estimate: int = 1
    evidence: tuple[str, ...] = ()

    @property
    def primary_material(self) -> str:
        return normalize_material(self.materials[0]) if self.materials else "unknown"


@dataclass(frozen=True)
class SceneSurvey:
    """The literal scene survey the self-hosted vision pass emits for one room."""

    scene_name: str = ""
    short_caption: str = ""
    literal_description: str = ""
    environment: str = ""
    visual_style: str = ""
    lighting: str = ""
    atmosphere: str = ""
    # Ambient qualities of the room; the audio-source recipe (services/audio/sources.py) uses this
    # as the world-ambience prompt so the room's bed matches what the vision pass saw.
    ambient_sound: str = ""
    surfaces: tuple[SurveySurface, ...] = ()
    objects: tuple[SurveyObject, ...] = ()
    schema_version: int = 1


def classify_separability(obj: SurveyObject) -> str:
    """The liftable/pushable heuristic: ``dynamic`` (a movable object -> M3-GAME-01), ``static``
    (a built-in surface, not a movable object), or ``reject`` (a compound/grouped candidate that
    is never a single asset). Adapted from image-blaster's object-extraction rules."""
    if obj.compound:
        return _REJECT
    if obj.architectural or (obj.semantic and obj.semantic in ARCHITECTURAL_SEMANTICS):
        return _STATIC
    if obj.liftable or obj.pushable:
        return _DYNAMIC
    return _STATIC


def segmented_objects(survey: SceneSurvey) -> list[SurveyObject]:
    """The dynamic (player-movable) objects, in survey order — the M3-GAME-01 segmentation set."""
    return [o for o in survey.objects if classify_separability(o) == _DYNAMIC]


def validate_survey(survey: SceneSurvey) -> list[str]:
    """Return a sorted list of problems ([] if the survey is well-formed against the enums)."""
    problems: list[str] = []
    seen_surface_ids: set[str] = set()
    for s in survey.surfaces:
        where = f"surface {s.id}"
        if s.id in seen_surface_ids:
            problems.append(f"{where}: duplicate id")
        seen_surface_ids.add(s.id)
        if normalize_material(s.material) not in MATERIALS:  # pragma: no cover - total map
            problems.append(f"{where}: material {s.material!r} does not map to the enum")
        if s.class_override is not None and s.class_override not in SURFACE_CLASSES:
            problems.append(f"{where}: class_override {s.class_override!r} not a Bible §4 class")
        if s.semantic is not None and normalize_semantic(s.semantic) is None:
            problems.append(f"{where}: semantic {s.semantic!r} normalises to nothing")
        if s.confidence is not None and not 0.0 <= s.confidence <= 1.0:
            problems.append(f"{where}: confidence {s.confidence} out of [0, 1]")

    seen_object_ids: set[str] = set()
    for o in survey.objects:
        where = f"object {o.id}"
        if o.id in seen_object_ids:
            problems.append(f"{where}: duplicate id")
        seen_object_ids.add(o.id)
        sep = classify_separability(o)
        if o.architectural and (o.liftable or o.pushable):
            problems.append(f"{where}: architectural object also marked liftable/pushable")
        if sep == _DYNAMIC and o.semantic and o.semantic in ARCHITECTURAL_SEMANTICS:
            problems.append(f"{where}: dynamic object has an architectural semantic")
        if o.count_estimate < 1:
            problems.append(f"{where}: count_estimate must be >= 1")
    return sorted(problems)


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b, strict=True)))


class SurveyVisionLabeler:
    """A ``classify.VisionLabeler`` backed by a scene survey.

    Matches each collision-mesh patch to the nearest survey surface by centroid (within
    ``match_radius_A``) and returns its material / semantic / optional class override. A patch with
    no nearby survey surface falls back to the default ``VisionLabel`` (material ``unknown``), so
    the geometric graph stays valid where the vision pass said nothing.
    """

    def __init__(self, survey: SceneSurvey, match_radius_A: float = 0.5) -> None:
        self._survey = survey
        self._radius = match_radius_A

    def label(self, patch: Patch, geom_class: str, confidence: float) -> VisionLabel:
        best: SurveySurface | None = None
        best_d = self._radius
        for s in self._survey.surfaces:
            d = _distance(patch.centroid, s.centroid)
            if d <= best_d:
                best, best_d = s, d
        if best is None:
            return VisionLabel()
        override = best.class_override if best.class_override in SURFACE_CLASSES else None
        return VisionLabel(
            material=normalize_material(best.material),
            semantic=normalize_semantic(best.semantic),
            class_override=override,
            confidence=best.confidence if best.confidence is not None else confidence,
        )


def _as_tuple3(v: object) -> tuple[float, float, float]:
    if not isinstance(v, (list, tuple)) or len(v) != 3:
        raise ValueError(f"expected a 3-vector, got {v!r}")
    return (float(v[0]), float(v[1]), float(v[2]))


def parse_survey(data: dict) -> SceneSurvey:
    """Build a :class:`SceneSurvey` from the model's flat JSON record (image-blaster style)."""
    surfaces = tuple(
        SurveySurface(
            id=str(s["id"]),
            material=str(s.get("material", "unknown")),
            centroid=_as_tuple3(s["centroid"]),
            semantic=s.get("semantic"),
            class_override=s.get("class_override"),
            confidence=s.get("confidence"),
        )
        for s in data.get("surfaces", [])
    )
    objects = tuple(
        SurveyObject(
            id=str(o["id"]),
            name=str(o.get("name", o["id"])),
            description=str(o.get("description", "")),
            materials=tuple(str(m) for m in o.get("materials", [])),
            semantic=o.get("semantic"),
            liftable=bool(o.get("liftable", False)),
            pushable=bool(o.get("pushable", False)),
            architectural=bool(o.get("architectural", False)),
            compound=bool(o.get("compound", False)),
            count_estimate=int(o.get("count_estimate", 1)),
            evidence=tuple(str(e) for e in o.get("evidence", [])),
        )
        for o in data.get("objects", [])
    )
    return SceneSurvey(
        scene_name=str(data.get("scene_name", "")),
        short_caption=str(data.get("short_caption", "")),
        literal_description=str(data.get("literal_description", "")),
        environment=str(data.get("environment", "")),
        visual_style=str(data.get("visual_style", "")),
        lighting=str(data.get("lighting", "")),
        atmosphere=str(data.get("atmosphere", "")),
        ambient_sound=str(data.get("ambient_sound", "")),
        surfaces=surfaces,
        objects=objects,
        schema_version=int(data.get("schema_version", 1)),
    )


# re-exported for callers that build a labeler without importing ``classify`` directly
__all__ = [
    "MATERIALS",
    "SURFACE_CLASSES",
    "ARCHITECTURAL_SEMANTICS",
    "SurveySurface",
    "SurveyObject",
    "SceneSurvey",
    "SurveyVisionLabeler",
    "normalize_material",
    "normalize_semantic",
    "classify_separability",
    "segmented_objects",
    "validate_survey",
    "parse_survey",
]
