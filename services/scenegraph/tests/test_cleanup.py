"""M1-SCEN-01 mesh cleanup tests on synthetic meshes (AT-2)."""

from pathlib import Path

from scenegraph.cleanup import CleanupConfig, boundary_loops, clean_mesh, remove_floaters
from scenegraph.mesh import Mesh, read_obj, write_obj

# ---- synthetic mesh builders ----

# Unit cube, y up. 8 verts, 6 quad faces each split into 2 triangles. Every edge
# is shared by exactly two triangles, so a full cube is watertight.
_CUBE_V = [
    (0, 0, 0),
    (1, 0, 0),
    (1, 0, 1),
    (0, 0, 1),  # bottom y=0
    (0, 1, 0),
    (1, 1, 0),
    (1, 1, 1),
    (0, 1, 1),  # top y=1
]
_CUBE_QUADS = {
    "bottom": (0, 1, 2, 3),
    "top": (4, 5, 6, 7),
    "side01": (0, 1, 5, 4),
    "side12": (1, 2, 6, 5),
    "side23": (2, 3, 7, 6),
    "side30": (3, 0, 4, 7),
}


def _quad_tris(q):
    return [(q[0], q[1], q[2]), (q[0], q[2], q[3])]


def cube(drop=()):
    tris = []
    for name, q in _CUBE_QUADS.items():
        if name in drop:
            continue
        tris += _quad_tris(q)
    return Mesh([(float(a), float(b), float(c)) for a, b, c in _CUBE_V], tris)


def grid_plane(n):
    """n x n vertex grid in the y=0 plane -> 2*(n-1)^2 connected triangles."""
    verts = [(float(i), 0.0, float(j)) for i in range(n) for j in range(n)]
    tris = []
    for i in range(n - 1):
        for j in range(n - 1):
            a = i * n + j
            b = a + 1
            c = a + n
            d = c + 1
            tris += [(a, b, c), (b, d, c)]
    return Mesh(verts, tris)


# ---- tests ----


def test_full_cube_is_watertight_and_unchanged():
    mesh = cube()
    assert mesh.is_watertight()
    cleaned, stats = clean_mesh(mesh)
    assert stats.watertight
    assert stats.floater_triangles_removed == 0
    assert stats.holes_filled == 0
    assert stats.ceiling_capped == 0


def test_floater_removed():
    base = grid_plane(8)  # 98 triangles, one component
    v = list(base.vertices)
    t = list(base.triangles)
    o = len(v)
    v += [(50.0, 50.0, 50.0), (51.0, 50.0, 50.0), (50.0, 51.0, 50.0)]
    t.append((o, o + 1, o + 2))  # a lone floating triangle, ~1% of the mesh
    mesh = Mesh(v, t)
    cleaned, stats = clean_mesh(mesh, CleanupConfig(min_component_fraction=0.02))
    assert stats.components == 2
    assert stats.floater_triangles_removed == 1
    # the floater's far-away vertices are gone
    assert all(x < 40 for (x, _, _) in cleaned.vertices)


def test_small_hole_filled_watertight():
    mesh = cube(drop=("bottom",))  # a 4-edge hole in the floor
    assert not mesh.is_watertight()
    cleaned, stats = clean_mesh(mesh, CleanupConfig(max_hole_edges=40))
    assert stats.holes_filled == 1
    assert stats.watertight
    assert cleaned.is_watertight()


def test_ceiling_capped_when_loop_is_large():
    # max_hole_edges=3 makes the 4-edge top loop NOT a "small hole"; the ceiling
    # rule fills it because its centroid sits at the top of the up-range.
    mesh = cube(drop=("top",))
    cleaned, stats = clean_mesh(mesh, CleanupConfig(max_hole_edges=3, ceiling_band=0.2))
    assert stats.ceiling_capped == 1
    assert stats.holes_filled == 0
    assert stats.watertight


def test_large_side_opening_left_open():
    # A large opening on a side wall (mid-height) is a doorway/window: not small,
    # not the ceiling, so it is left open.
    mesh = cube(drop=("side12",))
    cleaned, stats = clean_mesh(mesh, CleanupConfig(max_hole_edges=3, ceiling_band=0.2))
    assert stats.holes_filled == 0
    assert stats.ceiling_capped == 0
    assert not stats.watertight


def test_fill_all_holes_forces_watertight():
    mesh = cube(drop=("side12",))
    cleaned, stats = clean_mesh(mesh, CleanupConfig(max_hole_edges=3, fill_all_holes=True))
    assert stats.watertight


def test_boundary_loops_on_open_cube():
    mesh = cube(drop=("top",))
    loops = boundary_loops(mesh)
    assert len(loops) == 1
    assert set(loops[0]) == {4, 5, 6, 7}


def test_degenerate_triangles_dropped():
    v = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    v = [(float(a), float(b), float(c)) for a, b, c in v]
    mesh = Mesh(v, [(0, 1, 2), (0, 0, 1), (1, 1, 1)])  # two degenerate
    _, stats = clean_mesh(mesh)
    assert stats.degenerate_removed == 2


def test_obj_roundtrip(tmp_path: Path):
    mesh = cube()
    p = tmp_path / "cube.obj"
    write_obj(mesh, p)
    back = read_obj(p)
    assert back.vertex_count == mesh.vertex_count
    assert back.triangle_count == mesh.triangle_count
    assert back.is_watertight()


def test_obj_face_formats(tmp_path: Path):
    p = tmp_path / "faces.obj"
    p.write_text(
        "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 1 1 0\n"
        "f 1/1/1 2/2/2 3/3/3\n"  # v/vt/vn
        "f 2 4 3\n",  # plain, quad-free
        encoding="utf-8",
    )
    mesh = read_obj(p)
    assert mesh.vertex_count == 4
    assert mesh.triangle_count == 2


def test_remove_floaters_keeps_largest_even_if_below_threshold():
    # Two tiny equal components; the largest is always kept.
    a = Mesh([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1, 2)])
    mesh = Mesh(
        a.vertices + [(9.0, 9.0, 9.0), (9.0, 9.0, 9.0)][:0] + [(9, 0, 0), (10, 0, 0), (9, 1, 0)],
        [(0, 1, 2), (3, 4, 5)],
    )
    kept, comps, removed = remove_floaters(mesh, min_fraction=0.9)
    assert comps == 2
    assert removed == 1  # one kept (largest/first), one dropped
    assert kept.triangle_count == 1
