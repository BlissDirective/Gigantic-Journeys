"""Pure-Python mirrors of the Unity splat path (M1-UNITY-01, build-61 device fix).

Standard library only (CI installs nothing for this service). Three pieces:

* ``decode_package``: reads an aras-p UnityGaussianSplatting 1.1.1 asset's raw files
  (``_pos/_oth/_col/_shs/_chk.bytes``; Norm11 position/scale, 10.10.10.2 rotation,
  Norm8x4 colour in the swizzled 2048-wide texture, Norm6 SH, 256-splat chunks) back to
  linear splats, exactly like ``LoadSplatData`` in ``GaussianSplatting.hlsl``.
* ``linearize``: what the package importer makes of a 3DGS PLY row (sigmoid opacity, exp
  scale, normalised wxyz -> xyzw quaternion, SH0 -> colour, SH rest per coefficient).
* ``gsplat_splat`` / ``unity_splat``: one splat projected and shaded the way gsplat 1.4
  (``rasterize_mode="antialiased"``, eps2d 0.3) and the GJ fork of the package's
  ``CSCalcViewData`` + ``RenderGaussianSplats`` do it, so a test can compare the pixel
  footprint, opacity and colour of the two for the same splat and camera.
  ``package_original=True`` reproduces the unpatched package (no antialiased opacity
  compensation; vertical frustum clamp from the horizontal FOV).

The Unity side models the shipped room: the PLY frame goes into the scene through the
descriptor transform (rotation, scale ``(s, s, -s)``: a mirror), the camera is a Unity
camera (left-handed world, OpenGL view space, projection flipped for a render target as
on Metal / Vulkan).
"""

from __future__ import annotations

import math
import random
import struct
from dataclasses import dataclass, field
from pathlib import Path

SH_C0 = 0.28209479177387814
SH_C1 = 0.4886025119029199
SH_C2 = (
    1.0925484305920792,
    -1.0925484305920792,
    0.31539156525252005,
    -1.0925484305920792,
    0.5462742152960396,
)
CHUNK = 256
TEX_WIDTH = 2048
EPS2D = 0.3

Vec = tuple[float, float, float]


# --- small linear algebra -------------------------------------------------------------


def dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b, strict=True))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b, strict=True))


def scale(a, s: float):
    return tuple(x * s for x in a)


def cross(a, b) -> Vec:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    n = math.sqrt(dot(a, a))
    return tuple(x / n for x in a)


def matmul(a, b):
    return [
        [sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def matvec(m, v):
    return tuple(sum(m[i][k] * v[k] for k in range(len(v))) for i in range(len(m)))


def transpose(m):
    return [list(r) for r in zip(*m, strict=True)]


def inv3(m):
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def quat_wxyz_to_mat(q) -> list[list[float]]:
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ]


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# --- PLY rows -------------------------------------------------------------------------


@dataclass
class RawSplat:
    """A 3DGS / nerfstudio export PLY row (log scale, logit opacity, wxyz, SH channel-major)."""

    pos: Vec
    f_dc: Vec
    f_rest: list[float]  # 45: R coeffs 1..15, then G, then B
    opacity: float
    log_scale: Vec
    rot_wxyz: tuple[float, float, float, float]


@dataclass
class LinearSplat:
    pos: Vec
    rot_xyzw: tuple[float, float, float, float]
    scale: Vec
    color: Vec  # f_dc * SH_C0 + 0.5
    opacity: float
    sh: list[Vec] = field(default_factory=list)  # 15 coefficients, rgb each


def synth_splats(count: int, seed: int = 7) -> list[RawSplat]:
    """Deterministic splats on a jittered 0.25 m lattice (distinct positions)."""
    rnd = random.Random(seed)  # noqa: S311 - test fixture data, not security
    side = max(2, math.ceil(count ** (1 / 3)))
    out = []
    for i in range(count):
        gx, gy, gz = i % side, (i // side) % side, i // (side * side)
        pos = tuple(0.25 * g + rnd.uniform(-0.05, 0.05) - 0.5 for g in (gx, gy, gz))
        out.append(
            RawSplat(
                pos=pos,
                f_dc=tuple(rnd.uniform(-1.5, 1.5) for _ in range(3)),
                f_rest=[rnd.uniform(-0.25, 0.25) for _ in range(45)],
                opacity=rnd.uniform(-3.0, 4.0),
                log_scale=tuple(rnd.uniform(-6.0, -2.0) for _ in range(3)),
                rot_wxyz=tuple(rnd.uniform(-1.0, 1.0) for _ in range(4)),
            )
        )
    return out


def ply_bytes(splats: list[RawSplat]) -> bytes:
    names = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2"]
    names += [f"f_rest_{i}" for i in range(45)]
    names += ["opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    head = "ply\nformat binary_little_endian 1.0\n" + f"element vertex {len(splats)}\n"
    head += "".join(f"property float {n}\n" for n in names) + "end_header\n"
    body = bytearray()
    for s in splats:
        row = [*s.pos, 0.0, 0.0, 0.0, *s.f_dc, *s.f_rest, s.opacity, *s.log_scale, *s.rot_wxyz]
        body += struct.pack(f"<{len(row)}f", *row)
    return head.encode("ascii") + bytes(body)


def linearize(s: RawSplat) -> LinearSplat:
    w, x, y, z = s.rot_wxyz
    n = math.sqrt(w * w + x * x + y * y + z * z)
    return LinearSplat(
        pos=s.pos,
        rot_xyzw=(x / n, y / n, z / n, w / n),
        scale=tuple(math.exp(v) for v in s.log_scale),
        color=tuple(v * SH_C0 + 0.5 for v in s.f_dc),
        opacity=sigmoid(s.opacity),
        sh=[(s.f_rest[k], s.f_rest[15 + k], s.f_rest[30 + k]) for k in range(15)],
    )


# --- package decode -------------------------------------------------------------------


def _half(bits: int) -> float:
    return struct.unpack("<e", struct.pack("<H", bits & 0xFFFF))[0]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _norm11(enc: int) -> Vec:
    return ((enc & 2047) / 2047.0, ((enc >> 11) & 1023) / 1023.0, ((enc >> 21) & 2047) / 2047.0)


def _norm565(enc: int) -> Vec:
    return ((enc & 31) / 31.0, ((enc >> 5) & 63) / 63.0, ((enc >> 11) & 31) / 31.0)


def _decode_rotation(enc: int) -> tuple[float, float, float, float]:
    pq = ((enc & 1023) / 1023.0, ((enc >> 10) & 1023) / 1023.0, ((enc >> 20) & 1023) / 1023.0)
    idx = round(((enc >> 30) & 3) / 3.0 * 3.0)
    q = [v * math.sqrt(2.0) - 1.0 / math.sqrt(2.0) for v in pq]
    w = math.sqrt(1.0 - min(1.0, max(0.0, dot(q, q))))
    x, y, z = q
    if idx == 0:
        return (w, x, y, z)
    if idx == 1:
        return (x, w, y, z)
    if idx == 2:
        return (x, y, w, z)
    return (x, y, z, w)


def _morton_16x16(t: int) -> tuple[int, int]:
    def compact(v: int) -> int:
        v &= 0x55555555
        v = (v ^ (v >> 1)) & 0x33333333
        v = (v ^ (v >> 2)) & 0x0F0F0F0F
        v = (v ^ (v >> 4)) & 0x00FF00FF
        v = (v ^ (v >> 8)) & 0x0000FFFF
        return v

    t &= 0xFF
    return compact(t), compact(t >> 1)


def texture_index(idx: int) -> int:
    """SplatIndexToTextureIndex: 16x16 Morton tiles in a 2048-wide texture."""
    x0, y0 = _morton_16x16(idx)
    tiles = TEX_WIDTH // 16
    tile = idx >> 8
    return ((tile // tiles) * 16 + y0) * TEX_WIDTH + (tile % tiles) * 16 + x0


def _inv_square_centered01(x: float) -> float:
    x -= 0.5
    x *= 0.5
    return math.copysign(math.sqrt(abs(x)), x) + 0.5


def decode_package(files: dict[str, bytes], count: int) -> list[LinearSplat]:
    """Decode the package's Norm11 / Norm11 / Norm8x4 / Norm6 files (the shipped formats)."""
    pos_b, oth_b, col_b, shs_b, chk_b = (files[k] for k in ("pos", "oth", "col", "shs", "chk"))
    chunks = []
    for c in range(len(chk_b) // 64):
        u = struct.unpack_from("<4I6f6I", chk_b, c * 64)
        col = [(_half(v), _half(v >> 16)) for v in u[0:4]]
        posr = [(u[4], u[5]), (u[6], u[7]), (u[8], u[9])]
        scl = [(_half(v), _half(v >> 16)) for v in u[10:13]]
        shr = [(_half(v), _half(v >> 16)) for v in u[13:16]]
        chunks.append((col, posr, scl, shr))
    out = []
    for i in range(count):
        col_r, pos_r, scl_r, sh_r = chunks[i // CHUNK]
        p = _norm11(struct.unpack_from("<I", pos_b, i * 4)[0])
        rot_enc, scl_enc = struct.unpack_from("<II", oth_b, i * 8)
        sc = _norm11(scl_enc)
        rgba = struct.unpack_from("<4B", col_b, texture_index(i) * 4)
        sh_enc = struct.unpack_from("<16H", shs_b, i * 32)
        pos = tuple(_lerp(*pos_r[k], p[k]) for k in range(3))
        s = tuple(_lerp(*scl_r[k], sc[k]) ** 8 for k in range(3))
        c = [_lerp(*col_r[k], rgba[k] / 255.0) for k in range(4)]
        sh = []
        for k in range(15):
            n = _norm565(sh_enc[k])
            sh.append(tuple(_lerp(*sh_r[ch], n[ch]) for ch in range(3)))
        out.append(
            LinearSplat(
                pos=pos,
                rot_xyzw=_decode_rotation(rot_enc),
                scale=s,
                color=(c[0], c[1], c[2]),
                opacity=_inv_square_centered01(c[3]),
                sh=sh,
            )
        )
    return out


def read_package_dir(folder: Path, stem: str) -> dict[str, bytes]:
    return {
        k: (folder / f"{stem}_{k}.bytes").read_bytes() for k in ("pos", "oth", "col", "shs", "chk")
    }


# --- shading --------------------------------------------------------------------------


def sh_color(lin: LinearSplat, dir_splat_minus_cam: Vec, degree: int) -> Vec:
    """3DGS / gsplat SH evaluation (+0.5 is in ``lin.color``), clamped at 0."""
    x, y, z = norm(dir_splat_minus_cam)
    basis = []
    if degree >= 1:
        basis += [-SH_C1 * y, SH_C1 * z, -SH_C1 * x]
    if degree >= 2:
        xx, yy, zz = x * x, y * y, z * z
        basis += [
            SH_C2[0] * x * y,
            SH_C2[1] * y * z,
            SH_C2[2] * (2 * zz - xx - yy),
            SH_C2[3] * x * z,
            SH_C2[4] * (xx - yy),
        ]
    return tuple(
        max(0.0, lin.color[ch] + sum(b * lin.sh[k][ch] for k, b in enumerate(basis)))
        for ch in range(3)
    )


@dataclass
class Footprint:
    """A projected splat: centre (pixels, y down), opacity after compensation, colour."""

    center: tuple[float, float]
    opacity: float
    color: Vec
    conic: tuple[float, float, float]  # inverse 2D covariance (xx, xy, yy), y down
    quad: tuple[tuple[float, float], tuple[float, float]] | None = None  # Unity axis1/axis2

    def alpha(self, px: float, py: float) -> float:
        dx, dy = px - self.center[0], py - self.center[1]
        if self.quad is not None:
            (a, c), (b, d) = self.quad  # offset = p.x * axis1 + p.y * axis2
            det = a * d - b * c
            qx = (d * dx - b * dy) / det
            qy = (-c * dx + a * dy) / det
            if abs(qx) > 2 or abs(qy) > 2:
                return 0.0
            return min(1.0, math.exp(-(qx * qx + qy * qy)) * self.opacity)
        cx, cxy, cy = self.conic
        power = -0.5 * (cx * dx * dx + 2 * cxy * dx * dy + cy * dy * dy)
        return min(0.999, self.opacity * math.exp(power))


@dataclass
class PinholeCamera:
    """OpenCV camera in the PLY frame (x right, y down, z forward), principal point centred."""

    c2w_rot: list[list[float]]
    c2w_pos: Vec
    fy: float
    width: int
    height: int


def _cov3d(lin: LinearSplat):
    x, y, z, w = lin.rot_xyzw
    r = quat_wxyz_to_mat((w, x, y, z))
    rs = [[r[i][j] * lin.scale[j] for j in range(3)] for i in range(3)]
    return matmul(rs, transpose(rs))


def gsplat_splat(lin: LinearSplat, cam: PinholeCamera, degree: int) -> Footprint:
    """gsplat 1.4 fully_fused_projection (antialiased, eps2d 0.3) for one splat."""
    w2c = transpose(cam.c2w_rot)
    t = matvec(w2c, sub(lin.pos, cam.c2w_pos))
    fx = fy = cam.fy
    cx, cy = cam.width / 2.0, cam.height / 2.0
    tan_x, tan_y = 0.5 * cam.width / fx, 0.5 * cam.height / fy
    lim_x_pos = (cam.width - cx) / fx + 0.3 * tan_x
    lim_x_neg = cx / fx + 0.3 * tan_x
    lim_y_pos = (cam.height - cy) / fy + 0.3 * tan_y
    lim_y_neg = cy / fy + 0.3 * tan_y
    tx = t[2] * min(lim_x_pos, max(-lim_x_neg, t[0] / t[2]))
    ty = t[2] * min(lim_y_pos, max(-lim_y_neg, t[1] / t[2]))
    tz = t[2]
    j = [[fx / tz, 0.0, -fx * tx / (tz * tz)], [0.0, fy / tz, -fy * ty / (tz * tz)]]
    cov_c = matmul(matmul(w2c, _cov3d(lin)), transpose(w2c))
    cov2 = matmul(matmul(j, cov_c), transpose(j))
    a, b, d = cov2[0][0], cov2[0][1], cov2[1][1]
    det_orig = a * d - b * b
    a, d = a + EPS2D, d + EPS2D
    det = a * d - b * b
    comp = math.sqrt(max(0.0, det_orig / det))
    center = (fx * t[0] / t[2] + cx, fy * t[1] / t[2] + cy)
    color = sh_color(lin, sub(lin.pos, cam.c2w_pos), degree)
    return Footprint(center, lin.opacity * comp, color, (d / det, -b / det, a / det))


@dataclass
class UnityRoom:
    """The descriptor transform that puts the PLY frame into the Unity scene."""

    position: Vec
    rotation_xyzw: tuple[float, float, float, float]
    scale: Vec  # GJ rooms: (s, s, -s)

    def linear(self):
        x, y, z, w = self.rotation_xyzw
        r = quat_wxyz_to_mat((w, x, y, z))
        return [[r[i][j] * self.scale[j] for j in range(3)] for i in range(3)]

    def object_to_world(self):
        m = self.linear()
        return [m[i] + [self.position[i]] for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def unity_camera_from(cam: PinholeCamera, room: UnityRoom):
    """The Unity camera for the same view: eye, forward, up (world) and right handedness."""
    m = room.linear()
    eye = add(room.position, matvec(m, cam.c2w_pos))
    col = transpose(cam.c2w_rot)
    fwd = norm(matvec(m, col[2]))
    up = norm(matvec(m, scale(col[1], -1.0)))
    return eye, fwd, up


def unity_splat(
    lin: LinearSplat,
    cam: PinholeCamera,
    room: UnityRoom,
    degree: int,
    package_original: bool = False,
) -> Footprint:
    """GJ CSCalcViewData + RenderGaussianSplats for one splat (Metal / Vulkan target)."""
    eye, fwd, up = unity_camera_from(cam, room)
    right = cross(up, fwd)  # Unity (left-handed) camera right
    view = [
        [*right, -dot(right, eye)],
        [*up, -dot(up, eye)],
        [*scale(fwd, -1.0), dot(fwd, eye)],
        [0.0, 0.0, 0.0, 1.0],
    ]
    o2w = room.object_to_world()
    mv = matmul(view, o2w)
    aspect = cam.width / cam.height
    cot = 2.0 * cam.fy / cam.height
    near, far = 0.01, 100.0
    proj = [
        [cot / aspect, 0.0, 0.0, 0.0],
        [0.0, -cot, 0.0, 0.0],  # GPU projection for a render target: y flipped
        [0.0, 0.0, -(far + near) / (far - near), -2 * far * near / (far - near)],
        [0.0, 0.0, -1.0, 0.0],
    ]
    p4 = (*lin.pos, 1.0)
    clip = matvec(matmul(proj, mv), p4)
    ndc = (clip[0] / clip[3], clip[1] / clip[3])
    center = ((ndc[0] + 1) * 0.5 * cam.width, (ndc[1] + 1) * 0.5 * cam.height)

    # CalcCovariance2D (GJ fork: limY from the vertical FOV).
    vp = matvec(mv, p4)[:3]
    if package_original:
        aspect_p = proj[0][0] / proj[1][1]
        tan_fx = 1.0 / proj[0][0]
        tan_fy = 1.0 / (proj[1][1] * aspect_p)
    else:
        tan_fx = 1.0 / abs(proj[0][0])
        tan_fy = 1.0 / abs(proj[1][1])
    lim_x, lim_y = 1.3 * tan_fx, 1.3 * tan_fy
    vx = min(lim_x, max(-lim_x, vp[0] / vp[2])) * vp[2]
    vy = min(lim_y, max(-lim_y, vp[1] / vp[2])) * vp[2]
    vz = vp[2]
    focal = cam.width * proj[0][0] / 2
    jm = [
        [focal / vz, 0.0, -(focal * vx) / (vz * vz)],
        [0.0, focal / vz, -(focal * vy) / (vz * vz)],
        [0.0, 0.0, 0.0],
    ]
    w3 = [row[:3] for row in mv[:3]]
    t = matmul(jm, w3)
    cov = matmul(matmul(t, _cov3d(lin)), transpose(t))
    a, b, d = cov[0][0] + EPS2D, cov[0][1], cov[1][1] + EPS2D

    # DecomposeCovariance (antimatter15 variant used by the package).
    mid = 0.5 * (a + d)
    radius = math.hypot((a - d) / 2.0, b)
    l1 = mid + radius
    l2 = max(mid - radius, 0.1)
    dv = norm((b, l1 - a))
    dv = (dv[0], -dv[1])
    s1 = min(math.sqrt(2.0 * l1), 4096.0)
    s2 = min(math.sqrt(2.0 * l2), 4096.0)
    axis1 = (s1 * dv[0], s1 * dv[1])
    axis2 = (s2 * dv[1], s2 * -dv[0])

    comp = 1.0
    if not package_original:
        det_blur = a * d - b * b
        det_orig = (a - EPS2D) * (d - EPS2D) - b * b
        comp = math.sqrt(max(0.0, det_orig / max(det_blur, 1e-12)))

    # View direction: object-space (camera - centre), negated in ShadeSH.
    center_world = matvec(o2w, p4)[:3]
    m_inv = inv3([row[:3] for row in o2w[:3]])
    obj_view = matvec(m_inv, sub(eye, center_world))
    color = sh_color(lin, scale(obj_view, -1.0), degree)
    det = a * d - b * b
    # Pixel offsets in the flipped target are y down, like the gsplat image.
    return Footprint(center, lin.opacity * comp, color, (d / det, b / det, a / det), (axis1, axis2))
