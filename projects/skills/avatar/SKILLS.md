# gj-avatar — Working Handbook

Remit: the player's character. **In v1 that means a curated roster of pre-made, rigged, grounded semi-photoreal 1:12 characters, with no face or body capture and no biometric processing** (AUTH #020, ADR-0006; roster spec AUTH #024; SPEC §3.2). Custom likeness avatars (selfie capture, head/body merge, consent, likeness confirmation) are the **V2** track (`research/rnd/README.md`). This handbook covers both, and every section says which one applies. Re-read it at every session start and append to the Session log when you learn something (`agents/grok/README.md` §3, §9).

Executing agent: the **Builder** owns M2-AVAT-01 (Unity rig gate, retarget, selection, cosmetics). The **Operator** handles Blender/Editor GUI work and long batch exports. Owned paths (kit role block): `services/avatar`, `unity/Assets/Avatar`. **Heads-up:** `services/avatar/README.md` still describes the pre-AUTH #020 pipeline (image-to-3D head, consent gate). Treat it as stale and flag it to the Coordinator; this handbook doesn't edit it (out of scope).

Research list: `projects/skills/avatar/RESOURCES.md` (104 link-checked entries).

## 1. Rules this hat must follow

| Rule | Source |
|---|---|
| Session start, branches, PR template, evidence | `agents/grok/README.md` §3–§5 |
| AUTH before any spend (CC4, Human Generator, marketplace packs, commissions), any new vendor, or edits to SPEC, ADRs or DESIGN_SYSTEM decision 4 | `agents/grok/README.md` §6; REVIEW_RUBRIC B2, B3; AUTH #024 ("its own spend AUTH if used") |
| **v1: no face or body capture path exists** (M2-AVAT-01 AT-3). Any biometric work is V2 and gated | SECURITY_CHECKLIST §5 banner; ADR-0006; REVIEW_RUBRIC C6 |
| The 13+ age gate stays a v1 requirement | SECURITY_CHECKLIST §5.6 |
| Pins; commercial-safe licences; every asset recorded with version and licence | SECURITY_CHECKLIST §7.1, §7.3, §7.4; REVIEW_RUBRIC C8 |
| Bots never handle raw user photos or video | SECURITY_CHECKLIST §6.5 |
| Performance: state the SPEC §6 effect; animation + IK ≤ 4 ms; ≤ 2 IK chains beyond feet | REVIEW_RUBRIC D1, D2 |
| Tokens only in any selection or store UI; contrast; touch targets | REVIEW_RUBRIC G1–G4 |
| Units (A = avatar height, 1.75 m → 14.6 cm), scale multiplier | Movement Bible §1 |
| Shared skeleton, procedural layer (foot/hand IK, look-at) and the 2-chain limit | Movement Bible §2 |
| Clip pipeline: retarget to the GJ shared humanoid skeleton | Movement Bible §11–§12 |
| Tool sockets for the carried tools (grapple coil, matchstick pole) | Movement Bible §3.6; AUTH #021 |
| Reactive idle and the blendshape set it needs | Movement Bible §7 |
| Contact frames for the §9 audio | Movement Bible §9 |
| Avatar creation UX: likeness confirmation and wardrobe (both V2 in practice) | Design Skills rules 15, 16 (§3.6) |
| Readability at 1:12: rim light + contact shadow | Design Skills rule 20 (§3.7); DESIGN_SYSTEM decision 1 |
| Store after a win, cosmetic-only, no pay-to-win | Design Skills rule 26 (§3.11); SPEC §3.8 |
| Roster art spec, fidelity, rig standard, cosmetics, sourcing | DESIGN_SYSTEM decision 4 (v1 roster block, AUTH #024) |

## 2. Capture flow

**v1: none.** The player *selects* a character. Selection is instant, the chosen character carries into play and the diorama, and copy says "your character" (DESIGN_SYSTEM decision 4; M2-AVAT-01 AT-2). Any design that adds a camera to the character flow is out of scope for v1.

**V2 (reference only, not authorised):**
- DESIGN_SYSTEM decision 4's locked text describes the future flow: a full-body shot with a 360° rotation, then a face close-up with rotation, with retakes allowed.
- The kit role block adds lighting guidance and front/left/right face angles.
- The optional iPhone Duo variant (tent posture, rear cameras) is also V2 (M2-DUO-01, redirected by ADR-0006).
- Nothing may be built until the consent gate (§6) and a V2 AUTH exist.

## 3. Head/body merge

**v1:** there's nothing to merge. Each roster character is authored as one body on an open base:
- MakeHuman (CC0 exports) via MPFB2, or Human Generator, uplifted in Blender (primary track, AUTH #024).
- CC4 + Mixamo is the contingency licence track, and needs its own spend AUTH.
- Head proportions follow "about 7 heads" (SPEC §3.2).

**V2:**
- A photo head (image-to-3D or a regressor onto ICT-FaceKit/FLAME-2023-Open) is joined to a parametric body at the neck seam. Match skin tone and UVs across the seam, and keep the head at metric size so eye height stays at 1A.
- Licensing is the real constraint. SMPL/SMPL-X, BFM, DECA/EMOCA/MICA weights, PIFuHD/ECON and PanoHead are **non-commercial**. Only ICT-FaceKit (MIT) and FLAME-2023-Open geometry (CC-BY) are clean bases (`research/rnd/README.md`).
- Vendor heads were dropped: Meshy/Tripo by AUTH #019, then Avatar SDK was deferred by AUTH #020.

## 4. Retopo and bake budgets

- **One character on screen at a time.** The budget is set per character, "sized to hold 30 fps with Tier 0/Tier 1 reactivity on the reference device" (`design/proposals/character-roster-v1.md` §3).
- **Exact poly, texture and material-count numbers are TBD.** No repo document fixes them. Set them in M2-AVAT-01 from a device measurement, then record them in the M2 PR and DESIGN_SYSTEM §12 Field notes (REVIEW_RUBRIC H2).
- **Pipeline (open-base track, sourcing doc §3):**
  1. Open base.
  2. Sculpt and uplift.
  3. Retopo: quad remesh (Blender QuadriFlow, Instant Meshes), then manual cleanup on the face and hands.
  4. UVs.
  5. Bake high → low (normal, AO) in Blender Cycles.
  6. Grounded PBR textures.
  7. LODs (Decimate/meshoptimizer), then Unity.
- **Mobile rules:**
  - ASTC-compressed textures.
  - Atlas to cut material count.
  - A LOD Group, because the 1:12 character is small on screen most of the time.
  - Face detail only needs to hold up in the selection screen and photo mode (proposal §2).
- **Shading:**
  - One unified character shader (URP Lit/Shader Graph).
  - An environment probe sampled from the splat.
  - A warm rim light (Fresnel) plus a contact shadow (DESIGN_SYSTEM decisions 1 and 4; Design Skills rule 20).
  - The "realism+" SKU is a material tier on the same mesh, not new geometry (SPEC §3.8).
- **Owning topology and UVs** (open-base track) is what lets V2 push to hero-photoreal on the same rig (sourcing doc §5).

## 5. Rig validation (the heart of v1)

The rig standard (SPEC §3.2, DESIGN_SYSTEM decision 4, proposal §3):
- **Skeleton:** Unity Humanoid mapping on a fixed hierarchy, fixed names and a fixed count.
- **Pose and scale:** canonical T-pose (or A-pose), eye height and scale normalized to 1A, consistent forward axis.
- **IK and contact:** standard foot/hand IK targets plus contact markers, so the §9 contact frames line up on every character.
- **Tool sockets (AUTH #021):** grapple coil on the back, and matchstick pole in hand and stowed.
- **Faces:** a minimal shared blendshape set (blinks, a few expressions) for the Bible §7 reactive idle. No full FACS, no lip-sync.

**Automated rig-conformance gate** (M2-AVAT-01 AT-1). Every character **and every cosmetic** must pass it:
- It checks bone count, T-pose, eye height, scale and socket presence.
- Implement it as an Editor `AssetPostprocessor` plus EditMode tests (`Avatar.isHuman`, `HumanTrait` coverage, `Animator.GetBoneTransform` for eye height vs 1A).
- Run it in the `unity-tests` workflow so it's a real CI check.

**Clip test:** every character and cosmetic plays the full verb + tool set with no clipping or rig breakage: parkour, climb families, dive-roll, tic-tac, vault variants, wall-run, grapple swing/ascend/rappel and pole-vault (M2-AVAT-01 AT-2; proposal §6). There are no per-character animations. Retarget is the only path (Unity Humanoid retargeting; Bible §12).

**Casting and readability** (M2-AVAT-01 AT-5):
- Eight characters (≥ 6 floor) across body type, apparent gender presentation, skin tone and apparent age.
- Each has a distinct silhouette and a colorblind-distinct hero color, so any two are tellable apart at 15 cm on bright, dark and cluttered scans.

**Clean-IP review per character** (M2-AVAT-01 AT-3; sourcing doc §1):
- Full commercial rights to embed in a game build.
- No resemblance to any identifiable real person.
- No scanned-people libraries, and no MetaHuman (Unreal-only).
- Daz only with per-asset Interactive Licenses.

## 6. Consent gate and deletion

**v1:** there is no biometric data, so SECURITY_CHECKLIST §5 is **not applicable** except §5.6 (13+ gate). §6.2 (face/body photo deletion) is marked V2. What v1 must still do:
- Keep "no capture path exists" true, and prove it (M2-AVAT-01 AT-3).
- Cover character selection and owned cosmetics in per-user delete-all (SPEC §7; `legal/RETENTION_SCHEDULE.md`; M0-LEGAL-02).
- Keep the 13+ gate ahead of account features.

**V2 gate (when custom avatars return):**
- No face or body bytes leave the device and no job is created until a consent record exists (user id, policy version, timestamp, locale, hash of the exact text, stated retention) (§5.1).
- Consent is its own step, never bundled (§5.2).
- Training use is a separate opt-in, default off (§5.3).
- Withdrawal and delete complete within 30 days, including vendor-side (§5.4).
- Counsel reviews the copy before launch (§5.5).
- Photos are deleted on device, in storage and at the vendor right after generation, with a media-free receipt (§6.2).
- Processing runs on infrastructure we control (`research/rnd/README.md`).
- The draft copy already exists as a V2 artifact in `legal/BIPA_CONSENT.md` (M0-LEGAL-01 cancelled for v1).
- Laws to map: Illinois BIPA, Texas CUBI, Washington MHMDA. The Everalbum (FTC) and Meta/Texas CUBI outcomes show the downside.

## 7. Likeness confirmation UX

**v1:** replaced by **character selection**:
- One primary action per screen.
- Characters shown in the diorama with their hero color and silhouette.
- Cosmetics preview live on the chosen character.
- The store appears only after a win, never after a loss (Design Skills rule 26; DESIGN_SYSTEM decisions 4 and 9).

**V2:** Design Skills rule 15 and the decision 4 locked text:
- The generated head turns slowly next to the source photo, with "Is this you?" and Yes / Retake / Tweak.
- Tweak offers four coarse controls: skin tone, hair, glasses, build.
- No slider editor.
- The target is "recognizable in a blind test, generated in under 2 minutes" (kit role block; SPEC §6 still lists avatar generation < 2 min as a target).
- Measure identity with a commercially-licensed or self-trained recogniser, because the ArcFace/InsightFace weights are non-commercial (`research/rnd/README.md`).
- Stay short of hyperreal at 15 cm, because feature mismatch drives the uncanny valley (Mori; Kätsyri et al.).

## 8. Mistakes to avoid

- Letting biometric work creep into v1: a "quick selfie tint", a face-detect SDK, TrueDepth APIs. That is V2 and needs consent scaffolding plus an AUTH.
- Picking a base or tool without reading its licence: MakeHuman app vs assets, MB-Lab forks, Daz game-embed terms, non-commercial research weights, Hunyuan3D territory limits.
- Buying CC4, Human Generator or a pack without a spend AUTH (AUTH #024 approved $0 spend).
- Per-character bone surgery or per-character clips. Retarget or reject.
- Cosmetics that pass in the idle pose but clip during wall-run, grapple coil or climbs. Run the full clip test.
- Hyperreal faces at 15 cm, or detailed faces that cost texture memory nobody sees in play.
- Inventing budget numbers. Measure on device and record them in Field notes.
- Trusting `services/avatar/README.md` (stale; see the top of this file).

## 9. Checklists

**Pre-PR (character/cosmetic):**
- [ ] Rig-conformance gate green in CI (bone count, T-pose, eye height = 1A, scale, sockets).
- [ ] Clip test across the full verb + tool set; clip or screenshots attached; `gj-qa-release` visual pass requested.
- [ ] Rights record: source, licence, version, commercial game-embed rights, and a no-real-person-resemblance note (SECURITY_CHECKLIST §7.4; M2-AVAT-01 AT-3).
- [ ] Budget: tris/textures/materials vs the recorded M2 budget; SPEC §6 effect stated (D1).
- [ ] Readability on bright, dark and cluttered scans; hero color passes the deuteranopia check (Design Skills §4).
- [ ] No face or body capture code path, permission string or SDK added (AT-3).
- [ ] Any selection/store UI uses tokens only and meets 44 pt targets (G1, G4).

**Per roster character:** open-base or licensed source recorded · casting-matrix slot · silhouette + hero color distinct · retargets with no fixes · sockets present · blendshape set present · LODs · passes all five-environment play (M2-AVAT-01 AT-4, suggested).

## 10. Pointers

`ADRs/0006-v1-avatar-curated-character-roster.md` · `design/proposals/character-roster-v1.md` · `research/vendors/character-roster-sourcing.md` · `research/rnd/README.md` · `research/vendors/avatar-selfhost.md`, `avatar-alternatives.md`, `meshy.md` · DESIGN_SYSTEM decision 4 · SPEC §3.2, §3.8, §7 · SECURITY_CHECKLIST §5, §6 · `legal/BIPA_CONSENT.md` (V2), `legal/RETENTION_SCHEDULE.md` · tickets M2-AVAT-01, M0-LEGAL-01 (cancelled → V2), M0-LEGAL-02, M0-LEGAL-04 (cancelled).

## Session log

| Date | Learned | Changed |
|---|---|---|
| 2026-09-24 | Builder authored the first handbook foundation. | Initial SKILLS.md + curated RESOURCES.md starter set. |
| 2026-09-26 | AUTH #024 picked open-base authoring as primary at $0 spend, while the proposal had recommended licensing. Per-character poly/texture budgets aren't fixed anywhere yet (M2-AVAT-01). `services/avatar/README.md` predates AUTH #020. `legal/BIPA_CONSENT.md` is a V2 artifact. | gj-operator expanded RESOURCES.md to 104 link-checked entries and rewrote SKILLS.md around the AT-2 topics with an explicit v1/V2 split (M0-SKILL-05). |
