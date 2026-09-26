# Reconstruction Spike — Operator Runbook (Modal)

`services/reconstruction/OPERATOR_RUNBOOK.md` · 2026-09-24, SfM speed-up 2026-09-26 · For **gj-operator** (Grok Bot). Stands up the Modal GPU host and runs the self-host reconstruction spike (M1-CAPT-03) under the **$100 cap (AUTH #031)** on the **Modal account (AUTH #033)**. Companion: `modal_app.py`, `README.md`, `DATASETS.md`, `Dockerfile`.

> The VM is only the **control plane** — Modal runs the GPU job in its own cloud, provisions/pulls our image, runs it, tears it down. The VM needs the `modal` CLI + a token + network. **No GPU on the VM.**

## Guardrails (read first)
- **Secrets golden rule:** a token/password/card lives only in (1) GitHub Actions secrets, (2) the VM `~/projects/gigantic-journeys/.env.local`, and (3) the Owner's password manager. **Never in chat, a commit, a ticket, a screenshot, or a log.**
- **Owner-only, never the Bot:** creating the account identity, setting the password, entering the **payment card**, and setting the **spend limit**. The Bot drives the browser *to* those screens and **pings the Owner** to complete them; the Bot never types the Owner's password or card, and never stores the account password.
- **Bot cannot write GitHub secrets** (its fine-grained PAT has no Secrets scope, §8.1). The Bot writes the token to `.env.local`; the **Owner** adds it to GitHub secrets if/when CI needs it.
- **Corpus only.** Smoke-test on the public dataset first; only consented corpus rooms after that. Never real user scans (ADR-0005 / AUTH #030).

## Step 0 — Prerequisites (Operator)
- Repo cloned on the VM; Python 3.11+ (`python3 --version`). Docker is **not** required locally (Modal builds the image remotely from our `Dockerfile`).
- Network egress to `modal.com` (see the environment network policy).

## Step 1 — Create the Modal account (Operator drives, Owner completes)
1. Open a browser on the VM to **`https://modal.com/signup`**.
2. **Ping the Owner with the account-creation screen** (screenshot/handoff). The Owner then, on that screen:
   - completes sign-up (their identity — GitHub/Google SSO or email) and **sets the password**;
   - adds a **payment method**;
   - sets the **workspace budget / spend limit** (Settings → Usage & Billing) to match the **$100 spike cap** (AUTH #031). **This is the real cumulative cap.** The in-code guard (`CostLedger`, $100 / $50-per-day) starts from a fresh ledger on every `modal run`, so it only stops a *single* run whose estimate would cross a cap; it does not add up across runs. Modal budgets are **monthly** and reset each cycle, while the spike cap is one-time: lower the budget after the spike (Starter includes $30/month of compute credit).
3. The account belongs to the Owner. The Bot does **not** retain the password or card.

## Step 2 — Provision + store the API token
1. In the Modal dashboard: **Settings → API Tokens → New Token** (or run `modal token new`, which prints a URL for the Owner to authorize). This yields a **token id** + **token secret** — a *machine* credential (safe for the Bot to handle), distinct from the account password.
2. **Operator** writes it to the VM `.env.local` (never echo it):
   ```
   MODAL_TOKEN_ID=ak-...
   MODAL_TOKEN_SECRET=as-...
   ```
   Confirm `.env.local` is git-ignored (it is; §1.2) and `chmod 600`.
3. **Owner** (not the Bot) adds the same two values to **GitHub Actions secrets** *only if* CI will drive Modal later — the Bot's PAT has no Secrets scope by design (§8.1). For the spike, `.env.local` alone is enough.
4. Credential created → it's logged (this account = AUTH #033; §8.6). Rotate per milestone (§8.1).

## Step 3 — Install + authenticate the Modal CLI (Operator)
From the repo root, in the git-ignored `.venv`:
```
python3 -m venv .venv && .venv/bin/pip install modal
. .venv/bin/activate
# Export ONLY the two Modal values (never `set -a; . ./.env.local`, which would
# export every secret in the file, e.g. GITHUB_TOKEN). Nothing is echoed.
export MODAL_TOKEN_ID="$(grep -E '^MODAL_TOKEN_ID=' .env.local | cut -d= -f2-)"
export MODAL_TOKEN_SECRET="$(grep -E '^MODAL_TOKEN_SECRET=' .env.local | cut -d= -f2-)"
modal app list >/dev/null && echo "modal auth ok"
```
The Modal CLI reads `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` from the environment, so neither `modal token set` nor `~/.modal.toml` is needed — no browser on the VM.

## Step 4 — Smoke test on a public dataset (no corpus, no privacy risk)
Mip-NeRF 360, scene **`room`** (indoor), the 4x-downsampled **`images_4`** set (smaller upload, faster CPU SfM, cheaper). The archive is ~12.5 GB (~25 GB with extraction); `data/mipnerf360/` and `out/` are git-ignored.
```
PYTHONPATH=services/reconstruction python3 -c "from pathlib import Path; from reconstruction.fetch_dataset import fetch; fetch('mipnerf360', Path('./data/mipnerf360'))"
modal run services/reconstruction/modal_app.py \
    --images ./data/mipnerf360/room/images_4 --scan-id smoke --source public --rate 1.10
```
- `--source public`: only `public` and `corpus` are accepted; `user` is rejected locally before upload and again in the container (ADR-0005 / AUTH #030).
- **SfM defaults (2026-09-26):** CUDA COLMAP 4.1.1 runs GPU SIFT extraction, then GPU matching with `--matcher auto`, then the **incremental** `mapper`.
  - `--matcher auto` uses **exhaustive** matching for captures of up to 500 images. Beyond 500 it switches to **sequential** matching: 15-frame overlap, quadratic overlap, and vocab-tree loop detection every 10 frames.
  - On the 311-image room, SfM takes about 3 min (it was about 16 min on CPU COLMAP) and the whole pipeline about 9.5 min, at baseline splat quality.
  - Selectable alternatives:
    - `--sfm glomap`: the GLOMAP global mapper (`colmap view_graph_calibrator` + `colmap global_mapper`; GLOMAP ships inside COLMAP since 4.0). On this scene it was about 10-60 s slower and about 0.15 dB lower PSNR. Re-try it on large captures (1000+ frames), where global SfM is expected to win.
    - `--matcher sequential`: linear in frame count, for long ordered captures. On the room it saved about 30 s, but its quality was less stable: PSNR 30.1-31.1 dB over 3 runs, against 31.3 dB for exhaustive in 2 of 2 runs.
    - `--matcher vocab_tree`: for large unordered sets.
    - `--no-gpu-features`: CPU SIFT. Diagnostic only; slow.
- **SfM-only sweep** (no training; about $0.46 on the room): `modal run services/reconstruction/modal_app.py --images <dir> --bench --out ./out/bench` runs every matcher × mapper and writes `sfm-bench.json` (step times, registered images, points, mean reprojection error). Use `--matchers` / `--mappers` to narrow it.
- `--rate 1.10`: the A10G $/hr. `cost.json` now prices **GPU + CPU + memory** the way Modal bills them. CPU and memory are billed per second as `max(reserved, used)`, and a background meter samples the container's cgroup counters. `usd` is the full total; `gpu_usd` / `cpu_usd` / `memory_usd` break it down, and `usage` shows the basis. The function reserves 8 cores (hard limit 8, so a CPU-heavy step can't burst onto the bill) and 16 GiB. The 2026-09-26 runs matched Modal's metered bill to within about 2%. Expect about **$0.26 per room**. The 1 h timeout caps a runaway run at about $1.60.
- `cost.json` also records `stage_seconds` (sfm / train / compress / mesh), `sfm` (step times, registered images, reprojection error), and `quality`: PSNR / SSIM / LPIPS from `ns-eval` on the held-out views (every 8th image). One rendered eval view (ground truth | render) lands as `<scan_id>-eval-view.jpg` for a visual check.
- **Image builds are layered.** Each `# modal-layer:` section of the `Dockerfile` (base, torch, gsplat, nerfstudio, colmap) is its own cached Modal layer. The `reconstruction/` package is mounted at container start, not baked in.
  - A code edit triggers **no rebuild**.
  - A COLMAP-layer edit rebuilds in about 1 min.
  - Only base/torch/gsplat edits pay the ~17 min gsplat compile.
  - Comment-only Dockerfile edits never rebuild.
  - Image builds are billed as CPU time: about $0.13 for a full build.
- Success = a `.spz`/`.sog` splat + `.obj` mesh + `cost.json` (+ eval view) land in `./out`.

## Step 5 — Run a corpus room + record cost
```
modal run services/reconstruction/modal_app.py --images ./data/<corpus-room>/images --scan-id room1 --source corpus --rate <gpu $/hr>
```
- Copy the `cost.json` per-scan numbers into `research/vendors/reconstruction-spike-report.md` §2 (stage times, full $/scan, PSNR/SSIM).
- **Check spend before every run:** `modal billing summary` (month to date) and `modal billing report --for today --show-resources` (per app, per resource). These read-only commands work with the Operator token.
- **Halt at the cap.** Keep a running total of every run's `cost.json` and check the billing summary. The Modal workspace spend limit is the real cumulative stop. The in-code `SpendCapError` only fires when a *single* run's estimate would cross a cap, because each run starts a fresh ledger. Near the limit, stop and ping the Owner. Do not raise the cap (Owner-only).

## SfM notes (CUDA COLMAP 4.1.1, conda-forge)
- Installed with micromamba into `/opt/colmap` (appended to `PATH`).
- Two conda-forge quirks are handled in the `Dockerfile`:
  1. `openimageio=3.1` must be listed explicitly. The colmap 4.1.x builds link it without declaring it.
  2. `CONDA_OVERRIDE_ARCHSPEC=x86_64_v3` must be set. Otherwise the solver picks AVX-512 builds for Modal's builder CPU, and `colmap` dies with **SIGILL** on GPU hosts without AVX-512. This happened once on 2026-09-26.
- The vocabulary tree used for loop detection is baked into the image (sha256-pinned).
- Headless: the CUDA SIFT path needs no display or OpenGL.

## Step 6 — Hand outputs to the iOS render leg
The compressed splat (`./out/<scan_id>.spz`) is the input for **M1-UNITY-01** (the iOS Metal render de-risk). Keep splats behind signed URLs when they move to storage (§3.1); never commit raw scan media (§6.1/§6.5).

## References
`agents/grok/roles/gj-operator.md` · `governance/AGENT_GOVERNANCE.md` · SECURITY_CHECKLIST §1/§8 · AUTH #006 (Operator), #031 ($100 spike), #033 (Modal account) · `research/vendors/reconstruction-cost-and-trainer-analysis.md` · `services/reconstruction/{README.md,DATASETS.md,Dockerfile,modal_app.py}`.
