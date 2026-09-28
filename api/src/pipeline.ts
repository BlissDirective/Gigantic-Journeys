import type { Recorder } from "./recorder.js";
import {
  objectPaths,
  withTimeout,
  type EnvironmentStore,
  type ObjectStorage,
  type ReconstructionService,
} from "./services.js";
import {
  TIMEOUTS_MS,
  type JourneyResult,
  type PackageResult,
  type PipelineResult,
  type ReconstructResult,
  type ScanSubmittedData,
  type SceneGraphResult,
} from "./types.js";

function now(): string {
  return new Date().toISOString();
}

// The services each step needs. Injected so tests use fakes and the Inngest
// wrapper picks real adapters (Modal + Supabase) or fakes from the environment.
export interface PipelineDeps {
  recorder: Recorder;
  recon: ReconstructionService;
  storage: ObjectStorage;
  store: EnvironmentStore;
}

// --- reconstruct: REAL (M1-PIPE-01). Runs the self-host reconstruction, stores
// the splat + collision mesh (+ thumbnail) in the private 'environments' bucket
// under the owner-prefixed path, and records the asset pointers + counts on the
// environments row. Every external call site is bounded by a timeout. ---
export async function reconstruct(data: ScanSubmittedData, deps: PipelineDeps): Promise<ReconstructResult> {
  deps.recorder.record({ scanId: data.scanId, step: "reconstruct", status: "reconstructing", at: now() });

  await withTimeout(TIMEOUTS_MS.store, "markProcessing", (s) =>
    deps.store.markProcessing(data.environmentId, s),
  );

  // Off-site guard lives inside the Modal adapter too; the recon call is the one
  // long-running vendor step, bounded by the reconstruct timeout.
  const out = await withTimeout(TIMEOUTS_MS.reconstruct, "reconstruct", (s) =>
    deps.recon.reconstruct(data, s),
  );

  const paths = objectPaths(data.userId, data.environmentId);
  const thumbnailObject = out.thumbnail ? paths.thumbnail : null;

  await withTimeout(TIMEOUTS_MS.store, "upload splat", (s) => deps.storage.upload(paths.splat, out.splat, s));
  await withTimeout(TIMEOUTS_MS.store, "upload mesh", (s) => deps.storage.upload(paths.mesh, out.mesh, s));
  if (out.thumbnail && thumbnailObject) {
    await withTimeout(TIMEOUTS_MS.store, "upload thumbnail", (s) =>
      deps.storage.upload(thumbnailObject, out.thumbnail!, s),
    );
  }

  const packageBytes =
    out.splat.bytes.length + out.mesh.bytes.length + (out.thumbnail?.bytes.length ?? 0);
  const assets = {
    splatObject: paths.splat,
    meshObject: paths.mesh,
    thumbnailObject,
    splatCount: out.splatCount,
    packageBytes,
  };
  await withTimeout(TIMEOUTS_MS.store, "attachAssets", (s) =>
    deps.store.attachAssets(data.environmentId, assets, s),
  );

  return { scanId: data.scanId, environmentId: data.environmentId, ...assets, costUsd: out.costUsd };
}

// --- scenegraph / journey: STILL STUBS. The real steps (mesh cleanup + surface
// classification + traversal graph, then summit/route/vista generation) are the
// M1-SCEN-* tickets and depend on the M1-DATA-01 schema freeze; they slot in
// behind this same signature. Kept as recorded no-ops so the durable workflow and
// its ordering/idempotency are exercised end to end today. ---
export async function scenegraph(data: ScanSubmittedData, deps: PipelineDeps): Promise<SceneGraphResult> {
  deps.recorder.record({ scanId: data.scanId, step: "scenegraph", status: "scene-graph", at: now() });
  return { scanId: data.scanId, nodeCount: 0 };
}

export async function journey(data: ScanSubmittedData, deps: PipelineDeps): Promise<JourneyResult> {
  deps.recorder.record({ scanId: data.scanId, step: "journey", status: "generating-journey", at: now() });
  return { scanId: data.scanId, routeCount: 0 };
}

// --- package: marks the environment ready to view (delivery is signed-URL only
// via the environment-urls edge function). Full package assembly + CDN delivery
// is M4-PLAT-01; publishing (moderation-gated) is a later user action. ---
export async function packageEnvironment(
  data: ScanSubmittedData,
  deps: PipelineDeps,
): Promise<PackageResult> {
  deps.recorder.record({ scanId: data.scanId, step: "package", status: "packaging", at: now() });
  await withTimeout(TIMEOUTS_MS.store, "setStatus ready", (s) =>
    deps.store.setStatus(data.environmentId, "ready", s),
  );
  return { scanId: data.scanId, environmentId: data.environmentId, status: "ready" };
}

// Injectable stage set so tests can assert ordering and simulate a failing step.
export interface PipelineStages {
  reconstruct: (data: ScanSubmittedData, deps: PipelineDeps) => Promise<ReconstructResult>;
  scenegraph: (data: ScanSubmittedData, deps: PipelineDeps) => Promise<SceneGraphResult>;
  journey: (data: ScanSubmittedData, deps: PipelineDeps) => Promise<JourneyResult>;
  package: (data: ScanSubmittedData, deps: PipelineDeps) => Promise<PackageResult>;
}

export const defaultStages: PipelineStages = {
  reconstruct,
  scenegraph,
  journey,
  package: packageEnvironment,
};

// Orchestrates the four steps in order. Idempotent transitions are guaranteed by
// the recorder (dedup by scanId+step). A thrown step error propagates so Inngest
// retries that step (M1-PIPE-01 AT-1); the Inngest wrapper turns a terminal error
// into a NonRetriableError and drives the row to 'failed'.
export async function runPipeline(
  data: ScanSubmittedData,
  deps: PipelineDeps,
  stages: PipelineStages = defaultStages,
): Promise<PipelineResult> {
  const reconstructResult = await stages.reconstruct(data, deps);
  const scenegraphResult = await stages.scenegraph(data, deps);
  const journeyResult = await stages.journey(data, deps);
  const packageResult = await stages.package(data, deps);
  return {
    scanId: data.scanId,
    reconstruct: reconstructResult,
    scenegraph: scenegraphResult,
    journey: journeyResult,
    package: packageResult,
    status: "complete",
  };
}
