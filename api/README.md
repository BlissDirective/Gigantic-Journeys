# `api/` — durable pipeline (Inngest)

Owner: gj-platform. Ticket: **M0-PIPE-01**.

The durable workflow that turns a submitted scan into a playable, packaged environment. In M0 it is a **skeleton**: one Inngest function whose four steps are logged stubs that record status transitions and return typed results. M1 fills each step with the real service call.

## The pipeline
Event **`scan.submitted`** → function **`journey/pipeline`** with four ordered steps:

`reconstruct` → `scenegraph` → `journey` → `package`

Each `step.run(...)` is memoized by Inngest, so a thrown error retries that step (resuming, not restarting). Steps are idempotent — the recorder dedupes status transitions by `scanId + step`, so replaying the same event adds no duplicates. Every step has an explicit timeout budget in `src/types.ts` (`TIMEOUTS_MS`).

## Layout
- `src/types.ts` — event, status, result types + `TIMEOUTS_MS`.
- `src/recorder.ts` — `Recorder` interface + `InMemoryRecorder` (M1 → Supabase-backed).
- `src/pipeline.ts` — the four step stubs, the injectable `PipelineStages`, and `runPipeline`.
- `src/inngest/client.ts` — the typed Inngest client.
- `src/inngest/functions.ts` — the `journey/pipeline` durable function.
- `src/server.ts` — a local-dev serve endpoint (`/api/inngest`).
- `src/pipeline.test.ts` — ordering, idempotency, retry-propagation, timeout tests.

## Scripts
```bash
npm install        # generates package-lock.json (committed)
npm run lint       # eslint (flat config, typescript-eslint)
npm run typecheck  # tsc --noEmit (strict)
npm test           # node --test via tsx
npm run dev        # tsx src/server.ts  (serve on http://localhost:3000/api/inngest)
```
For the full local loop: `npm run dev` in one shell, then `npx inngest-cli@latest dev -u http://localhost:3000/api/inngest` in another, and send a `scan.submitted` event from the Inngest dev UI.

## Secrets
Names only live in `.env.example`; real values live in the Operator VM `.env.local` (staging) and CI secrets, never in the repo (SECURITY_CHECKLIST §1). Keys this project reads: `INNGEST_EVENT_KEY`, `INNGEST_SIGNING_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`.

## Deploy — BLOCKED in M0 (AT-6)
There is **no Vercel deploy in this ticket.** Deploying this workflow waits on the **Vercel account AUTH (#012)** and the **Inngest account AUTH (#013)**; production keys are CI-only. Until then this runs locally only.
