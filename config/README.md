# `config/`

## `movement.json`

The single source of truth for movement tuning constants, shared by the Unity controller and the traversal validator (`design/MOVEMENT_BIBLE.md` §10). The file here is the §10 JSON block, byte for byte, extracted by the Coordinator on 2026-09-14.

Rules:

- **Changing any value is a design change.** Bible §10 is one of the three sections whose edits require an `AUTH REQUEST` (design-change). The Bible and this file change together in one PR that cites `APPROVED #n`; CI (`governance.yml`, job `movement-sync`) fails if they diverge.
- The Unity copy at `unity/Assets/StreamingAssets/movement.json` is copied, never hand-edited; regenerate it with `python .github/scripts/copy_movement_to_unity.py`. CI (`governance.yml`, job `movement-sync`) fails if it is not byte-identical.
- Loaders (C# in `unity/`, Python in `services/traversal/`) are created by ticket `M0-MOVE-01`. The **Python loader** (`services/traversal/movement.py`, with the `with_margin` 85 % helper) is landed. The **C# loader** rides the first-Editor-open step (CSharpier lint). The **JSON Schema** `config/movement.schema.json` is a protected path (`auth_gate.py`) and lands under its own `APPROVED #n`.
- Values are initial; M1 telemetry tunes them, still through AUTH.

Owner of the file: `gj-gameplay`. Consumer with veto on changes: `gj-scenegraph` (validator).
