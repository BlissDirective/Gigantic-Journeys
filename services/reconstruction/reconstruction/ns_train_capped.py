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


# MCMC regularisers (Kheradmand et al., "3D Gaussian Splatting as Markov Chain Monte
# Carlo", and gsplat's simple_trainer / later nerfstudio defaults): an L1 pull on the
# opacities and scales so relocation finds "dead" splats to move to under-fitted areas.
MCMC_OPACITY_REG = 0.01
MCMC_SCALE_REG = 0.01
MCMC_MIN_OPACITY = 0.005
MCMC_REFINE_STOP_FRACTION = 25_000 / 30_000


def install_mcmc(cap: int, stats: dict, iterations: int = 30_000) -> None:
    """Swap Splatfacto's DefaultStrategy for gsplat's MCMCStrategy capped at ``cap``.

    nerfstudio 1.1.5 Splatfacto only builds a DefaultStrategy; gsplat 1.4.0 ships
    MCMCStrategy (Apache-2.0). Differences bridged here: MCMC's ``step_post_backward``
    needs the means learning rate (read from the means optimizer, which the scheduler
    updates), it has no ``absgrad`` attribute and its ``initialize_state`` takes no
    scene scale. The two MCMC regularisers are added to Splatfacto's training loss.
    The growth limit (``install_growth_limit``) only patches DefaultStrategy, so it is
    inert here; MCMC never exceeds ``cap`` by construction.
    """
    import torch
    from gsplat.strategy import MCMCStrategy
    from nerfstudio.models.splatfacto import SplatfactoModel

    class _SplatfactoMCMC(MCMCStrategy):
        absgrad = False

        def initialize_state(self, scene_scale: float = 1.0):  # noqa: ARG002
            return super().initialize_state()

        def step_post_backward(self, params, optimizers, state, step, info, packed=False, lr=None):
            if lr is None:
                lr = optimizers["means"].param_groups[0]["lr"]
            super().step_post_backward(params, optimizers, state, step, info, lr=lr)
            stats["max_count"] = max(stats["max_count"], len(params["means"]))

    populate = SplatfactoModel.populate_modules

    def populate_mcmc(self):
        populate(self)
        self.strategy = _SplatfactoMCMC(
            cap_max=cap,
            refine_start_iter=self.config.warmup_length,
            refine_stop_iter=int(iterations * MCMC_REFINE_STOP_FRACTION),
            refine_every=self.config.refine_every,
            min_opacity=MCMC_MIN_OPACITY,
        )
        self.strategy_state = self.strategy.initialize_state()
        stats["strategy"] = "mcmc"
        stats["mcmc_cap"] = cap

    loss_dict = SplatfactoModel.get_loss_dict

    def get_loss_dict_mcmc(self, outputs, batch, metrics_dict=None):
        loss = loss_dict(self, outputs, batch, metrics_dict)
        if self.training:
            loss["mcmc_opacity_reg"] = (
                MCMC_OPACITY_REG * torch.sigmoid(self.gauss_params["opacities"]).mean()
            )
            loss["mcmc_scale_reg"] = MCMC_SCALE_REG * torch.exp(self.gauss_params["scales"]).mean()
        return loss

    SplatfactoModel.populate_modules = populate_mcmc
    SplatfactoModel.get_loss_dict = get_loss_dict_mcmc


def _max_iterations(rest: list[str]) -> int:
    if "--max-num-iterations" in rest:
        return int(rest[rest.index("--max-num-iterations") + 1])
    return 30_000


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" in argv:
        split = argv.index("--")
        own, rest = argv[:split], argv[split + 1 :]
    else:
        own, rest = argv, []
    parser = argparse.ArgumentParser(prog="reconstruction.ns_train_capped")
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--mcmc-cap", type=int, default=0)
    args = parser.parse_args(own)
    stats = install_growth_limit(args.budget)
    if args.mcmc_cap > 0:
        install_mcmc(args.mcmc_cap, stats, _max_iterations(rest))

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
