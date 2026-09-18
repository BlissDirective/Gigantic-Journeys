# Proposal — Sound design + environment reactivity (v1)

**Status: PROPOSAL for Owner review · 2026-09-18 · Coordinator.** Rationale doc (not a decision). Deepens SPEC §3.6 and Movement Bible §9 (feedback matrix) / §7 (reactions); adopting it is a design-change **AUTH** touching SPEC §3.6 and the locked Bible §7/§9, plus new tickets. Pairs with the movement plan (`movement-v1-expansion.md`) — this is the layer that makes the traversal *land*.

## 0. Thesis
The captured place is the star; **sound and reactivity are the cheapest, biggest production value that make it feel real and alive at 15 cm.** Two principles, both mirroring the game's core "no synthetic objects" purity:
- **Diegetic-first.** Sound comes from real materials and real events; music is restrained, never a wallpaper soundtrack that fights the immersion of *your real room*.
- **Scale-aware everything.** A tiny person in a real space is the defining audio problem: reverb tuned to the *captured room's actual size and materials*, and every sound pitched/scaled so **Lego clicks stay tiny and floor booms stay big**. This is the signature idea.

## 1. Sound design system (the "realistic sounds")

### 1.1 Material × event taxonomy (extends Bible §9)
Materials come from the scene graph labels (Bible §4): wood, tile/stone, carpet/rug, fabric/cushion, Lego/plastic, paper/cardboard, metal, glass, plant, curtain — **plus tool materials**: steel pin, fiber twine, matchstick wood. Events expand beyond §9's footstep/land/grab/slide to cover the full v1 verb + tool set:
- **Locomotion:** footstep per gait (walk/jog/run/sprint/crouch/balance) — brightness and weight scale with speed.
- **Contacts:** step-up, hop, vault (+ kong/speed/underbar), mantle, wall-push, **tic-tac** (wall kick), **wall-run** (continuous surface scrape), **dive-roll** (whoosh → tumble), the 4 landing tiers, grab, slide.
- **Climb:** per-hand/per-foot placement ticks for each climb family (stud tick, rung clank, pole scrape, free-climb scuffs).
- **Tools (new, AUTH #021):** grapple — pin **mount thunk** + metallic *ting*, twine **creak/whip**, **swing whoosh**, **reel zip**, **coil pat**; pole-vault — **plant thunk** + shaft **flex/whip**.
- **Reactions (§7):** the idle/peer/brush/sit sounds.
- **System/UI:** capture coaching, quality-gate chimes, publish, rating, store, summit/vista/flag stingers.

### 1.2 Feel rules
- Each event is a **layered** sound (transient + body + tail), with **round-robin variants + micro-pitch randomization** so nothing machine-guns.
- **Impact-scaled:** gain and brightness track velocity/impact (a hard land is louder and brighter than a soft step; a grab at max reach strains).
- **Contact-frame accurate:** footfalls and hand plants fire on the same contact frames motion-warping targets, so audio and animation are locked.

### 1.3 The signature: scale-aware acoustics
Derive an **acoustic profile from the reconstructed room** — estimated room volume + surface materials (both already in the scene graph) → reverb parameters (RT60, early reflections, damping). A big echoey room vs a dead little shoebox; a tiled bathroom rings, a carpeted den is soft. **Every captured place then sounds unique and real.** Three ambition levels (recommend the middle):
- *Simple:* a handful of room-size reverb presets picked by estimated volume. Cheap.
- ***Parametric (recommended):*** a runtime reverb whose size/decay/damping are computed from room volume + a material-absorption average. One reverb bus, near-zero runtime cost, big payoff.
- *Advanced (V2):* per-zone acoustics / geometry-informed early reflections.

### 1.4 Spatialization, ambience, mix
- **3D positional audio**, listener blended just behind the avatar (intimacy) biased toward the camera (clarity); distance attenuation scaled to the world.
- **Ambience / room tone:** a subtle, scale-appropriate bed — the muffled hum of being tiny in a big room, faint material-driven detail (a breeze in the plant, a hint of the outside near a window). Keeps the world from feeling dead; ducks under action.
- **Dynamic mix:** category buses (movement / world / tools / UI / music); sidechain ducking so a critical cue (a beam, a flag) always reads; loudness-normalized; a strict hierarchy so footsteps never mask a landing warning.

### 1.5 Budget + sourcing (clean-IP, like the movement free tier)
- Mobile audio budget: a sample-memory cap, a polyphony/voice cap, streamed ambience, compressed clips.
- **Source from CC0 / royalty-free libraries** (e.g. freesound CC0) or self-recorded foley — **no licensed/encumbered audio**, consistent with our clean-IP posture. Custom "tiny-object" foley (the Owner recording real small sounds) is a lovely V2 polish, not required for v1.

## 2. Environment reactivity system (the "reactive environments")

### 2.1 Tier 0 (ships) — deepen §9
Audio (above) + **particles** (dust puff, grit, fiber lint, petal, spark, splinter — keyed to material×event) + **haptics** (light footstep at run+, medium grab/vault, heavy land/plant/mount) + **camera shake** (hard/recover landings, flag plant, big grapple releases). All **scaled by the environment scale multiplier**, so Lego clicks stay tiny.

### 2.2 Tier 1 (ships) — soft procedural reactivity
Per SPEC §3.6: object segmentation + **shader-driven displacement, no physics** — cushions **dent** under footfalls/landings, curtains/plants/paper **sway and flutter** on brush or pass, cords/soft-hanging **swing**, dust motes stir. **Extended to the new verbs/tools:** a wall-run leaves a brief scuff/dust trail; the grapple twine sways and the pin's anchor object quivers on mount; a rappel bells a curtain; a pole-vault plant flexes a soft surface. Authored material-keyed off the scene graph; must hold **30 fps (M3 exit test)**.

### 2.3 Reactive light + shadow
The avatar keeps its contact shadow + rim light (Design Skills rule 20) and is lit by the **environment probe from the splat**; dust/motes near the avatar catch light. Keeps the tiny body grounded in the photoreal world.

### 2.4 The boundary (unchanged)
**Tier 2 — real rigid/soft-body physics (knock objects over, true cloth)** stays the **research track (SPEC §5), not v1.** v1 reactivity is "alive and responsive" via audio + soft shader reactions, deliberately not physics simulation — the same budget + purity discipline as no-synthetic-objects.

## 3. Music (a genuine identity fork)
Recommendation: **restrained, adaptive, diegetic-leaning.** No constant soundtrack (it fights the "your real place" immersion). Instead: a quiet ambient bed + **sparse adaptive stings at key beats** — a swell approaching the summit, a flourish on flag-plant, a chord on a vista reveal, and the **signature shrink-transition theme** (DESIGN_SYSTEM decision 3). Sound design carries moment-to-moment; music punctuates. This matches the Design Skills restraint ("store after a win, never a loss"). The Owner picks the identity (see the question).

## 4. Accessibility
Playable fully muted: **visual/caption cues** for key audio events (approaching hazard-free edges, summit/vista, tool-ready), a **Reduce Motion** extension to camera shake, and a **haptics toggle** — consistent with the locked accessibility baseline (DESIGN_SYSTEM decision 10).

## 5. Integration & pipeline
Reuses the Bible §12 pipeline: the feedback matrix wires via `SurfaceMaterial` events and Tier 1 hooks emitted for `gj-scenegraph` segmentation. Audio, particles, haptics, and Tier 1 reactions **all key off the same scene-graph material labels + contact frames**, and **all scale by the environment multiplier** (pitch, gain, reverb size, particle size, haptic strength). One source of truth, many reactions.

## 6. Governance — what adopting this changes (AUTH-gated)
- **SPEC §3.6** — deepen the tier definitions (audio system, scale-aware acoustics, Tier 1 extensions).
- **MOVEMENT_BIBLE §9** — extend the feedback matrix to the new verbs/tools + add the sound-layering / scale-reverb / mix rules; **§7** — reaction sounds. (Bible edits are AUTH-gated; small additions can also ride the Field-notes append.)
- **New tickets:** audio engine + material/event bank; scale-aware acoustic reverb from the scene graph; Tier 1 reactivity extension to tools/verbs; foley/library sourcing; accessibility cues.

## 7. Decision needed before editing the protected docs
**Music identity** — pick one: (a) **restrained adaptive stings** (recommended — diegetic immersion, sound is the star), (b) **fuller adaptive soundtrack** (more "game," more production), or (c) **no music at all** (pure diegetic). On your answer I'll file the AUTH, deepen SPEC §3.6 + the Bible, and write the audio/reactivity tickets. Unless you object, I'll adopt the **parametric scale-aware acoustics** (§1.3 middle) and the Tier-1 extensions as specified.
