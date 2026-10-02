# M1-AVAT-01 (Unity, preset path): roster load, parameter application, character picker

2026-10-02, gj-operator. Preset path only. The on-device biometric pipeline (M1-AVAT-02) and consent copy are
**not** built (hard gate). Player-facing copy says "your character" (DESIGN_SYSTEM §9, AUTH #044 addendum).

## What was built (`unity/Assets/GiganticJourneys/Avatar/`, assembly `GJ.Avatar`)
- **Data shipping:** `data/avatar/roster/{roster.json, presets/*.json}` is copied byte-identically to
  `unity/Assets/StreamingAssets/avatar/roster/` by `.github/scripts/copy_roster_to_unity.py`. Drift fails pytest
  (`.github/scripts/tests/test_roster_unity_copy.py`) and an EditMode test.
- **`AvatarParams`** parses avatar_params v1.0.0 as strictly as the schema: every field required, no extra fields at any
  level (a biometric or landmark field is rejected, never ignored), ranges 0..1, palette indices 0..31,
  enums, slug patterns, `base_rig` = gj-humanoid-1A, and `preset_id` required for presets.
- **`CharacterRoster`** loads the manifest and the 8 presets: provenance must match the entry, ids must be unique, hero colours
  must parse, the count must meet the floor (6), and file paths must stay inside the roster directory. Casting labels are never shown.
- **`AvatarAppearance`** applies a parameter set to the shared rig, **visual only**. The movement body (collider,
  motor, sockets, IK targets) is never touched, so every character moves identically (AT-1). Art contract for
  gj-design's gj-humanoid-1A: a `Visual` child scaled within height ±6% / build ±12%; face blend shapes
  `face_shape, face_width, jaw, brow, nose, eyes`; renderers prefixed `skin`/`hair`/`outfit` take the skin
  palette, hair palette and hero colour through a MaterialPropertyBlock; variant children
  `hair_*`/`glasses_*`/`facial_hair_*`/`headwear_*` with exactly the selected one active.
- **`PlaceholderRig`** is a primitive stand-in that follows the same contract, until the rigged mesh lands.
- **`CharacterSelectView`** (UI Toolkit, built in code): "Choose your character", 8 cards (hero-colour swatch +
  number, so no casting labels and no names until gj-design names them), live preview on the rig, "Play as this character",
  and the choice is remembered (`PlayerPrefs gj.character.preset`). Selection is shown by a check mark plus a thick outline, not
  hue alone. Cards are 96×120 (≥ 48 px targets).

## Evidence (box: Unity 6000.0.84f1)
`M1-AVAT-01/roster-tests.xml`: **19/19 passed** (`CharacterRosterTests`). The shipped roster has 8 valid presets
on the shared rig, each with a distinct hero colour, and is byte-identical to the repo data. 11 schema-rejection cases
(range, integer, enum, rig, version, missing preset_id, unknown `landmarks`/`face_embedding`, slug, missing field)
agree with the frozen schema fixtures (`custom_avatar` valid; `avatar_biometric_field`, `avatar_out_of_range` rejected).
Applying all 8 presets never changes the rig root or the movement collider, and each slot has exactly one active
variant. The picker copy contains no "avatar", and the choice persists.

Screenshot: `qa/evidence/M1-AVAT-01/01-placeholder-rig-eight-presets.png` (all 8 presets on the placeholder rig).

## Open
- **Final art:** gj-design's rigged gj-humanoid-1A mesh with the blend shapes and variants above, plus final skin and hair
  palettes (the 32-step ramps in `AvatarAppearance` are provisional) and any player-facing character names.
- **AT-1 in full:** "moves identically across environments" with motion matching, #043, IK and tool sockets needs those
  systems on the real rig. The appearance layer is already proven not to touch the movement body.
- Wiring the picker into the app flow (first run / settings) comes with the shell screens.
