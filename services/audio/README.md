# `services/audio/` — audio data + scale-aware acoustics (Brain-B, M1-GAME-04 / AUTH #022)

The deterministic **data + reference model** half of the v1 audio system (SPEC §3.6, Movement Bible §9).
The Unity/C# audio engine (gj-gameplay) is the runtime that plays it; this tree is the authoritative
contract it mirrors — no audio is synthesized here.

## What's here
- **`acoustics.py` + `../../data/audio/acoustics.json`** — scale-aware acoustics:
  - `reverb_from_scene_graph(doc)` → a parametric room reverb (RT60 via **Sabine**, wet, HF damping)
    from the reconstructed room's **volume + surface materials** (frozen scene_graph), so a big tiled
    room rings and a small carpeted one is dead (AT-2).
  - `scale_pitch_semitones(multiplier, weight)` / `scale_gain_db(multiplier)` — pitch/level shift with
    the environment **scale multiplier**, so **Lego clicks stay tiny and floor booms stay big** (AT-3).
  - Absorption coefficients are mid-band (500 Hz–1 kHz) Sabine values per the 11 scene_graph materials.
- **`bank.py` + `../../data/audio/sound_bank.json`** — the **material × event sound bank**: every v1
  verb/tool/event → mix bus (movement/world/tools/ui/music), sound layers (transient/body/tail),
  round-robin count, impact scaling, scale weight, and whether it varies by surface material.
  `validate_bank()` enforces **coverage of every verb in the frozen traversal_graph enum** (AT-1) and
  well-formedness; locomotion carries ≥ 4 round-robin variants so a 2-minute run never machine-guns.
- **`tests/`** — Sabine correctness, big-live-vs-small-dead reverb, scale pitch/gain monotonicity +
  clamps, and full bank coverage/validity (15 tests).

## The C# engine mirrors this
`data/audio/acoustics.json` and `sound_bank.json` are the single source of truth, like
`config/movement.json` is for movement. The Unity audio engine reads the same files (or a copied
StreamingAssets mirror) and reproduces the Sabine reverb + scale math here. Keep them in lockstep; a
sync check (mirroring `check_movement_sync.py`) can be added when the engine lands.

## Not here (gj-gameplay / provenance)
The audio engine, AudioMixer buses + sidechain ducking, 3D spatialization, contact-frame wiring, and
the actual **CC0/royalty-free clip files** are gj-gameplay. Clip provenance is recorded in
`qa/audio-sources.md` (AT-4). The music identity is **restrained adaptive stings** (AUTH #022).
