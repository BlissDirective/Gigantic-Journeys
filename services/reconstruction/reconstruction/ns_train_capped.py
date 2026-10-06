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
from pathlib import Path

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


# DN-Splatter-style depth + normal regularisation (capture-render-quality-v1 items 2+3,
# M1-PIPE-03). Starting weights from DN-Splatter's defaults; tuned by the corpus A/B.
DEPTH_PRIOR_WEIGHT = 0.2  # Pearson on rendered inverse depth vs the mono prior
SENSOR_DEPTH_WEIGHT = 0.2  # edge-aware log-L1 vs ARKit / LiDAR depth (when present)
NORMAL_WEIGHT = 0.1  # normal_consistency(rendered normals, prior normals)
NORMAL_TV_WEIGHT = 0.05  # normal_tv(rendered normals)
DEPTH_MIN_ALPHA = 0.5  # only pixels the splat actually covers


def install_depth_normal(
    prior_dir: str | None,
    stats: dict,
    sensor_dir: str | None = None,
    start_step: int = 500,
    weights: tuple[float, float, float, float] = (
        DEPTH_PRIOR_WEIGHT,
        SENSOR_DEPTH_WEIGHT,
        NORMAL_WEIGHT,
        NORMAL_TV_WEIGHT,
    ),
) -> None:
    """Add the ``dn_torch`` losses (mirrors of ``depth_normal.py``) to Splatfacto's loss.

    * prior (``depth_prior_cache`` folder, Depth Anything V2 *Small* disparity): aligned to
      the rendered inverse depth with ``dn_torch.align_scale_shift`` (the ``depth_prior``
      contract; ARKit depth replaces the rendered reference once captures carry it), then
      ``pearson_depth_loss`` on inverse depth, and normals derived from the aligned prior
      (``normals_from_depth``; no monocular-normal network) drive ``normal_consistency``.
    * sensor (optional ``<stem>.depth.f32`` metric depth, ARKit/LiDAR): ``edge_aware_log_l1``.
    * ``normal_tv`` on the rendered normals.
    The datamanager attaches each frame's maps to the batch by its image file stem.
    """
    import torch
    from nerfstudio.data.datamanagers.full_images_datamanager import FullImageDatamanager
    from nerfstudio.models.splatfacto import SplatfactoModel

    from . import dn_torch as dt
    from .depth_prior_cache import read_map

    w_prior, w_sensor, w_normal, w_tv = weights
    stats.update(
        depth_normal={
            "prior_dir": bool(prior_dir),
            "sensor_dir": bool(sensor_dir),
            "weights": list(weights),
            "start_step": start_step,
            "applied_steps": 0,
            "frames_with_prior": 0,
        }
    )
    cache: dict = {}

    next_train = FullImageDatamanager.next_train

    def next_train_dn(self, step):
        camera, data = next_train(self, step)
        idx = int(camera.metadata["cam_idx"])
        if idx not in cache:
            stem = Path(self.train_dataset.image_filenames[idx]).stem
            prior = read_map(Path(prior_dir), stem) if prior_dir else None
            sensor = read_map(Path(sensor_dir), stem) if sensor_dir else None
            cache[idx] = tuple(
                torch.from_numpy(m).float() if m is not None else None for m in (prior, sensor)
            )
            stats["depth_normal"]["frames_with_prior"] += prior is not None
        prior, sensor = cache[idx]
        if prior is not None:
            data["gj_prior"] = prior.to(self.device)
        if sensor is not None:
            data["gj_sensor"] = sensor.to(self.device)
        return camera, data

    populate = SplatfactoModel.populate_modules

    def populate_dn(self):
        populate(self)
        self.config.output_depth_during_training = True

    get_outputs = SplatfactoModel.get_outputs

    def get_outputs_dn(self, camera):
        c = camera[0] if camera.shape else camera
        self._gj_intr = tuple(float(v) for v in (c.fx, c.fy, c.cx, c.cy, c.width))
        return get_outputs(self, camera)

    loss_dict = SplatfactoModel.get_loss_dict

    def resize(m, h, w):
        return torch.nn.functional.interpolate(
            m[None, None], size=(h, w), mode="bilinear", align_corners=False
        )[0, 0]

    def get_loss_dict_dn(self, outputs, batch, metrics_dict=None):
        loss = loss_dict(self, outputs, batch, metrics_dict)
        depth = outputs.get("depth")
        if not self.training or depth is None or self.step < start_step:
            return loss
        depth = depth[..., 0]
        h, w = depth.shape
        valid = outputs["accumulation"][..., 0] > DEPTH_MIN_ALPHA
        fx, fy, cx, cy, width = self._gj_intr
        k = w / width
        normals = dt.normals_from_depth(depth, fx * k, fy * k, cx * k, cy * k)
        applied = False
        if "gj_prior" in batch:
            disp = resize(batch["gj_prior"], h, w)
            inv = 1.0 / depth.clamp_min(1e-3)
            m = valid & (disp > 0)
            if int(m.sum()) > 64:
                loss["dn_prior_pearson"] = w_prior * dt.pearson_depth_loss(inv, disp, m)
                aligned = dt.to_metric(disp, inv.detach(), m).clamp_min(1e-3)
                prior_n = dt.normals_from_depth(1.0 / aligned, fx * k, fy * k, cx * k, cy * k)
                loss["dn_normal"] = w_normal * dt.normal_consistency(normals, prior_n, m)
                applied = True
        if "gj_sensor" in batch:
            gt = resize(batch["gj_sensor"], h, w)
            gray = self.get_gt_img(batch["image"])[..., :3].mean(-1)
            gray = resize(gray, h, w) if gray.shape != (h, w) else gray
            loss["dn_sensor"] = w_sensor * dt.edge_aware_log_l1(depth, gt, gray, valid)
            applied = True
        if applied:
            loss["dn_normal_tv"] = w_tv * dt.normal_tv(normals, valid)
            stats["depth_normal"]["applied_steps"] += 1
        return loss

    FullImageDatamanager.next_train = next_train_dn
    SplatfactoModel.populate_modules = populate_dn
    SplatfactoModel.get_outputs = get_outputs_dn
    SplatfactoModel.get_loss_dict = get_loss_dict_dn


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
    parser.add_argument("--depth-prior-dir", default="")
    parser.add_argument("--sensor-depth-dir", default="")
    args = parser.parse_args(own)
    stats = install_growth_limit(args.budget)
    if args.mcmc_cap > 0:
        install_mcmc(args.mcmc_cap, stats, _max_iterations(rest))
    if args.depth_prior_dir or args.sensor_depth_dir:
        # After install_mcmc: both wrap get_loss_dict, so the losses add up.
        install_depth_normal(args.depth_prior_dir or None, stats, args.sensor_depth_dir or None)

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
