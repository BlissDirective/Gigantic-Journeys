// Builds the pipeline's service dependencies from the environment. When the
// staging Supabase creds and the Modal endpoint are both present, real adapters
// are used; otherwise in-memory fakes, so local dev and CI (function discovery,
// tests) run with no secrets and no live services.

import { ModalReconstructionService, modalConfigFromEnv } from "./adapters.modal.js";
import {
  SupabaseEnvironmentStore,
  SupabaseObjectStorage,
  supabaseConfigFromEnv,
} from "./adapters.supabase.js";
import { FakeReconstructionService, InMemoryEnvironmentStore, InMemoryObjectStorage } from "./fakes.js";
import type { PipelineDeps } from "./pipeline.js";
import { InMemoryRecorder } from "./recorder.js";

export function buildDeps(env: NodeJS.ProcessEnv = process.env): { deps: PipelineDeps; live: boolean } {
  const recorder = new InMemoryRecorder();
  const supa = supabaseConfigFromEnv(env);
  const modal = modalConfigFromEnv(env);
  if (supa && modal) {
    return {
      deps: {
        recorder,
        recon: new ModalReconstructionService(modal),
        storage: new SupabaseObjectStorage(supa),
        store: new SupabaseEnvironmentStore(supa),
      },
      live: true,
    };
  }
  return {
    deps: {
      recorder,
      recon: new FakeReconstructionService(),
      storage: new InMemoryObjectStorage(),
      store: new InMemoryEnvironmentStore(),
    },
    live: false,
  };
}
