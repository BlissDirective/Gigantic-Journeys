# Proposal — Character roster art spec (v1)

**Status: PROPOSAL for Owner review · 2026-09-19 · Coordinator.** Rationale doc (not a decision). Deepens SPEC §3.2 (avatar) + §3.8 (cosmetic IAP) + §8 (M2), the locked DESIGN_SYSTEM decision 4, and ticket M2-AVAT-01, all under the v1 avatar decision (AUTH #020 / ADR-0006). Adopting it is a design-change **AUTH** touching SPEC and the locked DESIGN_SYSTEM. Grounded in the Owner's direction: ship **generated characters for v1** (no biometric), put the realism budget into the **video→playable environment and world-class movement**, and take the time to make it legendary.

## 0. Thesis
The environment is the star; **the character is the piece you move through it.** So the roster's job is narrow and demanding: a small set of **rigged, semi-photoreal 1:12 characters** that (a) **read instantly at 15 cm**, (b) **move flawlessly with the entire v1 verb + tool set** on one shared skeleton, (c) let **players see themselves** without any photo or capture, and (d) are **provably clean-IP with zero biometric** — no resemblance to any real person. Three principles:
- **One skeleton, many skins.** Every character shares the GJ humanoid skeleton and the shared animation/traversal set — the roster is authored art, never a per-user generation step, so all characters move identically well and cosmetics never touch the rig.
- **Grounded, not hyperreal.** "Semi-photoreal" means believable materials and lighting that sit in a real splat — deliberately short of hyperreal faces (uncanny valley is a needless risk at 15 cm, and stylization keeps the characters unmistakably *not* real people). The realism spend goes into **materials, splat-integrated lighting, and movement**, which is what actually sells "real at 15 cm."
- **Cosmetic-only, no advantage.** The two IAP SKUs reskin the chosen character; every character has identical capability. No pay-to-win, ever (Design Skills rule 26).

## 1. Roster composition — casting without capture
Because there's no likeness capture in v1, the roster *is* how players see themselves — so it must be **broad and inclusive by construction**. Recommend a launch roster of **8** (the M2 floor is ≥6), cast against an explicit matrix so the spread is intentional, not accidental:
- **Body type / build** (the parametric height/build dimension), **apparent gender presentation** (including at least one androgynous/neutral read), **skin tone** (a wide, evenly-spread range), **apparent age** (young-adult through older-adult), and a **distinct silhouette + hero color per character** so any two are tellable apart at 15 cm.
- **Archetype flavor, not stats:** each character reads as a character (e.g., an explorer, an athlete, an everyday person, a tinkerer) purely cosmetically — no gameplay differences.
- **Free defaults are complete:** a non-paying player gets a fully-realized character; cosmetics add variety, never completeness.

## 2. Art direction — "grounded semi-photoreal at 15 cm"
- **Proportions:** realistic, about **7 heads** (SPEC §3.2), true-scale 1:12 (1.75 m → ~14.6 cm) expressed in avatar-height units **A** so everything survives the per-environment scale multiplier.
- **Materials & shader:** stylized-grounded PBR under **one unified character shader** lit by the **environment probe sampled from the splat**, plus the signature **rim light + contact shadow** (Design Skills rule 20) so the tiny body pops off the photoreal floor. Cloth/skin/hair tuned to read at distance, not for macro close-ups.
- **Faces:** warm and expressive but **low-to-moderate detail** — they're seen up close only in selection and photo mode. A small, curated **blendshape set** (blinks, a few expressions) drives the reactive idle (Bible §7); **no full FACS / no lip-sync** in v1.
- **Silhouette-first:** design each character silhouette-out (Design Skills rule 20 readability), verified against bright / dark / cluttered test scans and against colorblind-distinct hero colors.
- **Reference bar:** the materiality and readability of *Astro Bot* / high-end mobile characters at tiny scale; grounded-real (not stylized-cartoon, not hyperreal-human).

## 3. The rig standard — the GJ humanoid skeleton (the technical heart)
This is what makes M2-AVAT-01 AT-1 pass ("retargets with no manual per-character fixes"). Define **one** rig contract every character and every cosmetic conforms to:
- **Skeleton:** a fixed humanoid bone hierarchy + naming + count, **Unity 6 Humanoid** avatar mapping so Mixamo/warped clips and the motion-matching set retarget automatically; a canonical **T-pose (or A-pose)**, normalized **eye height and scale to 1A**, consistent forward axis.
- **IK + contact:** standardized **foot and hand IK targets** and **contact markers** so the §9 audio/reactivity **contact frames** line up on every character (footfalls, hand plants).
- **Tool attach sockets (AUTH #021):** fixed sockets for the **carried tools** — the safety-pin grapple + coiled twine on the back, the matchstick pole in hand/stowed — so grapple/pole-vault animations and the reel/coil state machine work identically across the roster.
- **Facial rig:** the minimal shared blendshape names above.
- **Mobile budget:** a per-character **poly + texture + material-count budget** and **LODs** sized to hold 30 fps with Tier 0/Tier 1 reactivity on the reference device; a single character on screen at a time keeps this cheap.
- **Validation:** an automated rig-conformance check (bone count, T-pose, eye height, scale, socket presence) gates every character and cosmetic — this is the "no manual per-character fixes" guarantee.

## 4. The cosmetic system (the two IAP SKUs)
- **SKU 1 — outfit pack:** swappable outfits authored on **rig-clean silhouettes** (casual, athletic, layered, dressed — the four already named in the locked decision 4) as mesh/material swaps that **never break the skeleton and never clip during the full verb + tool set** (wall-run, dive-roll, climbs, grapple coil-on-back, pole carry). Every outfit passes the same rig-conformance + a **clip test across the verb set**.
- **SKU 2 — "realism+" materials:** a higher-fidelity **material/shader upgrade** (better skin/cloth/hair response, sharper maps) applied to the chosen character — a quality tier, not new geometry.
- **Presentation:** both **preview live on the chosen character in the diorama**; the store appears **after a win, never a loss** (rule 26); clear prices, one-tap restore, no timers/gacha/scarcity. "Your character" copy (decision 4).

## 5. Sourcing & IP — clean-IP, zero biometric (a genuine fork)
Whatever the path, three hard gates hold: **full commercial rights**, **no resemblance to any identifiable real person** (no biometric, no likeness — a review step per character), and **one shared skeleton**. Three viable paths (the fork in §8):
- **(A) License / commission a rigged pack (recommended for v1):** buy commercially-licensed rigged semi-photoreal characters (reputable marketplace) or commission an artist; retarget to the GJ skeleton. Cleanest IP, predictable quality, fastest to ship. Cost: per-character or pack license/commission fees (a spend AUTH).
- **(B) AI-generate the base once, then rig in-house:** generate base meshes (image/text-to-3D) a single time, clean + rig them. Lowest art spend, full control. Risks: per-model commercial-rights + **no-real-person-resemblance verification**, cleanup/quality burden, and generator ToS (the Meshy identifiable-person ban is why this needs care).
- **(C) Author on an open, commercially-licensed human base:** build variations on an open base-mesh system + author textures/outfits in-house. Full ownership, no per-character license, but the most in-house art effort.

Recommend **(A)** to ship v1 cleanly and fast, with **(C)** as the "own everything" path if you'd rather not license, and **(B)** only behind the strict resemblance + rights gate.

## 6. Movement integration (the whole point of one skeleton)
Every character must pass the **entire v1 movement set identically** — the parkour vocabulary, the climb families, and the AUTH #021 additions (dive-roll, tic-tac, vault variants, wall-run) and tools (grapple swing/ascend/rappel, pole-vault). No character-specific animation exists; the shared retarget + standardized sockets are what let M2-AVAT-01 AT-4 ("moves identically well across five environments") hold. Ties to M1-MOVE-01/02 and M3-MOVE-01.

## 7. Accessibility & representation
Broad inclusive casting (§1); colorblind-distinct hero colors + distinct silhouettes so characters are tellable apart without relying on color; readable at 15 cm on bright/dark/cluttered scans; "your character" copy; no capture means no one is excluded by a scanner that reads their face or body poorly.

## 8. Governance — what adopting this changes (AUTH-gated)
- **SPEC §3.2** — deepen with roster composition (target count + inclusive casting), the grounded-semi-photoreal fidelity target, and the rig-standard summary.
- **SPEC §3.8** — sharpen the two cosmetic SKUs (outfit silhouettes + "realism+" as a material tier; clip-test + rig-conformance gates).
- **SPEC §8 (M2)** — align the M2 exit to the rig-conformance validation + cosmetic clip test.
- **DESIGN_SYSTEM decision 4 (LOCKED)** — add the **v1 roster art spec** block (fidelity target, silhouette/hero-color rule, rig standard, cosmetic clip test) beneath the existing v1 banner. *Locked doc → AUTH-gated.*
- **M2-AVAT-01** — sharpen ATs with the rig-conformance check, the cosmetic clip test across the verb+tool set, the inclusive-casting matrix, and the no-real-person-resemblance review.
- **Spend** — if the sourcing fork picks (A) license/commission, that license/commission budget is a **separate spend AUTH** (with a number and a cap), filed once you pick the path.

## 9. Decisions needed before editing the protected docs
1. **Sourcing path (§5):** (A) license/commission a rigged pack *(recommended)*, (B) AI-generate-once + rig in-house, or (C) author on an open base.
2. **Fidelity target (§2):** grounded semi-photoreal, readable-at-15 cm, stylized-safe faces *(recommended)*, or push toward hero photoreal.
3. **Launch roster size (§1):** 8 with an inclusive matrix *(recommended)*, 6 (minimum), or 10–12 (fuller).

On your answers I'll file the AUTH (and a separate spend AUTH if you pick a paid sourcing path), deepen SPEC §3.2/§3.8/§8 and DESIGN_SYSTEM decision 4, and sharpen M2-AVAT-01. Unless you object, I'll adopt the **one-skeleton rig standard**, the **cosmetic clip-test gate**, and the **inclusive-casting matrix** as specified.
