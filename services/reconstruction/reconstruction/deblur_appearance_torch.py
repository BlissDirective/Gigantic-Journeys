"""Training-time BAD-Gaussians deblur + Splatfacto-W appearance (items 4+5), torch side.

capture-render-quality-v1 (external-synthesis-builds.md), M1-PIPE-03. **Method-only
reimplementation** (AUTH #049): written from the papers' published method against the
pinned nerfstudio 1.1.5 / gsplat 1.4.0 Splatfacto; no BAD-Gaussians or Splatfacto-W code
or weights are copied (both upstreams are Apache-2.0 anyway; neither ships weights), and
nothing comes from academic Inria 3DGS forks.

* **Deblur (BAD-Gaussians).** Each training image gets a learnable in-exposure camera
  trajectory: start/end offsets ``delta_s, delta_e`` in se(3) (zero-initialised, so it
  starts as the sharp model). ``N`` virtual sub-frames along the trajectory are rendered
  and averaged, and the average is compared with the (possibly blurred) photo. The
  trajectory is linear in the Lie algebra around the recorded pose: the small-angle form
  of ``exposure_trajectory.sample_linear`` (slerp/lerp), with ``exposure_weights``
  averaging. Novel / eval views render the single recorded pose (sharp).
* **Appearance (Splatfacto-W).** Each training image gets a learned embedding -> small
  MLP -> affine colour transform (3x3 matrix + bias: exposure, white balance, colour
  drift), zero-initialised last layer so it starts at identity. Applied to the rendered
  RGB for training images only; eval / novel views use the canonical identity transform,
  exactly ``appearance.AppearanceModel.transform_for(None)``.

Both are installed by ``ns_train_capped`` (``--deblur-samples`` / ``--appearance``) by
wrapping ``SplatfactoModel.get_outputs`` / ``get_loss_dict``. Their parameters live in a
private Adam stepped lazily at the start of the next training forward (the gradients of
the previous backward), so nerfstudio's optimizer config is untouched. torch is imported
lazily; the module imports on CPU-only CI.
"""

from __future__ import annotations

DEBLUR_LR = 5e-4
APPEARANCE_LR = 1e-3
APPEARANCE_DIM = 32
APPEARANCE_REG = 1e-2  # pulls the transforms toward identity (keeps a canonical look)


def so3_exp(w):
    """Rodrigues: axis-angle (..., 3) -> rotation matrices (..., 3, 3); exact near 0."""
    import torch

    theta2 = (w * w).sum(-1, keepdim=True)[..., None]
    theta = theta2.clamp_min(1e-12).sqrt()
    zero = torch.zeros_like(w[..., 0])
    k = torch.stack(
        [zero, -w[..., 2], w[..., 1], w[..., 2], zero, -w[..., 0], -w[..., 1], w[..., 0], zero],
        dim=-1,
    ).reshape(*w.shape[:-1], 3, 3)
    small = theta2 < 1e-8
    a = torch.where(small, 1 - theta2 / 6, torch.sin(theta) / theta)
    b = torch.where(small, 0.5 - theta2 / 24, (1 - torch.cos(theta)) / theta2.clamp_min(1e-12))
    eye = torch.eye(3, dtype=w.dtype, device=w.device).expand_as(k)
    return eye + a * k + b * (k @ k)


def apply_delta(c2w, delta):
    """Right-multiply a camera-to-world (3, 4) by exp(delta) (delta = [w(3), v(3)])."""
    import torch

    r = so3_exp(delta[..., :3])
    rot = c2w[..., :3, :3] @ r
    trans = c2w[..., :3, 3] + (c2w[..., :3, :3] @ delta[..., 3:, None])[..., 0]
    return torch.cat([rot, trans[..., None]], dim=-1)


def trajectory_deltas(delta_s, delta_e, num_samples: int):
    """(N, 6) deltas from start (t=0) to end (t=1); N=1 -> mid (exposure_trajectory)."""
    import torch

    if num_samples < 1:
        raise ValueError("num_samples must be >= 1")
    if num_samples == 1:
        t = torch.tensor([0.5], dtype=delta_s.dtype, device=delta_s.device)
    else:
        t = torch.linspace(0.0, 1.0, num_samples, dtype=delta_s.dtype, device=delta_s.device)
    return (1 - t)[:, None] * delta_s[None] + t[:, None] * delta_e[None]


def render_order(num_samples: int) -> list[int]:
    """Sub-frame render order with the mid-exposure sample LAST, so gsplat's densification
    statistics (taken from the last rasterisation) come from the recorded pose."""
    mid = (num_samples - 1) // 2
    return [k for k in range(num_samples) if k != mid] + [mid]


class TrainState:
    """Per-image deblur trajectories + appearance MLP, with a private lazily-stepped Adam."""

    def __init__(self, num_images: int, device, deblur_samples: int, appearance: bool) -> None:
        import torch

        self.deblur_samples = deblur_samples
        self.appearance = appearance
        params: list[dict] = []
        self.delta = None
        if deblur_samples > 1:
            self.delta = torch.nn.Parameter(torch.zeros(num_images, 2, 6, device=device))
            params.append({"params": [self.delta], "lr": DEBLUR_LR})
        self.embed = self.mlp = None
        if appearance:
            self.embed = torch.nn.Embedding(num_images, APPEARANCE_DIM).to(device)
            torch.nn.init.normal_(self.embed.weight, std=0.01)
            self.mlp = torch.nn.Sequential(
                torch.nn.Linear(APPEARANCE_DIM, 64), torch.nn.ReLU(), torch.nn.Linear(64, 12)
            ).to(device)
            torch.nn.init.zeros_(self.mlp[-1].weight)
            torch.nn.init.zeros_(self.mlp[-1].bias)
            params.append(
                {
                    "params": [*self.embed.parameters(), *self.mlp.parameters()],
                    "lr": APPEARANCE_LR,
                }
            )
        self.opt = torch.optim.Adam(params) if params else None
        self.steps = 0

    def step_pending(self) -> None:
        """Apply the gradients left by the previous backward, then clear them."""
        if self.opt is None:
            return
        groups = [p for g in self.opt.param_groups for p in g["params"]]
        if any(p.grad is not None for p in groups):
            self.opt.step()
            self.steps += 1
        self.opt.zero_grad(set_to_none=True)

    def sub_poses(self, c2w, idx: int):
        """(N, 3, 4) in-exposure poses for training image ``idx``."""
        d = trajectory_deltas(self.delta[idx, 0], self.delta[idx, 1], self.deblur_samples)
        return apply_delta(c2w[None].expand(len(d), 3, 4), d)

    def color_transform(self, idx: int):
        """(3x3 matrix, bias) for training image ``idx``; identity at initialisation."""
        import torch

        out = self.mlp(self.embed(torch.tensor([idx], device=self.embed.weight.device)))[0]
        eye = torch.eye(3, device=out.device, dtype=out.dtype)
        return eye + out[:9].reshape(3, 3), out[9:]

    def apply_color(self, rgb, idx: int):
        m, b = self.color_transform(idx)
        return (rgb @ m.T + b).clamp(0.0, 1.0)

    def reg_loss(self, idx: int):
        m, b = self.color_transform(idx)
        import torch

        eye = torch.eye(3, device=m.device, dtype=m.dtype)
        return APPEARANCE_REG * (((m - eye) ** 2).sum() + (b**2).sum())


def with_pose(camera, c2w):
    """Shallow copy of a nerfstudio ``Cameras`` with a new ``camera_to_worlds`` (no re-init)."""
    import copy

    cam = copy.copy(camera)
    object.__setattr__(cam, "camera_to_worlds", c2w)
    return cam


def install_deblur_appearance(stats: dict, deblur_samples: int, appearance: bool) -> None:
    """Patch Splatfacto so training renders blur-aware and appearance-corrected."""
    import torch
    from nerfstudio.models.splatfacto import SplatfactoModel

    stats.update(
        deblur_appearance={
            "deblur_samples": deblur_samples,
            "appearance": appearance,
            "method": "method-only reimplementation (AUTH #049)",
            "applied_steps": 0,
        }
    )
    get_outputs = SplatfactoModel.get_outputs
    loss_dict = SplatfactoModel.get_loss_dict

    def state(model) -> TrainState:
        st = getattr(model, "_gj_da", None)
        if st is None:
            st = TrainState(model.num_train_data, model.device, deblur_samples, appearance)
            model._gj_da = st
        return st

    def get_outputs_da(self, camera):
        meta = camera.metadata or {}
        if not self.training or "cam_idx" not in meta:
            return get_outputs(self, camera)  # eval / novel views: sharp + canonical
        idx = int(meta["cam_idx"])
        st = state(self)
        st.step_pending()
        self._gj_idx = idx
        if st.delta is not None:
            poses = st.sub_poses(camera.camera_to_worlds.reshape(-1, 3, 4)[0], idx)
            renders = [
                get_outputs(self, with_pose(camera, poses[k][None]))
                for k in render_order(st.deblur_samples)
            ]
            out = dict(renders[-1])  # mid-exposure: depth / alpha / densify stats
            out["rgb"] = torch.stack([r["rgb"] for r in renders]).mean(0)
        else:
            out = get_outputs(self, camera)
        if st.embed is not None:
            out["rgb"] = st.apply_color(out["rgb"], idx)
        stats["deblur_appearance"]["applied_steps"] += 1
        return out

    def get_loss_dict_da(self, outputs, batch, metrics_dict=None):
        loss = loss_dict(self, outputs, batch, metrics_dict)
        st = getattr(self, "_gj_da", None)
        if self.training and st is not None and st.embed is not None:
            loss["appearance_reg"] = st.reg_loss(self._gj_idx)
        return loss

    SplatfactoModel.get_outputs = get_outputs_da
    SplatfactoModel.get_loss_dict = get_loss_dict_da
