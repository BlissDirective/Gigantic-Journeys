// Error taxonomy + classification for the durable pipeline (M1-PIPE-01 AT-1/AT-2).
//
// A step's failure is either RETRYABLE (transient: a vendor 5xx, a network blip,
// a timeout) or TERMINAL (a bad input or a policy violation that will fail the
// same way on every retry). The Inngest wrapper (inngest/functions.ts) turns a
// terminal error into a NonRetriableError so Inngest stops retrying, and lets a
// retryable one propagate so Inngest retries the memoized step.

import type { PipelineStep, ScanSource } from "./types.js";

export abstract class PipelineError extends Error {
  abstract readonly retryable: boolean;
  readonly step?: PipelineStep;

  constructor(message: string, step?: PipelineStep) {
    super(message);
    this.name = new.target.name;
    this.step = step;
  }
}

// Transient: retry the step.
export class RetryableError extends PipelineError {
  readonly retryable = true;
}

// Permanent: do not retry; the run fails and the environments row goes 'failed'.
export class TerminalError extends PipelineError {
  readonly retryable = false;
}

// Defence in depth: a real user scan must never be sent to off-site compute
// (ADR-0005 / AUTH #030). The reconstruction container guards this too
// (reconstruction/models.py require_offsite_source); this is the pipeline-side
// guard so we never even dispatch such a job.
export class SourceNotAllowedError extends TerminalError {}

const OFFSITE_SOURCES: ReadonlySet<ScanSource> = new Set(["public", "corpus"]);

export function assertOffsiteAllowed(source: ScanSource): void {
  if (!OFFSITE_SOURCES.has(source)) {
    throw new SourceNotAllowedError(
      `source ${JSON.stringify(source)} may not be sent to off-site compute; ` +
        `allowed: corpus, public (real user scans never leave our infrastructure, ` +
        `ADR-0005 / AUTH #030)`,
      "reconstruct",
    );
  }
}

// Classify any thrown value. A PipelineError says so itself. An AbortError
// (a hit timeout) is transient. Anything else is treated as retryable by default,
// so a transient fault we did not model still gets Inngest's retry rather than a
// silent permanent failure.
export function isRetryable(err: unknown): boolean {
  if (err instanceof PipelineError) return err.retryable;
  if (err instanceof Error && (err.name === "AbortError" || err.name === "TimeoutError")) {
    return true;
  }
  return true;
}

// Map an HTTP status from a vendor call to a classified pipeline error: 408/429
// and 5xx are transient (retry); every other non-2xx is terminal (bad request,
// auth, not found — retrying will not help).
export function httpError(status: number, label: string, detail?: string): PipelineError {
  const retry = status === 408 || status === 429 || status >= 500;
  const suffix = detail ? ` — ${detail.slice(0, 300)}` : "";
  const message = `${label} failed: HTTP ${status}${suffix}`;
  return retry ? new RetryableError(message) : new TerminalError(message);
}
