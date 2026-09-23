import { defaultStages } from "../pipeline.js";
import { InMemoryRecorder } from "../recorder.js";
import { inngest } from "./client.js";

// The M0 durable workflow: one function, four stub steps. Each step.run is
// memoized by Inngest, so a retry resumes at the failed step rather than
// re-running the whole pipeline. M1 replaces the in-memory recorder with a
// Supabase-backed one and fills each step with the real service call.
export const journeyPipeline = inngest.createFunction(
  { id: "journey-pipeline", name: "journey/pipeline" },
  { event: "scan.submitted" },
  async ({ event, step }) => {
    const data = event.data;
    const recorder = new InMemoryRecorder();

    const reconstruct = await step.run("reconstruct", () =>
      defaultStages.reconstruct(data, recorder),
    );
    const scenegraph = await step.run("scenegraph", () =>
      defaultStages.scenegraph(data, recorder),
    );
    const journey = await step.run("journey", () => defaultStages.journey(data, recorder));
    const pkg = await step.run("package", () => defaultStages.package(data, recorder));

    return {
      scanId: data.scanId,
      reconstruct,
      scenegraph,
      journey,
      package: pkg,
      status: "complete" as const,
    };
  },
);

export const functions = [journeyPipeline];
