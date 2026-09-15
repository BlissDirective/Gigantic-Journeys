# ADR-0004: Movement architecture: five assemblies, motion matching spike, motion warping

Date: 2026-09-15 · Status: Accepted (recorded from Movement Bible v1.0 §2, §13 and AUTH #001) · Authorization: APPROVED #000 (record), #001 (spend) · Owner Bot: gj-gameplay

## Context
Traversal is the product. The avatar's movement must feel like a real body at 15 cm while fitting a 4 ms animation budget and a 60 MB motion database on a 2023 mid-tier Android.

## Decision
Five layers as separate Unity assemblies (Intent, Traversal query, Animation selection, Motion warping, Procedural) plus a shared assembly with `IVerbProvider` so V2 tools add verbs without touching the core. Locomotion via the open MIT motion matcher (jlpm22) with inertialized blending, decided by the M1 spike (`M1-MOVE-01`): pass at ≥ 30 fps p99, ≤ 4 ms animation, ≤ 60 MB, else blend trees with inertialization. Contact verbs use Kinemation Motion Warping: Climb & Interact ($19.99, AUTH #001). All constants live in `config/movement.json`, shared with the traversal validator. Clips come from the free Mixamo whitelist (Bible §11), Owner Rokoko Vision captures, and the Move.ai trial.

## Alternatives considered
- MxM commercial license, Ultimate Traversal Anims, traceur capture: deferred to V2 by AUTH #001.
- Root-motion scaling plus IK instead of motion warping: kept as the fallback in Bible §2.

## Consequences
The Bible's Sections 3, 5, and 10 are change-controlled by AUTH; `config/movement.json` is checked against §10 in CI. The motion-db report (`qa/motion-db-report.md`) is a deliverable of the spike.

## Follow-ups
M0-MOVE-01, M0-UNITY-03, M1-MOVE-01.
