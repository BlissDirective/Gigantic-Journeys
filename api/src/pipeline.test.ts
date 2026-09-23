import assert from "node:assert/strict";
import { test } from "node:test";

import { defaultStages, runPipeline, type PipelineStages } from "./pipeline.js";
import { InMemoryRecorder } from "./recorder.js";
import { TIMEOUTS_MS, type ScanSubmittedData } from "./types.js";

const data: ScanSubmittedData = { scanId: "scan-1", mode: "room" };

test("runs the four steps in order and completes", async () => {
  const order: string[] = [];
  const spy: PipelineStages = {
    reconstruct: (d, r) => {
      order.push("reconstruct");
      return defaultStages.reconstruct(d, r);
    },
    scenegraph: (d, r) => {
      order.push("scenegraph");
      return defaultStages.scenegraph(d, r);
    },
    journey: (d, r) => {
      order.push("journey");
      return defaultStages.journey(d, r);
    },
    package: (d, r) => {
      order.push("package");
      return defaultStages.package(d, r);
    },
  };
  const recorder = new InMemoryRecorder();
  const result = await runPipeline(data, recorder, spy);

  assert.deepEqual(order, ["reconstruct", "scenegraph", "journey", "package"]);
  assert.equal(result.status, "complete");
  assert.equal(result.package.packageUri, "stub://package/scan-1");
  assert.equal(recorder.transitions().length, 4);
});

test("is idempotent per scan id: a re-run adds no duplicate transitions", async () => {
  const recorder = new InMemoryRecorder();
  await runPipeline(data, recorder);
  await runPipeline(data, recorder);
  assert.equal(recorder.transitions().length, 4);
});

test("a thrown step error propagates so Inngest retries the step", async () => {
  const recorder = new InMemoryRecorder();
  const failing: PipelineStages = {
    ...defaultStages,
    journey: () => {
      throw new Error("boom");
    },
  };
  await assert.rejects(() => runPipeline(data, recorder, failing), /boom/);
  // The steps before the failure still recorded; the failing one and after did not.
  assert.ok(recorder.has("scan-1", "reconstruct"));
  assert.ok(recorder.has("scan-1", "scenegraph"));
  assert.ok(!recorder.has("scan-1", "package"));
});

test("every step has a positive timeout constant", () => {
  assert.ok(TIMEOUTS_MS.reconstruct > 0);
  assert.ok(TIMEOUTS_MS.scenegraph > 0);
  assert.ok(TIMEOUTS_MS.journey > 0);
  assert.ok(TIMEOUTS_MS.package > 0);
});
