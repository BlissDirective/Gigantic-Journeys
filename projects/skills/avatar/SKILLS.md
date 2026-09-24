# gj-avatar — Working Handbook

Remit: characters. **v1 = a curated roster of pre-made, rigged, semi-photoreal 1:12 characters (AUTH #020/#024) with NO biometric processing.** Custom likeness avatars are a **V2** track. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context (read carefully — the v1/V2 split is a hard line)
- **v1: no face/body capture, no avatar vendor, no biometric consent** (ADR-0006 / AUTH #020). SECURITY_CHECKLIST §5 is a **V2 gate** (except the 13+ age gate, which is v1).
- Roster = **8** characters (≥6 = M2 floor) on **one enforced GJ rig** (Unity Humanoid, normalized, foot/hand IK + contact markers, AUTH #021 carried-tool sockets, automated rig-conformance gate). Fidelity: grounded semi-photoreal for v1; V2 hero-photoreal roadmap on the same rig (AUTH #024).
- **Sourcing: dual-track, clean-IP, zero biometric** — open-base authoring primary (MakeHuman CC0 / Human Generator + Blender, $0 now); leaner CC4/Mixamo license path is a contingency needing its own spend AUTH. Scanned-real-people libraries and MetaHuman (Unreal-only) are rejected.

## Principles (v1)
- **One rig standard, enforced by a gate.** Every character passes rig-conformance + a verb+tool clip test (grapple/pole-vault/wall-run) before it ships (cosmetic SKUs too).
- **Clean IP only.** Track license + version for every base/asset (SECURITY_CHECKLIST §7.4). No identifiable-person photos anywhere in v1.
- **Mobile-first authoring.** LOD, texture atlasing, poly budget, baked materials for iPhone.

## Principles (V2 — when biometric returns)
- No face/body bytes leave device until a **consent record** exists (SECURITY_CHECKLIST §5.1); training use is a separate default-off opt-in; delete within 30 days incl. vendor-side; process on infra we control.
- Watch **uncanny valley at small scale** (1:12) — likeness preservation vs comfort; auto-rigging + retarget onto the GJ rig.

## Pitfalls
- Drifting biometric work into v1 — it is explicitly out (AUTH #020). If a task needs face data, stop: it's V2 and needs consent scaffolding.
- Shipping a character that fails the rig/verb clip test → broken traversal/tool animations.

## Checklist
- **v1:** rig-conformance ✓ · verb+tool clip test ✓ · license/version recorded ✓ · mobile budget ✓ · zero identifiable-person data ✓.

## Pointers
`design/proposals/character-roster-v1.md` · `research/vendors/character-roster-sourcing.md` · `ADRs/0006-*` · SPEC §3.2/§3.8 · SECURITY_CHECKLIST §5/§6 · tickets M2-AVAT-01.
