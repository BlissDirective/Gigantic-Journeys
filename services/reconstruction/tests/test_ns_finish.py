"""ns_finish PLY scoring helpers (no torch / nerfstudio needed)."""

import argparse

import pytest
from reconstruction.ns_finish import parse_score_ply, ply_fields, ply_header, read_export_ply


def test_parse_score_ply():
    name, path = parse_score_ply("shipped-v1-400k=/vol/a.ply")
    assert name == "shipped-v1-400k" and str(path) == "/vol/a.ply"
    for bad in ("noequals", "=x.ply", "Bad Name=x.ply", "ok="):
        with pytest.raises(argparse.ArgumentTypeError):
            parse_score_ply(bad)


def test_read_export_ply_round_trips_the_export_layout(tmp_path):
    np = pytest.importorskip("numpy")
    fields = ply_fields(9)
    data = np.arange(3 * len(fields), dtype="<f4").reshape(3, len(fields))
    path = tmp_path / "s.ply"
    path.write_bytes(ply_header(3, fields, "1.1.5") + data.tobytes())
    got_fields, got = read_export_ply(path)
    assert got_fields == fields
    assert np.array_equal(got, data)
