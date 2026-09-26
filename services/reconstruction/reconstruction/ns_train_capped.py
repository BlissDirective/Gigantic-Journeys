"""``ns-train`` with a densification limit (runs inside the CUDA container).

nerfstudio 1.1.5's Splatfacto uses gsplat's ``DefaultStrategy``, which grows
splats without any ceiling (``ReconstructionConfig.splat_budget`` was not
enforced). This wrapper patches ``DefaultStrategy._grow_gs`` so a refine step
never grows the model past the budget: when the candidates for duplication /
splitting exceed the remaining headroom, only the highest-gradient ones grow.
Duplication and splitting each add one net splat per candidate, so a refine
step lands at (or, if a splat is picked by both rules, marginally above) the
budget. It is therefore a *growth* limit that also saves training time and GPU
memory; the *hard* cap is applied after training by ``reconstruction.ns_finish``.

Usage (the trainer builds this argv):
    python -m reconstruction.ns_train_capped --budget 2000000 -- splatfacto ...

torch / gsplat / nerfstudio are imported only in ``main`` so the package
imports on a machine without them (CI).
"""

from __future__ import annotations

import argparse
import os
import sys

from .splat_ops import STATS_ENV, growth_headroom


def install_growth_limit(budget: int) -> dict:
    """Patch gsplat's DefaultStrategy so growth stops at ``budget`` splats."""
    import torch
    from gsplat.strategy import DefaultStrategy

    original = DefaultStrategy._grow_gs
    stats = {"budget": budget, "limited_steps": 0, "max_count": 0}

    @torch.no_grad()
    def _grow_gs_capped(self, params, optimizers, state, step):
        count = len(params["means"])
        room = growth_headroom(count, budget)
        grads = state["grad2d"] / state["count"].clamp_min(1)
        candidates = grads > self.grow_grad2d
        screen = None
        if step < self.refine_scale2d_stop_iter and state.get("radii") is not None:
            screen = state["radii"] > self.grow_scale2d
            candidates = candidates | screen
        n_candidates = int(candidates.sum().item())
        if n_candidates > room:
            stats["limited_steps"] += 1
            # Keep only the `room` strongest candidates: zero the others'
            # accumulated gradient (and screen size) so the original rule skips them.
            score = torch.where(candidates, grads, torch.full_like(grads, -1.0))
            if screen is not None:
                score = torch.where(screen, score.clamp_min(0) + 1e9, score)
            drop = torch.ones_like(candidates)
            if room > 0:
                drop[torch.topk(score, room).indices] = False
            state["grad2d"][drop] = 0.0
            if screen is not None:
                state["radii"][drop] = 0.0
        result = original(self, params, optimizers, state, step)
        stats["max_count"] = max(stats["max_count"], len(params["means"]))
        return result

    DefaultStrategy._grow_gs = _grow_gs_capped
    return stats


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        split = argv.index("--")
        own, rest = argv[:split], argv[split + 1 :]
    else:
        own, rest = argv, []
    parser = argparse.ArgumentParser(prog="reconstruction.ns_train_capped")
    parser.add_argument("--budget", type=int, required=True)
    args = parser.parse_args(own)
    stats = install_growth_limit(args.budget)

    from nerfstudio.scripts.train import entrypoint

    sys.argv = ["ns-train", *rest]
    try:
        entrypoint()
    finally:
        path = os.environ.get(STATS_ENV)
        if path:
            import json

            with open(path, "w", encoding="utf-8") as fh:
                json.dump(stats, fh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
