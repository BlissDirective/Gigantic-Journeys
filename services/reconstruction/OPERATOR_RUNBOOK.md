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
   - sets a **spend limit** (Settings → Usage/Billing) as a hard backstop that matches the **$100 spike cap** (AUTH #031). The pipeline also self-halts at $100 / $50-per-day in code.
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
```
pip install modal
# token auth is picked up from MODAL_TOKEN_ID / MODAL_TOKEN_SECRET in the env
python -c "import modal; print('modal ok')"
```
Load `.env.local` into the shell env (e.g. `set -a; . ./.env.local; set +a`) so the CLI sees the token — no browser needed on the VM.

## Step 4 — Smoke test on a public dataset (no corpus, no privacy risk)
```
python -c "from pathlib import Path; from reconstruction.fetch_dataset import fetch; fetch('mipnerf360', Path('./data/mipnerf360'))"
modal run services/reconstruction/modal_app.py --images ./data/mipnerf360/<scene>/images --scan-id smoke --rate 1.0
```
First `modal run` builds the image from `Dockerfile` in Modal's cloud (a few minutes, once). Success = a `.spz`/`.sog` splat + `.obj` mesh + `cost.json` land in `./out`.

## Step 5 — Run a corpus room + record cost
```
modal run services/reconstruction/modal_app.py --images ./data/<corpus-room>/images --scan-id room1 --source corpus --rate <gpu $/hr>
```
- Copy the `cost.json` per-scan numbers into `research/vendors/reconstruction-spike-report.md` §2 (GPU time + $/scan).
- **Halt at the cap.** If `cost.json` shows the spike total nearing $100, stop and ping the Owner — do not raise the cap (Owner-only). The pipeline raises `SpendCapError` before a run that would cross it.

## Step 6 — Hand outputs to the iOS render leg
The compressed splat (`./out/<scan_id>.spz`) is the input for **M1-UNITY-01** (the iOS Metal render de-risk). Keep splats behind signed URLs when they move to storage (§3.1); never commit raw scan media (§6.1/§6.5).

## References
`agents/grok/roles/gj-operator.md` · `governance/AGENT_GOVERNANCE.md` · SECURITY_CHECKLIST §1/§8 · AUTH #006 (Operator), #031 ($100 spike), #033 (Modal account) · `research/vendors/reconstruction-cost-and-trainer-analysis.md` · `services/reconstruction/{README.md,DATASETS.md,Dockerfile,modal_app.py}`.
