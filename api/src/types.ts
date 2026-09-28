// Shared types for the Gigantic Journeys durable pipeline.
// M0 skeleton was logged stubs (M0-PIPE-01); M1-PIPE-01 makes the reconstruct
// step real (Modal reconstruction -> private storage -> environments row) and
// keeps scenegraph/journey as honest stubs until M1-DATA-01 (schema freeze) and
// the M1-SCEN tickets land.

export const SCAN_SUBMITTED = "scan.submitted" as const;

export type CaptureMode = "room" | "tabletop";

// Provenance of a scan. Mirrors reconstruction/models.py Source. Only 'public'
// and 'corpus' may be sent to off-site compute (a rented Modal GPU); a real
// 'user' scan never leaves our infrastructure (ADR-0005 / AUTH #030). Enforced as
// a terminal guard in errors.assertOffsiteAllowed before any reconstruct call.
export type ScanSource = "public" | "corpus" | "user";

// Row lifecycle in public.environments (matches the environment_status enum in
// 20260926120000_m1_environments_staging.sql). Publishing (published) is a later
// user action gated by moderation (M4); the pipeline only drives processing ->
// ready | failed.
export type EnvironmentStatus = "processing" | "ready" | "published" | "failed" | "archived";

export interface ScanSubmittedData {
  scanId: string;
  mode: CaptureMode;
  // The pre-created environments row this run fills, and its owner. The row is
  // inserted at capture time (M1-CAPT-01); the pipeline writes assets + status.
  environmentId: string;
  userId: string;
  source: ScanSource;
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

// The reconstruct step's result: where the derived assets landed in the private
// 'environments' bucket (never public URLs — delivery is signed-URL only via the
// environment-urls edge function) plus the recorded counts and cost.
export interface ReconstructResult {
  scanId: string;
  environmentId: string;
  splatObject: string;
  meshObject: string;
  thumbnailObject: string | null;
  splatCount: number;
  packageBytes: number;
  costUsd: number;
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
  environmentId: string;
  status: EnvironmentStatus;
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
// E3), enforced with an AbortSignal in services.withTimeout.
export const TIMEOUTS_MS = {
  reconstruct: 600_000,
  scenegraph: 120_000,
  journey: 60_000,
  package: 120_000,
  // Fast metadata writes (environments row + storage object PUT).
  store: 30_000,
} as const satisfies Record<PipelineStep | "store", number>;
