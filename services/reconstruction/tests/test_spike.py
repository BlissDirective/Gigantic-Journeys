"""The spike driver (dry-run) and the dataset resolver."""

import json

import pytest
from reconstruction.fetch_dataset import DATASETS, resolve_url
from reconstruction.spike import build_parser, count_images, main, run_spike


def _images(tmp_path):
    d = tmp_path / "images"
    d.mkdir()
    for name in ("a.jpg", "b.png", "c.heic", "notes.txt"):
        (d / name).write_bytes(b"x")
    return d


def test_count_images_ignores_non_images(tmp_path):
    assert count_images(_images(tmp_path)) == 3


def test_count_images_missing_dir(tmp_path):
    assert count_images(tmp_path / "nope") == 0


def test_dry_run_end_to_end(tmp_path):
    images = _images(tmp_path)
    cost = tmp_path / "cost.json"
    rc = main(
        [
            "--images",
            str(images),
            "--scan-id",
            "t1",
            "--work-dir",
            str(tmp_path / "work"),
            "--cost-sheet",
            str(cost),
            "--dry-run",
            "--rate",
            "1.0",
        ]
    )
    assert rc == 0
    data = json.loads(cost.read_text())
    assert data["scan_id"] == "t1"
    assert data["within_budget"] is True
    assert data["usd"] >= 0
    assert data["format"] == "spz"


def test_run_spike_auto_counts_images(tmp_path):
    args = build_parser().parse_args(
        ["--images", str(_images(tmp_path)), "--work-dir", str(tmp_path / "w"), "--dry-run"]
    )
    run = run_spike(args)
    assert run.package.scan_id == "spike"
    assert run.within_budget is True


def test_resolve_url_known():
    assert resolve_url("mipnerf360").startswith("http")
    assert "mipnerf360" in DATASETS


def test_resolve_url_unknown():
    with pytest.raises(KeyError):
        resolve_url("does-not-exist")
