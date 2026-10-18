"""AUTH #051 guards of the bedroom stage-2 Runpod launcher (no network, no pods)."""

from __future__ import annotations

import json
import tarfile

import pytest
from tools import runpod_bedroom as rbd
from tools import runpod_bedroom_job as job


def test_auth_gate(tmp_path):
    log = tmp_path / "log.md"
    log.write_text(
        "| #050 | x |\n| #051 | 2026-10-17 | Runpod Secure Cloud ... | **APPROVED** by Owner |\n"
    )
    assert rbd.auth_051_approved(log)
    log.write_text("| #051 | 2026-10-17 | Runpod Secure Cloud ... | pending |\n")
    assert not rbd.auth_051_approved(log)
    log.write_text("Next free number: #051\n")
    assert not rbd.auth_051_approved(log)


def test_frames_must_be_the_blurred_set(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "f0.jpg").write_bytes(b"x")
    with pytest.raises(SystemExit):
        rbd.check_frames(raw)
    blurred = tmp_path / "blurred"
    blurred.mkdir()
    (blurred / "f0.jpg").write_bytes(b"x")
    with pytest.raises(SystemExit):  # no blur_log.json beside it
        rbd.check_frames(blurred)
    (tmp_path / "blur_log.json").write_text("{}")
    assert rbd.check_frames(blurred) == 1


def test_out_must_be_private_staging(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        rbd.check_out(tmp_path / "out")
    monkeypatch.setattr(rbd, "STAGING_ROOT", tmp_path)
    out = rbd.check_out(tmp_path / "work" / "stage2")
    assert out.is_dir() and (out.stat().st_mode & 0o777) == 0o700


def test_ledger_and_bundle(tmp_path):
    assert rbd.ledger_spent(tmp_path / "none.json") == 0.0
    led = tmp_path / "l.json"
    led.write_text(json.dumps([{"est_usd": 1.25}, {"est_usd": 0.5}]))
    assert rbd.ledger_spent(led) == 1.75
    frames, sparse = tmp_path / "blurred", tmp_path / "sparse"
    frames.mkdir()
    sparse.mkdir()
    (frames / "f0.jpg").write_bytes(b"x")
    for part in ("cameras.bin", "images.bin", "points3D.bin", "frames.bin"):
        (sparse / part).write_bytes(b"0")
    with tarfile.open(rbd.bundle(frames, sparse, tmp_path)) as tar:
        names = tar.getnames()
    assert "gj/data/frames/f0.jpg" in names and "gj/runpod_bedroom_job.py" in names
    assert "gj/data/sparse/frames.bin" not in names
    assert not any("raw" in n.split("/") for n in names)


def test_recipe_scales_densify_threshold_with_deblur():
    pytest.importorskip("numpy")
    base = job.recipe_args(1)
    assert "--pipeline.model.densify-grad-thresh" not in base
    five = job.recipe_args(5)
    i = five.index("--pipeline.model.densify-grad-thresh")
    assert float(five[i + 1]) == pytest.approx(0.0008 / 5)


def test_smoke_ok():
    assert not job.smoke_ok({"splat_count": 0})[0]
    assert not job.smoke_ok({"splat_count": 5, "growth": {"deblur_appearance": {}}})[0]
    ok = {"splat_count": 5, "growth": {"deblur_appearance": {"applied_steps": 300}}}
    assert job.smoke_ok(ok)[0]
