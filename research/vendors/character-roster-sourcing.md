# Character roster sourcing — dual-track assessment (License/Commission vs Open-Base-Authored)

**Status: research · 2026-09-19 · Coordinator.** Requested by the Owner (2026-09-19): run **both** a license/commission track and an open-base authoring track **in parallel** — "one for speed, one for control" — and assess cost, control, art outcome, character outcome, etc. Fidelity: **grounded semi-photoreal for v1, pushing toward hero-photoreal in V2** (with the custom-avatar track). Roster size: **8** (inclusive matrix). Pairs with `design/proposals/character-roster-v1.md`. Verify all prices/terms before purchase — figures are ranges as of the Jan 2026 knowledge cutoff.

## 0. The key insight — the rig standard is the contract; sourcing is pluggable
Because every character conforms to the **GJ humanoid skeleton + socket + mobile-budget contract** (proposal §3), *where a character comes from doesn't matter to the game* — a licensed character and an in-house-authored one are interchangeable once retargeted. That is exactly why running both tracks in parallel is cheap: they converge on one contract, and we pick the best of each for launch. It also means the sourcing decision is **reversible and mixable** — not a one-way door.

## 1. Hard gates (both tracks, every character)
1. **Full commercial rights** to embed the mesh in a shipped iOS game build (not just "render" rights — some EULAs allow renders but not real-time game embedding; see Daz below).
2. **No resemblance to any identifiable real person** — no photogrammetry of real humans, no likeness. This is a per-source review, and it disqualifies scanned-people libraries.
3. **One shared skeleton** — retargets to the GJ humanoid rig with no per-character bone surgery.
4. **Clean-IP throughout** — consistent with the movement (AUTH #001 free-tier) and audio (CC0) posture.

## 2. Track A — License / Commission (the speed track)

### Sub-options
- **A1 — Parametric/generated character tools (recommended core of this track).** Tools that *generate* semi-photoreal humans (not scans of real people), commercially licensed, auto-rigged, Unity-exportable:
  - **Reallusion Character Creator 4 (CC4)** — parametric semi-photoreal humans, SkinGen materials, auto-rig, Unity export, huge content ecosystem, commercial license; characters are generated, **not** real-person likenesses. *Straddles A and C* — it's both "license a pipeline" and an authoring tool. **Best single fit.** Cost: CC4 Pipeline ~$300 one-time + optional content packs (verify).
  - **Human Generator (Blender addon)** — modern-ish parametric humans, commercial license on output, one-time ~$100 (verify). Good for both tracks.
  - **Mixamo (Adobe)** — free rigged characters + auto-rigger + animations, commercial-usable per Adobe terms; library is limited/older-looking. **Not the final roster, but ideal for pipeline + movement bring-up** (and we already use Mixamo clips, AUTH #001).
- **A2 — Marketplace packs.** Unity Asset Store / Sketchfab / ArtStation / CGTrader rigged semi-photoreal humans. Cost ~$20–150/character or a pack license. Quality/consistency vary; must fit the rig and pass the resemblance gate.
- **A3 — Commission.** Hire a character artist/studio for bespoke rigged characters. Highest art control, owned work-for-hire, but ~$2,000–8,000+/character and weeks–months. Best reserved for a few **hero** characters, as a *separate later spend AUTH*, not the whole roster.

### Reject / caution
- **Scanned-real-people libraries (Renderpeople, AXYZ, Twindom, etc.):** photogrammetry of real humans → fails gate 2 (resemblance + publicity rights). **Reject** for characters. (Scanned *clothing/prop* reference is fine.)
- **MetaHuman (Epic):** license restricts use to **Unreal Engine** — **cannot ship in a Unity build. Disqualified.** (Common misconception; worth stating.)
- **Daz 3D / Genesis:** free app, but embedding meshes in a real-time game build requires per-asset **Interactive Licenses** (base EULA covers renders, not game embedding) → license cost + bookkeeping per figure. Viable but license-heavy; only if a specific Genesis asset is worth it.

### Scorecard
| Dimension | Track A (license/commission) |
|---|---|
| **Cost** | Low–moderate: tools ~$100–300 one-time (CC4/Human Generator); packs ~$20–150 each; commission ~$2–8k+/hero character (separate AUTH) |
| **Control** | Medium (parametric tools) to High (commission); low for fixed marketplace packs |
| **IP / ownership** | Licensed (read each EULA); commission = owned work-for-hire |
| **Art outcome** | Fast to a good, consistent baseline (CC4 especially); commission = on-brand |
| **Character outcome** | Solid semi-photoreal quickly; less bespoke unless commissioned |
| **Timeline** | Days–weeks (tools/packs); weeks–months (commission) |
| **Resemblance risk** | Low with generated/parametric; **high with scanned-people packs (rejected)** |
| **Forward-compat to hero-photoreal (V2)** | Medium — CC4 can push fidelity; you don't fully own topology/UVs unless commissioned |

## 3. Track C — Author on an open, commercially-licensed base (the control track)

### Tools / bases
- **MakeHuman** — the application is AGPL, but **its assets and exported models are CC0 (public domain)** → output is fully commercial-usable and **owned outright**, $0. Base look is a bit dated → needs sculpt/texture uplift in Blender to hit "grounded semi-photoreal." **Strongest ownership + cost story.**
- **MB-Lab (Blender)** — parametric humans (ManuelBastioniLAB successor); output historically permitted commercial use — **verify the current fork's asset license** before shipping. $0 addon.
- **Human Generator (Blender)** — paid one-time (~$100), commercial output license; more modern than MakeHuman; usable in this track too.
- **From-scratch base mesh + Blender** — maximum control/quality, maximum labor.

### How the control track works
Stand up an in-house Blender pipeline: open base → sculpt/retopo to the GJ art bar → author textures/materials (grounded semi-photoreal) → outfits on the four rig-clean silhouettes → rig to the GJ humanoid skeleton → LODs → Unity. Once the **base + pipeline** is set, each additional character gets cheaper, and you **own topology + UVs**, which is what lets you push **texture/material/displacement fidelity to hero-photoreal in V2** and reuse the exact same rig for the V2 custom-avatar model (`research/rnd/`).

### Scorecard
| Dimension | Track C (open-base authored) |
|---|---|
| **Cost** | Mostly in-house Blender labor; bases $0 (MakeHuman CC0 / MB-Lab) or ~$100 one-time (Human Generator); no per-character license |
| **Control** | Highest — you author and own everything, tuned to the exact rig + art bar |
| **IP / ownership** | Fully owned (CC0 base + authored work) — the cleanest posture |
| **Art outcome** | As good as the artist; open bases need uplift to reach the bar |
| **Character outcome** | Bespoke, on-brand, owned; scales once the pipeline is built |
| **Timeline** | Slowest to a first polished character; amortizes across the roster |
| **Forward-compat to hero-photoreal (V2)** | **Highest** — own topology/UVs → climb fidelity without re-sourcing; shares the rig with the V2 custom-avatar model |

## 4. The parallel plan ("one for speed, one for control")
Run both against the single rig contract, converge at M2:
- **Speed track (A) — now:** license CC4 (+ Mixamo for free bring-up) and get **2–3 characters onto the GJ skeleton immediately** to validate the whole pipeline — retarget, the full verb + tool set (wall-run, dive-roll, climbs, grapple, pole), the cosmetic clip-test, and the mobile budget. This **de-risks the pipeline in days** and can fill launch slots if the owned line runs late.
- **Control track (C) — in parallel:** stand up the open-base Blender pipeline and author the **owned, on-brand hero characters** to the exact bar, built forward-compatible to hero-photoreal.
- **Convergence gate (M2):** the launch **8** is whichever characters have cleared the rig-conformance + clip-test + readability-at-15 cm bar — most likely a **mix**: a few owned hero characters + licensed characters filling the inclusive-casting matrix. The **owned line becomes the V2 hero-photoreal + custom-avatar foundation**; licensed characters can be retired or kept as ownership allows.

This is low-risk precisely because the rig is the contract: neither track is a bet-the-roster commitment.

## 5. Fidelity roadmap (v1 grounded → V2 hero-photoreal)
- **v1:** grounded semi-photoreal — believable materials + splat-integrated lighting + rim light/contact shadow, readable at 15 cm, stylized-safe faces (no uncanny valley, no real-person resemblance). Realism spend goes to **materials, lighting integration, and movement**.
- **V2:** push toward **hero-photoreal** on the **same rig** — higher-fidelity skin/cloth/hair (the "realism+" material tier is the on-ramp), enabled by the owned topology/UVs from track C, and unified with the **V2 custom-avatar model** (`research/rnd/`: synthetic-first, local-GPU, on-prem, identity-preserving). Because both ride the same GJ skeleton + animation set, climbing fidelity and adding custom avatars **does not change the game loop** — it's an art + model uplift, not a re-architecture.

## 6. Cost summary + proposed bounded spend
- **Track C tooling:** ~$0 (MakeHuman CC0 / MB-Lab) to ~$100 one-time (Human Generator). Rest is in-house labor.
- **Track A tooling:** CC4 Pipeline ~$300 one-time + optional content packs; Mixamo $0.
- **Marketplace packs (optional):** ~$20–150/character if used to fill the matrix.
- **Commission (optional, deferred):** ~$2–8k+/hero character — a **separate later spend AUTH**, only if wanted.
- **Proposed bounded spend AUTH for roster tooling/licenses:** a one-time cap of **~$1,000** covers CC4 Pipeline + Human Generator + a couple of content/outfit packs — enough to run **both** tracks' tooling. Well under the standing caps. Commission stays out of this cap (its own AUTH if/when desired).

All figures **subject to price/term verification before purchase** — I can pull live, license-vetted options and current prices as a follow-up if you want firm numbers before approving the cap.

## 7. Recommendation
- **Adopt the dual-track plan (§4)** against the one rig contract; launch **8** with an inclusive matrix; **v1 grounded → V2 hero-photoreal** on the same rig (§5).
- **Track A core = CC4** (+ Mixamo for free pipeline bring-up); **Track C base = MakeHuman (CC0) or Human Generator**, uplifted in Blender.
- **Reject** scanned-real-people libraries and **MetaHuman** (Unreal-only); treat **Daz** as case-by-case (Interactive License).
- **To proceed to the AUTH + protected-doc edits I need:** your OK on the **~$1,000 one-time tooling/license cap** (or a different number), and a green light on the parallel plan. On that I'll file the design AUTH (roster art spec) + a bounded spend AUTH, deepen SPEC §3.2/§3.8/§8 and DESIGN_SYSTEM decision 4, and sharpen M2-AVAT-01.
