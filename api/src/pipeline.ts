import type { Recorder } from "./recorder.js";
import type {
  JourneyResult,
  PackageResult,
  PipelineResult,
  ReconstructResult,
  ScanSubmittedData,
  SceneGraphResult,
} from "./types.js";

function now(): string {
  return new Date().toISOString();
}

// --- The four steps. Each records exactly one status transition and returns a
// typed result. All are M0 stubs; M1 wires the real services (self-host / KIRI
// reconstruction, scene-graph, journey generation, packaging) behind TIMEOUTS_MS. ---

export async function reconstruct(
  data: ScanSubmittedData,
  recorder: Recorder,
): Promise<ReconstructResult> {
  recorder.record({ scanId: data.scanId, step: "reconstruct", status: "reconstructing", at: now() });
  return {
    scanId: data.scanId,
    splatUri: `stub://splat/${data.scanId}`,
    meshUri: `stub://mesh/${data.scanId}`,
  };
}

export async function scenegraph(
  data: ScanSubmittedData,
  recorder: Recorder,
): Promise<SceneGraphResult> {
  recorder.record({ scanId: data.scanId, step: "scenegraph", status: "scene-graph", at: now() });
  return { scanId: data.scanId, nodeCount: 0 };
}

export async function journey(
  data: ScanSubmittedData,
  recorder: Recorder,
): Promise<JourneyResult> {
  recorder.record({ scanId: data.scanId, step: "journey", status: "generating-journey", at: now() });
  return { scanId: data.scanId, routeCount: 0 };
}

export async function packageEnvironment(
  data: ScanSubmittedData,
  recorder: Recorder,
): Promise<PackageResult> {
  recorder.record({ scanId: data.scanId, step: "package", status: "packaging", at: now() });
  return { scanId: data.scanId, packageUri: `stub://package/${data.scanId}` };
}

// Injectable stage set so tests can assert ordering and simulate a failing step.
export interface PipelineStages {
  reconstruct: (data: ScanSubmittedData, recorder: Recorder) => Promise<ReconstructResult>;
  scenegraph: (data: ScanSubmittedData, recorder: Recorder) => Promise<SceneGraphResult>;
  journey: (data: ScanSubmittedData, recorder: Recorder) => Promise<JourneyResult>;
  package: (data: ScanSubmittedData, recorder: Recorder) => Promise<PackageResult>;
}

export const defaultStages: PipelineStages = {
  reconstruct,
  scenegraph,
  journey,
  package: packageEnvironment,
};

// Orchestrates the four steps in order. Idempotent transitions are guaranteed by
// the recorder (dedup by scanId+step). A thrown step error propagates so Inngest
// retries that step (M0-PIPE-01 AT-2/AT-3/AT-5).
export async function runPipeline(
  data: ScanSubmittedData,
  recorder: Recorder,
  stages: PipelineStages = defaultStages,
): Promise<PipelineResult> {
  const reconstructResult = await stages.reconstruct(data, recorder);
  const scenegraphResult = await stages.scenegraph(data, recorder);
  const journeyResult = await stages.journey(data, recorder);
  const packageResult = await stages.package(data, recorder);
  return {
    scanId: data.scanId,
    reconstruct: reconstructResult,
    scenegraph: scenegraphResult,
    journey: journeyResult,
    package: packageResult,
    status: "complete",
  };
}
