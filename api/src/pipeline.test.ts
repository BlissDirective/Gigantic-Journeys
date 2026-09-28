import assert from "node:assert/strict";
import { test } from "node:test";

import { FakeReconstructionService, InMemoryEnvironmentStore, InMemoryObjectStorage } from "./fakes.js";
import { defaultStages, runPipeline, type PipelineDeps, type PipelineStages } from "./pipeline.js";
import { InMemoryRecorder } from "./recorder.js";
import { TIMEOUTS_MS, type ScanSubmittedData } from "./types.js";

const data: ScanSubmittedData = {
  scanId: "scan-1",
  mode: "room",
  environmentId: "env-1",
  userId: "user-1",
  source: "corpus",
};

function deps(): PipelineDeps {
  return {
    recorder: new InMemoryRecorder(),
    recon: new FakeReconstructionService(),
    storage: new InMemoryObjectStorage(),
    store: new InMemoryEnvironmentStore(),
  };
}

test("runs the four steps in order and completes", async () => {
  const order: string[] = [];
  const d = deps();
  const spy: PipelineStages = {
    reconstruct: (x, dd) => {
      order.push("reconstruct");
      return defaultStages.reconstruct(x, dd);
    },
    scenegraph: (x, dd) => {
      order.push("scenegraph");
      return defaultStages.scenegraph(x, dd);
    },
    journey: (x, dd) => {
      order.push("journey");
      return defaultStages.journey(x, dd);
    },
    package: (x, dd) => {
      order.push("package");
      return defaultStages.package(x, dd);
    },
  };
  const result = await runPipeline(data, d, spy);

  assert.deepEqual(order, ["reconstruct", "scenegraph", "journey", "package"]);
  assert.equal(result.status, "complete");
  assert.equal(result.package.status, "ready");
  assert.equal(result.reconstruct.splatObject, "user-1/env-1/splat.spz");
  assert.equal(d.recorder.transitions().length, 4);
});

test("is idempotent per scan id: a re-run adds no duplicate transitions", async () => {
  const d = deps();
  await runPipeline(data, d);
  await runPipeline(data, d);
  assert.equal(d.recorder.transitions().length, 4);
});

test("a thrown step error propagates so Inngest retries the step", async () => {
  const d = deps();
  const failing: PipelineStages = {
    ...defaultStages,
    journey: () => {
      throw new Error("boom");
    },
  };
  await assert.rejects(() => runPipeline(data, d, failing), /boom/);
  // The steps before the failure still recorded; the failing one and after did not.
  assert.ok(d.recorder.has("scan-1", "reconstruct"));
  assert.ok(d.recorder.has("scan-1", "scenegraph"));
  assert.ok(!d.recorder.has("scan-1", "package"));
});

test("every step has a positive timeout constant", () => {
  assert.ok(TIMEOUTS_MS.reconstruct > 0);
  assert.ok(TIMEOUTS_MS.scenegraph > 0);
  assert.ok(TIMEOUTS_MS.journey > 0);
  assert.ok(TIMEOUTS_MS.package > 0);
  assert.ok(TIMEOUTS_MS.store > 0);
});
