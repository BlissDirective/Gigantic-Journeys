# `services/reactivity/` — Tier-1 reactivity matrix (Brain-B, M3-GAME-01 / AUTH #022)

The deterministic **data + reference** half of Tier-1 environment reactivity (SPEC §3.6). The Unity
shader-displacement + particle system (gj-gameplay) is the runtime; this tree is the authoritative
matrix it consumes. **Shader displacement only — no physics** (Tier 2 is research, SPEC §5).

## What's here
- **`../../data/reactivity/reactivity.json`** — the **feedback matrix**:
  - **`material_response`** (per scene_graph material) — how a surface reacts: a **displacement**
    kind (none / dent / sway / flutter / swing), a **stiffness** (0..1), and a default **particle**.
    So fabric-cushion/carpet **dent**, curtain **sways**, plant/paper **flutter**, tile/metal/glass
    stay rigid (AT-1).
  - **`event_reaction`** (per gameplay event — every verb/tool/landing/reaction) — what it triggers:
    a **particle**, a **haptic** level, a **camera shake** level, and whether it **displaces** the
    surface. A wall-run **scuffs**, a rappel **sways** a curtain, the grapple pin-mount reacts the
    anchor (AT-2).
  - **`scale`** — reactions scale by `ref_multiplier / multiplier`, so a tinier world's dust/dents
    stay tiny. **`budget`** — the 30 fps M3-exit floor + a max-concurrent-reactions cap.
- **`reactivity.py`** — `validate_reactivity` enforces coverage of **every scene_graph material** and
  **every traversal_graph verb**, plus enum/stiffness/budget well-formedness.
- **`tests/`** — material + verb coverage, soft-vs-rigid displacement, the AT-2 verb/tool reactions,
  the no-physics budget, and validator negatives.

## One source of truth, many reactions
The matrix keys off the **same** scene_graph materials + traversal_graph verbs as the audio bank
(`services/audio`), per the proposal's §5 ("one feedback matrix, many reactions"). The particle /
haptic / camera-shake channels also feed **Tier 0** (M1-GAME-03); the displacement channel is Tier 1
(this ticket). The C# runtime mirrors `data/reactivity/reactivity.json`; a `check_reactivity_sync.py`
(mirroring the audio `check_audio_sync.py`) can enforce byte-identity once the engine lands.

## Not here (gj-gameplay)
The object segmentation of the splat, the displacement shaders, the particle systems, haptics, and
camera shake — and the 30 fps device pass (AT-3) — are the Unity runtime.
