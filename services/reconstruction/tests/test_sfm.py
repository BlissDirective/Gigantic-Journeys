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

ANALYZER_OUT = """I20260926 model_analyzer.cc:40] Rigs: 1
Cameras: 1
Frames: 311
Registered frames: 311
Images: 311
Registered images: 311
Points: 98765
Observations: 812345
Mean track length: 8.225
Mean observations per image: 2612.04
Mean reprojection error: 0.6123px
"""


def test_select_sfm_returns_the_named_adapter():
    assert isinstance(select_sfm("colmap"), ColmapSfM)
    assert isinstance(select_sfm("glomap"), GlomapSfM)
    assert select_sfm("colmap", use_gpu=False).use_gpu is False
    assert select_sfm("glomap", matcher="exhaustive").matcher == "exhaustive"


def test_unknown_matcher_is_rejected():
    with pytest.raises(ReconstructionError):
        select_sfm("glomap", matcher="spatial")


def test_parse_model_analyzer():
    stats = sfm_module.parse_model_analyzer(ANALYZER_OUT)
    assert stats["registered_images"] == 311
    assert stats["points"] == 98765
    assert stats["mean_reprojection_error_px"] == pytest.approx(0.6123)
    assert stats["mean_track_length"] == pytest.approx(8.225)


def _fake_run(calls):
    def run(argv, check, capture_output=False, text=False):
        calls.append([str(a) for a in argv])
        return subprocess.CompletedProcess(argv, 0, stdout=ANALYZER_OUT, stderr="")

    return run


def test_select_sfm_rejects_unknown():
    with pytest.raises(ReconstructionError):
        select_sfm("meshroom")


@pytest.mark.parametrize(("use_gpu", "flag"), [(False, "0"), (True, "1")])
def test_colmap_passes_gpu_flags(tmp_path, monkeypatch, use_gpu, flag):
    calls: list[list[str]] = []
    monkeypatch.setattr(sfm_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", _fake_run(calls))
    scan = ScanInput(scan_id="s1", image_dir=tmp_path, image_count=3, source=Source.PUBLIC)
    poses = ColmapSfM(use_gpu=use_gpu, matcher="exhaustive").run(scan, tmp_path / "work")

    extract, match, mapper, analyze = calls
    assert extract[1] == "feature_extractor"
    assert extract[-2:] == ["--FeatureExtraction.use_gpu", flag]
    assert match[1] == "exhaustive_matcher"
    assert match[-2:] == ["--FeatureMatching.use_gpu", flag]
    assert mapper[1] == "mapper"
    assert analyze[1] == "model_analyzer"
    assert poses.stats["mapper"] == "incremental"
    assert poses.stats["mean_reprojection_error_px"] == pytest.approx(0.6123)
    assert {"extract_s", "match_s", "map_s", "sfm_s"} <= set(poses.stats)


def test_glomap_runs_view_graph_calibration_then_global_mapper(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(sfm_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", _fake_run(calls))
    scan = ScanInput(scan_id="s1", image_dir=tmp_path, image_count=3, source=Source.PUBLIC)
    poses = GlomapSfM(matcher="sequential").run(scan, tmp_path / "work")

    assert [c[1] for c in calls] == [
        "feature_extractor",
        "sequential_matcher",
        "view_graph_calibrator",
        "global_mapper",
        "model_analyzer",
    ]
    assert "--SequentialMatching.loop_detection" in calls[1]
    assert poses.stats["mapper"] == "global"
    assert "calibrate_s" in poses.stats


def test_largest_model_is_picked(tmp_path):
    import struct

    for name, count in (("0", 5), ("1", 40)):
        d = tmp_path / name
        d.mkdir()
        (d / "images.bin").write_bytes(struct.pack("<Q", count))
    assert sfm_module._largest_model(tmp_path).name == "1"


def test_auto_matcher_is_exhaustive_for_small_captures_sequential_for_long():
    limit = sfm_module.AUTO_EXHAUSTIVE_MAX_IMAGES
    assert sfm_module.resolve_matcher("auto", 311) == "exhaustive"
    assert sfm_module.resolve_matcher("auto", limit) == "exhaustive"
    assert sfm_module.resolve_matcher("auto", limit + 1) == "sequential"
    assert sfm_module.resolve_matcher("vocab_tree", 10) == "vocab_tree"
    with pytest.raises(ReconstructionError):
        sfm_module.resolve_matcher("spatial", 10)


def test_default_adapter_is_incremental_with_auto_matcher(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(sfm_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", _fake_run(calls))
    scan = ScanInput(scan_id="s1", image_dir=tmp_path, image_count=311, source=Source.PUBLIC)
    poses = select_sfm().run(scan, tmp_path / "work")
    assert [c[1] for c in calls] == [
        "feature_extractor",
        "exhaustive_matcher",
        "mapper",
        "model_analyzer",
    ]
    assert poses.stats["matcher"] == "exhaustive"
    assert poses.stats["matcher_requested"] == "auto"
