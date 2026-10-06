"""Torch mirror of the DN-Splatter / mono-prior Brain-B contracts (runs in the CUDA container).

capture-render-quality-v1 items 2+3 (M1-PIPE-03). The math is the data contract in
``depth_normal.py`` (losses) and ``depth_prior.py`` (scale/shift alignment); this module
re-expresses it on torch tensors so Splatfacto can apply it to the *rendered* depth inside
the training loop (``ns_train_capped.install_depth_normal``). Do not change the math here
without changing the stdlib reference: ``tests/test_dn_torch.py`` asserts parity against it
(skipped where torch is absent, e.g. CI).

Shapes: depth / image / mask are ``[H, W]``; normals ``[H, W, 3]``. ``mask`` is boolean.
Pixels with non-positive ground-truth depth are always invalid (as in the reference).
Edge cases return a zero tensor like the reference returns ``0.0``.

Also here (no reference needed, pure geometry): ``normals_from_depth`` derives camera-space
normals from a depth map and the intrinsics, so the normal losses need **no monocular-normal
network** (and no extra weights licence, capture-render-quality-v1 §2).

torch is imported lazily so the package still imports without it.
"""

from __future__ import annotations


def _t():
    import torch

    return torch


def _valid(gt, mask):
    v = gt > 0
    return v & mask if mask is not None else v


def image_gradient_mag(image):
    """Forward-difference gradient magnitude, 0 on the last column / row (reference rule)."""
    torch = _t()
    gx = torch.zeros_like(image)
    gy = torch.zeros_like(image)
    gx[:, :-1] = image[:, 1:] - image[:, :-1]
    gy[:-1, :] = image[1:, :] - image[:-1, :]
    return torch.sqrt(gx * gx + gy * gy)


def edge_aware_log_l1(pred, gt, image, mask=None, *, edge_weight: float = 1.0):
    """Mirror of ``depth_normal.edge_aware_log_l1`` (sensor depth, ARKit / LiDAR)."""
    torch = _t()
    if pred.shape != gt.shape or image.shape != gt.shape:
        raise ValueError("pred, gt, image must share dimensions")
    v = _valid(gt, mask) & (pred > 0)
    if not bool(v.any()):
        return pred.sum() * 0.0
    w = torch.exp(-edge_weight * image_gradient_mag(image))
    err = w * (torch.log1p(pred.clamp_min(0)) - torch.log1p(gt.clamp_min(0))).abs()
    return err[v].mean()


def pearson_depth_loss(pred, gt, mask=None):
    """Mirror of ``depth_normal.pearson_depth_loss``: 1 - Pearson r (scale/shift invariant)."""
    if pred.shape != gt.shape:
        raise ValueError("pred and gt must share dimensions")
    v = _valid(gt, mask)
    if int(v.sum()) < 2:
        return pred.sum() * 0.0
    p = pred[v]
    g = gt[v]
    p = p - p.mean()
    g = g - g.mean()
    vp = (p * p).sum()
    vg = (g * g).sum()
    if float(vp.detach()) <= 0.0 or float(vg.detach()) <= 0.0:
        return pred.sum() * 0.0
    corr = (p * g).sum() / (vp * vg).sqrt()
    return 1.0 - corr.clamp(-1.0, 1.0)


def _unit(n):
    m = n.norm(dim=-1, keepdim=True)
    return n / m.clamp_min(1e-12) * (m > 0)


def normal_consistency(pred, ref, mask=None):
    """Mirror of ``depth_normal.normal_consistency``: 1 - mean cosine."""
    cos = (_unit(pred) * _unit(ref)).sum(-1)
    if mask is not None:
        if not bool(mask.any()):
            return pred.sum() * 0.0
        cos = cos[mask]
    return 1.0 - cos.mean()


def normal_tv(normals, mask=None):
    """Mirror of ``depth_normal.normal_tv``: mean L2 to the right / down neighbour."""
    torch = _t()
    dx = (normals[:, 1:] - normals[:, :-1]).norm(dim=-1)
    dy = (normals[1:, :] - normals[:-1, :]).norm(dim=-1)
    if mask is not None:
        dx = dx[mask[:, 1:] & mask[:, :-1]]
        dy = dy[mask[1:, :] & mask[:-1, :]]
    else:
        dx, dy = dx.flatten(), dy.flatten()
    n = dx.numel() + dy.numel()
    if n == 0:
        return normals.sum() * 0.0
    return (dx.sum() + dy.sum()) / torch.tensor(float(n), device=normals.device)


def align_scale_shift(relative, metric, mask=None):
    """Mirror of ``depth_prior.align_scale_shift``: least-squares (scale, shift)."""
    v = metric > 0
    if mask is not None:
        v = v & mask
    if int(v.sum()) < 2:
        raise ValueError("need at least 2 valid pixels to align scale/shift")
    r = relative[v]
    m = metric[v]
    mr, mm = r.mean(), m.mean()
    var = ((r - mr) ** 2).sum()
    if float(var.detach()) <= 0.0:
        raise ValueError("relative depth has no variance; cannot solve scale")
    scale = ((r - mr) * (m - mm)).sum() / var
    return scale, mm - scale * mr


def to_metric(relative, metric, mask=None):
    """Mirror of ``depth_prior.to_metric``."""
    scale, shift = align_scale_shift(relative, metric, mask)
    return scale * relative + shift


def normals_from_depth(depth, fx: float, fy: float, cx: float, cy: float):
    """Camera-space unit normals ``[H, W, 3]`` from a depth map (central differences).

    OpenCV camera (x right, y down, z forward); normals face the camera (negative z).
    Border pixels copy their neighbour; invalid (<= 0) depth gives a zero normal.
    """
    torch = _t()
    h, w = depth.shape
    ys, xs = torch.meshgrid(
        torch.arange(h, device=depth.device, dtype=depth.dtype),
        torch.arange(w, device=depth.device, dtype=depth.dtype),
        indexing="ij",
    )
    pts = torch.stack(((xs - cx) / fx * depth, (ys - cy) / fy * depth, depth), dim=-1)
    pad = torch.nn.functional.pad(pts.permute(2, 0, 1)[None], (1, 1, 1, 1), mode="replicate")[0]
    pad = pad.permute(1, 2, 0)
    du = pad[1:-1, 2:] - pad[1:-1, :-2]
    dv = pad[2:, 1:-1] - pad[:-2, 1:-1]
    n = torch.cross(du, dv, dim=-1)
    n = torch.where(n[..., 2:3] > 0, -n, n)
    return _unit(n) * (depth > 0)[..., None]
