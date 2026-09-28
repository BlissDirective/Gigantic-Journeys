import assert from "node:assert/strict";
import { test } from "node:test";

import { ModalReconstructionService } from "./adapters.modal.js";
import { SupabaseEnvironmentStore, SupabaseObjectStorage } from "./adapters.supabase.js";
import {
  assertOffsiteAllowed,
  httpError,
  isRetryable,
  RetryableError,
  SourceNotAllowedError,
  TerminalError,
} from "./errors.js";
import { FakeReconstructionService, InMemoryEnvironmentStore, InMemoryObjectStorage } from "./fakes.js";
import { packageEnvironment, reconstruct } from "./pipeline.js";
import { InMemoryRecorder } from "./recorder.js";
import { withTimeout } from "./services.js";
import type { ScanSubmittedData } from "./types.js";

const data: ScanSubmittedData = {
  scanId: "scan-1",
  mode: "room",
  environmentId: "env-1",
  userId: "user-1",
  source: "corpus",
};

const b64 = (s: string): string => Buffer.from(s).toString("base64");

// --- reconstruct persistence (M1-PIPE-01) ---

test("reconstruct stores assets under the owner-prefix and updates the row in order", async () => {
  const storage = new InMemoryObjectStorage();
  const store = new InMemoryEnvironmentStore();
  const recon = new FakeReconstructionService({ splatCount: 100, costUsd: 0.2 });
  const result = await reconstruct(data, { recorder: new InMemoryRecorder(), recon, storage, store });

  assert.equal(result.splatObject, "user-1/env-1/splat.spz");
  assert.equal(result.meshObject, "user-1/env-1/collision.obj");
  assert.equal(result.thumbnailObject, "user-1/env-1/thumbnail.png");
  assert.equal(result.splatCount, 100);
  assert.equal(result.costUsd, 0.2);
  assert.ok(result.packageBytes > 0);
  assert.deepEqual(store.ops, ["markProcessing:env-1", "attachAssets:env-1"]);
  assert.ok(storage.objects.has("user-1/env-1/splat.spz"));
  assert.ok(storage.objects.has("user-1/env-1/collision.obj"));
  assert.ok(storage.objects.has("user-1/env-1/thumbnail.png"));
});

test("reconstruct omits the thumbnail object when the backend returns none", async () => {
  const storage = new InMemoryObjectStorage();
  const store = new InMemoryEnvironmentStore();
  const recon = new FakeReconstructionService({ withThumbnail: false });
  const result = await reconstruct(data, { recorder: new InMemoryRecorder(), recon, storage, store });
  assert.equal(result.thumbnailObject, null);
  assert.ok(!storage.objects.has("user-1/env-1/thumbnail.png"));
});

test("package marks the environment ready", async () => {
  const store = new InMemoryEnvironmentStore();
  const result = await packageEnvironment(data, {
    recorder: new InMemoryRecorder(),
    recon: new FakeReconstructionService(),
    storage: new InMemoryObjectStorage(),
    store,
  });
  assert.equal(result.status, "ready");
  assert.ok(store.ops.includes("setStatus:env-1:ready"));
});

// --- error taxonomy + classification (M1-PIPE-01 AT-1) ---

test("off-site guard rejects a real user scan and allows corpus/public", () => {
  assert.throws(() => assertOffsiteAllowed("user"), SourceNotAllowedError);
  assert.doesNotThrow(() => assertOffsiteAllowed("corpus"));
  assert.doesNotThrow(() => assertOffsiteAllowed("public"));
});

test("error classification: retryable vs terminal", () => {
  assert.equal(isRetryable(new RetryableError("x")), true);
  assert.equal(isRetryable(new TerminalError("x")), false);
  assert.equal(isRetryable(new SourceNotAllowedError("x")), false);
  assert.equal(isRetryable(new Error("unmodeled")), true); // default: transient
  assert.equal(httpError(500, "a").retryable, true);
  assert.equal(httpError(429, "a").retryable, true);
  assert.equal(httpError(408, "a").retryable, true);
  assert.equal(httpError(400, "a").retryable, false);
  assert.equal(httpError(404, "a").retryable, false);
});

test("withTimeout surfaces a hit deadline as a retryable error", async () => {
  await assert.rejects(
    withTimeout(
      5,
      "slow",
      (signal) =>
        new Promise<never>((resolve, reject) => {
          signal.addEventListener("abort", () => reject(new Error("aborted")));
        }),
    ),
    (err: unknown) => err instanceof RetryableError && /timed out after 5 ms/.test(err.message),
  );
});

// --- Modal adapter (stubbed fetch) ---

test("ModalReconstructionService decodes assets on success", async () => {
  const body = {
    splat_b64: b64("SPLAT"),
    mesh_b64: b64("MESH"),
    thumbnail_b64: b64("THUMB"),
    splat_count: 7,
    cost_usd: 0.19,
  };
  const saved = globalThis.fetch;
  globalThis.fetch = (async () =>
    new Response(JSON.stringify(body), {
      status: 200,
      headers: { "content-type": "application/json" },
    })) as typeof fetch;
  try {
    const svc = new ModalReconstructionService({ endpoint: "https://modal.example/recon" });
    const out = await svc.reconstruct(data, AbortSignal.timeout(1000));
    assert.equal(out.splatCount, 7);
    assert.equal(out.costUsd, 0.19);
    assert.equal(new TextDecoder().decode(out.splat.bytes), "SPLAT");
    assert.equal(new TextDecoder().decode(out.mesh.bytes), "MESH");
    assert.ok(out.thumbnail);
    assert.equal(new TextDecoder().decode(out.thumbnail.bytes), "THUMB");
  } finally {
    globalThis.fetch = saved;
  }
});

test("ModalReconstructionService rejects a user scan before any request", async () => {
  let called = false;
  const saved = globalThis.fetch;
  globalThis.fetch = (async () => {
    called = true;
    return new Response("{}");
  }) as typeof fetch;
  try {
    const svc = new ModalReconstructionService({ endpoint: "https://modal.example/recon" });
    await assert.rejects(
      () => svc.reconstruct({ ...data, source: "user" }, AbortSignal.timeout(1000)),
      SourceNotAllowedError,
    );
    assert.equal(called, false);
  } finally {
    globalThis.fetch = saved;
  }
});

test("ModalReconstructionService maps a 503 to a retryable error", async () => {
  const saved = globalThis.fetch;
  globalThis.fetch = (async () => new Response("upstream down", { status: 503 })) as typeof fetch;
  try {
    const svc = new ModalReconstructionService({ endpoint: "https://modal.example/recon" });
    await assert.rejects(
      () => svc.reconstruct(data, AbortSignal.timeout(1000)),
      (e: unknown) => e instanceof RetryableError,
    );
  } finally {
    globalThis.fetch = saved;
  }
});

test("ModalReconstructionService treats a malformed body as terminal", async () => {
  const saved = globalThis.fetch;
  globalThis.fetch = (async () =>
    new Response(JSON.stringify({ splat_b64: "x" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    })) as typeof fetch;
  try {
    const svc = new ModalReconstructionService({ endpoint: "https://modal.example/recon" });
    await assert.rejects(() => svc.reconstruct(data, AbortSignal.timeout(1000)), TerminalError);
  } finally {
    globalThis.fetch = saved;
  }
});

// --- Supabase adapters (stubbed fetch) ---

test("SupabaseObjectStorage.upload POSTs to the bucket path and succeeds on 200", async () => {
  const saved = globalThis.fetch;
  let seenUrl = "";
  let seenMethod = "";
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    seenUrl = String(input);
    seenMethod = init?.method ?? "GET";
    return new Response(null, { status: 200 });
  }) as typeof fetch;
  try {
    const s = new SupabaseObjectStorage({
      url: "https://proj.supabase.co",
      serviceRoleKey: "svc",
      bucket: "environments",
    });
    await s.upload(
      "user-1/env-1/splat.spz",
      { bytes: new Uint8Array([1, 2, 3]), contentType: "application/octet-stream" },
      AbortSignal.timeout(1000),
    );
    assert.equal(seenMethod, "POST");
    assert.equal(
      seenUrl,
      "https://proj.supabase.co/storage/v1/object/environments/user-1/env-1/splat.spz",
    );
  } finally {
    globalThis.fetch = saved;
  }
});

test("SupabaseObjectStorage.upload maps 500 to retryable and 403 to terminal", async () => {
  const saved = globalThis.fetch;
  try {
    const s = new SupabaseObjectStorage({ url: "https://p.sb", serviceRoleKey: "k", bucket: "environments" });
    const asset = { bytes: new Uint8Array([1]), contentType: "x" };
    globalThis.fetch = (async () => new Response("err", { status: 500 })) as typeof fetch;
    await assert.rejects(
      () => s.upload("p", asset, AbortSignal.timeout(1000)),
      (e: unknown) => e instanceof RetryableError,
    );
    globalThis.fetch = (async () => new Response("forbidden", { status: 403 })) as typeof fetch;
    await assert.rejects(
      () => s.upload("p", asset, AbortSignal.timeout(1000)),
      (e: unknown) => e instanceof TerminalError,
    );
  } finally {
    globalThis.fetch = saved;
  }
});

test("SupabaseEnvironmentStore.setStatus PATCHes the row by id", async () => {
  const saved = globalThis.fetch;
  let seenUrl = "";
  let seenBody = "";
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    seenUrl = String(input);
    seenBody = String(init?.body ?? "");
    return new Response(null, { status: 204 });
  }) as typeof fetch;
  try {
    const st = new SupabaseEnvironmentStore({
      url: "https://p.sb",
      serviceRoleKey: "k",
      bucket: "environments",
    });
    await st.setStatus("env-1", "ready", AbortSignal.timeout(1000));
    assert.equal(seenUrl, "https://p.sb/rest/v1/environments?id=eq.env-1");
    assert.match(seenBody, /"status":"ready"/);
  } finally {
    globalThis.fetch = saved;
  }
});
