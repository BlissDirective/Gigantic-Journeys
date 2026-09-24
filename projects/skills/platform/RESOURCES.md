# gj-platform — Resources (curated foundation)

Curated, verified starter set for backend/security/orchestration. Expand to the full annotated top-100 in a live pass. All entries real/canonical.

## Supabase / Postgres / RLS
- Supabase — Row Level Security (supabase.com/docs/guides/auth/row-level-security) — policy patterns.
- Supabase — Storage + signed URLs (supabase.com/docs/guides/storage).
- PostgreSQL — RLS docs (postgresql.org/docs → CREATE POLICY).
- Supabase — Auth (Apple/Google sign-in) (supabase.com/docs/guides/auth).

## Durable workflows
- Inngest — docs (inngest.com/docs) — functions, steps, event schemas, `serve`.
- "Durable execution" patterns (Inngest/Temporal blogs) — idempotency, retries, step timeouts.

## Backend / mobile security
- OWASP — Mobile Top 10 (2024) + MASVS (owasp.org) — the §9 mapping.
- OWASP — ASVS (owasp.org) — server-side verification standard.
- Signed-URL / least-privilege patterns (cloud provider docs).

## CDN for large assets & cost
- Cloudflare R2 (developers.cloudflare.com/r2) — zero egress; Backblaze B2 + Bandwidth Alliance (backblaze.com).
- AWS S3 + CloudFront pricing (aws.amazon.com) — the egress cost to avoid.

## Event schema & privacy-by-design
- JSON Schema (json-schema.org) — validation at ingestion.
- Privacy by Design (Cavoukian, 7 principles) — foundational.

## Reference internal
- `api/`, `ADRs/0002-*`, `supabase/`, `data/schemas/`, SECURITY_CHECKLIST.
