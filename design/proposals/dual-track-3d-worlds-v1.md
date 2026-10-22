# Proposal: Dual-track 3D playable worlds + the instant-play reframing (v1)

- **Status:** **APPROVED in principle by the Owner, 2026-10-22.** AUTH **#053** (multi-agent team) and **#054** (SPEC §3/§4 reframe) are logged. The `AGENT_GOVERNANCE.md` (v1.2) and `SPEC.md` (v1.11) edits are **staged on the governance branch and await the Owner's sign-off on the exact wording before merge to `main`** (the two most-locked docs; "ask before implementation"). See §7 for the resolved decisions.
- **Date:** 2026-10-21
- **Author:** Claude Code (Coordinator)
- **Owner trigger:** chat 2026-10-20 — "I am going to be working on this new direction, and the original video to rendered playable environment simultaneously… Using two different Grok bots, and yourself. One grok bot continues on the current video to fully playable immersive environment, the other on the 3D playable worlds and character design and environment interaction/traversal system builds." Plus the Owner's prior question on whether fully-generated playable settings and body-scan avatars are feasible, and a request to research AI-rendering feasibility honestly.
- **Related proposals (Track B builds on these, does not replace them):** `custom-avatars-v1.md`, `character-roster-v1.md`, `journey-route-generation-v1.md`, `ios-splat-render-v1.md`, `movement-fluidity-realism-v1.md`, `external-synthesis-builds.md`.
- **Supersedes nothing yet.** This is a reframing + an operating-model change, filed as a proposal first per CLAUDE.md (SPEC/ADR/agent-model changes need `APPROVED #n`).

---

## 1. What this proposes (and what it does not)

**Proposes three linked changes, each gated on its own AUTH (§7):**

1. **Product reframing — add an instant-play loop.** Ship a **library of ready-to-play, authored/procedural semi-photoreal worlds** that a player enters immediately with a curated or custom 1:12 avatar — no capture required — so the first play happens in seconds, not after a scan-and-wait. This is a **scope addition** to `SPEC.md §3` (today every v1 environment comes from a user scan) and a corresponding edit to `§4` non-goals.
2. **Reposition capture as the premium / signature path, not the entry gate.** The scan→playable pipeline is **not abandoned** — it is the moat and the "wow", repositioned from "the only way in" to "the advanced, personal, higher-effort path." (See §2 for why abandoning it would be a mistake.)
3. **Dual-track operating model.** Two Grok Operators running in parallel on **disjoint, write-isolated surfaces** plus the Coordinator — an amendment to `governance/AGENT_GOVERNANCE.md` (which today specifies **one** consolidated Operator and single-threaded, sequential operation).

**Does not propose:**

- No change to `config/movement.json`, `data/schemas/`, the Movement Bible, the Design Skills doc, the design system, or the milestone table — those stay AUTH-locked and are **read-only** to both tracks unless a separate AUTH says otherwise.
- No end-to-end "AI generates a finished playable world on demand" claim. The research below says plainly that does not exist at ship quality in late 2026 (§3).
- No body-scan photoreal-avatar upload. The proposal recommends **staying on the AUTH #044 on-device parametric avatar** and keeping deeper photoreal in the V2 R&D track (§3c). Escalating to body-scan photoreal would be its own AUTH and is **not recommended** for v1.

---

## 2. The strategic reframing

The Owner's instinct is right on the product-feel problem and should be adopted: **a capture-first entry gate is a slow, high-variance first-run.** A new player must film a careful 60–90 s pass, wait on reconstruction, and hope the quality gate passes — before they ever play. That is a weak instant-fun loop and a weak conversion funnel.

**But capture is the moat, so reposition it, do not drop it.** "Play *your own* bedroom / your Lego build at 1:12" is the thing no competitor has and the reason this product is special. The whole reconstruction stack (M1-PIPE, the MapAnything front-end, the self-host splat pipeline, AUTH #046/#047/#051/#052 privacy machinery) is real, working, and nearly at a TestFlight build. Abandoning it would throw away the differentiator to chase a crowded "AI worlds" space.

**The synthesis:** make the fast loop the *front door* and the capture loop the *signature feature behind it*.

- **Instant loop (new, Track B):** pick an avatar → pick a beautiful prebuilt world → play a generated journey in seconds. This is the retention/virality/first-run surface.
- **Signature loop (existing, Track A):** "now scan your own room / build and play *that*." This is the moat, the share-driver, and the premium emotional payoff.

Both feed the **same** journey-generation and traversal brain. A world is a world to the game loop, whether it was authored, procedurally assembled, or reconstructed from a scan — provided it conforms to the one environment-package schema (§5). That shared contract is what lets the two tracks run in parallel without colliding.

---

## 3. Feasibility: can we build "fully rendered playable worlds"? (honest answer)

Two focused research passes (late-2026 state; sources in §9; fast-moving items flagged "verify"). **Bottom line: yes, we can ship beautiful, guaranteed-playable worlds on iPhone — but by authoring/procedural construction with AI accelerating *assets and blockouts*, not by on-demand end-to-end generation, which does not exist at ship quality.**

### 3a. Generative-3D-world landscape (Oct 2026)

The field splits in two, and only one half is usable:

- **World models = neural video rollouts, NOT geometry.** Google **Genie 3** (720p/24fps, coherent a few minutes, cloud research preview), **Odyssey-3**, **Decart Oasis 3**, **Luma** — you can walk through them, but there is **no exportable mesh, no collision, no scale, nothing to import into Unity.** Categorically useless for a shippable mobile game. Rule them out.
- **Exporters = actual geometry, with caveats.**

| Tool | Exports | Playability gap | Commercial licence | GJ fit |
|---|---|---|---|---|
| **World Labs — Marble** (GA Nov 2025; 1.1 Apr 2026) | Gaussian splat (SPZ/PLY) **+ a low-fidelity "collider" GLB + a hi-res textured GLB** | Collider is coarse blockout; **real-world scale not guaranteed**; holes off the captured path | Commercial + hi-res mesh on **paid tier (~Pro)**; verify live EULA | **Best candidate** — as an *offline authoring accelerator* (blockout + reference), never a runtime; import the **mesh**, not the raw splat |
| **Tencent HY-World 2.0** (Apr 2026) | mesh / 3DGS / point cloud (partly roadmap; 1.0 had export bugs) | immature; 4–8 GPUs to run | **Community licence w/ territory carve-outs, MAU limits** — real legal risk | Watch, do not pilot until hosted + LICENSE clarified |
| **Microsoft TRELLIS.2** (4B, Dec 2025) | mesh + PBR, **object/asset scale (not scenes)** | n/a (asset generator) | **MIT — cleanest licence here** | Pilot for **props/set-dressing** feeding authored scenes |
| **Meshy / Rodin / Tripo** | game-ready meshes + PBR | asset-level; albedo-baked-lighting cleanup | **paid tiers = commercial; free tiers often NC/attribution** — verify | Budget-friendly **asset** generation on paid plans |
| **CSM Cube** | — | — | — | **Avoid** — acquired by Google, winding down |

**Verdict:** No tool generates a fully playable, exportable, collision-ready, correctly-scaled environment on demand. The best (Marble) gives a splat + a coarse auto-collider at unverified scale — a ~60–70%-done blockout, which is punishing for a 1:12 character that *climbs*, where surface accuracy and scale are the whole feel. AI is an **accelerator for assets and first-pass blockouts**, not an environment factory.

### 3b. Mobile realism ceiling: authored/procedural vs. splat on iPhone

- **Authored Unity URP, semi-photoreal, is achievable and is the right path.** URP is where Unity invests; HDRP can't target iOS; the ADR's URP choice is correct. Unity's own *Fantasy Kingdom* mobile demo (min spec iPhone 13) shows the toolchain: GPU Resident Drawer, GPU occlusion culling, STP upscaling, baked lighting. The **1:12 diorama framing is an asset** — small, art-directed spaces are exactly where mobile GPUs look their best and sidestep open-world streaming problems. Ceiling = "convincing semi-photoreal diorama," which is the product, not "offline-render photoreal." The real constraint is **sustained fps (thermals)** and **texture memory** (ASTC, atlasing, streaming), not polycount.
- **Gaussian splats on iPhone are a rendering technique that still needs a parallel collision mesh.** Mobile real-time splat rendering is emerging (Mobile-GS ~116fps on Snapdragon 8 Gen 3; MetalSplatter on Metal) but **no public iPhone fps/memory numbers** yet, and a room-scale splat is **hundreds of MB uncompressed** — a real risk against the 150 MB/environment budget without aggressive SPZ compression. Crucially, **a splat has no surface, no collision, no metric scale**: you must derive a collider mesh (SplatBridge / PlayCanvas `splat-transform --collision-mesh` / SuGaR) and recover scale separately. Splats **add** a pipeline; they don't remove one.
- **Procedural generation gives playability by construction.** Rule-based / modular / WFC / Houdini-baked assembly emits geometry **and its colliders and nav graph in the same pass** — so playability and 1:12 scale are guaranteed, not inspected per-scene. Pair PCG *structure* (load-bearing, deterministic, collidable) with AI *skins* (tileable PBR materials, AI skyboxes behind collidable foreground, generated props) applied onto geometry we control — keeping legally-risky generative content off the collision path.

### 3c. Avatars: parametric (AUTH #044) vs. body-scan photoreal

The Owner floated full body-scan photoreal avatars. **Recommendation: stay on the AUTH #044 on-device parametric "idealized-me" avatar; do not escalate to body-scan photoreal for v1.** Rationale:

- **Privacy/legal:** AUTH #044 processes the face **on-device**, fits a parameter set, and discards the media — no biometric upload, no vendor, no DPA, counsel-gated under BIPA/CUBI/MHMDA. Body-scan photoreal with upload re-opens all of that and is a much heavier consent/retention burden.
- **Rigging risk:** the whole roster is rig-conformant **by construction** on one shared skeleton (AUTH #024), so every avatar moves identically well through the full verb+tool set. A photoreal body scan is a per-user generation step that must still be force-fit to that rig or it breaks traversal — exactly the per-character-fix problem M2 is designed to avoid.
- **Instant-fun:** the curated roster already delivers instant avatar selection with zero capture; parametric custom is the opt-in personal touch. That already satisfies the Owner's "play as yourself, instantly" goal without the photoreal escalation.

Deeper photoreal likeness stays in the V2 R&D track (`research/rnd/`), unified with the realism+ SKU on-ramp. If the Owner still wants body-scan photoreal explored, that is a separate AUTH + its own proposal; I'd scope it as V2 research, not a v1 workstream.

### 3d. Recommended production pipeline (the thing we actually build)

**Author in Unity URP; build structure procedurally/modularly so collision + scale are guaranteed by construction; skin with licensed/indemnified assets; use splat/generative tools strictly as offline authoring accelerators that export standard meshes — never as the runtime.**

1. **Geometry & playability (load-bearing):** modular / PCG-assembled worlds in Unity; kit-of-parts placed by rule-based or Houdini-baked generation; **colliders + NavMesh emitted in the same pass**; scale authored → 1:12 exact.
2. **Realism skin:** baked lightmaps + probes; PBR from **Poly Haven (CC0)** and Fab/Megascans; AI tileable materials (indemnified source) for variety; AI skyboxes (e.g. Blockade Labs) for distant backdrops.
3. **Optional realism boost, de-risked:** Marble (paid) or photo captures → **export the collider + textured mesh** → import the *mesh* so it inherits the same collision/scale pipeline. Keep raw splat rendering out of the shipping runtime until MetalSplatter has public iPhone perf/memory numbers inside budget.
4. **Mobile budget as a gate:** ASTC, atlasing, occlusion culling, STP upscaling, one baked sun, sustained-fps thermal profiling on an iPhone-13-class device per quality tier.

This produces dozens of worlds at predictable, parallelizable, licence-clean cost, with playability structural rather than earned per scene.

---

## 4. The one contract that decouples everything: the environment package

Today's published **environment package** (SPEC §3.7) is: splat + collision mesh + scene graph + environment spec + thumbnail, vendor-neutral and versioned, conforming to the frozen `data/schemas/` (scene_graph, traversal_graph, environment_spec). The journey/traversal brain (SPEC §3.3–§3.5) consumes that package and nothing else.

**Key architectural point:** make the authored/procedural worlds of Track B emit the **same** environment package. Then:

- Track A (scan→package) and Track B (authored/procedural→package) are **two producers feeding one consumer.**
- The game loop (journey generation, validator, traversal, reactivity) is written **once** and is identical for scanned and authored worlds.
- The schema is the API boundary between the tracks. Neither track edits the schema (it is AUTH-locked); both target it.

This is also what makes two parallel Operators safe (§6): they work on disjoint producer trees that meet only at a frozen, read-only contract.

---

## 5. Dual-track workstream structure

| | **Track A — Capture→Playable** | **Track B — Authored Worlds + Characters + Traversal** | **Coordinator (Claude)** |
|---|---|---|---|
| **Owner-agent** | Grok Operator A (`gj-operator`, existing) | Grok Operator B (new) + Claude Builder when scriptable | this session |
| **Mission** | the moat: user video → reconstructed splat + collision → package | the instant loop: beautiful prebuilt worlds, the character/rig system, the environment-interaction & traversal builds | governance, AUTH, PROGRESS, Brain-B (journey/traversal), 100% security-sensitive + periodic secondary review |
| **Primary trees (write-owned)** | `services/reconstruction/`, capture/upload client, `qa/evidence/M1-PIPE-*`, reconstruction ops (Modal/RunPod) | `unity/` world + character + interaction scenes, authored/procedural world tooling, `design/worlds/` (new), roster/cosmetics art, traversal/interaction gameplay code | `governance/`, `SPEC.md`/`ADRs/` (edits only via AUTH), `PROGRESS.md`, `tickets/` table |
| **Ticket namespace (proposed)** | keep `M1-PIPE-*`, `M1-SCEN-*` (capture side) | new `M*-WORLD-*`, `M*-CHAR-*`, `M*-INTX-*` (worlds / characters / interaction-traversal) | governance tickets |
| **Branches** | `ticket/<id>` as today | `ticket/<id>` in the new namespaces | `claude/gigantic-journeys-governance-*` |
| **Reads (never writes)** | the shared schemas, `config/movement.json`, the brain | same | — |

**Write-isolation rules (the safety contract):**

1. **Disjoint trees.** Each tree above has exactly one writing track. The two Operators never edit the same file set — satisfying AGENT_GOVERNANCE §4 ("at most one agent writes to a given branch or file set at a time") *across* surfaces rather than by serializing on one.
2. **The schema is frozen and shared.** `data/schemas/`, `config/movement.json`, the Movement Bible, Design Skills, the design system — AUTH-locked, read-only to both tracks. Any needed change is a Coordinator-filed AUTH, not a track edit.
3. **One merger per PR.** Each track self-reviews and merges its own PRs on green CI (AUTH #007). The Operator merges only its own artifact PRs, never code. No cross-track merges.
4. **Shared-contract changes serialize through the Coordinator.** If either track needs the environment-package schema extended (e.g. an "authored-world" provenance field), that is one Coordinator AUTH + one schema PR that both tracks then target — never a concurrent edit.
5. **Cadence.** 2-hour Operator sync as today (`agents/grok/README.md`); the Coordinator does the weekly + checkpoint secondary review across both tracks and owns the single PROGRESS table.
6. **Bounded parallel, not a return to the eight-bot model.** Two Operators on two fixed surfaces is a **standing, write-isolated parallelism**, explicitly scoped — not an open multi-agent fan-out. The token-cost and context-fragility arguments in AGENT_GOVERNANCE §1 still bind: no third Operator, no duplicate work, no two agents on one surface.

---

## 6. Governance & required approvals (NOT YET APPROVED)

Per CLAUDE.md hard rules, the following must be approved by the Owner before any execution. I will **not** self-approve, fabricate approval, or merge the SPEC/agent-model edits until these are logged.

1. **AUTH (agent-model): amend `governance/AGENT_GOVERNANCE.md`** to permit **two standing Grok Operators on disjoint, write-isolated surfaces** (Track A capture, Track B worlds/characters/interaction) plus the Coordinator, with the §5 write-isolation rules as the compensating controls. This is the change that AGENT_GOVERNANCE itself says needs an AUTH.
2. **AUTH (design-change): edit `SPEC.md §3` and `§4`** to add the **authored/procedural prebuilt-world library** as a v1 surface and reposition capture as the premium path, and to carve the **procedural/authored-world exception** into the "no synthetic game objects" non-goal (authored worlds are not synthetic *placed* game objects, but §4 must say so explicitly, and `BACKLOG.md` updated).
3. **AUTH (milestone-plan), if needed:** if Track B gets its own milestone rows (e.g. `M*-WORLD`/`M*-CHAR`/`M*-INTX`), editing the §8 table is a milestone-plan change.
4. **Spend AUTHs, deferred until a tool is actually chosen:** any paid tier — World Labs Marble Pro, Fab Professional, KitBash3D Unlimited, paid Meshy/Rodin/Tripo, indemnified AI-material source — is spend and needs `APPROVED #n`; capture each licence's text in `legal/` before ship. **No spend is requested by this proposal.**
5. **ADR, only if we ever put raw splats in the runtime** (vs. mesh-export) — that would be an architecture decision; not proposed here.

AUTH #052 (the bedroom-package Supabase relay) is **already logged and is unrelated** to this pivot; it is noted here only to prevent number confusion.

---

## 7. Owner decisions — RESOLVED 2026-10-22

1. **Agent model → beyond two bots.** The Owner directed: *"Remove restriction completely, I will ultimately be using a full team of grok bots: two for development, several for marketing, one for sales management/accounting."* Logged as **AUTH #053**; `AGENT_GOVERNANCE.md` amended to v1.2 (team model; correctness/security invariants preserved).
2. **v1 scope → reframe.** The Owner chose *"Make it v1 (reframe)."* Logged as **AUTH #054**; `SPEC.md` v1.11 adds §3.12 (authored world library) and repositions capture as premium.
3. **Avatars → parametric + more variation.** The Owner chose *"Stay parametric, increase variation in curated roster/selectable avatar characteristics."* Recorded under AUTH #054 as a Track B mandate (no body-scan photoreal in v1); a `avatar_params` schema expansion, if needed, gets its own AUTH.
4. **Tree/ticket ownership:** proceeding with the §5 split and the `WORLD`/`CHAR`/`INTX` namespaces as the default (Owner did not redirect); characters stay inside Track B unless the Owner later splits them out.
5. **First worlds:** proceeding with ≈3–5 worlds for a first playable (SPEC §3.12); art direction/themes to be set per `design/worlds/` tickets.

### Original open-decision text (for the record)

1. **Agent-model amendment:** approve two standing, write-isolated Operators + Coordinator as in §5? (If yes, I draft the AGENT_GOVERNANCE amendment + the `gj-operator-b` role pack and file the AUTH.)
2. **v1 scope:** should the **instant prebuilt-world loop become a first-class v1 surface** (SPEC §3 edit), with capture repositioned as premium — or stay a post-v1 track while capture remains the v1 core? This decides whether Track B is v1 or V-next.
3. **Avatars:** confirm **staying on AUTH #044 on-device parametric** (my recommendation) — or do you want a separate V2 proposal scoping body-scan photoreal?
4. **Tree/ticket ownership:** are the §5 trees and the `WORLD`/`CHAR`/`INTX` ticket namespaces the split you want, or should characters be their own third surface rather than folded into Track B?
5. **First worlds:** how many prebuilt worlds for a first playable (I'd suggest 3–5 to prove the loop), and what art direction / themes?

I'll hold the AGENT_GOVERNANCE and SPEC edits until you answer 1–3; 4–5 I can proceed on with sensible defaults if you'd rather I just pick.

---

## 8. Risks

- **Two-bot coordination cost.** Mitigated by hard write-isolation (§5) and the single shared schema (§4); the failure mode AGENT_GOVERNANCE warns about (two agents, one surface, conflicting writes) is structurally prevented, not just discouraged.
- **Scope dilution of the moat.** Mitigated by keeping Track A fully resourced and framing capture as the signature payoff, not a deprecated path.
- **"AI worlds" over-promise.** The research is explicit: no on-demand playable generation. The build plan leans on authored/procedural with AI as accelerator, so we never ship on a capability that doesn't exist.
- **Fast-moving tool facts.** Marble tiers, Hunyuan licence, MetalSplatter iPhone numbers, CSM status — all flagged "verify on primary source before spend/ship."
- **Licence landmines.** Hunyuan community licence (territory/MAU carve-outs), NC free tiers on asset generators — handled by the "paid-commercial / MIT / CC0 only, captured in `legal/`" rule.

---

## 9. Sources

Generative-3D landscape: World Labs/Marble (worldlabs.ai/blog/marble-world-model; docs.worldlabs.ai/marble/export/gaussian-splat), Genie 3 (deepmind.google/models/genie), Hunyuan HY-World 2.0 (github.com/Tencent-Hunyuan/HY-World-2.0), TRELLIS.2 (huggingface.co/microsoft/TRELLIS.2-4B), Meshy/Rodin/Tripo comparison (strayspark.studio, picoberry.ai), CSM (radiancefields.com/platforms/csm), Odyssey-3 / Decart (the-decoder.com, techcrunch.com), splat-collision reality (top3d.ai, radiancefields.com).
Mobile ceiling: Unity Fantasy Kingdom (unity.com/en/demos/fantasy-kingdom), URP vs HDRP (juegostudio.com), Fab/Megascans licensing (dev.epicgames.com/documentation/en-us/fab), KitBash3D (help.kitbash3d.com), Mobile-GS (arxiv.org/abs/2603.11531), MetalSplatter (github.com/Spatial-Explorer/MetalSplatter), SplatBridge (radiancefields.com/splatbridge-...), PlayCanvas collision (developer.playcanvas.com/user-manual/splat-transform/collision), SuGaR (arxiv.org/html/2311.12775v3), Blockade Labs (blockadelabs.com/tos), Adobe Firefly indemnity (computerworld.com), Houdini/Unity (sidefx.com/forum/topic/88078).
Fast-moving items (Marble tiers, Hunyuan licence, MetalSplatter iPhone perf, CSM status) are flagged "verify" above and must be re-checked on primary pages before any spend or ship decision.
