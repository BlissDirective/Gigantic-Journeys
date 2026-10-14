"""Item-6 phase-1 Runpod launcher/job: corpus-only guard, bundle contents, baseline parse."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile

import pytest
from tools import runpod_mapanything as rm
from tools import runpod_mapanything_job as job


def _room(tmp_path, clip_id="rooms/medieval-great-hall-winchester"):
    room = tmp_path / clip_id.split("/")[1]
    (room / "frames").mkdir(parents=True)
    (room / "frames" / "f0.jpg").write_bytes(b"x")
    (room / "sparse").mkdir()
    (room / "sparse" / "images.bin").write_bytes(b"")
    run = {"clip_id": clip_id, "pipeline": {"stage_seconds": {"sfm": 372.3}}, "gpu": "A10G"}
    (room / "run.json").write_text(json.dumps(run))
    return room


def test_corpus_only(tmp_path):
    assert rm.room_clip_id(_room(tmp_path)) == "rooms/medieval-great-hall-winchester"
    with pytest.raises(SystemExit):
        rm.room_clip_id(_room(tmp_path, "owner/bedroom"))


def test_bundle_has_job_rooms_no_cache(tmp_path):
    room = _room(tmp_path)
    out = tmp_path / "b"
    out.mkdir()
    with tarfile.open(rm.bundle([room], out)) as tar:
        names = tar.getnames()
    assert "gj/runpod_mapanything_job.py" in names
    assert "gj/rooms/medieval-great-hall-winchester/run.json" in names
    assert not any("__pycache__" in n for n in names)


def test_baseline_reads_stage_seconds():
    b = job.baseline_from_run(json.loads('{"pipeline":{"stage_seconds":{"sfm":5.0}}}'))
    assert b["sfm_stage_s"] == 5.0


@pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")
def test_setup_script_parses():
    subprocess.run(["bash", "-n", str(rm.HERE / "runpod_mapanything_setup.sh")], check=True)
