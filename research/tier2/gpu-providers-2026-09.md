# Pay-as-you-go GPU providers: an alternative or supplement to Modal

2026-09-28 · gj-operator · **Research only. This is a recommendation, not an authorization.** No accounts were
created and no money was spent. Adding a vendor or a spend line needs the Owner's AUTH (SPEC §5, M1-RES-01 AT-3).
Companion to `research/tier2/compute-budget-2026-10.md`.

## 0. Why this exists

- The Modal **Starter** workspace has a **$20/month spend limit** plus the $30/month free credit. The dashboard shows
  a usage limit of $42.50. Raising the limit past Starter means the **$250/month Team plan**, a fixed fee on top of
  usage.
- Reconstruction (`services/reconstruction/modal_app.py`) runs GPU COLMAP/GLOMAP SfM and splatfacto (nerfstudio /
  gsplat) training. That takes about **8–25 min per scene on an A10G (24 GB)** and costs **$0.19–0.63 per scene** on
  Modal (measured).
- M1-RES-01 Tier 2 needs about **80–200 GPU-hours** on A100 80 GB / H100-class GPUs (estimated; compute-budget doc §2b).
- **Policy constraints (SPEC §108, ADR-0005):**
  - Reconstruction on third-party compute is **corpus-only**. Real user scans never leave project infrastructure.
  - Provider data handling therefore matters: isolation, region, retention/deletion, no training on customer data,
    and SOC 2.
  - AUTH #032 already names "**RunPod-flex/Modal**" as the approved serverless-GPU compute for the spike and early
    production, with a later move to spot/reserved capacity at scale.

## 1. Method and conventions

- **Prices:** every price was read from the provider's own public pricing page or public price API on
  **2026-09-28 (~8:00–8:10 PM CT)**. Sources are listed in §6.
- **USD per GPU-hour, on-demand list price** unless the row says spot or community. Marketplace prices (Vast.ai,
  TensorDock, Salad) are live snapshots and change by the minute.
- **Measured** = a number from our own Modal runs. **(est.)** = my assumption.
- **Per-scene estimate (est.):** A10G runtime of 8–25 min ÷ an assumed relative speed, times the $/h shown. Speed factors:
  - A10G / A10 = 1.0
  - L4 ≈ 0.75
  - A40 / A6000 ≈ 1.05
  - L40S ≈ 1.25 (measured: 20–25 % faster on Modal, spike report)
  - RTX 4090 ≈ 1.5 (not benchmarked; **must be measured** before we rely on it)

  Container start and image pull are **not** included. Our CUDA image is large, and a cold pull can add minutes per job
  on a fresh host. Batching many scenes per pod amortizes it.
- **Research month (est.):** 80 h and 200 h at the single-GPU A100 80 GB price, and 200 h at the H100 price (the
  compute-budget "high" case). GPU only. Storage, CPU (where billed separately) and plan fees are excluded unless
  noted.
- **H100 caveat (measured, spike report):** the gsplat image is built with `TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9"`. It
  runs on A100/A10G/A40/L4/L40S/4090 but **not on H100 (sm_90)** until 9.0 is added and gsplat is recompiled (about
  17 min of build).

## 2. Comparison table

| Provider (product) | 24–48 GB class $/h | A100 80 GB / H100 $/h | Billing granularity | Minimums / caps / tiers | Privacy and isolation notes | Est. $/scene | Est. research month (80 h A100 · 200 h A100 · 200 h H100) |
|---|---|---|---|---|---|---|---|
| **Modal** (baseline, serverless) | A10G $1.10 GPU; **$1.73 all-in** (8 cores + 16 GiB); L4 $0.80; L40S $1.95 | $2.50 (all-in $3.13) / $3.95 (all-in $4.58) | per second | Starter: $30 credit, **$20 spend cap**; more needs the **$250/mo Team plan** | SOC 2 Type II; gVisor sandbox; region pinning costs 1.15–1.75× | **$0.19–0.63 (measured)** | $250 · $626 · $916, **+ $250 Team fee** above the cap → $500 · $876 · $1,166 |
| **Runpod Secure Cloud pods** | L4 $0.49 · A40 $0.49 · RTX A6000 $0.53 · **RTX 4090 $0.74** · L40S $1.09 | A100 80 GB (PCIe/SXM) **$1.59** / H100 PCIe $2.89, **SXM $3.49** | per second | Prepaid credits, and pods stop at a $0 balance (a hard cap in practice); default **$80/h** account spend limit; low-balance email; a new pod needs ≥ 1 h of credit | **SOC 2 Type 2, SOC 3, ISO 27001:2022**, HIPAA/GDPR programs, DPA; Secure Cloud = T3/T4 DCs, "single-tenant" hosts; 31 regions, pickable | $0.06–0.19 (A40); $0.07–0.21 (4090) | **$127 · $318 · $698** (H100 SXM) / $578 (H100 PCIe) |
| Runpod **Community Cloud** pods | 4090 $0.34 · A40 $0.35 · L40S $0.79 | A100 SXM $1.39 / H100 PCIe $1.99 · SXM $2.69 | per second | same as above | ⚠ **Third-party hosts**, container isolation only, shared hardware. **Public-license corpus only** | $0.03–0.09 (4090) | $111 · $278 · $398 |
| **Runpod Serverless** (flex workers) | 24 GB (L4/A5000/3090) $0.69 · 4090 $1.10 · A40/A6000 $1.22 · L40S group $1.75 | $2.72 / $4.79 | per second | same credit model; active (always-on) workers are discounted | same as Secure (serverless runs on Runpod-managed fleet); workers are containers from **our Docker image** | $0.11–0.36 (24 GB) / $0.15–0.48 (A40) | $218 · $544 · $958 (research belongs on pods, not serverless) |
| **Lambda** (on-demand instances) | A10 24 GB $1.29 · A6000 48 GB $1.09 | **A100 80 GB only in 8× nodes** ($2.79/GPU = $22.32/h); 1× A100 is 40 GB ($1.99) / H100 1× PCIe **$3.29**, SXM $4.29 | per minute | No minimum; **no spend cap** (support forum: monitor manually); weekly invoice | SOC 2 Type II; Lambda-operated DCs; **free egress**; full VM (Docker available) | $0.14–0.43 (A6000) | 80 h A100 40 GB $159 (A100 80 GB only as an 8× node) · n/a · **$658** (PCIe) / $858 (SXM) |
| **Vast.ai** (marketplace) | live snapshot: 4090 min $0.34 / median $0.48 · L40S median $0.60 | A100 SXM4 median $0.80 / H100 SXM min $2.27, median $3.63 · H100 PCIe ~$1.94–2.04 | per second | Prepaid credit; on-demand, interruptible (≥ 50 % cheaper), or reserved; per-host bandwidth (median ~$0.004–0.005/GB) and storage (~$0.27/GB-mo) fees | ⚠ **Untrusted marketplace**: hosts are not independently audited and may be home rigs. Platform is SOC 2 Type II; "**Secure Cloud**" filter = vetted DC partners (ISO 27001 / T3–T4 encouraged, **not required**); median reliability 99.5 %. **Public-license corpus only** | $0.04–0.13 (4090) | $64 · $160 · $726 (H100 SXM median; very volatile) |
| Vast.ai **Secure Cloud** filter | 4090 ~$0.47–0.49 (only 2 offers seen) | A100 80 GB: none seen / H100 SXM $2.27–3.03 | per second | same | vetted DCs, DPA signed with Vast; per-host certs vary | $0.04–0.14 | n/a · n/a · $454–606 |
| **DigitalOcean GPU Droplets** (and Paperspace legacy) | Droplet L40S $1.57 · RTX 6000 Ada 48 GB $1.57 · RTX 4000 Ada 20 GB $0.76. Paperspace: A5000 $1.38, A6000 $1.89 | Droplet: no A100 / H100 $4.41 (1×). Paperspace: A100 80 GB $3.09 / H100 **$5.95** on-demand promo | Droplet: **per second, 5-min minimum**, billed while powered off. Paperspace: hourly + plan fee ($8–39/mo) | Billing alerts (email); Paperspace has account-wide limits; 10–15 TB transfer included on droplets | DO: SOC 2 Type II (known, not re-verified today); full VM | $0.17–0.52 (L40S) | Paperspace $247 · $618 · $1,190; DO $882 (200 h H100) |
| **CoreWeave** | L40S $2.25/GPU (8× node $18/h) · L40 $1.25/GPU | A100 $2.70/GPU (8× $21.60) / H100 $6.16/GPU (8× $49.24); spot 8× A100 $9.65, 8× H100 $19.71 | per hour (on-demand) | **Not self-serve for us:** 8-GPU nodes, Kubernetes (CKS), sales-led onboarding; up to 60 % off with commitments | Strong enterprise posture; **free egress**; object storage $0.015–0.06/GB-mo | $0.24–0.75 | $216 · $540 · $1,232 (and you rent 8 GPUs at a time) |
| **Google Cloud: Cloud Run jobs (GPU)** | L4 $0.672 GPU + 8 vCPU / 32 GiB ≈ **$1.42 all-in**; RTX PRO 6000 96 GB $1.315 GPU | not offered on Cloud Run | per 100 ms (jobs: 1-min minimum) | GPU quota request needed; budgets = **alerts, not hard caps** | Enterprise DPA, region pinning, no training on customer data (Cloud terms); **runs our Docker image as-is** | $0.25–0.79 (L4) | n/a on Cloud Run |
| Google Cloud: **Spot VMs** | g2-standard-8 (L4) **$0.51** spot | a2-ultragpu-1g (A100 80 GB) $3.04 spot / a3-highgpu-1g (H100) $6.62 spot | per second (1-min minimum) | Preemptible at any time; GPU quota request; on-demand prices not captured (JS-rendered page) | as above | $0.09–0.28 | $243 · $608 · $1,324 (spot, so preemptible) |
| **AWS EC2** (g5/g6/g6e, p4de/p5) | g5.2xlarge (A10G) **$1.21** OD / **$0.46–0.60 spot**; g6.2xlarge (L4) $0.98 OD / $0.13 spot (anomalously low today); g6e.2xlarge (L40S) $2.24 OD | p4de.24xlarge 8× A100 80 GB $27.45 ($3.43/GPU, 8× only) / p5.4xlarge **1× H100 $6.88** | per second (60-s minimum, Linux) | New accounts start at **0 G/P vCPU quota** (needs a request); AWS Budgets alerts and **Budget Actions can stop instances**; SageMaker adds a managed-service premium (not priced today) | Strongest compliance (SOC 1/2/3, ISO, HIPAA BAA, DPA); region pinning; internet egress ~$0.09/GB | OD $0.16–0.51; spot $0.08–0.25 | $274 · $686 · $1,376 (OD) |
| **Azure** (NVadsA10 v5, NC A100 v4, NC H100 v5) | NV36ads_A10_v5 (full A10) $3.84 OD / **$0.71 spot** (South Central US) | NC24ads_A100_v4 $3.67 OD / **$0.68 spot** · NC40ads_H100_v5 $6.98 OD / **$1.29 spot** (East US) | per minute (verify) | GPU quota request; budgets are alerts (hard spending limits only on credit-type subscriptions); spot evictable | Enterprise compliance, region pinning | OD $0.51–1.60; spot $0.09–0.30 | OD $294 · $734 · $1,396; **spot $54 · $136 · $258** (if capacity holds) |
| **Together AI** | — (no single-GPU custom containers) | GPU clusters H100 $3.99 on-demand / $1.99 preemptible; dedicated inference H100 $3.99 (promo to 09/30) | hourly | Cluster/inference-oriented; not a job runner for our image | SOC 2 (known); model-serving focus | n/a | 200 h H100 ≈ $798 if a single-GPU slice were available (cluster sizing unverified) |
| **Replicate** | L40S $3.51 · T4 $0.81 | A100 80 GB $5.04 / H100 $5.49 | per second | Private models are billed for **setup + idle + active** time; needs Cog packaging | model-hosting platform; no DPA reviewed | $0.37–1.17 | $403 · $1,008 · $1,098 |
| **Baseten** | L4 (4×16) $0.85 · **A10G (8×32) $1.45** | A100 $4.00 / H100 $6.50 | per minute | Basic plan PAYG; Pro/Enterprise negotiated; needs Truss packaging | **SOC 2 Type II + HIPAA** (pricing page); self-host option | $0.19–0.61 | $320 · $800 · $1,300 |
| **Beam** (beam.cloud) | serverless 4090 $0.69 GPU (**$1.77 all-in** with 2 cores + 16 GiB); machines: A6000 from $0.54, L40S from $0.76 | serverless 80 GB tier $3.50 / machines: A100 80 GB from $1.36, H100 PCIe from $1.83 | per millisecond (serverless) | PAYG; BYO-cloud option (management fee) | Non-root containers; self-host option; compliance not verified today | $0.16–0.49 | serverless $280 · $700 · $700; machines $109 · $272 · $366 |
| **fal** | — (custom deployments: RTX PRO 6000 $2.99 list) | — / H100 $4.50 list ("as low as $1.89" negotiated) | per second (serverless) | **Custom apps via sales** (support@ contact) | Generative-media focus | n/a | 200 h H100 $900 at list |
| **SaladCloud** | RTX 4090 $0.16–0.33 · 3090 $0.09–0.17 (priority tiers; vCPU/RAM included) | none (consumer GPUs only) | per second; cold boot is free | PAYG, no minimum; Low/Lowest tiers preemptible | ⛔ **Consumer home PCs** ("chefs"); hypervisor + encryption; **SOC 2 Type I only**. Not acceptable for owner or user captures | $0.03–0.09 | n/a (no 80 GB GPUs) |
| **TensorDock** (marketplace) | RTX 4090 from $0.35 | A100 SXM4 from $1.80 / H100 SXM5 from $2.25 | per second (balance deducted continuously) | **$5 minimum deposit; servers are deleted when the balance hits $0** (hard cap, destructive) | ⚠ Independent hosts ("converted mining rigs" and T3/4 DCs); KVM VMs; hosts' SSH revoked. **Public-license corpus only** | $0.03–0.10 | $144 · $360 · $450 |

Beyond the table:

- **Container support.** Our image is a plain CUDA Dockerfile (`services/reconstruction/Dockerfile`, CUDA 12.4.1
  cudnn-devel, Ubuntu 22.04).
  - It runs unmodified wherever we get a Docker host with an NVIDIA driver that supports CUDA 12.4: Runpod pods,
    Lambda, Vast, TensorDock, DO, GCP/AWS/Azure VMs, CoreWeave. Every Vast host sampled reports CUDA ≥ 12.2; ≥ 12.4
    is required, so filter on it.
  - **Runpod Serverless** needs a small handler (`runpod.serverless.start`).
  - **Cloud Run jobs** take the image as-is.
  - **Replicate** needs Cog, **Baseten** needs Truss, **Beam** needs its SDK decorator, which is a Modal-like
    rewrite of `modal_app.py`.
  - The Modal-specific parts are `modal.Image.from_registry` + layer splitting, `add_local_dir` code mounts, and the
    `gj-corpus` `modal.Volume`.
- **Egress and storage.**
  - Runpod: no data-transfer fees; network volume $0.07/GB-mo.
  - Lambda and CoreWeave: free egress.
  - Hyperscalers: roughly $0.08–0.12/GB internet egress.
  - A scene is at most a few hundred MB, so egress is noise. Storage for 50 scans is < 50 GB, which is ≤ $4/mo
    anywhere.
- **Cold start.**
  - Serverless platforms (Runpod, Modal, Beam, Baseten, Cloud Run) cold-start in seconds when the image is cached.
    A fresh pull of our multi-GB CUDA image can take minutes, billed on most platforms. Salad does not bill for it.
  - VMs and pods take 1–5 min to boot, plus the pull.
  - For 8–25 min jobs, a cold start is a 5–30 % overhead (est.). Keeping one warm worker is not worth it at our volume.
- **Signup (not tested; from the pages).**
  - Card only: Runpod (prepaid; crypto needs KYC), Vast (prepaid), TensorDock (prepaid, $5), Lambda, DO, Replicate,
    Baseten, Beam, fal, Salad (no free trial).
  - Card plus quota/verification: GCP/AWS/Azure. GPU quota requests can take days for new accounts.
  - Sales-led: CoreWeave.
- **Reliability (reported).**
  - Runpod standard plans have no SLA. Community hosts vary; Secure Cloud is more stable.
  - Lambda H100 capacity often sells out.
  - Vast/TensorDock/Salad hosts can disappear mid-job (Vast median host reliability in the snapshot: 99.5 %).
  - Spot on all three hyperscalers is preemptible (DO spot gives ~2 h notice).
  - Checkpointing splatfacto every N steps makes all of these tolerable.

## 3. Findings

1. **Price is not the problem; the Modal plan structure is.** Modal's per-hour rates are in line with the market.
   The **$20 cap on Starter**, and the **$250/mo Team fee** needed to lift it, is what blocks the corpus runs and
   the Tier 2 month. That fee alone equals **80 A100-hours at Runpod Secure Cloud rates** ($1.59 × 80 = $127) twice
   over.
2. **Runpod Secure Cloud is roughly half of Modal's all-in price** for the research month: $127–318 on A100 80 GB vs
   $250–626 + $250. It has the compliance paperwork we need (SOC 2 Type 2, ISO 27001, DPA, region choice), and its
   prepaid-credit model is a *true hard cap*. It is also already named in AUTH #032.
3. **Corpus reconstruction is cheap everywhere.** Even at Modal prices, 50 scans × 3 runs is ≈ $45/mo. On a Runpod
   Secure A40/4090 it is about $10–30/mo (est.). The per-scene price matters less than having no cap-cliff.
4. **Marketplaces (Vast community, TensorDock, Runpod Community, Salad) are 30–70 % cheaper** but put our data on
   unaudited third-party hosts. **Allowed at most for the open-license stand-in corpus**, never for owner-consented
   corpus captures that show a real home, and never for user scans. My recommendation is to not use them at all
   while the corpus is small, because the savings are single-digit dollars.
5. **Hyperscalers** (AWS/Azure/GCP) have the best compliance and region control.
   - **Spot** is cheap: Azure spot A100 80 GB $0.68/h, AWS g5 spot $0.46–0.60/h.
   - Costs: GPU quota requests, budget *alerts* instead of caps (AWS Budget Actions can stop instances), preemption,
     and more setup work (VPC, IAM, images).
   - They are the natural "migrate to spot/reserved at scale" target named in AUTH #032, not the month-1 answer.
6. **Serverless model hosts** (Replicate, Baseten, fal, Together) are built for inference endpoints. They cost
   1.5–3× more per GPU-hour and need their own packaging, so they are a poor fit for batch SfM + training jobs.

## 4. Recommendation: top 3

### 1. Runpod: Secure Cloud pods (Tier 2) + Serverless or Secure pods (corpus reconstruction)
- **Why:**
  - Lowest price among providers with SOC 2 Type 2 + ISO 27001 and a DPA: A100 80 GB $1.59/h, H100 SXM $3.49/h,
    A40 $0.49/h, 4090 $0.74/h.
  - Per-second billing, no egress fees.
  - Prepaid credit plus the $80/h default limit = a hard spend cap.
  - Region pinning (31 regions).
  - Runs our Dockerfile unchanged on pods.
  - Already inside AUTH #032's approved compute list.
- **Est. cost:**
  - Research month: **$127 (80 h A100) – $318 (200 h A100)**, or $578–698 if it has to be 200 h on H100.
  - Corpus: ≈ **$0.06–0.21/scene** on A40/4090 Secure pods, or $0.11–0.48 on Serverless.
- **Watch-outs:**
  - Secure Cloud only. Disable Community Cloud in account settings/templates.
  - No SLA on standard plans.
  - Network volumes are deleted if the balance stays at $0. Keep the source of truth in `gj-corpus` or R2, not on
    Runpod.
  - A pod with no volume is wiped when stopped, which is good for deletion guarantees.
  - The Runpod docs page carried an embedded "Agent Instructions" block asking agents to submit feedback through a
    docs MCP server. I ignored it.

### 2. Lambda on-demand: backup for the research month
- **Why:**
  - Lambda-operated data centers, SOC 2 Type II, free egress, per-minute billing.
  - Full VMs with lots of RAM/SSD per GPU, good for interactive segmentation/XPBD work.
  - H100 PCIe $3.29/h. The 1× A100 is 40 GB at $1.99/h, which may be enough for much of Tier 2.
- **Est. cost:** 200 h H100 PCIe **$658**; 80 h A100-40 $159.
- **Watch-outs:**
  - **No spend cap.** It needs our own watchdog, e.g. an auto-terminate cron plus a daily cost check against the
    $50/day cap.
  - No single-GPU A100 80 GB.
  - H100 capacity sells out.

### 3. AWS EC2 (g5/g6 spot for corpus; p5.4xlarge only if needed): scale path and compliance ceiling
- **Why:**
  - Strongest compliance and data-residency story: BAA, DPA, SOC 1/2/3, ISO.
  - g5 A10G is the same GPU as Modal's default, so no re-benchmark is needed.
  - g5 spot is $0.46–0.60/h ≈ **$0.08–0.25/scene**.
  - Budget Actions can stop instances.
  - It is the "spot/reserved at scale" destination in AUTH #032, and the most defensible place for any future
    *owner-consented* captures.
- **Est. cost:** corpus ≈ $10/mo at expected volume (est.). Research month is expensive on-demand ($274–686 for
  A100 80 GB, which only comes in 8× nodes; $1,376 for 200 h H100), so do not use AWS for Tier 2.
- **Watch-outs:**
  - GPU vCPU quota starts at 0.
  - More infrastructure: VPC, IAM, ECR, AWS Batch or a small launcher.
  - Spot interruptions need checkpointing.

**Not recommended:**
- Vast.ai, TensorDock, Salad, Runpod Community: untrusted hosts.
- CoreWeave: 8-GPU nodes, sales-led.
- Replicate, Baseten, fal, Together: inference-priced, need repackaging.
- Paperspace: legacy, H100 $5.95.
- Azure spot: cheapest A100/H100 on paper ($0.68/$1.29) but capacity/eviction and quota friction. A reasonable
  hyperscaler alternative to #3 if the Owner already has an Azure tenant.

### Keep Modal?
**Yes, for small jobs.**
- It is integrated: the corpus intake app is deployed there, the `gj-corpus` volume lives there, and M1-PIPE-01's
  adapter targets it.
- It has the best developer loop (layered image, code mounts).
- The $30/mo credit makes the first ~15–40 scans per month effectively free.
- Plan: **Modal stays the default backend up to its Starter cap. Runpod takes overflow corpus runs and all Tier 2
  hours.** Do not buy the $250 Team plan for this.

## 5. Migration path (est. effort 3–5 engineer-days, Builder)

1. **Backend-neutral entry point (0.5–1 day).**
   - Factor the body of `reconstruct()` / `sfm_bench()` in `modal_app.py` into a plain CLI, e.g.
     `python -m reconstruction.run --images <dir|tar|url> --out <dir> --sfm colmap --matcher auto --profile ...`.
   - It emits the same cost sheet, with a `host`/`backend` field and a `rate_per_hour_usd` argument.
   - `modal_app.py` then becomes a thin wrapper, so there is no behavior change on Modal.
2. **Image (0.5 day, plus one ~17 min gsplat build).**
   - `docker build` the existing Dockerfile. The final `modal-skip` section already bakes in `reconstruction/`.
   - Push it to a **private** GHCR package under BlissDirective.
   - Add `9.0` to `TORCH_CUDA_ARCH_LIST` so the same image runs on H100.
   - Pin the CUDA driver floor (≥ 12.4) in the launcher's host filter.
3. **Storage (0.5–1 day).**
   - Stop depending on `modal.Volume` for inputs and outputs. Scene input and results go through signed URLs to the
     private Supabase `environments` bucket, or to R2 (AUTH #032's zero-egress delivery).
   - Tier 2 gets a Runpod network volume in one pinned region, holding **only** the open-license corpus.
   - Corpus copy: `modal volume get gj-corpus /open-video` → upload.
4. **Runpod Serverless handler (1 day).**
   - `services/reconstruction/runpod_handler.py` calls the step 1 CLI; the endpoint uses the private image.
   - In `api/` (M1-PIPE-01), add a `RunpodReconstructor` next to the existing fetch-based Modal adapter behind the
     same port. Select it with `RECON_BACKEND=modal|runpod`.
   - Same retryable/terminal error taxonomy. Keep the **off-site guard terminal**, so a non-corpus scan can never be
     dispatched to any third-party backend.
5. **Tier 2 on Secure pods (0.5 day).**
   - Pod template: private image + network volume + SSH/Jupyter.
   - Idle-shutdown script: stop after 30 min with GPU util < 5 %.
   - Prepaid credit sized to the approved monthly AUTH (e.g. $150–350), so the balance *is* the cap. Tag the spend
     separately for R6.
6. **Validation (0.5 day, ≈ $2).**
   - Re-run the Mip-NeRF 360 room benchmark on Runpod A40 and 4090. This replaces the 4090 speed-factor
     *assumption* with a measurement.
   - Record it in `research/vendors/reconstruction-spike-report.md`.

**Governance before any of this runs:**
- An Owner AUTH to open a Runpod account and fund it. A vendor addition plus a spend line, although AUTH #032
  already names Runpod as approved compute.
- Owner confirmation that Secure-Cloud-only + open-license-corpus-only satisfies SPEC §108.
- Review of Runpod's DPA through its Trust Center.

## 6. Sources (all fetched 2026-09-28, ~8:00–8:10 PM CT)

| Provider | URL | What |
|---|---|---|
| Modal | modal.com/pricing (via `compute-budget-2026-10.md`, fetched 2026-09-28) | A10G/L4/L40S/A100/H100 rates, Starter terms |
| Runpod | https://www.runpod.io/pricing (page says "Updated September 27, 2026") | Pods secure/community, serverless, storage |
| Runpod | https://docs.runpod.io/references/billing-information | per-second billing, prepaid credits, $0-balance stop, $80/h limit, no transfer fees |
| Runpod | https://trust.runpod.io/ ; https://docs.runpod.io/references/security-and-compliance | SOC 2 Type 2, SOC 3, ISO 27001, DPA, Secure vs Community isolation |
| Lambda | https://lambda.ai/pricing | instance prices |
| Lambda | https://docs.lambda.ai/public-cloud/billing/ ; deeptalk.lambda.ai/t/…/4121 | per-minute billing; no spend limit |
| Vast.ai | https://vast.ai/pricing ; public offers API `console.vast.ai/api/v0/bundles` (snapshot of 64 on-demand 1-GPU offers) | per-second billing; live prices, bandwidth/storage fees, reliability |
| Vast.ai | https://vast.ai/compliance ; https://docs.vast.ai/guides/reference/faq/security | SOC 2 Type II platform, Secure Cloud criteria |
| DigitalOcean | https://www.digitalocean.com/pricing/gpu-droplets | droplet prices (effective 2026-08-01), per-second, 5-min minimum, billing alerts |
| Paperspace | https://www.paperspace.com/pricing | A100/H100/A6000 prices, plan fees, billing limits |
| CoreWeave | https://www.coreweave.com/pricing | 8-GPU node prices, spot, free egress |
| Google Cloud | https://cloud.google.com/run/pricing | Cloud Run GPU per-second rates, jobs 1-min minimum |
| Google Cloud | https://cloud.google.com/spot-vms/pricing | g2 / a2-ultragpu / a3-highgpu spot |
| AWS | `b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/…/US East (N. Virginia)/Linux` (on-demand); `website.spot.ec2.aws.a2z.com/spot.js` (spot, us-east-1 / us-west-2) | g5/g6/g6e/p4de/p5 prices |
| Azure | `prices.azure.com/api/retail/prices` (Retail Prices API; East US, South Central US) | NVadsA10 v5, NC A100 v4, NC H100 v5 OD/spot |
| Together | https://www.together.ai/pricing | clusters, dedicated inference |
| Replicate | https://replicate.com/pricing | hardware per-second prices; private-model billing |
| Baseten | https://www.baseten.co/pricing/ ; https://docs.baseten.co/deployment/resources | per-minute instance prices; SOC 2 II/HIPAA |
| Beam | https://www.beam.cloud/pricing | serverless per-second rates; machine rates |
| fal | https://fal.ai/pricing | H100/B200/RTX PRO 6000 list |
| SaladCloud | https://salad.com/pricing ; https://salad.com/security ; https://salad.com/enterprise/ | priority-tier prices; consumer-node security model; SOC 2 Type I |
| TensorDock | https://www.tensordock.com/ (`/pricing` returned 404) | "from" prices, marketplace model, deposit / $0-delete billing |

Not re-verified today, stated from general knowledge and marked as such in the table:
- DO's SOC 2 status.
- Hyperscaler egress rates.
- Azure per-minute billing.
- SageMaker premium.
- GCP on-demand GPU VM prices (the page is JS-rendered and timed out).
