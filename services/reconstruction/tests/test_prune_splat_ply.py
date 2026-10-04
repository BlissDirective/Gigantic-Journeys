"""tools.prune_splat_ply on a synthetic splat PLY (box tool; skipped without numpy)."""

import json

import pytest

np = pytest.importorskip("numpy")

from reconstruction.splat_ops import DisplayPrune  # noqa: E402
from tools import prune_splat_ply as tool  # noqa: E402

FIELDS = [
    "x",
    "y",
    "z",
    "opacity",
    "scale_0",
    "scale_1",
    "scale_2",
    "rot_0",
    "rot_1",
    "rot_2",
    "rot_3",
]


def write_ply(path, rows):
    header = f"ply\nformat binary_little_endian 1.0\nelement vertex {len(rows)}\n"
    header += "".join(f"property float {f}\n" for f in FIELDS) + "end_header\n"
    data = np.array([tuple(r) for r in rows], dtype=[(f, "<f4") for f in FIELDS])
    path.write_bytes(header.encode() + data.tobytes())


def cloud(rng, n=4000):
    xyz = rng.uniform(0, 1, size=(n, 3))
    rows = []
    for p in xyz:
        rows.append(
            [*p, 3.0, np.log(rng.uniform(0.003, 0.006)), np.log(0.003), np.log(0.003), 1, 0, 0, 0]
        )
    return rows


def test_prunes_floaters_giants_needles_and_respects_the_budget(tmp_path):
    rng = np.random.default_rng(1)
    rows = cloud(rng)
    rows.append([0.5, 0.5, 0.5, -6.0, -5, -5, -5, 1, 0, 0, 0])  # faint
    rows.append([0.5, 0.5, 0.5, 3.0, np.log(0.5), -5, -5, 1, 0, 0, 0])  # giant
    rows.append([0.2, 0.2, 0.2, 3.0, np.log(0.0057), np.log(1e-4), -9, 1, 0, 0, 0])  # needle
    rows.append([40.0, 40.0, 40.0, 3.0, -5.5, -5.5, -5.5, 1, 0, 0, 0])  # far floater
    src, dst = tmp_path / "in.ply", tmp_path / "out.ply"
    write_ply(src, rows)
    stats_path = tmp_path / "stats.json"
    assert (
        tool.main(
            [
                str(src),
                str(dst),
                "--budget",
                "3000",
                "--density-grid",
                "10",
                "--min-neighbourhood",
                "5",
                "--stats",
                str(stats_path),
            ]
        )
        == 0
    )
    header, out = tool.read_ply(dst)
    stats = json.loads(stats_path.read_text())
    assert len(out) == stats["output"] == 3000
    assert "element vertex 3000" in header
    assert stats["faint"] >= 1 and stats["giant"] >= 1 and stats["needle"] >= 1
    assert out["opacity"].min() > -6.0
    assert out["x"].max() < 2.0, "far floater cropped"
    assert out.dtype.names == tuple(FIELDS), "same vertex layout"


def test_budget_keeps_the_most_opaque(tmp_path):
    rng = np.random.default_rng(2)
    rows = cloud(rng, 2000)
    for i, r in enumerate(rows):
        r[3] = 0.0 if i % 2 else 4.0
    src = tmp_path / "in.ply"
    write_ply(src, rows)
    _, data = tool.read_ply(src)
    idx, stats = tool.prune(data, DisplayPrune(budget=900, min_neighbourhood=0))
    assert stats["output"] == 900
    assert (data["opacity"][idx] == 4.0).all()
