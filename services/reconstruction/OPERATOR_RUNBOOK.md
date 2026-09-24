# Reconstruction Spike — Operator Runbook (Modal)

`services/reconstruction/OPERATOR_RUNBOOK.md` · 2026-09-24 · For **gj-operator** (Grok Bot). Stands up the Modal GPU host and runs the self-host reconstruction spike (M1-CAPT-03) under the **$100 cap (AUTH #031)** on the **Modal account (AUTH #033)**. Companion: `modal_app.py`, `README.md`, `DATASETS.md`, `Dockerfile`.

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
    --images ./data/mipnerf360/room/images_4 --scan-id smoke \
    --source public --sfm colmap --rate 1.10
```
- `--source public`: only `public` and `corpus` are accepted; `user` is rejected locally before upload and again in the container (ADR-0005 / AUTH #030).
- `--sfm colmap`: GLOMAP is not in the image yet. The image's COLMAP is the Ubuntu 22.04 apt build (3.7, **no CUDA**), so SIFT runs on CPU while the A10G idles — expect SfM to dominate wall time (tens of minutes for ~300 images with exhaustive matching). The function timeout is 1 h.
- `--rate 1.10`: Modal A10G ≈ $0.000306/s ≈ $1.10/hr (plus small CPU/memory charges), so `cost.json` stays close to the bill. Worst case per run ≈ $1.20 (1 h timeout).
- First `modal run` builds the image from `Dockerfile` in Modal's cloud (several minutes, once). The build context is pinned to `services/reconstruction/` and only `reconstruction/` is uploaded.
- Success = a `.spz`/`.sog` splat + `.obj` mesh + `cost.json` land in `./out`.

## Step 5 — Run a corpus room + record cost
```
modal run services/reconstruction/modal_app.py --images ./data/<corpus-room>/images --scan-id room1 --source corpus --rate <gpu $/hr>
```
- Copy the `cost.json` per-scan numbers into `research/vendors/reconstruction-spike-report.md` §2 (GPU time + $/scan).
- **Halt at the cap.** Keep a running total of every run's `cost.json` (and check Settings → Usage & Billing). The Modal workspace spend limit is the real cumulative stop; the in-code `SpendCapError` only fires when a *single* run's estimate would cross a cap, because each run starts a fresh ledger. Near $100, stop and ping the Owner — do not raise the cap (Owner-only).

## Follow-up — faster SfM (CUDA COLMAP / GLOMAP)
Not done yet; propose to the Builder once the smoke test passes. Cheapest paths to GPU SIFT/matching: base the image on (or copy the binaries from) the official CUDA-enabled `colmap/colmap` Docker image, or install a CUDA build of COLMAP from conda-forge. Then set `GJ_COLMAP_CUDA=1` in the Dockerfile (switches SIFT to GPU) and, if GLOMAP is added, use `--sfm glomap`. Record the choice and pins in the spike report.

## Step 6 — Hand outputs to the iOS render leg
The compressed splat (`./out/<scan_id>.spz`) is the input for **M1-UNITY-01** (the iOS Metal render de-risk). Keep splats behind signed URLs when they move to storage (§3.1); never commit raw scan media (§6.1/§6.5).

## References
`agents/grok/roles/gj-operator.md` · `governance/AGENT_GOVERNANCE.md` · SECURITY_CHECKLIST §1/§8 · AUTH #006 (Operator), #031 ($100 spike), #033 (Modal account) · `research/vendors/reconstruction-cost-and-trainer-analysis.md` · `services/reconstruction/{README.md,DATASETS.md,Dockerfile,modal_app.py}`.
