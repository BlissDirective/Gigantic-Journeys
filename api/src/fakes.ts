// In-memory fakes for the pipeline ports, so pipeline logic is tested with no
// live services and no secrets (mirrors services/reconstruction/reconstruction/fakes.py).

import type {
  EnvironmentAssets,
  EnvironmentStore,
  ObjectStorage,
  ReconstructedAsset,
  ReconstructionOutput,
  ReconstructionService,
} from "./services.js";
import type { EnvironmentStatus, ScanSubmittedData } from "./types.js";

function asset(text: string, contentType: string): ReconstructedAsset {
  return { bytes: new TextEncoder().encode(text), contentType };
}

export class FakeReconstructionService implements ReconstructionService {
  readonly calls: ScanSubmittedData[] = [];
  constructor(
    private readonly opts: {
      splatCount?: number;
      costUsd?: number;
      withThumbnail?: boolean;
      failWith?: () => Error;
    } = {},
  ) {}

  async reconstruct(data: ScanSubmittedData): Promise<ReconstructionOutput> {
    this.calls.push(data);
    if (this.opts.failWith) throw this.opts.failWith();
    const out: ReconstructionOutput = {
      splat: asset(`splat:${data.scanId}`, "application/octet-stream"),
      mesh: asset(`mesh:${data.scanId}`, "model/obj"),
      splatCount: this.opts.splatCount ?? 42,
      costUsd: this.opts.costUsd ?? 0.185,
    };
    if (this.opts.withThumbnail ?? true) out.thumbnail = asset(`thumb:${data.scanId}`, "image/png");
    return out;
  }
}

export class InMemoryObjectStorage implements ObjectStorage {
  readonly objects = new Map<string, ReconstructedAsset>();
  async upload(path: string, asset: ReconstructedAsset): Promise<void> {
    this.objects.set(path, asset);
  }
}

export class InMemoryEnvironmentStore implements EnvironmentStore {
  readonly statuses: EnvironmentStatus[] = [];
  readonly assets = new Map<string, EnvironmentAssets>();
  readonly ops: string[] = [];

  async markProcessing(environmentId: string): Promise<void> {
    this.ops.push(`markProcessing:${environmentId}`);
    this.statuses.push("processing");
  }
  async attachAssets(environmentId: string, assets: EnvironmentAssets): Promise<void> {
    this.ops.push(`attachAssets:${environmentId}`);
    this.assets.set(environmentId, assets);
  }
  async setStatus(environmentId: string, status: EnvironmentStatus): Promise<void> {
    this.ops.push(`setStatus:${environmentId}:${status}`);
    this.statuses.push(status);
  }
}
