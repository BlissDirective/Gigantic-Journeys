# gj-gameplay — Working Handbook

Remit: movement, traversal tools, and character controller feel on the reconstructed environment. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- Movement is Bible-locked; constants live in `config/movement.json` (loader `services/traversal/movement.py`, schema `config/movement.schema.json`). Verb set (AUTH #021): parkour + dive-roll, tic-tac, vault variants, wall-run, plus the traversal-tools layer (safety-pin grapple, matchstick pole-vault) via `IVerbProvider`.
- v1 avatar = curated pre-made roster (AUTH #020/#024) on one enforced rig (Unity Humanoid + foot/hand IK + contact markers + tool sockets). No biometric.
- Render target: Unity 6 URP, iOS/Metal, 30 fps; the splat render is M1-UNITY-01 (the #1 risk).

## Principles
- **Feel first.** Coyote time, input buffering, acceleration/deceleration curves, anticipation/landing — the small stuff is the game. Tune, don't theorize.
- **movement.json is the single source of truth.** All speeds/heights/reach come from it with the 0.85 safety margin (`with_margin`). Gameplay and the reachability validator must agree.
- **Contact-driven traversal.** Warped contact clips (Motion Warping asset, AUTH #001) + IK for hands/feet on real surfaces; inertialized blending for transitions.
- **Mobile perf is a budget.** URP, IL2CPP release, GPU/CPU frame budget; profile on device, not the editor.

## Techniques
- Motion matching vs blend-tree spike (M1-MOVE-01) before committing the locomotion core.
- `IVerbProvider` for verbs + tools so new verbs slot in without controller rewrites.
- Collision uses the derived Open3D mesh, not the splat; keep the character controller against clean geometry.
- Tier-0 material feedback (M1-GAME-03) + scale-aware audio (AUTH #022, M1-GAME-04).

## Pitfalls
- Tuning in the editor and shipping mush on device — always profile on a real iPhone.
- Letting splat rendering cost starve the movement frame budget — coordinate with M1-UNITY-01 (splat budget/LOD).
- Diverging from movement.json (hardcoded magic numbers) → validator/leaderboard mismatch.

## Checklist
Locomotion feel passes on device ✓ · verbs via IVerbProvider ✓ · constants from movement.json ✓ · IK/contact on real surfaces ✓ · 30 fps at splat budget ✓.

## Pointers
`design/MOVEMENT_BIBLE.md` · `config/movement.json` + `services/traversal/` · SPEC §3.5 · tickets M1-MOVE-01/02, M1-GAME-01..04, M1-UNITY-01.
