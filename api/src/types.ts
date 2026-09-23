// Shared types for the Gigantic Journeys durable pipeline (M0 skeleton).

export const SCAN_SUBMITTED = "scan.submitted" as const;

export type CaptureMode = "room" | "tabletop";

export interface ScanSubmittedData {
  scanId: string;
  mode: CaptureMode;
}

export type PipelineStep = "reconstruct" | "scenegraph" | "journey" | "package";

export type PipelineStatus =
  | "reconstructing"
  | "scene-graph"
  | "generating-journey"
  | "packaging"
  | "complete";

export interface StatusTransition {
  scanId: string;
  step: PipelineStep;
  status: PipelineStatus;
  at: string; // ISO-8601 timestamp
}

export interface ReconstructResult {
  scanId: string;
  splatUri: string;
  meshUri: string;
}

export interface SceneGraphResult {
  scanId: string;
  nodeCount: number;
}

export interface JourneyResult {
  scanId: string;
  routeCount: number;
}

export interface PackageResult {
  scanId: string;
  packageUri: string;
}

export interface PipelineResult {
  scanId: string;
  reconstruct: ReconstructResult;
  scenegraph: SceneGraphResult;
  journey: JourneyResult;
  package: PackageResult;
  status: "complete";
}

// Every external call site gets an explicit timeout (SECURITY_CHECKLIST / REVIEW_RUBRIC
// E3). The M0 steps are stubs; M1 wires the real services behind these budgets.
export const TIMEOUTS_MS = {
  reconstruct: 600_000,
  scenegraph: 120_000,
  journey: 60_000,
  package: 120_000,
} as const satisfies Record<PipelineStep, number>;
