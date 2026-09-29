"""M1-SCEN-02 planar-patch segmentation."""

from scenegraph import geometry as g
from scenegraph.mesh import Mesh
from scenegraph.segment import segment_planar


def add_quad(V, T, corners, want):
    """Append a quad (two triangles) oriented so its normal faces ``want``."""
    base = len(V)
    V.extend([(float(x), float(y), float(z)) for x, y, z in corners])
    a, b, c, d = base, base + 1, base + 2, base + 3
    tris = [(a, b, c), (a, c, d)]
    n = g.tri_normal(V[a], V[b], V[c])
    if g.dot(n, want) < 0:
        tris = [(a, c, b), (a, d, c)]
    T.extend(tris)


def test_three_disjoint_quads_are_three_patches():
    V, T = [], []
    # floor +y (large), wall +x (medium), ceiling -y (small) — distinct sizes -> stable order
    add_quad(V, T, [(-3, 0, -3), (3, 0, -3), (3, 0, 3), (-3, 0, 3)], (0, 1, 0))
    add_quad(V, T, [(3, 0, -2), (3, 2, -2), (3, 2, 2), (3, 0, 2)], (1, 0, 0))
    add_quad(V, T, [(-1, 2, -1), (1, 2, -1), (1, 2, 1), (-1, 2, 1)], (0, -1, 0))
    patches = segment_planar(Mesh(V, T))
    assert len(patches) == 3
    # largest first: floor, then wall, then ceiling
    assert patches[0].normal == (0.0, 1.0, 0.0)
    assert patches[1].normal == (1.0, 0.0, 0.0)
    assert patches[2].normal == (0.0, -1.0, 0.0)
    assert patches[0].triangle_count == 2


def test_two_planes_sharing_an_edge_split_by_normal():
    # An open "L": a floor and a wall that share the x-axis edge. Different normals,
    # so they must not merge into one patch even though they are connected.
    V = [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),  # shared edge 0-1
        (2.0, 0.0, 2.0),
        (0.0, 0.0, 2.0),  # floor
        (0.0, 2.0, 0.0),
        (2.0, 2.0, 0.0),  # wall rises from the shared edge
    ]
    T = [(0, 1, 2), (0, 2, 3), (0, 4, 5), (0, 5, 1)]
    patches = segment_planar(Mesh(V, T))
    assert len(patches) == 2
    # The two planes have perpendicular normals (one horizontal floor, one vertical
    # wall), so they must not have merged.
    assert abs(g.dot(patches[0].normal, patches[1].normal)) < 0.01
    horiz = [p for p in patches if abs(p.normal[1]) > 0.5]
    vert = [p for p in patches if abs(p.normal[1]) < 0.5]
    assert len(horiz) == 1 and len(vert) == 1


def test_coplanar_grid_is_one_patch():
    # A 3x3 vertex grid of connected coplanar triangles -> a single patch.
    V, T = [], []
    n = 3
    for i in range(n):
        for j in range(n):
            V.append((float(i), 0.0, float(j)))
    for i in range(n - 1):
        for j in range(n - 1):
            a = i * n + j
            T.append((a, a + 1, a + n))
            T.append((a + 1, a + n + 1, a + n))
    patches = segment_planar(Mesh(V, T))
    assert len(patches) == 1
    assert patches[0].triangle_count == 2 * (n - 1) ** 2


def test_degenerate_triangles_are_skipped():
    V = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)]
    # one real triangle + one degenerate (repeated vertex)
    patches = segment_planar(Mesh(V, [(0, 1, 2), (0, 0, 1)]))
    assert len(patches) == 1
    assert patches[0].triangle_count == 1
