# Learned / physics-based motion — exploration & spike plan (#8)

**Tier-2 R&D exploration · 2026-10-01 · Builder (AUTH #027) · ticket M2-RES-01**
Context: AUTH #043 plan item **#8** ("learned/physics motion"), Owner-directed to *open and explore now*.
Compute line: Tier-2 **AUTH #040** ($500/mo) on **AUTH #039** RunPod (Modal fallback). No new AUTH or spend
to produce this exploration (desk research). This is forward/v2 research — **v1 ships classic motion
matching** (M1-MOVE-01) regardless of anything here.

---

## 0. TL;DR / recommendation

Three sub-directions, very different maturity for *our* constraints (1:12 character, iOS, procedurally
generated scanned levels, ≤4 ms anim CPU / ≤60 MB motion DB):

| Direction | Runtime on an iPhone? | Offline value to us | Verdict |
|---|---|---|---|
| **8a — Learned Motion Matching (LMM)** | ✅ tiny MLPs, sub-ms; **shrinks the DB** | compresses + stabilises the clip DB | **Strongest near-term; v1.1/v2 candidate** |
| **8b — Neural motion synthesis / diffusion** | ⚠️ real-time only at WebGPU/desktop (30–120 ms), not our per-frame budget | **generate/augment** vocabulary + transitions, bake into the clip DB | **Offline tool, not runtime** |
| **8c — Physics-based RL control (AMP/ASE/PARC)** | ❌ full-body physics + policy at 30 fps on mobile is the blocker | augment traversal mocap on scanned terrain; feasibility | **v2 north star; offline + distill** |

**Recommendation:** open a Tier-2 R&D track with **three scoped experiments** (A/B/C below), each with its own
go/no-go gate and all **offline/GPU** (no v1 runtime commitment). Experiment B directly **improves v1 quality**
(it manufactures more/better clips for the classic matcher and is the real form of the Owner's "video → usable
motion" idea). A and C de-risk v2. Nothing here touches a frozen schema, `movement.json`, or the v1 critical
path; user scans never enter training (SPEC §3.3) — only our own mocap and the consented corpus.

---

## 1. What #8 is

Two frontier families, both aimed at motion that **generalises beyond the clips we captured** — essential
because our levels are the player's unseen, scanned rooms:

- **Learned / generative kinematic motion** (8a + 8b): neural models that compress, select, or *synthesise*
  animation from a motion dataset.
- **Physics-based learned control** (8c): a controller trained (usually by RL) to *drive a simulated body*,
  so it can improvise over novel geometry rather than replay a clip.

## 2. Our hard constraints (these decide everything)

- **Mobile frame budget (Bible §2):** anim + IK + warping ≤ **4 ms/frame**, motion DB ≤ **60 MB**, ≤ 2 IK
  chains, 30 fps floor. iOS-only v1 (AUTH #003); measured on the Owner's iPhones.
- **Procedural levels:** no hand-authored level to overfit to; motion must adapt to arbitrary scanned terrain.
- **1:12 scale, deliberately non-realistic feel** (floaty gravity, miniature cadence — AUTH #043): real human
  mocap is *reference*, not ground truth; our target feel is tuned, not physical.
- **Processing on our own infra (SPEC §3.3):** any training/inference on user data stays self-hosted. Training
  data for #8 is **our own captures + CC0/licensed mocap + the consented corpus only** — never user scans.
- **On-device inference reality:** Core ML (CPU/GPU/ANE) + Unity **Sentis** run **small MLPs sub-millisecond**;
  **diffusion and physics-stepping at 30 fps on a phone are not** today. This single fact sorts the three
  directions above.

## 3. Landscape (2025 state)

### 3a. Learned Motion Matching — the mobile-realistic one
Classic Motion Matching (our v1 plan, Bible §13) does a nearest-neighbour search over a large unstructured clip
DB each frame. **Learned Motion Matching** (Holden et al., 2020) replaces the DB + search with three *small*
neural networks (compressor / stepper / projector) — it **shrinks the DB** (directly helping our 60 MB budget)
and runs the selection as tiny MLP evals (sub-ms, mobile-fine). 2024–25 work makes it **stable and fast** with
Lipschitz-continuous networks + a Sparse Mixture of Experts, and adds **environment-aware** variants (choosing
motion from surrounding geometry) — directly relevant to traversing scanned surfaces. This is the one family
that is both a **runtime** candidate for us (iPhone-feasible) and an incremental step from the v1 plan.

### 3b. Neural motion synthesis / diffusion — an offline generator
2025 pushed motion diffusion toward interactivity: autoregressive/streaming models (DartControl, ICLR 2025;
MotionStreamer; ARDY) and systems like Uthana's real-time windowed diffusion (30 future frames from 7 past,
**30–120 ms end-to-end in-browser via WebGPU**). But the field's own caveat stands: standard diffusion needs
seconds per clip, and even the fast variants hit **tens of milliseconds on WebGPU/desktop**, an order of
magnitude over our 4 ms phone budget. **Conclusion for us: not a runtime technique**, but an excellent
**offline generator** — synthesise transitions and fill vocabulary gaps, then bake the results into the clip DB
the classic/learned matcher ships. This is the technically sound form of "analyse motion → usable motion."

### 3c. Physics-based RL control — the north star, hardware-gated
AMP (adversarial motion priors, 2021) and ASE (reusable skill embeddings, 2022) train a *simulated* body to
move in the style of a mocap set; **PARC** (2025) is squarely on our problem — "**physics-based augmentation
with RL for terrain-traversal character controllers**," iteratively augmenting a motion dataset and training an
agile motion-tracking controller. This is the holy grail for procedural levels (the controller *improvises*
over your desk). The blocker is runtime: a trained policy net is small, but **stepping a full-body physics sim
at 30 fps on a phone is not viable today**, and training is GPU-heavy. Realistic path for us: use it **offline**
to (i) augment our traversal mocap with physically-plausible variants on scanned-terrain, and (ii) prove
feasibility; **distill** to kinematic clips/controllers for runtime. Pure on-device physics control is v2+.

### 3d. On-device inference reality (iOS)
Core ML runs on CPU/GPU/ANE; 2024–25 adds MLTensor; coremltools converts PyTorch → `.mlpackage`; Unity
**Sentis** runs ONNX models in-engine. Tiny MLPs (LMM-style) are **sub-millisecond per frame** — fine. The ANE
excels at batched transformers (LLM/ASR), not necessarily per-frame tiny-MLP latency, so the realistic runtime
target is a **small Sentis/Core ML MLP on GPU/CPU**, i.e. the LMM shape — not diffusion, not physics stepping.

## 4. Fit vs our constraints

| Approach | Mobile runtime | DB size | Adapts to novel terrain | Training cost | Best use for us |
|---|---|---|---|---|---|
| Classic MM (v1) | ✅ (search) | ✗ large (≤60 MB cap) | partial (data-bound) | none | **v1 ship** |
| LMM (8a) | ✅ tiny MLPs | ✅ **compresses** | partial→good (env-aware) | moderate (GPU) | **v1.1/v2 runtime** |
| Diffusion/synthesis (8b) | ✗ (10s of ms) | n/a | ✅ generative | moderate–high | **offline clip augmentation** |
| Physics-RL (8c) | ✗ (sim @30fps) | n/a | ✅✅ best | high (RL, GPU) | **offline augment + v2 research** |

## 5. The spike — three experiments (all offline/GPU, Tier-2)

**Experiment A — LMM on our whitelist** *(de-risks a v1.1/v2 runtime upgrade)*
Reproduce Learned Motion Matching on the ~110-clip whitelist (Bible §11) once M1-MOVE-01 builds the classic
baseline. Measure **DB size** (LMM vs classic), transition quality, and **on-device per-frame cost** via a
Sentis/Core ML export on a reference iPhone. **Go/no-go:** LMM beats classic on DB size **without exceeding the
4 ms budget**, at equal-or-better transition quality.

**Experiment B — offline neural augmentation of the traversal vocabulary** *(improves v1 directly)*
Use a motion model (a VAE/diffusion generator, and/or PARC-style physics augmentation) **offline** to expand our
captured vocabulary into variants on scanned-terrain (vault/mantle/climb across many edge geometries), then feed
the cleaned results into the clip DB the v1 matcher uses. This is the real "video → usable motion" bridge: it
turns our own mocap (Rokoko/Move.ai) + the corpus into **more, better clips** with **zero runtime cost**.
**Go/no-go:** measurable coverage/quality gain on corpus rooms with no DB-budget blowout; all assets clean-IP
(our captures + CC0/licensed).

**Experiment C — physics-RL feasibility (PARC-style)** *(v2 north star)*
Train one traversal verb (e.g. mantle or vault) with an AMP/PARC-style controller in sim; measure adaptivity to
novel edges and estimate a **distillation** path to a runtime-affordable form. **Go/no-go:** a credible
distillation story to ≤4 ms runtime, or a clear "v2+/hardware-gated" verdict. No v1 dependency either way.

## 6. Compute & cost
All three run on **Tier-2 compute (AUTH #040, $500/mo) via RunPod (AUTH #039)**, Modal fallback — the budget
already exists; **no new spend AUTH**. Order of magnitude: A ≈ a few GPU-days (small nets); B ≈ a few GPU-days
per augmentation round; C ≈ the heaviest (RL training), bounded by the monthly line and pausable. **No user
scans** in training — our mocap + the consented corpus only (SPEC §3.3). A per-experiment compute estimate is
recorded against `research/tier2/compute-budget-2026-10.md` before each run.

## 7. Go/no-go & what v1 does regardless
- **v1 ships classic motion matching** (M1-MOVE-01). None of A/B/C gate v1.
- **A green** → schedule an LMM runtime upgrade for v1.1/v2.
- **B green** → fold the augmented clips into the v1 DB (a v1 quality win, within budget).
- **C green** → a v2 physics-adaptive-traversal track; **C red** → documented as hardware-gated, revisit at a
  future device baseline.

## 8. Risks
- **IP / training data:** only our own captures + CC0/licensed mocap + the consented corpus; **no third-party
  footage or user scans** become training data (legal + SPEC §3.3). Reference-only for inspiration.
- **Mobile runtime:** diffusion and physics stepping are **not** v1/v1.1 runtime — treat as offline only; the
  only runtime candidate is the LMM-shaped tiny MLP.
- **Scope creep:** this is R&D on a bounded budget with go/no-go gates; it must never slow the v1 critical path.
- **Determinism:** v1's journey/validator rely on the deterministic reach model (Brain B); any learned runtime
  motion must still respect the authored reach contract (`movement.json` + the 0.85 margin), not drift from it.

## 9. Sources
- [Learned Motion Matching (Holden et al., 2020)](https://www.researchgate.net/publication/343616124_Learned_motion_matching)
- [Stable & fast motion matching — Lipschitz nets + Sparse MoE](https://www.sciencedirect.com/science/article/abs/pii/S0097849324000463)
- [Environment-aware Motion Matching (2025)](https://arxiv.org/pdf/2510.22632)
- [DartControl — diffusion autoregressive real-time motion (ICLR 2025)](https://arxiv.org/pdf/2410.05260)
- [ARDY — autoregressive diffusion, interactive motion](https://arxiv.org/pdf/2607.08741)
- [PARC — physics-based augmentation + RL for terrain-traversal controllers (2025)](https://arxiv.org/abs/2505.04002)
- [AMP — adversarial motion priors (2021)](https://www.researchgate.net/publication/353626682_AMP_adversarial_motion_priors_for_stylized_physics-based_character_control)
- [Core ML on-device inference](https://www.codecentric.de/en/knowledge-hub/blog/core-ml-inference-on-ios)
