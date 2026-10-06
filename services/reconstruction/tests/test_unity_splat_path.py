"""Unity splat path regression tests (M1-UNITY-01, build 61 device distortion).

* Package round trip: a synthetic PLY (``synth_splats(600, seed=7)``, no capture data)
  converted by the pinned aras-p importer with the shipped formats (Norm11 / Norm11 /
  Norm8x4 / Norm6, ``SplatRoomScene.RunConvertPly``) decodes back to the importer's
  linearisation of the same rows within the formats' quantisation steps.
* Shader-math parity: one splat projected and shaded by the GJ fork of the package's
  ``CSCalcViewData`` (Unity camera, mirrored room transform, flipped render target) has
  the same centre, footprint, opacity and SH colour as gsplat 1.4's antialiased
  projection, for SH degree 0..2, portrait and landscape views, and for splats decoded
  from the package as well as straight from the PLY. The unpatched package
  (``package_original``) must fail the same comparison: too opaque small splats, and in
  landscape a footprint stretched by the vertical frustum clamp.

Regenerate the fixture after a package bump: write ``ply_bytes(synth_splats(600, 7))``,
run ``SplatRoomScene.RunConvertPly -gjSplatPly <ply> -gjOutDir Assets/GJTmpFixture`` and
copy the ``_chk/_oth/_pos/_shs`` files and the gzipped ``_col`` file here.
"""

import gzip
import math
from pathlib import Path

import pytest
from tools.unity_splat_math import (
    PinholeCamera,
    UnityRoom,
    add,
    cross,
    decode_package,
    gsplat_splat,
    linearize,
    matvec,
    norm,
    scale,
    sub,
    synth_splats,
    transpose,
    unity_camera_from,
    unity_splat,
)

FIXTURE = Path(__file__).parent / "fixtures" / "unity_package_synth"
COUNT = 600

# The bedroom descriptor's transform (a mirror: z scale negative).
ROOM = UnityRoom(
    position=(0.3647, 1.4357, 0.0756),
    rotation_xyzw=(0.434529, 0.560436, -0.546248, 0.445768),
    scale=(1.5245, 1.5245, -1.5245),
)


def look_at(eye, target) -> list[list[float]]:
    """OpenCV camera-to-world rotation (columns: right, down, forward) with -y up."""
    z = norm(sub(target, eye))
    x = norm(cross((0.0, -1.0, 0.0), z))
    y = cross(z, x)
    return [[x[i], y[i], z[i]] for i in range(3)]


def camera(eye, target, width, height, fov_y_deg) -> PinholeCamera:
    fy = 0.5 * height / math.tan(math.radians(fov_y_deg) / 2)
    return PinholeCamera(look_at(eye, target), eye, fy, width, height)


CAMERAS = {
    "portrait-eval": camera((0.3, -0.2, -2.5), (0.0, 0.0, 0.0), 899, 1599, 57.14),
    "landscape-phone": camera((-0.4, 0.1, -2.0), (0.1, 0.0, 0.2), 1599, 738, 60.0),
    "close-oblique": camera((0.9, -0.6, -1.0), (0.0, 0.1, 0.1), 900, 1600, 57.14),
}


def load_fixture() -> dict[str, bytes]:
    files = {
        k: (FIXTURE / f"gj_synth_fixture_{k}.bytes").read_bytes()
        for k in ("pos", "oth", "shs", "chk")
    }
    files["col"] = gzip.decompress((FIXTURE / "gj_synth_fixture_col.bytes.gz").read_bytes())
    return files


def nearest(splats, pos):
    return min(splats, key=lambda s: sum((a - b) ** 2 for a, b in zip(s.pos, pos, strict=True)))


def test_synthetic_package_decodes_back_to_the_ply_rows():
    decoded = decode_package(load_fixture(), COUNT)
    expected = [linearize(s) for s in synth_splats(COUNT, seed=7)]
    assert len(decoded) == COUNT
    seen = set()
    for d in decoded:
        e = nearest(expected, d.pos)
        seen.add(id(e))
        # Norm11 positions in 256-splat chunks a few lattice cells wide.
        assert max(abs(a - b) for a, b in zip(d.pos, e.pos, strict=True)) < 0.003
        # Rotation (10.10.10.2 smallest-three): same orientation up to sign.
        cos = abs(sum(a * b for a, b in zip(d.rot_xyzw, e.rot_xyzw, strict=True)))
        assert cos > 1 - 1e-4
        # Scale: 11/10-bit steps of scale^(1/8), so a small relative error.
        assert max(abs(a / b - 1) for a, b in zip(d.scale, e.scale, strict=True)) < 0.01
        # SH0 colour and opacity: 8-bit in the chunk range (opacity through its
        # square-centred remap, coarsest around 0.5).
        assert max(abs(a - b) for a, b in zip(d.color, e.color, strict=True)) < 0.005
        assert abs(d.opacity - e.opacity) < 0.06
        # SH rest: 5/6/5 bits over the chunk's shared range (+-0.25 here).
        for k in range(15):
            assert max(abs(a - b) for a, b in zip(d.sh[k], e.sh[k], strict=True)) < 0.02
    assert len(seen) == COUNT, "every PLY row comes back exactly once"


def test_room_transform_keeps_the_view_unmirrored():
    for cam in CAMERAS.values():
        eye, fwd, up = unity_camera_from(cam, ROOM)
        right_unity = cross(up, fwd)  # what a Unity camera with this forward/up calls right
        right_ply = norm(matvec(ROOM.linear(), transpose(cam.c2w_rot)[0]))
        assert max(abs(a - b) for a, b in zip(right_unity, right_ply, strict=True)) < 1e-9
        assert abs(sum(a * b for a, b in zip(fwd, up, strict=True))) < 1e-9
        assert eye == add(ROOM.position, matvec(ROOM.linear(), cam.c2w_pos))


OFFSETS = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.5, -0.5), (-2.0, 1.0), (0.7, 2.2)]


def _compare(lin, cam, degree, package_original=False):
    g = gsplat_splat(lin, cam, degree)
    u = unity_splat(lin, cam, ROOM, degree, package_original)
    return g, u


@pytest.mark.parametrize("cam_name", sorted(CAMERAS))
@pytest.mark.parametrize("degree", [0, 1, 2])
@pytest.mark.parametrize("source", ["ply", "package"])
def test_gj_unity_shader_matches_gsplat_antialiased(cam_name, degree, source):
    cam = CAMERAS[cam_name]
    if source == "ply":
        splats = [linearize(s) for s in synth_splats(60, seed=11)]
    else:
        splats = decode_package(load_fixture(), COUNT)[::10]
    for lin in splats:
        g, u = _compare(lin, cam, degree)
        assert max(abs(a - b) for a, b in zip(g.center, u.center, strict=True)) < 1e-6
        assert u.opacity == pytest.approx(g.opacity, rel=1e-9, abs=1e-12)
        assert max(abs(a - b) for a, b in zip(g.color, u.color, strict=True)) < 1e-9
        # Pixel footprint (shape, orientation and the y-down screen) at offsets from
        # the centre scaled to the splat's size; gsplat clamps alpha at 0.999.
        size = math.sqrt(max(u.quad[0][0] ** 2 + u.quad[0][1] ** 2, 1e-12))
        for dx, dy in OFFSETS:
            px, py = g.center[0] + dx * size * 0.4, g.center[1] + dy * size * 0.4
            ga, ua = g.alpha(px, py), min(u.alpha(px, py), 0.999)
            if ua > 0.0:
                assert ua == pytest.approx(ga, abs=1e-7), (cam_name, lin.pos, dx, dy)
            else:
                # Outside the package's quad (2.83 sigma; gsplat goes to 3): faint there.
                assert ga <= g.opacity * math.exp(-4.0) + 1e-9


def test_unpatched_package_renders_small_splats_too_opaque():
    cam = CAMERAS["portrait-eval"]
    for size_m, at_least in ((0.0008, 1.8), (0.002, 1.15), (0.05, 1.0)):
        lin = linearize(synth_splats(1, seed=5)[0])
        lin.pos = (0.0, 0.0, 0.0)
        lin.scale = (size_m, size_m, size_m)
        g, u = _compare(lin, cam, 0, package_original=True)
        _, fixed = _compare(lin, cam, 0)
        # Sub-pixel to pixel-wide splats keep the 0.3 px^2 filter without its compensation.
        assert u.opacity / g.opacity >= at_least
        assert fixed.opacity == pytest.approx(g.opacity, rel=1e-9)


def test_unpatched_package_stretches_off_screen_splats_in_landscape():
    cam = CAMERAS["landscape-phone"]
    # A 5 cm splat 1 m away, well above the view (3x the vertical half-FOV).
    eye = cam.c2w_pos
    col = transpose(cam.c2w_rot)
    tan_y = 0.5 * cam.height / cam.fy
    center = add(eye, add(scale(col[2], 1.0), scale(col[1], -3.0 * tan_y)))
    lin = linearize(synth_splats(1, seed=3)[0])
    lin.pos = center
    lin.scale = (0.05, 0.05, 0.05)
    lin.rot_xyzw = (0.0, 0.0, 0.0, 1.0)
    g, fixed = _compare(lin, cam, 0)
    _, orig = _compare(lin, cam, 0, package_original=True)

    def extent(fp):
        return max(math.hypot(*fp.quad[0]), math.hypot(*fp.quad[1]))

    def g_extent():
        a, b, d = g.conic  # inverse covariance; the largest axis is 1/sqrt(min eig)
        mid, r = 0.5 * (a + d), math.hypot(0.5 * (a - d), b)
        return math.sqrt(2.0 / (mid - r))

    assert extent(fixed) == pytest.approx(g_extent(), rel=1e-6)
    assert extent(orig) > 1.3 * g_extent()
