"""GsplatTrainer builds a headless ns-train/ns-export command line (no binaries needed)."""

import json
import subprocess

from reconstruction import CameraPoses, ReconstructionConfig
from reconstruction import trainer as trainer_module
from reconstruction.trainer import GsplatTrainer


def test_gsplat_trainer_reads_colmap_model_headless(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    out = tmp_path / "gsplat"

    def fake_run(argv, check):
        argv = [str(a) for a in argv]
        calls.append(argv)
        if argv[1] == "splatfacto":
            cfg = out / "s1" / "splatfacto" / "run" / "config.yml"
            cfg.parent.mkdir(parents=True)
            cfg.write_text("x")
        elif argv[0].endswith("ns-eval"):
            results = {"psnr": 31.23456, "ssim": 0.912, "lpips": 0.2, "fps": 9.0}
            out_json = argv[argv.index("--output-path") + 1]
            with open(out_json, "w") as fh:
                json.dump({"results": results}, fh)
            renders = tmp_path / "gsplat" / "eval_renders"
            renders.mkdir()
            for i in range(3):
                (renders / f"{i:04d}-img.jpg").write_bytes(b"jpg")
        else:
            (out / "splat.ply").write_bytes(b"ply\nelement vertex 7\nend_header\n")

    monkeypatch.setattr(trainer_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", fake_run)
    images = tmp_path / "images"
    poses = CameraPoses(
        scan_id="s1", sparse_dir=tmp_path / "sparse" / "0", registered_images=3, image_dir=images
    )
    model = GsplatTrainer().train(poses, tmp_path, ReconstructionConfig(train_iters=100))

    train, export, evaluate = calls
    assert train[1] == "splatfacto"
    assert train[train.index("--vis") + 1] == "tensorboard"
    assert train[train.index("--max-num-iterations") + 1] == "100"
    parser = train.index("colmap")
    assert train[parser + 1 :].count("--images-path") == 1
    assert train[train.index("--images-path") + 1] == str(images.resolve())
    assert export[1] == "gaussian-splat"
    assert export[export.index("--load-config") + 1].endswith("run/config.yml")
    assert model.splat_count == 7
    assert evaluate[evaluate.index("--load-config") + 1].endswith("run/config.yml")
    assert model.metrics["psnr"] == 31.2346
    assert model.metrics["ssim"] == 0.912
    assert model.metrics["eval_views"] == 3
    assert "fps" not in model.metrics
    assert {"train_s", "export_s", "eval_s"} <= set(model.metrics)
    assert model.preview_image.name == "0001-img.jpg"


def test_eval_failure_never_fails_training(tmp_path, monkeypatch):
    out = tmp_path / "gsplat"

    def fake_run(argv, check):
        argv = [str(a) for a in argv]
        if argv[1] == "splatfacto":
            cfg = out / "s1" / "splatfacto" / "run" / "config.yml"
            cfg.parent.mkdir(parents=True)
            cfg.write_text("x")
        elif argv[0].endswith("ns-eval"):
            raise subprocess.CalledProcessError(1, argv)
        else:
            (out / "splat.ply").write_bytes(b"ply\nelement vertex 7\nend_header\n")

    monkeypatch.setattr(trainer_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", fake_run)
    poses = CameraPoses(scan_id="s1", sparse_dir=tmp_path / "sparse" / "0", registered_images=3)
    model = GsplatTrainer().train(poses, tmp_path, ReconstructionConfig(train_iters=100))
    assert model.splat_count == 7
    assert "eval_error" in model.metrics
    assert model.preview_image is None
