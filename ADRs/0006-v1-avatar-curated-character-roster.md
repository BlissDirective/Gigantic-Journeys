# ADR-0006: v1 avatar is a curated character roster (no biometric); custom avatars are V2

Date: 2026-09-18 · Status: Accepted · Authorization: APPROVED #020 · Supersedes: the avatar decision in ADR-0005 (and #019) · Owner: coordinator (governance), claude-builder (character system)

## Context
ADR-0005 (and AUTH #019) had v1 generate a recognizable avatar from the player's own face via Avatar SDK/MetaPerson on-prem. Even on the cleanest vendor terms, that path carries the project's largest risk surface: biometric law (BIPA/CUBI/MHMDA), a consent flow, an enterprise/on-prem contract + DPA, App Store scrutiny of face processing, and identity-fidelity quality risk. The Owner chose to remove all of that from v1 and focus the build on the product's actual differentiator — **video → playable environment, and world-class, fluid, reactive traversal** — shipping generated characters instead of the player's likeness.

## Decision
**v1 avatar = a curated roster of pre-made, rigged, semi-photorealistic 1:12 characters** (target ~6–12 at launch) that the player selects. Customization is **cosmetic only**, through the two existing IAP SKUs (outfit pack, "realism+" materials) plus free defaults — no slider face editor, no likeness capture.

- **No face or body capture and no biometric processing in v1.** The only user media is room/tabletop scans (not the player). This removes BIPA/CUBI/MHMDA scope, the biometric consent flow, and any avatar vendor from v1.
- All characters share the **GJ humanoid skeleton** and the shared animation/traversal set, so every character moves identically well; the roster is an authored art asset, not a per-user generation step.
- **Custom avatars from the player's own likeness are deferred to V2**, as a deliberate own-model R&D track (synthetic-first, local-GPU; `research/rnd/`), graduating into the product only when it clears identity-fidelity and compliance gates.

## Alternatives considered
- **Avatar SDK/MetaPerson on-prem (ADR-0005 / #019):** best vendor path, but still biometric, still an enterprise contract + DPA, still App Store face-processing scrutiny — all deferred, not needed for v1.
- **Self-host a face model now:** the good models are non-commercially licensed and it's an ML research program (`research/vendors/avatar-selfhost.md`); it belongs in V2, not v1.
- **Procedural unique characters:** adds a generation system that competes with the movement focus; roster + cosmetics is simpler and ships.

## Consequences
- **Massive de-risking of v1:** zero biometric data means SECURITY_CHECKLIST §5 (biometric consent) is a **V2 gate, not a v1 gate**; the BIPA consent copy becomes a V2 artifact; no avatar vendor, DPA, or on-prem contract; faster, lower-risk App Store and legal review.
- **Focus shifts to the hero features** — reconstruction (self-host, ADR-0005) and traversal quality. M2 reframes from "recognizable avatar" to "character roster + rig + retarget to the movement system."
- **The cosmetic IAP fits cleanly:** the outfit/realism SKUs reskin the chosen character (previewed on it in the diorama).
- **Cost:** authoring a small roster of rigged, semi-photoreal characters (licensed/commissioned/generated-once art) — an art+integration task, not ML.
- **Reversal:** V2 adds custom avatars on top of the same rig and animation set without changing the game loop.

## Follow-ups
- SPEC v1.3 (§1, §2, §3.2, §3.9, §4, §7, §8 M2, §9); SECURITY_CHECKLIST §5/§6/§12; DESIGN_SYSTEM decision 4 — updated under AUTH #020.
- New ticket **M2-CHAR-01** (character roster + rig + retarget + selection). Retire/redirect: M0-LEGAL-01 (BIPA consent) → V2, M0-LEGAL-04 (avatar vendor terms) → cancelled, M2-DUO-01 (rear-camera face capture) → V2.
- V2 own-avatar R&D charter (`research/rnd/`).
