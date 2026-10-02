# Experiment B (offline clip augmentation): status report

**M2-RES-01 / Experiment B · 2026-10-02 · gj-operator (Grok Bot) · NOT RUN: blocked on inputs and on spend
beyond the cash caps.** Spec: `research/tier2/experiment-b-run-spec.md`. No GPU was used and nothing was spent.

## 1. Compute check (done first, as the spec requires)

The spec sizes one augmentation round at **"a few GPU-days"** (§4) under the Tier-2 line (AUTH #040,
$500/month) on Runpod (#039), with Modal as the fallback. Reading "a few" as 2–4 GPU-days (48–96 GPU-hours):

| Host (list price) | 2 GPU-days | 3 GPU-days | 4 GPU-days |
|---|---|---|---|
| Runpod Secure RTX 4090 ($0.74/h) | $36 | $53 | $71 |
| Runpod Secure RTX A6000 ($0.53/h) | $25 | $38 | $51 |
| Modal A10G all-in ($1.73/h) | $83 | $125 | $166 |
| Modal A100 80 GB all-in ($3.13/h) | $150 | $225 | $300 |

Add ~10–20 % for setup, failed seeds and re-runs.

**Verdict: it fits the authorization but not the money actually available.**
- AUTH #040 ($500/month) covers it.
- The Runpod prepaid balance is **$48.57** with auto-pay off, which makes it a hard cap. That balance is also
  the reconstruction overflow budget. The expected round (3 GPU-days on a 4090, ≈ $53–64) exceeds it, and
  even the low case would use most of it.
- Modal's workspace limit is **$20/month**, with $13.17 left in October after the M1-CAPT-03 pass. That is
  far below any case above.
- Running a round therefore needs **new money from the Owner**: a Runpod top-up of about **$75–100** per
  round, or a higher Modal limit. Per the instruction, I stopped at the estimate.

## 2. Inputs: none of the four are ready

Even with the money, the experiment cannot start yet:

| Spec input (§1) | State on 2026-10-02 | Blocking ticket |
|---|---|---|
| Seed clip DB: the ~110-clip Bible §11 whitelist on the GJ skeleton | Not built. There are 0 FBX clips in `unity/Assets`. | M1-MOVE-01 (open) |
| The Owner's Rokoko Vision / Move.ai captures of the P0 verbs | None captured | Owner action (M0-OWNER-01 is open; the open-video clips are environment stand-ins, not motion) |
| Corpus `traversal_graph` / `environment_spec` per room (the demand grid) | Not generated. The 15 corpus reconstructions exist (M1-CAPT-03), but video SfM has **no metric scale**, so `distance_A` / `rise_A` cannot be computed until a scale source exists (a capture-bundle metric scale from M1-CAPT-01, or a manual scale reference). After that, the M1-SCEN chain runs on CPU at $0. | M1-CAPT-01, M1-SCEN-01/02 |
| A motion generator (Track 1 kinematic VAE/diffusion, Track 2 PARC-style RL) | No code or model in the repo. Choosing one is a research/Builder task, and any licensed model would need an IP check (spec §6). | M2-RES-01 |

## 3. Coverage delta vs the go/no-go threshold

- Go threshold (spec §0): **≥ 0.80** of demanded cells covered, **≥ 70 %** of the P0 baseline gap cells
  closed, DB ≤ 60 MB, and no quality regression.
- **Measured delta: none.** No augmentation ran.
- The only graph available is the frozen desk-tabletop fixture
  (`data/schemas/environment/fixtures/valid/traversal_graph.desk-tabletop.json`). Running
  `python services/traversal/motion_coverage.py` on it (stdlib, $0) gives **12 demanded cells**:
  - climb-up ×3, stud-climb ×2, controlled-drop, grapple-ascend, mantle, precision-jump, run,
    running-jump, walk.
  - Against today's clip inventory (empty), coverage is **0 / 12 = 0.00**, and all 12 cells are gaps.
- So the engine and the go/no-go arithmetic work end to end. The baseline is simply empty until
  M1-MOVE-01 builds the clip DB.

## 4. What unblocks it, in order

1. **M1-MOVE-01** builds the ~110-clip DB. This is the baseline inventory, $0.
2. The Owner captures the P0 verbs (Rokoko Vision / Move.ai, both free tier under AUTH #001).
3. A metric scale for the corpus. Then run M1-SCEN-01→04 on the corpus collision meshes to get the real
   demand grid ($0, CPU).
4. Pick the generator. The Owner then funds one round: a Runpod top-up of ≈ $75–100 (4090,
   3 GPU-days + margin), or a higher Modal limit.
5. Run spec §2 steps 1–6. Write the before/after coverage, gaps closed, DB MB and quality into this file.
