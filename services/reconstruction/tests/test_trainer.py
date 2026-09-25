"""GsplatTrainer builds a headless ns-train/ns-export command line (no binaries needed)."""

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
        else:
            (out / "splat.ply").write_bytes(b"ply\nelement vertex 7\nend_header\n")

    monkeypatch.setattr(trainer_module, "require", lambda tool: f"/usr/bin/{tool}")
    monkeypatch.setattr(subprocess, "run", fake_run)
    images = tmp_path / "images"
    poses = CameraPoses(
        scan_id="s1", sparse_dir=tmp_path / "sparse" / "0", registered_images=3, image_dir=images
    )
    model = GsplatTrainer().train(poses, tmp_path, ReconstructionConfig(train_iters=100))

    train, export = calls
    assert train[1] == "splatfacto"
    assert train[train.index("--vis") + 1] == "tensorboard"
    assert train[train.index("--max-num-iterations") + 1] == "100"
    parser = train.index("colmap")
    assert train[parser + 1 :].count("--images-path") == 1
    assert train[train.index("--images-path") + 1] == str(images.resolve())
    assert export[1] == "gaussian-splat"
    assert export[export.index("--load-config") + 1].endswith("run/config.yml")
    assert model.splat_count == 7
