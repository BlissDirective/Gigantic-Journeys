// Supabase adapters (service role): the private 'environments' bucket and the
// public.environments row. HTTP via built-in fetch — no new dependency, so the
// pip/npm audit surface is unchanged. The service-role key bypasses RLS
// server-side (the migration has no client insert/update policy for this path);
// it comes only from the environment, never the repo (SECURITY_CHECKLIST §1).

import { httpError } from "./errors.js";
import type { EnvironmentAssets, EnvironmentStore, ObjectStorage, ReconstructedAsset } from "./services.js";
import type { EnvironmentStatus } from "./types.js";

export interface SupabaseConfig {
  url: string;
  serviceRoleKey: string;
  bucket: string;
}

// null when the staging creds are absent (local dev / CI discovery), so the
// pipeline falls back to fakes rather than crashing on import.
export function supabaseConfigFromEnv(env: NodeJS.ProcessEnv = process.env): SupabaseConfig | null {
  const url = env.SUPABASE_URL;
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !serviceRoleKey) return null;
  return { url, serviceRoleKey, bucket: env.ENVIRONMENTS_BUCKET ?? "environments" };
}

async function bodySnippet(res: Response): Promise<string> {
  try {
    return (await res.text()).slice(0, 300);
  } catch {
    return "";
  }
}

export class SupabaseObjectStorage implements ObjectStorage {
  constructor(private readonly cfg: SupabaseConfig) {}

  async upload(path: string, asset: ReconstructedAsset, signal: AbortSignal): Promise<void> {
    // Paths are owner-prefixed uuids + fixed filenames (services.objectPaths), so
    // no segment needs URL-encoding.
    const endpoint = `${this.cfg.url}/storage/v1/object/${this.cfg.bucket}/${path}`;
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.cfg.serviceRoleKey}`,
        apikey: this.cfg.serviceRoleKey,
        "x-upsert": "true",
      },
      // Copy into a fresh ArrayBuffer-backed view so the Blob part type is exact
      // (a generic Uint8Array may be SharedArrayBuffer-backed).
      body: new Blob([new Uint8Array(asset.bytes)], { type: asset.contentType }),
      signal,
    });
    if (!res.ok) throw httpError(res.status, `storage upload ${path}`, await bodySnippet(res));
  }
}

export class SupabaseEnvironmentStore implements EnvironmentStore {
  constructor(private readonly cfg: SupabaseConfig) {}

  private async patch(environmentId: string, body: Record<string, unknown>, signal: AbortSignal): Promise<void> {
    const endpoint = `${this.cfg.url}/rest/v1/environments?id=eq.${environmentId}`;
    const res = await fetch(endpoint, {
      method: "PATCH",
      headers: {
        authorization: `Bearer ${this.cfg.serviceRoleKey}`,
        apikey: this.cfg.serviceRoleKey,
        "content-type": "application/json",
        prefer: "return=minimal",
      },
      body: JSON.stringify(body),
      signal,
    });
    if (!res.ok) {
      throw httpError(res.status, `environments PATCH ${environmentId}`, await bodySnippet(res));
    }
  }

  async markProcessing(environmentId: string, signal: AbortSignal): Promise<void> {
    await this.patch(environmentId, { status: "processing" }, signal);
  }

  async attachAssets(environmentId: string, assets: EnvironmentAssets, signal: AbortSignal): Promise<void> {
    await this.patch(
      environmentId,
      {
        splat_object: assets.splatObject,
        mesh_object: assets.meshObject,
        thumbnail_object: assets.thumbnailObject,
        splat_count: assets.splatCount,
        package_bytes: assets.packageBytes,
      },
      signal,
    );
  }

  async setStatus(environmentId: string, status: EnvironmentStatus, signal: AbortSignal): Promise<void> {
    await this.patch(environmentId, { status }, signal);
  }
}
