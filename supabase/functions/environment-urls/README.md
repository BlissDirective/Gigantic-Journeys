# `environment-urls` edge function

Issues **short-lived (≤15 min) signed URLs** for environment assets so the client never touches storage directly (SPEC §3; SECURITY_CHECKLIST §3.1–§3.3). Part of M1-CAPT-02 / M1-PIPE-01. Requires the `environments` table + private `environments` bucket from `supabase/migrations/20260926120000_m1_environments_staging.sql` (AUTH #034).

## Contract
`POST` with a Supabase user JWT in `Authorization: Bearer <jwt>` and JSON body:
```json
{ "environment_id": "<uuid>", "action": "download" }
```
- **`download`** (default) — returns signed GET URLs (TTL 900 s) for the environment's `splat_object`, `mesh_object`, `thumbnail_object`. Allowed for the **owner** or any caller when the environment is **published AND moderation-cleared** — enforced by RLS on `environments`, not by this function.
- **`upload`** — owner-only signed PUT URLs for (re)placing those objects (e.g. a new thumbnail).

Response:
```json
{ "environment_id": "<uuid>", "action": "download", "ttl_seconds": 900,
  "urls": { "splat_object": "https://…", "mesh_object": "https://…", "thumbnail_object": "https://…" } }
```

## Why it's safe
- **Authz first:** the caller-scoped client (their JWT + anon key) reads the row through RLS, so a caller only ever gets URLs for a row they may see. The service-role key is used **only to sign**, never handed to the client.
- **No direct storage exposure:** the `environments` bucket is private; there is no public read policy. Delivery is only these signed URLs (≤15 min), with the CDN forwarding the signature.
- **No secrets in the repo:** `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` are auto-injected by the Supabase edge runtime (SECURITY_CHECKLIST §1, §2.3).

## Who writes the assets
The reconstruction pipeline (Modal/Inngest) writes splat/mesh/thumbnail with the **service-role key directly** (it bypasses RLS server-side) and sets the object paths on the `environments` row — it does not call this function. The raw *scan* upload (capture bundle) is a separate bucket/flow (M1-CAPT-01).

## Deploy & test
```bash
supabase functions deploy environment-urls        # verify_jwt stays ON
# local:
supabase functions serve environment-urls
curl -sS -X POST http://localhost:54321/functions/v1/environment-urls \
  -H "Authorization: Bearer $USER_JWT" -H "content-type: application/json" \
  -d '{"environment_id":"<uuid>","action":"download"}'
```

## Follow-ups
- Per-caller rate limiting (abuse), and tightening CORS to the app origin once a web surface exists.
- A companion `scans` bucket + upload function for the raw capture bundle (M1-CAPT-01).
