// Modal reconstruction adapter (self-host Gaussian-splat backend, ADR-0005).
//
// Calls a Modal web endpoint that runs the reconstruct() function in
// services/reconstruction/modal_app.py and returns the derived assets. The
// endpoint expects { scan_id, source } and resolves the scan bundle location on
// its side (the capture->reconstruction upload contract is M1-CAPT-01/M1-CAPT-02;
// this adapter is the TS boundary). It returns base64 asset bytes for a first
// contract; a signed-URL handoff (Modal writes to a temp bucket, returns URLs we
// stream) is the scale-up once assets are large — tracked with M1-CAPT-02.
//
// EXPOSING THE ENDPOINT is the Operator's M1-CAPT-02 step: add a
// @modal.web_endpoint wrapper over reconstruct() and a Modal-Key/Modal-Secret
// proxy auth token. No token or URL is committed; both come from the environment.

import { assertOffsiteAllowed, httpError, TerminalError } from "./errors.js";
import type { ReconstructedAsset, ReconstructionOutput, ReconstructionService } from "./services.js";
import type { ScanSubmittedData } from "./types.js";

export interface ModalConfig {
  endpoint: string;
  tokenId?: string;
  tokenSecret?: string;
}

export function modalConfigFromEnv(env: NodeJS.ProcessEnv = process.env): ModalConfig | null {
  const endpoint = env.MODAL_RECONSTRUCT_URL;
  if (!endpoint) return null;
  return { endpoint, tokenId: env.MODAL_TOKEN_ID, tokenSecret: env.MODAL_TOKEN_SECRET };
}

interface ModalReconstructResponse {
  splat_b64: string;
  splat_content_type?: string;
  mesh_b64: string;
  mesh_content_type?: string;
  thumbnail_b64?: string;
  splat_count: number;
  cost_usd: number;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function parseResponse(raw: unknown): ModalReconstructResponse {
  if (typeof raw !== "object" || raw === null) {
    throw new TerminalError("reconstruct returned a non-object body", "reconstruct");
  }
  const obj = raw as Record<string, unknown>;
  const splat = asString(obj.splat_b64);
  const mesh = asString(obj.mesh_b64);
  const splatCount = obj.splat_count;
  const costUsd = obj.cost_usd;
  if (!splat || !mesh || typeof splatCount !== "number" || typeof costUsd !== "number") {
    throw new TerminalError(
      "reconstruct response missing splat_b64/mesh_b64/splat_count/cost_usd",
      "reconstruct",
    );
  }
  return {
    splat_b64: splat,
    splat_content_type: asString(obj.splat_content_type),
    mesh_b64: mesh,
    mesh_content_type: asString(obj.mesh_content_type),
    thumbnail_b64: asString(obj.thumbnail_b64),
    splat_count: splatCount,
    cost_usd: costUsd,
  };
}

function decode(b64: string, contentType: string): ReconstructedAsset {
  return { bytes: new Uint8Array(Buffer.from(b64, "base64")), contentType };
}

export class ModalReconstructionService implements ReconstructionService {
  constructor(private readonly cfg: ModalConfig) {}

  async reconstruct(data: ScanSubmittedData, signal: AbortSignal): Promise<ReconstructionOutput> {
    assertOffsiteAllowed(data.source); // never dispatch a real user scan off-site

    const headers: Record<string, string> = { "content-type": "application/json" };
    if (this.cfg.tokenId && this.cfg.tokenSecret) {
      headers["Modal-Key"] = this.cfg.tokenId;
      headers["Modal-Secret"] = this.cfg.tokenSecret;
    }

    const res = await fetch(this.cfg.endpoint, {
      method: "POST",
      headers,
      body: JSON.stringify({ scan_id: data.scanId, source: data.source }),
      signal,
    });
    if (!res.ok) {
      let detail = "";
      try {
        detail = (await res.text()).slice(0, 300);
      } catch {
        detail = "";
      }
      throw httpError(res.status, "reconstruct", detail);
    }

    let body: unknown;
    try {
      body = await res.json();
    } catch {
      throw new TerminalError("reconstruct returned invalid JSON", "reconstruct");
    }
    const parsed = parseResponse(body);
    const out: ReconstructionOutput = {
      splat: decode(parsed.splat_b64, parsed.splat_content_type ?? "application/octet-stream"),
      mesh: decode(parsed.mesh_b64, parsed.mesh_content_type ?? "model/obj"),
      splatCount: parsed.splat_count,
      costUsd: parsed.cost_usd,
    };
    if (parsed.thumbnail_b64) out.thumbnail = decode(parsed.thumbnail_b64, "image/png");
    return out;
  }
}
