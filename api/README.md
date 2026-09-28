# `api/` — durable pipeline (Inngest)

Owner: gj-platform. Tickets: **M0-PIPE-01** (skeleton), **M1-PIPE-01** (real steps).

The durable workflow that turns a submitted scan into a playable, packaged environment. M0-PIPE-01 landed a **skeleton** (four logged stubs). **M1-PIPE-01** makes the **reconstruct** step real — it runs the self-host Gaussian-splat reconstruction (Modal, ADR-0005), stores the splat + collision mesh (+ thumbnail) in the private `environments` bucket, and records the asset pointers + counts + status on the `environments` row. `scenegraph` and `journey` stay honest stubs until the M1-DATA-01 schema freeze and the M1-SCEN tickets land; they slot in behind the same signature.

## The pipeline
Event **`scan.submitted`** → function **`journey/pipeline`** with four ordered steps:

`reconstruct` (real) → `scenegraph` (stub) → `journey` (stub) → `package`

Each `step.run(...)` is memoized by Inngest, so a thrown error retries that step (resuming, not restarting). Steps are idempotent — the recorder dedupes status transitions by `scanId + step`, and the environments row is updated in place (upsert-style PATCH by id). Every external call site has an explicit timeout budget in `src/types.ts` (`TIMEOUTS_MS`), enforced with an `AbortSignal` in `services.withTimeout`.

**Error classification (M1-PIPE-01).** `src/errors.ts` splits failures into **retryable** (a vendor 5xx/429/408, a network blip, a hit timeout) and **terminal** (a bad input or a policy violation). The Inngest wrapper turns a terminal error into a `NonRetriableError` (Inngest stops retrying and the row goes `failed`); a retryable error propagates so Inngest retries the memoized step. The **off-site guard** (`assertOffsiteAllowed`) is terminal: a real `user` scan is never dispatched to off-site compute (ADR-0005 / AUTH #030) — defence in depth alongside the container-side guard in `reconstruction/models.py`.

**Real vs fake.** `src/deps.ts` builds the pipeline's services from the environment: when `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` **and** `MODAL_RECONSTRUCT_URL` are all set, it uses the real Supabase + Modal adapters; otherwise in-memory fakes, so local dev, tests, and CI function-discovery run with no secrets and no live services.

## Layout
- `src/types.ts` — event, status, result types (incl. `ScanSubmittedData` with `userId`/`environmentId`/`source`, and `EnvironmentStatus`) + `TIMEOUTS_MS`.
- `src/errors.ts` — `RetryableError` / `TerminalError` / `SourceNotAllowedError`, `isRetryable`, `httpError`, `assertOffsiteAllowed`.
- `src/services.ts` — the `ReconstructionService` / `ObjectStorage` / `EnvironmentStore` ports, `objectPaths`, `withTimeout`.
- `src/fakes.ts` — in-memory fakes for the three ports (test + no-creds fallback).
- `src/adapters.supabase.ts` — service-role Storage upload + `environments` PATCH via `fetch` (no new dependency).
- `src/adapters.modal.ts` — the Modal web-endpoint reconstruction client (base64 asset contract; signed-URL handoff is the scale-up, M1-CAPT-02).
- `src/deps.ts` — builds real adapters or fakes from the environment.
- `src/recorder.ts` — `Recorder` interface + `InMemoryRecorder`.
- `src/pipeline.ts` — the steps (reconstruct real; scenegraph/journey stubs), the injectable `PipelineStages`/`PipelineDeps`, and `runPipeline`.
- `src/inngest/client.ts` — the typed Inngest client.
- `src/inngest/functions.ts` — the `journey/pipeline` durable function (terminal→NonRetriable, row→failed).
- `src/server.ts` — a local-dev serve endpoint (`/api/inngest`).
- `src/pipeline.test.ts` — ordering, idempotency, retry-propagation, timeout tests.
- `src/services.test.ts` — reconstruct persistence, error classification, the off-site guard, `withTimeout`, and the Modal + Supabase adapters (stubbed `fetch`).

## Scripts
```bash
npm install        # generates package-lock.json (committed)
npm run lint       # eslint (flat config, typescript-eslint)
npm run typecheck  # tsc --noEmit (strict)
npm test           # node --test via tsx (all src/**/*.test.ts)
npm run dev        # tsx src/server.ts  (serve on http://localhost:3000/api/inngest)
```
For the full local loop: `npm run dev` in one shell, then `npx inngest-cli@latest dev -u http://localhost:3000/api/inngest` in another, and send a `scan.submitted` event (with `scanId`, `mode`, `environmentId`, `userId`, `source`) from the Inngest dev UI.

## Secrets
Names only live in `.env.example`; real values live in the Operator VM `.env.local` (staging) and CI secrets, never in the repo (SECURITY_CHECKLIST §1). Keys this project reads: `INNGEST_EVENT_KEY`, `INNGEST_SIGNING_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `ENVIRONMENTS_BUCKET` (optional), `MODAL_RECONSTRUCT_URL`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`.

## Remaining for M1-PIPE-01 / hand-off to M1-CAPT-02
- **Expose the Modal web endpoint** (Operator, M1-CAPT-02): wrap `reconstruction/modal_app.py`'s `reconstruct()` in a `@modal.web_endpoint` with a `Modal-Key`/`Modal-Secret` proxy-auth token, returning the response shape `adapters.modal.ts` expects. Deploy `environment-urls` to staging (needs a Supabase access token).
- **scenegraph / journey real steps** — blocked on M1-DATA-01 (schema freeze) + the M1-SCEN tickets.
- **Per-job cost cap** ($50/day halt) and the corpus end-to-end run are **M1-CAPT-02** (this pipeline records `cost_usd` per run; the cap-halt lives with the capture→reconstruction wiring).
- **Retryable-exhaustion sweep** — an Inngest `onFailure` that also reaps stuck `processing` rows.

## Deploy — still gated
There is **no Vercel deploy in this ticket.** Deploying this workflow uses the **Vercel (#012)** and **Inngest (#013)** accounts; production keys are CI-only. Runs locally / against staging until then.
