"""SfM adapter selection and the COLMAP SIFT GPU flags (no binaries needed)."""

import subprocess

import pytest
from reconstruction import (
    ColmapSfM,
    GlomapSfM,
    ReconstructionError,
    ScanInput,
    Source,
    select_sfm,
)
from reconstruction import sfm as sfm_module


def test_select_sfm_returns_the_named_adapter():
    assert isinstance(select_sfm("colmap"), ColmapSfM)
    assert isinstance(select_sfm("glomap"), GlomapSfM)
    assert select_sfm("colmap", use_gpu=False).use_gpu is False


def test_select_sfm_rejects_unknown():
    with pytest.raises(ReconstructionError):
        select_sfm("meshroom")


@pytest.mark.parametrize(("use_gpu", "flag"), [(False, "0"), (True, "1")])
def test_colmap_passes_sift_gpu_flags(tmp_path, monkeypatch, use_gpu, flag):
    calls: list[list[str]] = []
    monkeypatch.setattr(sfm_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", lambda argv, check: calls.append([str(a) for a in argv]))
    scan = ScanInput(scan_id="s1", image_dir=tmp_path, image_count=3, source=Source.PUBLIC)
    ColmapSfM(use_gpu=use_gpu).run(scan, tmp_path / "work")

    extract, match, mapper = calls
    assert extract[1] == "feature_extractor"
    assert extract[-2:] == ["--SiftExtraction.use_gpu", flag]
    assert match[1] == "exhaustive_matcher"
    assert match[-2:] == ["--SiftMatching.use_gpu", flag]
    assert mapper[1] == "mapper"
