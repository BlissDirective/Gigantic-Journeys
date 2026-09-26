// supabase/functions/environment-urls/index.ts
//
// Signed-URL issuer for environment assets (M1-CAPT-02 / M1-PIPE-01).
//
// The client never touches storage directly. It calls this edge function, which
//   1) checks the caller's auth (their JWT) and, via RLS on `environments`, that
//      they may access the requested environment (owner, or published + cleared);
//   2) mints short-lived (<=15 min) signed URLs with the service-role key.
// Direct storage URLs are never exposed; the CDN forwards the signature
// (SPEC §3; SECURITY_CHECKLIST §3.1-§3.3). Requires the migration
// 20260926120000_m1_environments_staging.sql (AUTH #034) applied.
//
// The reconstruction pipeline (Modal/Inngest) writes assets with the service-role
// key directly (it bypasses RLS server-side); it does not need this function. The
// `upload` action here is the owner-scoped client path (e.g. replacing a thumbnail).
//
// Deploy: `supabase functions deploy environment-urls` (verify_jwt stays on).
// Env (auto-injected by the Supabase edge runtime): SUPABASE_URL,
// SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const TTL_SECONDS = 900; // hard cap: 15 minutes (SECURITY_CHECKLIST §3.1)
const BUCKET = "environments";
const ASSET_KEYS = ["splat_object", "mesh_object", "thumbnail_object"] as const;

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

// Permissive for now (native app uses bearer tokens, not cookies). Restrict the
// origin once the web surface exists.
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...CORS, "content-type": "application/json" },
  });
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);

  const authHeader = req.headers.get("Authorization") ?? "";
  if (!authHeader.startsWith("Bearer ")) {
    return json({ error: "missing bearer token" }, 401);
  }

  let payload: { environment_id?: string; action?: string };
  try {
    payload = await req.json();
  } catch {
    return json({ error: "invalid json body" }, 400);
  }
  const environmentId = payload.environment_id;
  const action = payload.action ?? "download";
  if (!environmentId) return json({ error: "environment_id is required" }, 400);
  if (action !== "download" && action !== "upload") {
    return json({ error: "action must be 'download' or 'upload'" }, 400);
  }

  // Caller-scoped client: RLS decides which rows this user can see.
  const asCaller = createClient(SUPABASE_URL, ANON_KEY, {
    global: { headers: { Authorization: authHeader } },
  });
  const { data: userData, error: userErr } = await asCaller.auth.getUser();
  if (userErr || !userData?.user) return json({ error: "unauthorized" }, 401);
  const uid = userData.user.id;

  // RLS returns the row only if the caller owns it or it is published + cleared.
  const { data: env, error: envErr } = await asCaller
    .from("environments")
    .select(
      "id, user_id, status, moderation_state, splat_object, mesh_object, thumbnail_object",
    )
    .eq("id", environmentId)
    .maybeSingle();
  if (envErr) return json({ error: "lookup failed" }, 500);
  if (!env) return json({ error: "not found" }, 404); // hidden by RLS or absent

  // Upload is owner-only; download is already gated to owner-or-published by RLS.
  if (action === "upload" && env.user_id !== uid) {
    return json({ error: "forbidden" }, 403);
  }

  // Service-role client signs the URLs; the key never leaves the server.
  const asService = createClient(SUPABASE_URL, SERVICE_ROLE_KEY);
  const store = asService.storage.from(BUCKET);
  const record = env as Record<string, string | null>;
  const urls: Record<string, string> = {};

  for (const key of ASSET_KEYS) {
    const path = record[key];
    if (!path) continue;
    if (action === "download") {
      const { data, error } = await store.createSignedUrl(path, TTL_SECONDS);
      if (error || !data) return json({ error: `sign failed for ${key}` }, 500);
      urls[key] = data.signedUrl;
    } else {
      const { data, error } = await store.createSignedUploadUrl(path);
      if (error || !data) {
        return json({ error: `upload-sign failed for ${key}` }, 500);
      }
      urls[key] = data.signedUrl;
    }
  }

  return json({
    environment_id: environmentId,
    action,
    ttl_seconds: action === "download" ? TTL_SECONDS : null,
    urls,
  });
});
