# M0-PIPE-01 — evidence

**2026-09-23 · Builder.** Local checks mirroring CI's `lint.yml` TypeScript job (`npm ci --ignore-scripts` → lint → typecheck → test → audit), run from `api/`.

| Check | Command | Result |
|---|---|---|
| Lint | `npm run lint` (eslint 9 flat config + typescript-eslint) | clean |
| Typecheck | `npm run typecheck` (`tsc --noEmit`, strict + noUncheckedIndexedAccess) | clean |
| Tests | `npm test` (`node --test` via tsx) | 4/4 pass |
| Audit | `npm audit --audit-level=high` | 0 vulnerabilities |
| Lockfile | `package-lock.json` committed | yes |
| Secrets | `.env.example` = PLACEHOLDER names only | no secrets committed |

Tests cover: step ordering (reconstruct → scenegraph → journey → package), idempotency (a re-run adds no duplicate transitions), retry propagation (a thrown step error rejects so Inngest retries), and the per-step timeout constants.

**Deploy: none (AT-6).** Deploying this workflow is blocked on the Vercel (#012) and Inngest (#013) account AUTHs; production keys are CI-only. Local loop: `npm run dev` + `npx inngest-cli@latest dev -u http://localhost:3000/api/inngest` (a live dev-server run log is a suggested extra to attach when the Owner runs it).
