# `data/avatar/roster/` — v1 preset roster (data)

The **canonical v1 character roster as data** — the Brain-B / data half of **M1-AVAT-01** (AUTH #044
custom avatars v1; AUTH #024 roster art + inclusive-casting spec). The Unity selection UI
(`gj-gameplay`, M1-AVAT-01) consumes this; the runtime, rig, and final art are theirs.

## What's here
- **`presets/roster-ava-01..08.json`** — the 8 launch presets, each a schema-valid
  [`avatar_params`](../../schemas/avatar/avatar_params.schema.json) on the shared rig
  (`gj-humanoid-1A`). Because preset and custom avatars share this one representation, every preset is
  **rig-conformant by construction** — the movement stack (motion matching, #043 fluidity, IK, tool
  sockets) works on it unchanged, with no per-avatar retarget.
- **`roster.json`** — the ordered manifest: each entry points at a preset file and carries
  **roster-level presentation/casting metadata** (`label`, `hero_color`, `gender_presentation`,
  `apparent_age`). This metadata is **not** part of `avatar_params`.
- **`tests/test_roster.py`** — validates every preset against the schema + the forbidden-key privacy
  guard, checks manifest↔file consistency, and asserts the casting matrix and hero-color guarantees.

## Casting matrix (AUTH #024)
The 8 launch presets (floor 6) spread across **body type** (height 0.40–0.76, build 0.34–0.72),
**apparent gender presentation** (masculine / feminine / androgynous), **skin tone** (8 distinct
across the 0–31 ramp), and **apparent age** (young-adult / adult / mature), with 8 distinct hair
styles. The test enforces these spreads so the roster can't silently drift toward sameness.

## Hero colors — readability basis
`hero_color` is the per-preset accent used for **silhouette readability at ~15 cm** and colorblind
distinctness. The values are the **Okabe–Ito** CVD-safe qualitative palette (7 chromatic, distinguishable
under deuteran/protan/tritan vision) plus a neutral grey for the 8th. They are a **readability basis**,
not final brand colors — `gj-design` may remap them to `design/tokens/` once those land.

## Not here (gj-gameplay / gj-design)
The base rig and `avatar_params` → rig application, the in-app selection UI, the final meshes/textures,
and the `StreamingAssets`/`Resources` copy the app loads at runtime. Player-facing copy calls these
**"your character"** (DESIGN_SYSTEM §9, AUTH #044 addendum); "avatar" is reserved for the opt-in
custom-create + consent flow.
