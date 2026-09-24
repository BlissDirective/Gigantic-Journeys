"""Data-contract validation and the PLY header parser."""

import pytest
from reconstruction import (
    CollisionMesh,
    CompressedSplat,
    EnvironmentPackage,
    Format,
    ReconstructionConfig,
    ReconstructionError,
    ScanInput,
    Source,
    read_ply_vertex_count,
)


def test_scan_input_rejects_empty_id(tmp_path):
    with pytest.raises(ReconstructionError):
        ScanInput(scan_id="", image_dir=tmp_path, image_count=100, source=Source.CORPUS)


def test_scan_input_rejects_non_positive_count(tmp_path):
    with pytest.raises(ReconstructionError):
        ScanInput(scan_id="s1", image_dir=tmp_path, image_count=0, source=Source.CORPUS)


def test_config_defaults_are_valid():
    config = ReconstructionConfig()
    assert config.splat_budget == 2_000_000
    assert config.compress_format is Format.SPZ
    assert config.sfm == "glomap"


def test_config_rejects_unknown_sfm():
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(sfm="metashape")


def test_config_rejects_bad_budget():
    with pytest.raises(ReconstructionError):
        ReconstructionConfig(splat_budget=0)


def test_read_ply_vertex_count(tmp_path):
    ply = tmp_path / "m.ply"
    ply.write_text("ply\nformat ascii 1.0\nelement vertex 1234\nend_header\n")
    assert read_ply_vertex_count(ply) == 1234


def test_read_ply_vertex_count_rejects_non_ply(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text("not a ply\n")
    with pytest.raises(ReconstructionError):
        read_ply_vertex_count(bad)


def test_total_size_is_splat_plus_mesh(tmp_path):
    splat = CompressedSplat("s1", tmp_path / "s.spz", Format.SPZ, 1000, 2000)
    mesh = CollisionMesh("s1", tmp_path / "s.obj", 500, 200)
    package = EnvironmentPackage(scan_id="s1", splat=splat, mesh=mesh)
    assert package.total_size_bytes == 1200
