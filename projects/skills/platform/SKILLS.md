# gj-platform — Working Handbook

Remit: backend — Supabase (auth, Postgres+RLS, storage), Inngest durable workflows, the API layer, signed-URL delivery, and event schemas. Re-read at session start; update when you learn something. Authored 2026-09-24.

## GJ context
- Architecture: ADR-0002. API skeleton `api/` (Inngest durable workflow, M0-PIPE-01, merged). Pipeline: scan.submitted → reconstruct → scenegraph → journey → package.
- Security is the merge gate here (SECURITY_CHECKLIST §2/§3): RLS on every table, signed URLs for all media, service-role only server-side.

## Principles
- **RLS on every table, in the same migration** that creates it (`enable row level security` + at least one policy); `supabase/scripts/check_rls.py` fails CI otherwise (§2.1). Patterns: owner-only (`user_id = auth.uid()`), published-read (published AND moderation-cleared), service-role-only.
- **Client uses only the anon key.** The service-role key is server-side only (Inngest/edge). No vendor keys in the binary (§9.1).
- **Signed URLs, ≤15 min TTL, issued after an authz check** for packages/splats/meshes/thumbnails (§3). Deep links resolve to an authz check, never to storage. CDN forwards the signature.
- **Zero-egress delivery.** Prefer Cloudflare R2 / Backblaze B2 (Bandwidth Alliance) — egress is the cost that scales with success (reconstruction analysis).
- **Schemas validated at ingestion** (telemetry, corrections, ratings, packages) with size/type limits (§9.4).
- **Cost caps.** Vendor/GPU keys carry per-key daily caps; the pipeline halts at $50/day (§8.5). Reconstruction spike cap $100 (AUTH #031) is enforced in `services/reconstruction/cost.py`.

## Techniques
- Inngest v3 (TS SDK): `Inngest`, `EventSchemas().fromRecord`, `createFunction`, `step.run`, `serve` from `inngest/node`. Idempotent steps + per-step timeouts (see `api/src/`).
- Supabase Storage: private buckets by default; owner id in the object path; bucket policies reviewed like table policies (§2.4).
- Migrations that create tables cite `APPROVED #n` (schema changes are AUTH-gated, §2.5).

## Pitfalls
- Table without RLS/policy → CI fail (and a real security hole).
- Exposing a direct storage URL or a >15 min TTL → §3 violation.
- Putting a service-role/vendor key anywhere client-reachable or in git.
- Adding a heavy `requirements.txt` that breaks the CI pip-audit (keep GPU deps in the Dockerfile).

## Checklist (pre-merge)
RLS + policy per new table ✓ · anon key client-only ✓ · signed URLs ≤15 min ✓ · schema validation at ingestion ✓ · cost cap wired ✓ · no secrets ✓ · schema change cites AUTH ✓.

## Pointers
`api/` · `ADRs/0002-*` · `supabase/` · SECURITY_CHECKLIST §2/§3/§8/§9 · `data/schemas/` · tickets M0-PIPE-01, M1-PIPE-01, M1-CAPT-02.
