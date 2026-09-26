"""Data-contract validation and the PLY header parser."""

import pytest
from reconstruction import (
    OFFSITE_SOURCES,
    CollisionMesh,
    CompressedSplat,
    EnvironmentPackage,
    Format,
    ReconstructionConfig,
    ReconstructionError,
    ScanInput,
    Source,
    read_ply_vertex_count,
    require_offsite_source,
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
    assert config.sfm == "colmap"  # incremental default (spike report 2026-09-26)


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


@pytest.mark.parametrize("value", ["public", "corpus", Source.PUBLIC, Source.CORPUS])
def test_offsite_source_allows_public_and_corpus(value):
    assert require_offsite_source(value) in OFFSITE_SOURCES


@pytest.mark.parametrize("value", ["user", Source.USER, "USER", "", "prod-scan"])
def test_offsite_source_rejects_user_and_unknown(value):
    with pytest.raises(ReconstructionError, match="off-site"):
        require_offsite_source(value)
