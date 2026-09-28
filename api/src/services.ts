// Ports the pipeline depends on (hexagonal boundary). Real adapters live in
// adapters.supabase.ts and adapters.modal.ts; in-memory fakes live in fakes.ts,
// so the pipeline logic is fully testable with no live services and no secrets.

import { RetryableError } from "./errors.js";
import type { EnvironmentStatus, ScanSubmittedData } from "./types.js";

// A derived asset in memory, ready to upload. Splats/meshes here are small
// (a room's compressed splat is well under the 150 MB package budget); the Modal
// adapter downloads the container's output bytes and hands them over.
export interface ReconstructedAsset {
  bytes: Uint8Array;
  contentType: string;
}

export interface ReconstructionOutput {
  splat: ReconstructedAsset;
  mesh: ReconstructedAsset;
  thumbnail?: ReconstructedAsset;
  splatCount: number;
  costUsd: number;
}

// Reconstruction backend (self-host Gaussian-splat on Modal, ADR-0005). The
// signal carries the reconstruct-step timeout.
export interface ReconstructionService {
  reconstruct(data: ScanSubmittedData, signal: AbortSignal): Promise<ReconstructionOutput>;
}

// Writes to the private 'environments' bucket with the service role (bypasses RLS
// server-side; the migration has no client insert/update policy for this path).
export interface ObjectStorage {
  upload(path: string, asset: ReconstructedAsset, signal: AbortSignal): Promise<void>;
}

export interface EnvironmentAssets {
  splatObject: string;
  meshObject: string;
  thumbnailObject: string | null;
  splatCount: number;
  packageBytes: number;
}

// Writes to public.environments (service role). The row is pre-created at capture
// time (M1-CAPT-01); the pipeline updates status + asset pointers on it.
export interface EnvironmentStore {
  markProcessing(environmentId: string, signal: AbortSignal): Promise<void>;
  attachAssets(environmentId: string, assets: EnvironmentAssets, signal: AbortSignal): Promise<void>;
  setStatus(environmentId: string, status: EnvironmentStatus, signal: AbortSignal): Promise<void>;
}

// Owner-prefixed object paths: '{user_id}/{environment_id}/...' — the storage RLS
// policy keys on the first path segment (the migration's environments_objects_owner_rw).
export function objectPaths(userId: string, environmentId: string): {
  splat: string;
  mesh: string;
  thumbnail: string;
} {
  const base = `${userId}/${environmentId}`;
  return {
    splat: `${base}/splat.spz`,
    mesh: `${base}/collision.obj`,
    thumbnail: `${base}/thumbnail.png`,
  };
}

// Run fn under a deadline. A hit deadline aborts the signal (so fetch cancels)
// and surfaces as a RetryableError, so Inngest retries the step (REVIEW_RUBRIC E3).
export async function withTimeout<T>(
  ms: number,
  label: string,
  fn: (signal: AbortSignal) => Promise<T>,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await fn(controller.signal);
  } catch (err) {
    if (controller.signal.aborted) {
      throw new RetryableError(`${label} timed out after ${ms} ms`);
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}
