# Vision pass v1 — the self-hosted scene survey (M1-SCEN-02 + M3-GAME-01)

**Status:** reference contract built (`services/scenegraph/scenegraph/vision_survey.py` + tests).
The real self-hosted vision *model* is Operator/GPU work that plugs into the existing
`classify.VisionLabeler` port. **No new AUTH and no protected-path change** — this is a
`services/`-level reference contract that produces data conforming to the already-frozen
`data/schemas/environment/scene_graph.json` (AUTH #037); it does **not** add or change a frozen
schema. Freezing a survey schema into `data/schemas/` later would need its own AUTH.

**Scope:** `claude-builder` (Brain-B contract + reference + tests). The self-hosted model, its
renders, and the on-device/GPU wiring are gj-gameplay / gj-operator.

## Why

`scene_graph.json`'s `material` field is annotated "(vision pass)" and `semantic` is "a coarse
object label from the vision pass". `classify.py` already stubs this: `GeometricStub` labels every
patch `material: "unknown"` and leaves a TODO-shaped `VisionLabeler` **port** for "a self-hosted
vision model on the reconstruction's own renders (never off-site)". This proposal fills that port
with a concrete, testable contract, and in the same move supplies M3-GAME-01 the segmented
*dynamic object* list that Tier-1 reactivity keys off.

The prompt **design** — a literal scene survey, one material + evidence per object, the "could a
human lift or push it?" separability test, and never a compound asset — is adapted from the
MIT-licensed **image-blaster** project (`neilsonnn/image-blaster`,
`.claude/skills/image-blast-uncover/IMAGE-BLAST.md`). The model is **ours** (SPEC §3.3): it runs on
our own infrastructure on the reconstruction's renders, trained only on the consented corpus
(AUTH #031), and a user's scan never leaves our infra. image-blaster is credited as prompt-design
prior art only; no code is copied.

## Pipeline place

```
reconstruction (splat + collision mesh, own infra)
      │  renders of the room from known poses
      ▼
self-hosted vision model  ──►  scene survey (JSON)   ◄── this contract
      │                                   │
      │ SurveyVisionLabeler               │ segmented_objects()
      ▼ (classify.VisionLabeler port)     ▼
M1-SCEN-02: per-patch material +      M3-GAME-01: dynamic objects + material
  semantic (+ optional class)           → Tier-1 reactivity (shared material labels)
      ▼
scene_graph.json  (frozen schema, AUTH #037)
```

The geometric core (`segment` → `classify` → `scene`) stays the deterministic, GPU-free spine;
the vision survey only *adds* material/semantic labels and the object set. A room with no survey
still produces a valid coarse graph (material `unknown`), so the vision pass is never a hard
dependency of traversal.

## The literal scene survey (prompt design)

The model is prompted to describe one render at a time as a **technical scene survey**, then the
per-render records are merged into one room survey. Rules carried over from image-blaster:

- **Observational language only.** Subject, arrangement, material, colour, shape, lighting,
  camera/view, environmental effects. No narrative or editorial framing ("feels like", "mysterious").
- **One material + evidence per object.** Deduplicate repeats into one candidate with a
  `count_estimate`; record which render(s) each label came from (`evidence`).
- **Separable single items only** (see the heuristic below); never a compound asset
  ("desk with items", "shelf contents").
- **Surfaces are not objects.** Floors, walls, ceilings, rugs, built-ins and fixtures are scene
  *surfaces* (they label patches), never movable objects.

### Survey JSON shape

Flat, like image-blaster's `image.json`, but every label is normalised onto GJ's frozen enums.

```json
{
  "schema_version": 1,
  "scene_name": "Toy Desk",
  "short_caption": "A small desk with a mug and a book under a window.",
  "literal_description": "…observational survey…",
  "environment": "…", "visual_style": "…", "lighting": "…", "atmosphere": "…",
  "ambient_sound": "quiet room tone with a faint clock tick",
  "surfaces": [
    { "id": "s-desk", "material": "oak", "centroid": [0,1,0],
      "semantic": "desk", "class_override": "walkable-hard", "confidence": 0.9 }
  ],
  "objects": [
    { "id": "mug", "name": "ceramic mug", "materials": ["glazed ceramic"],
      "semantic": "mug", "liftable": true, "pushable": false,
      "architectural": false, "compound": false, "count_estimate": 1,
      "evidence": ["view-02"] }
  ]
}
```

- `surfaces[]` feed M1-SCEN-02 patch labels (matched by centroid). `class_override` may refine the
  geometry-only class to a material-dependent one (e.g. `walkable-hard` → `walkable-soft`, or a
  `textured-vertical`/`ledge`/`stud` the geometry alone can't see).
- `objects[]` feed M3-GAME-01 (the dynamic ones) and are the provenance record for the rest.
- `ambient_sound` is the room's audible ambience; **the audio-source recipe
  (`services/audio/sources.py`) uses it as the world-ambience generation prompt**, so the room's
  sound bed matches what the vision pass saw.

## The liftable / pushable segmentation heuristic

`classify_separability(obj)` returns one of:

| result | rule | consumer |
|---|---|---|
| `dynamic` | `liftable` or `pushable` — a player could move it | **M3-GAME-01** segmentation + reactivity |
| `static` | architectural / a built-in surface, or present-but-immovable | scene surface (labels patches) |
| `reject` | `compound` (a set / pile / group — never one asset) | dropped, flagged in review |

`ARCHITECTURAL_SEMANTICS` (floor, wall, ceiling, window, door, stairs, column, railing, fixture,
rug, countertop, …) is the "never a dynamic object" guard. The decision is conservative: an object
is only `dynamic` when the model positively marks it liftable/pushable, so the segmentation set
stays tight.

## Normalisation onto the frozen enums

The model emits free text; `vision_survey` maps it onto the schema, never inventing a value:

- `normalize_material(text)` → one of the 11 `scene_graph.material` values (wood, tile-stone,
  carpet-rug, fabric-cushion, lego-plastic, paper-cardboard, metal, glass, plant, curtain) or
  **`unknown`** on a miss. Matching is on whole word tokens (so "corrugated" does not match "rug").
- `normalize_semantic(text)` → the `^[a-z][a-z-]{1,31}$` pattern, or `None`. Never free text.
- `class_override` must be a Bible §4 class or it is dropped.

`validate_survey(survey)` returns the problems (bad class override, out-of-range confidence,
architectural-and-liftable contradiction, duplicate ids, `count_estimate < 1`), so a model
regression is caught before the labels reach `scene_graph.json`.

## Wiring

- **M1-SCEN-02:** `SurveyVisionLabeler(survey)` implements `classify.VisionLabeler`; pass it to the
  scene builder instead of `GeometricStub` and each patch gets its survey material/semantic
  (matched to the nearest survey surface within `match_radius_A`, default to `unknown` otherwise).
- **M3-GAME-01:** `segmented_objects(survey)` is the dynamic-object set; each carries a normalised
  `primary_material`, so reactivity (`data/reactivity/reactivity.json`) and the audio bank share one
  material vocabulary — "one feedback matrix, many reactions".

## Not in scope / follow-ups

- The self-hosted vision **model** (choice, training on the corpus, render harness, on-device vs
  GPU) — gj-operator, under the reconstruction budget. This contract is what it must emit.
- Patch↔survey matching is centroid-nearest here; a production pass can project labelled render
  regions directly to patch ids. The port shape does not change.
- If a frozen survey schema under `data/schemas/` is ever wanted (for a C# mirror), that freeze is
  its own AUTH, like M1-DATA-01 (#037).
