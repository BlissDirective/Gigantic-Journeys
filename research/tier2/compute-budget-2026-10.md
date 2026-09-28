# Monthly compute budget recommendation (M1-RES-01 + reconstruction prototype)

2026-09-28 · gj-operator · **A recommendation, not an authorization.** The spend itself needs the Owner's AUTH
(SPEC §5; M1-RES-01 AT-3). Nothing here changes the Modal spend limit.

Sources: SPEC §5 (Tier 2 charter, R1–R6), `tickets/M1-RES-01.json`, ADR-0005 (addendum 4, AUTH #032: serverless
GPU for the spike and early production), AUTH #031 ($100 one-time spike cap), `governance/AUTHORIZATION_LOG.md`
standing limits ($50/day cap, Tier 2 line $400–1,000/month), `research/vendors/reconstruction-spike-report.md` (M1-CAPT-03
Modal runs, GPU COLMAP vs GLOMAP Mip-NeRF room benchmark, training sweep), `services/reconstruction/OPERATOR_RUNBOOK.md`,
modal.com/pricing (fetched 2026-09-28) and `modal billing rates` / `modal billing summary` (CLI 1.5.5, 2026-09-28).
**Measured** means a number from those runs or Modal's bill; **estimated** means it's my assumption.

## 1. Modal prices (verified 2026-09-28)

modal.com/pricing lists per-second prices, and they match `modal billing rates` for this workspace. Per hour:

| Resource | $/h | All-in $/h (GPU + 8 cores + 32 GiB) |
|---|---|---|
| T4 | 0.59 | — |
| L4 | 0.80 | — |
| **A10G** (the reconstruction default) | **1.10** | 1.73 (the reconstruction jobs reserve 8 cores + 16 GiB) |
| L40S | 1.95 | 2.58 |
| A100 40 GB | 2.10 | 2.73 |
| A100 80 GB | 2.50 | 3.13 |
| H100 | 3.95 | 4.58 |
| H200 / B200 / B300 | 4.54 / 6.25 / 7.10 | — |
| CPU (physical core) | 0.0473 per core | |
| Memory | 0.008 per GiB | |
| Volumes | $0.09/GiB-month, first 1 TiB/month free | |

- Starter plan (this workspace): **$30/month of free compute**, 10-GPU concurrency. Region pinning and
  non-preemptible execution cost 1.15–1.75× the base price. Our functions set neither (`modal_app.py`), so base
  prices apply.
- **Measured spend:** September month-to-date **$7.00 metered, $7.00 covered by credits, $0.00 billed**
  (`modal billing summary`, 2026-09-28). That is all of the M1-CAPT-03 spike so far: about **$93 of the AUTH #031
  $100 cap is left**.
- **Spend limit: not visible to us.** Neither the Modal CLI nor the SDK exposes the workspace budget
  (`Workspace.settings` only has `default-environment` and `image-builder-version`). Operator notes in the spike
  report say a **$20/month** limit (2026-09-26: "about $7.2 of the $20 limit"). The Owner can confirm it in the
  dashboard under Settings → Usage & Billing. I did not change it.

## 2. What the prototype needs

### 2a. Reconstruction prototype (M1-CAPT-03 / M1-PIPE-01; covered by AUTH #031 until the $100 runs out)
- **GPU:** A10G, 8 cores, 16 GiB (measured best $/scan; L40S is 20 % faster but costs 20 % more, spike report).
- **Per scan (measured, public Mip-NeRF 360 room, 311 images at 779×519):** 6.9 min pipeline and **$0.185**
  (runs D1/D2/F1/F2). SfM went 16.2 → 3.0 min with GPU COLMAP; GLOMAP was +$0.02–0.03 per scan and slower. The
  runaway ceiling is **$1.60 per run** (1 h timeout).
- **Per scan on real corpus captures (estimated):** 1–4× the room ($0.19–0.74). Phone video gives more frames at
  higher resolution, and exhaustive matching scales O(n²) up to 500 images.
- **Runs (estimated):** the M0-OWNER-01 day-one corpus is 10 rooms + 5 tabletops (15 scans). On 2026-09-28 it
  landed as 15 open-license stand-in clips in `gj-corpus:/open-video` (`a03639d`); none has been reconstructed
  yet, and several are 8–15 s single-pass or portrait clips (few frames, so likely ≤ 1× the room's cost). SPEC R1
  assumes 30 rooms + 20 tabletops (50 scans). Each scan gets 2–6 runs while tuning. Benchmark/sweep passes
  measured $2.47 and $3.55, so about $3 each.

### 2b. Tier 2 research (M1-RES-01; the SPEC §5 line; blocked until its monthly AUTH)
- **GPU:** SPEC §5 budgets hourly H100/A100. On Modal, the A100 80 GB (all-in $3.13/h) is the default
  recommendation. The H100 ($4.58/h all-in) is only worth it if the segmentation/embedding code needs it.
  **Constraint (measured):** the current gsplat image is not compiled for H100/B200/RTX PRO 6000 (sm_90+), so
  any Tier 2 work that reuses gsplat needs its CUDA arch added first.
- **Per-scan preprocessing target (SPEC R2):** ≤ $0.50 and ≤ 10 min per scan, ideally $0.25. On an A100 80 GB,
  10 min is $0.52 all-in, so R2 effectively means ≤ ~10 min on an A100 80 GB, or a cheaper GPU.
- **Hours (estimated):** 80–200 GPU-hours of interactive development (segmentation → tet embedding → XPBD
  experiments) plus corpus batches of 50 scans × 2–4 runs × ≤ $0.50.

## 3. Low / expected / high per month

| Line | Low | Expected | High | Basis |
|---|---|---|---|---|
| Reconstruction prototype | **$12** (15 scans × 2 runs × $0.19 + 2 sweeps) | **$45** (30 scans × 3 runs × $0.37 + 4 sweeps) | **$246** (50 scans × 6 runs × $0.74 + 8 sweeps) | $0.185/scan measured; multiplier, runs and scan counts estimated |
| Tier 2 research (M1-RES-01) | **$301** (80 h A100 80 GB + 100 scan runs × $0.50) | **$451** (120 h A100 80 GB + 150 runs) | **$1,017** (200 h H100 + 200 runs) | Modal list prices; hours and runs estimated; consistent with the SPEC §5 line of $400–1,000 |
| Storage (corpus volume) | $0 | $0 | $0 | 50 scans are far below the 1 TiB of free volume storage |
| Modal free credit | −$30 | −$30 | −$30 | Starter plan |
| **Total metered** | **$313** | **$496** | **$1,263** | |

The daily $50 cap (SECURITY_CHECKLIST §8.5) still applies: the high case reaches it at about 11 H100-hours in a day.

## 4. Recommendation

1. **Now, until M1-RES-01's AUTH:** set the Modal workspace budget to **$75/month** (the Owner does this; it is
   Owner-only). The $20 limit mentioned in the runbook notes blocks the corpus runs: the expected $45 of
   reconstruction alone exceeds it now that the 15-clip corpus is in `gj-corpus`. $75 covers the expected case plus one
   re-run pass. It stays under the AUTH #031 remainder ($93) and costs about $15–45 billed after the $30 credit.
   When the $100 spike cap is used up, reconstruction needs its own monthly line (expected ~$45/month at corpus
   scale).
2. **M1-RES-01 month 1:** file the spend AUTH at **$500/month** for Tier 2. That covers the expected $451 with
   ~10 % headroom and sits in the low half of SPEC §5's $400–1,000 line. The high case (~$1,000) needs H100-heavy
   work that isn't justified before R1/R2 have any measurements. With that AUTH, set the workspace budget to
   **$575/month** ($500 Tier 2 + $75 reconstruction). Track Tier 2 in its own Modal app or environment so
   R6 (budget discipline, paused within 24 h of the Owner's word) can be measured.
3. **Sequencing:** Tier 2 is still blocked on its monthly AUTH. A day-one corpus now exists (15 open-license clips,
   `a03639d`), but none of it has been reconstructed yet, and Tier 2 segments the reconstructed splats. Reconstruct
   the 15 clips first (expected ≈ $5–15 at 1–2 runs each, inside the AUTH #031 remainder). File the M1-RES-01 AUTH
   once those splats exist. Until then the right Tier 2 spend is $0.
