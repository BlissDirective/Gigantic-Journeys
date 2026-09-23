import type { PipelineStep, StatusTransition } from "./types.js";

// Records pipeline status transitions. The in-memory implementation dedupes by
// (scanId, step) so re-running the same event produces no duplicate transitions
// (idempotency, M0-PIPE-01 AT-5). M1 swaps in a Supabase-backed recorder behind
// this same interface.
export interface Recorder {
  record(transition: StatusTransition): void;
  has(scanId: string, step: PipelineStep): boolean;
  transitions(): readonly StatusTransition[];
}

export class InMemoryRecorder implements Recorder {
  private readonly seen = new Set<string>();
  private readonly log: StatusTransition[] = [];

  private key(scanId: string, step: PipelineStep): string {
    return `${scanId}:${step}`;
  }

  record(transition: StatusTransition): void {
    const key = this.key(transition.scanId, transition.step);
    if (this.seen.has(key)) return; // idempotent: skip a duplicate transition
    this.seen.add(key);
    this.log.push(transition);
  }

  has(scanId: string, step: PipelineStep): boolean {
    return this.seen.has(this.key(scanId, step));
  }

  transitions(): readonly StatusTransition[] {
    return this.log;
  }
}
