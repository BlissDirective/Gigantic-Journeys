import { NonRetriableError } from "inngest";

import { buildDeps } from "../deps.js";
import { isRetryable } from "../errors.js";
import { defaultStages, type PipelineDeps } from "../pipeline.js";
import { withTimeout } from "../services.js";
import { TIMEOUTS_MS, type ScanSubmittedData } from "../types.js";
import { inngest } from "./client.js";

// Run a step so that a TERMINAL error becomes a NonRetriableError (Inngest stops
// retrying) while a RETRYABLE one propagates unchanged (Inngest retries the
// memoized step). Classification is errors.isRetryable (M1-PIPE-01 AT-1).
function classifiedStep<T>(
  step: { run: (id: string, fn: () => Promise<T>) => Promise<T> },
  id: string,
  fn: () => Promise<T>,
): Promise<T> {
  return step.run(id, async () => {
    try {
      return await fn();
    } catch (err) {
      if (!isRetryable(err)) {
        throw new NonRetriableError(err instanceof Error ? err.message : String(err));
      }
      throw err;
    }
  });
}

async function markFailed(deps: PipelineDeps, environmentId: string): Promise<void> {
  try {
    await withTimeout(TIMEOUTS_MS.store, "setStatus failed", (s) =>
      deps.store.setStatus(environmentId, "failed", s),
    );
  } catch {
    // best-effort; the run already failed. A retryable-exhaustion sweep that also
    // reaps stuck 'processing' rows is a follow-up (Inngest onFailure).
  }
}

// The durable workflow: scan.submitted -> reconstruct (real) -> scenegraph ->
// journey (stubs) -> package. Each step.run is memoized by Inngest, so a retry
// resumes at the failed step. A terminal failure drives the environments row to
// 'failed'.
export const journeyPipeline = inngest.createFunction(
  { id: "journey-pipeline", name: "journey/pipeline" },
  { event: "scan.submitted" },
  async ({ event, step }) => {
    const data = event.data as ScanSubmittedData;
    const { deps } = buildDeps();

    try {
      const reconstruct = await classifiedStep(step, "reconstruct", () =>
        defaultStages.reconstruct(data, deps),
      );
      const scenegraph = await classifiedStep(step, "scenegraph", () =>
        defaultStages.scenegraph(data, deps),
      );
      const journey = await classifiedStep(step, "journey", () => defaultStages.journey(data, deps));
      const pkg = await classifiedStep(step, "package", () => defaultStages.package(data, deps));

      return {
        scanId: data.scanId,
        reconstruct,
        scenegraph,
        journey,
        package: pkg,
        status: "complete" as const,
      };
    } catch (err) {
      // Terminal failures (surfaced as NonRetriableError) are final: mark the row
      // failed. Retryable errors are left to Inngest to retry.
      if (err instanceof NonRetriableError && data.environmentId) {
        await markFailed(deps, data.environmentId);
      }
      throw err;
    }
  },
);

export const functions = [journeyPipeline];
