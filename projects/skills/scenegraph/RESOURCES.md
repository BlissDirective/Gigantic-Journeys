# gj-scenegraph — Resources (curated foundation)

Curated, verified starter set for scene understanding, affordances, and route/reachability. Expand to the full annotated top-100 in a live pass. All entries real/canonical.

## Scene understanding & segmentation
- Gaussian Grouping — github.com/lkeab/gaussian-grouping (ECCV 2024) — segment + edit 3D gaussians.
- Segment Anything (SAM / SAM 2) — segment-anything.com — 2D masks to lift into 3D.
- ScanNet / Matterport3D — indoor scene datasets and benchmarks for labels/affordances.

## Scene-level physics on splats/NeRF
- VR-GS (arXiv 2401.16663) — interactive physics on Gaussian splats.
- DecoupledGaussian (2025) — object/scene decoupling for interaction.
- PhysGaussian (arXiv 2311.12198) — physics-integrated gaussians.

## Reachability, route search, affordances
- Amit Patel — Red Blob Games (redblobgames.com) — A*, pathfinding, grids/graphs (canonical).
- "Motion Matching" & navmesh literature (Unity AI Navigation docs) — traversal graphs.
- Affordance detection surveys (robotics/vision) — object → action mapping.

## Parkour / climbing reachability (design reference)
- Assassin's Creed / Zelda BotW–TotK / Mirror's Edge — traversal reachability talks (GDC Vault).

## Reference internal
- `config/movement.json`, `config/movement.schema.json`, `services/traversal/movement.py`; SPEC §3.4; `design/proposals/journey-route-generation-v1.md`.
