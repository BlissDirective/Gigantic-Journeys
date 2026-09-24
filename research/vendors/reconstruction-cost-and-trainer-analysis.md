# Reconstruction Backend — Long-Term Cost & Trainer Analysis

`research/vendors/reconstruction-cost-and-trainer-analysis.md` · 2026-09-24 · Prepared by the Coordinator/Builder for the Owner. Decision-support for **M1-CAPT-03** and a possible **ADR-0005 addendum**. Answers the two questions the Owner raised after **AUTH #030** (self-host committed + prioritized; bridge conditional) and **AUTH #031** ($100 spike cap):
1. **Is self-host much more costly than a managed API (Kiri/Luma) long-term — is it sustainable?**
2. **gsplat/Splatfacto vs Brush — thorough comparison and a recommendation.**

> Snapshot caveat: GPU spot/marketplace rates fluctuate hourly; API pricing and product states move fast. Figures are July–Sept 2026 representative snapshots, not quotes. Per-scan dollar figures are **derived** (time × rate), not vendor-quoted. Uncertain items are flagged ⚠.

---

## TL;DR

- **Self-host is *not* "much more costly." It is cheaper at scale and roughly at per-scan parity even early.** The real cost of self-host is **engineering**, not compute — a fixed cost that repays itself past ~5,000–12,000 environments/month.
- **The managed option is effectively off the table on *terms*, not just price.** Luma discontinued reconstruction entirely; Kiri's API is "testing stage," has no published no-train/enterprise tier, so the written **no-train + DPA + residency** commitment AUTH #030 requires for real user homes likely **cannot be obtained** from it today.
- **The cheapest early path is itself self-host** — run our own pipeline on **scale-to-zero serverless GPU** (~$1/scan at near-zero volume, no idle bleed), dropping to ~$0.30–0.50/scan on spot/reserved GPUs as volume grows. Same price as "buying," but all data stays on our infra.
- **Reconstruction cost is nearly a rounding error** (one-time per environment, amortized over every download). The cost that scales with success is **CDN egress** — use **zero-egress storage (Cloudflare R2 / Backblaze B2)** and it nearly vanishes. This lever dwarfs the build-vs-buy decision.
- **Trainer: implement gsplat/Splatfacto first** (production-mature, Apache-2.0, quality-competitive, built-in compression, mature headless CUDA/Docker). Keep the pipeline **trainer-agnostic** and add **Brush** (Apache-2.0, wgpu, no CUDA lock-in) as a second adapter later.
- **The #1 program risk is the iOS Metal splat render, and it is *orthogonal* to every decision above.** As of Sept 2026 there is **no public demonstration of correctly depth-sorted Gaussian splats at 30 fps on a physical iPhone inside Unity.** This must be funded as its own engineering track; the trainer choice does not touch it.

---

## PART 1 — Cost & Sustainability

### 1.1 GPU rental snapshot (2026, on-demand $/GPU-hr)

| GPU | RunPod | Lambda | Vast.ai (on-dem / spot) | AWS (on-dem / spot) |
|---|---|---|---|---|
| L4 | $0.44 | — | ~$0.30–0.50 | ~$0.80 (G6) |
| L40S | $0.79–1.09 | — | from $0.39 | — |
| A100 80GB | $1.39 | $1.99–2.79 | $0.67–1.21 / ~$0.68 | ~$3.28–4.10 / ~50–70% off |
| H100 | $1.99–2.69 | $3.29–3.99 | ~$2.21 / ~$0.90 | ~$4–5 / 50–70% off |
| RTX 4090 | $0.34 (comm)–0.69 | — | $0.34 / $0.14 | — |
| RTX 5090 | $0.69–0.99 | — | $0.30–0.60 | — |

Reserved/committed saves ~40–60% but implies multi-year commitment — wrong shape for ramp-from-zero. ⚠ CoreWeave is "largely sold out" of 2026 capacity; Lambda *raised* H100 rates on demand pressure; consumer-card marketplace rates (Vast/RunPod-community) are cheapest but carry interruption risk. *Sources: gpuperhour/RunPod, Spheron, Vast.ai, Thunder Compute (2026).*

### 1.2 Self-host per-scan compute (150–300 phone images, room/tabletop)

Pipeline wall-clock on one box: **GLOMAP SfM (5–15 min, ~3.5× faster than COLMAP) → gsplat training (10–30 min, 7k–30k iters) → compress (1–3 min ⚠) → Open3D mesh (1–5 min ⚠)** ≈ **~0.5–0.75 GPU-box-hr/scan**. SfM and mesh are **CPU-bound**, so a fast GPU idles during them (at scale, split SfM onto cheap CPU nodes).

| GPU class | Rate | **Per-scan (derived)** |
|---|---|---|
| RTX 4090 (comm/spot) | $0.34 | **$0.20–0.31** |
| L40S | $0.39–0.79 | **$0.20–0.55** |
| A100 80GB | $0.68–1.39 | **$0.27–0.83** |
| H100 | $1.99–2.69 | **$0.60–1.35** (fast but *not* cost-optimal here) |

**Best cost/throughput: GLOMAP + gsplat on L40S/4090-class.** *Sources: gsplat (arXiv 2409.06765), GLOMAP (arXiv 2407.20219), Spheron deploy-3DGS.*

### 1.3 Managed API pricing (2026) — and the terms wall

| Provider | Per-scan | Splat output? | Status / terms |
|---|---|---|---|
| **Kiri Engine API** | **~$1.00/scan** (1 credit) | Yes (3DGS + mesh) | ⚠ **$500 minimum**; **"testing stage, subject to change"; no published no-train/enterprise tier.** |
| **Luma** | **N/A** | — | ⚠ **Discontinued.** Pivoted fully to generative video/image (Ray3.2, Uni-1). No reconstruction API exists. |
| **Polycam** | No public API rate | Yes | Content API is **contact-sales only**; subs $150–1,200/yr. Not a usable per-scan API. |

**Kiri at $1/scan is the only real public per-scan reconstruction API — but its default terms train on inputs, and the enterprise no-train tier AUTH #030 requires is not offered publicly.** So for **real user home scans**, managed is blocked on *terms*, before cost even enters. *Sources: kiriengine.app/api + /pricing, lumalabs.ai/llm-info, poly.cam/pricing.*

### 1.4 Serverless GPU — the smart early deployment (this *is* self-host)

Because volume ramps from near-zero, always-on GPUs bleed on idle. Scale-to-zero serverless bills only the ~0.5–0.75 hr/scan:

| Platform | GPU | **Per-scan** | Cold start |
|---|---|---|---|
| **RunPod Serverless** | L40S flex | **$0.88–1.31** | 30 s–2 min ⚠ (heavy CUDA image); dollar cost of cold start negligible |
| **Modal** | A100 80GB | **$1.00–1.50** | 15–30 s big containers |
| Replicate / Baseten | A100/H100 | $2–3.3 | too expensive for batch |

Running **our** pipeline on RunPod-flex/Modal costs **~$1/scan at near-zero volume** (parity with Kiri) with **no idle cost** and **all data on our infra**. This is self-host — just rented compute, not a data-training vendor. It fits the $100 spike cap cleanly. *Sources: Aliteq/Spheron RunPod 2026, Blaxel/GPUCloudCost Modal.*

> Nuance for production: rented GPU (serverless or dedicated) still means scan media transits a third party's hardware. Infra providers (RunPod/Modal/AWS) offer standard **compute DPAs and do not claim training rights** — a far lower bar than the no-train commitment an *AI* vendor like Kiri would have to make. Owned hardware removes even that. Either is compatible with AUTH #030; a Kiri-style API is not.

### 1.5 Fixed / overhead costs

| Cost | Rate | Note |
|---|---|---|
| Object storage | R2 $0.015/GB-mo; B2 ~$0.006 | 1 TB (≈10k envs @100 MB) ≈ **$15/mo** on R2 |
| **CDN egress** | **R2 $0/GB; B2 free (Bandwidth Alliance); S3+CloudFront ~$0.085/GB** | ⭐ **The biggest lever.** Identical for build *or* buy. Zero-egress storage ≈ removes it. |
| Orchestration/queue | ~$20–200/mo | Can be serverless |
| **Engineering — build** | **~$50k–150k ⚠** (≈0.25–0.75 FTE-yr) | The real cost of self-host |
| **Engineering — ops** | **~$25k–90k/yr ⚠** (≈0.1–0.4 FTE) | Pipeline drift, CUDA upgrades, QC, on-call |

*Sources: Backblaze/Cloudflare R2 (2026), Kore1/StealthAgents MLOps salary (2026).*

### 1.6 Crossover model (total monthly cost; delivery excluded as a wash)

Self-host per-scan improves with scale (flex→spot→reserved); engineering amortized ~$5k/mo. Managed = Kiri $1/scan, ~zero eng.

| Scans/mo | Self-host total | Managed (Kiri) | Winner |
|---:|---:|---:|:--|
| 100 | ~$5,125 | $100 | **Managed** (50×) |
| 1,000 | ~$5,830 | $1,000 | **Managed** (~6×) |
| 10,000 | ~$11,200 | $10,000 | ~even |
| 100,000 | ~$40,000 | $100,000 | **Self-host** (2.5×) |

**Crossover ≈ 8,000–12,000 scans/month** with engineering amortized. If engineering is a sunk/founder cost (count only marginal cash), self-host wins from **~1,000–3,000 scans/mo**.

### 1.7 Verdict on sustainability

**Self-host is sustainable and is the right long-term backend.** Marginal compute is $0.20–0.80 (rented) or ~$1 (serverless) vs Kiri's $1 — *cheaper or at parity*, widening in our favor with volume. The real cost is engineering, a fixed investment that repays past ~5–12k envs/mo. **Two structural facts make this easy:** (a) reconstruction is one-time-per-environment, amortized over every download, so its unit cost barely touches unit economics; (b) the cost that *does* scale with success — CDN egress — is a shared wash that **zero-egress storage nearly eliminates**. Managed is not a viable long-term alternative for real user data anyway (Luma gone; Kiri terms-blocked). **Do not over-optimize reconstruction and then bleed on egress.**

**Real risks:** engineering time (dominant), per-scan quality variance (we own every bad reconstruction), GPU supply/price volatility, ops toil, and — the one people forget — **managed vendor risk itself** (Luma *already* abandoned reconstruction; Kiri is self-described "testing stage").

---

## PART 2 — Trainer Comparison

Both candidates **pass the license gate (Apache-2.0)**. gsplat is a **clean-room Apache-2.0 reimplementation, not INRIA code** — it does not pull in the non-commercial INRIA/SuGaR license.

| | **gsplat / Splatfacto** | **Brush** |
|---|---|---|
| License | Apache-2.0 ✓ | Apache-2.0 ✓ |
| Maturity | **Production**, JMLR-published, v1.5+, commits Sept 2026 | **Pre-1.0 proof-of-concept** (0.x) |
| Backing | Luma AI + Berkeley AI Research + large community | Solo (A. Brussee; "not an official Google product") |
| Backend | Python + **CUDA (NVIDIA only)** | Rust + **wgpu (AMD/Intel/NVIDIA/Apple)** |
| Headless/Docker | Mature but CUDA-bound (nvidia-container-toolkit) | Single binary; vendor-agnostic but DIY container |
| Quality vs INRIA | ~parity (within ~0.5 dB), **verified** | Favorable but **unquantified** ⚠ |
| Speed | ~10–15% faster than INRIA, ~4× less VRAM | Claims ≥ gsplat, **unverified** ⚠ |
| SfM bundled | No → COLMAP/glomap (BSD) | No → COLMAP |
| Compression | **Built-in PngCompression** (upstream of SOGS) | Compressed PLY; route via external tools |
| Output | `.ply` + compressed | `.ply` + compressed |

*Sources: nerfstudio-project/gsplat (LICENSE, releases), docs.nerf.studio, JMLR v26/24-1476, ArthurBrussee/brush, radiancefields.*

**Recommendation: gsplat/Splatfacto first; pluggable adapter; Brush second.** gsplat is the only production-safe choice today. Brush earns a later slot specifically for its **CUDA-free wgpu backend** (cheaper/heterogeneous GPU fleets — AMD/Intel) and out-of-core (RAM-friendly) training.

**Adapter contract (identical for both):** `{images + COLMAP/glomap poses} → trainer → {.ply}` → shared post-step normalizes to `.spz` / `.sog` via **playcanvas/splat-transform (MIT)**. COLMAP/glomap (BSD) is a shared front-end so neither trainer owns SfM. Use gsplat's **MCMC strategy** to train to a *fixed splat budget* (directly serves the size/fps target).

---

## PART 3 — The iOS Render Path (the real risk)

**This is the program's #1 technical risk and it is independent of the trainer.** The trainer emits a file; the failure lives entirely in Unity's per-frame Metal depth sort.

### 3.1 Unity renderer survey
- **aras-p/UnityGaussianSplatting** — the de-facto renderer, **MIT** ✓. Supports **Unity 6 URP via render graph** (v1.1.x, 2026), APIs D3D12/Vulkan/**Metal**, reads PLY + **Scaniverse SPZ**. **No LOD/streaming** (self-described "toy visualization"). **iOS: README says "iOS devices definitely do not work."**
- **The blocker — Metal depth sort.** Splatting must re-sort all splats back-to-front **every frame**. aras-p's AMD-FidelityFX-derived **GPU radix sort** is fast on desktop but **glitches on Apple Metal**: issue **#226** ("Radix sort seems buggy on Mac M1 and iOS", open, Mar 2026) and a Unity Discussions thread both report correct rendering **only with sorting disabled** (i.e. visually wrong). No maintainer fix.

### 3.2 Proof that splats *do* run on iPhone — natively
- **scier/MetalSplatter** — **MIT**, native Swift/Metal, iPhone/iPad/macOS/visionOS, reads PLY/SPZ. Most credible "runs on a real iPhone" reference; wrappable as a Unity native plugin.
- **rayanht/msplat** — **Apache-2.0**, uses a **tile-local bitonic sort** (each 16×16 tile sorts ≤2048 gaussians in threadgroup memory), **~350 fps on M4 Max**. This is the reference for the sort technique that sidesteps the Metal radix-sort bug.
- Directional benchmark ⚠: iPhone 17 Pro, ~10M splats — narrowing sort keys 32→16-bit cut sort ~39.8 ms → ~22 ms, ~19 → ~23 fps. **On iOS the sort is the bottleneck, and 10M splats does not hit 30 fps** — you must fix the sort *and* cap splat count.

### 3.3 Does Brush's wgpu de-risk iOS? No.
wgpu proves the *algorithm* runs well on Apple Metal (WGSL→MSL), which retires the abstract "is it even possible" question — but Brush's Rust/WGSL kernels **cannot be dropped into Unity's HLSL→MSL pipeline**. Using a wgpu renderer instead of Unity would contradict the Unity 6 requirement. The fix is Unity-side and trainer-agnostic.

### 3.4 Mitigation (fund as its own track from day one)
1. Replace aras-p's radix sort with a **tile-local bitonic sort** (msplat approach), or
2. Ship a **native Metal render/sort plugin** for Unity (wrap **MetalSplatter**, MIT), and
3. **Cap the room to ~1–2.5M splats** (gsplat MCMC) + ship **SOG (~20×)** or **.spz (~10×)**.

### 3.5 Size / fps target
- **≤150 MB/env: comfortably achievable** — cap splats + SOG/.spz. (A 3–5M-splat room ≈ ~40–70 MB SOG / ~90–130 MB .spz; raw PLY ~1 GB.) Mobile-GS demonstrates 4.8 MB @116 fps on Snapdragon via distillation — headroom exists.
- **30 fps on iPhone: only with an explicit splat budget AND a working Metal sort.** Plan LOD/chunked streaming ourselves (aras-p has none).

*Sources: aras-p/UnityGaussianSplatting (LICENSE, releases, issue #226), Unity Discussions, scier/MetalSplatter, rayanht/msplat, nianticlabs/spz (MIT), playcanvas/splat-transform (MIT), PlayCanvas SOGS blog, Mobile-GS.*

---

## PART 4 — Recommendation & spike plan

**Architecture (recommended):**
- **Front-end:** COLMAP/glomap (BSD) for poses — shared.
- **Trainer:** gsplat/Splatfacto (Apache-2.0), MCMC to a fixed splat budget; **pluggable adapter**, Brush later.
- **Compression:** `.spz` and/or `.sog` via splat-transform (MIT); target ~1–2.5M splats, ≤150 MB.
- **Mesh:** Open3D (MIT) collision mesh.
- **Compute:** **serverless GPU (RunPod-flex/Modal)** for the spike and early production (~$1/scan, scale-to-zero); migrate to spot/reserved/owned at scale.
- **Delivery:** **zero-egress storage (R2/B2)** — the biggest long-term cost lever.
- **iOS render:** a **dedicated Unity-side track** — tile-local bitonic sort or a MetalSplatter-based native plugin + splat budget. Prove correct 30 fps on a physical iPhone.

**How the $100 (AUTH #031) is best spent — render-path-first.** Reconstruction (gsplat) is the *de-risked* half; the render is the unknown. Recommended order: (1) run gsplat on a **public dataset** first (validate quality/cost/timing, no privacy exposure), (2) compress to .spz/.sog under budget, (3) put it into Unity and **hit the Metal-sort wall on a real iPhone** early — that is where the program risk actually lives. Corpus rooms (Owner-supplied, consented) follow once the path is proven.

**What can start now with $0 and no devices:** the `services/reconstruction/` headless pipeline scaffold (gsplat-first, pluggable, CPU-testable on a synthetic fixture, Dockerfile/CUDA, license manifest, spike-report skeleton). The GPU run needs input data + the $100; the iOS render track needs Unity + a Mac + an iPhone (Operator/QA VM + UNITY_LICENSE + device).

**Decisions that would need the Owner's AUTH:** formalizing gsplat-first + the render-track plan into an **ADR-0005 addendum** (protected path). Recommended after the direction is confirmed / the spike firms it up (M1-CAPT-03 AT-4).

---

## Uncertainty flags
- GPU spot/marketplace rates fluctuate hourly; GCP L4/A100 figures looked mislabeled and were dropped from the summary.
- COLMAP timing swings from ~10 min to hours with image count/resolution — the largest per-scan variable.
- Compression/mesh timings and engineering build/ops costs are estimates; eng cost dominates the crossover — validate against the real team.
- Kiri per-credit cost is "subject to change"; no public volume/enterprise pricing.
- Brush's exact latest version/date and its speed/quality-vs-INRIA claims are not independently verified.
- The iPhone-17-Pro 10M-splat sort benchmark is directional (source not firmly attributable). wuyize25/gsplat-unity's iOS support/license were not confirmed.
