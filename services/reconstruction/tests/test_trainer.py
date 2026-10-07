"""GsplatTrainer builds headless ns-train / ns_finish command lines (no binaries needed)."""

import json
import subprocess

import pytest
from reconstruction import CameraPoses, ReconstructionConfig
from reconstruction.trainer import (
    DEFAULT_PROFILE,
    PROFILES,
    GsplatTrainer,
    TrainerError,
    TrainProfile,
)


def _fake_run(tmp_path, calls, *, vertices=7, fail_eval=False, finish_extra=None):
    out = tmp_path / "gsplat"

    def fake_run(argv, check, env=None):
        argv = [str(a) for a in argv]
        calls.append(argv)
        module = argv[2]
        if module == "reconstruction.ns_train_capped":
            assert env is not None and "GJ_GROWTH_STATS" in env
            cfg = out / "s1" / "splatfacto" / "run" / "config.yml"
            cfg.parent.mkdir(parents=True)
            cfg.write_text("x")
            with open(env["GJ_GROWTH_STATS"], "w") as fh:
                json.dump({"budget": 5, "limited_steps": 2, "max_count": 5}, fh)
            return
        assert module == "reconstruction.ns_finish"
        report = {"trained_splats": 9, "capped_splats": vertices, "cap_applied": True}
        report.update(finish_extra or {})
        if "--eval" in argv:
            if fail_eval:
                raise subprocess.CalledProcessError(1, argv)
            report["results"] = {"psnr": 31.23456, "ssim": 0.912, "lpips": 0.2, "fps": 9.0}
            report["eval_views"] = 3
            renders = out / "eval_renders"
            renders.mkdir()
            for i in range(3):
                (renders / f"eval_img_{i:04d}.png").write_bytes(b"png")
        (out / "finish.json").write_text(json.dumps(report))
        (out / "splat.ply").write_bytes(f"ply\nelement vertex {vertices}\nend_header\n".encode())

    return fake_run


def _poses(tmp_path):
    return CameraPoses(
        scan_id="s1",
        sparse_dir=tmp_path / "sparse" / "0",
        registered_images=3,
        image_dir=tmp_path / "images",
    )


def test_gsplat_trainer_trains_capped_then_finishes(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    config = ReconstructionConfig(train_iters=3000, splat_budget=7)
    model = GsplatTrainer().train(_poses(tmp_path), tmp_path, config)

    train, finish = calls
    assert train[train.index("--budget") + 1] == "7"
    ns = train[train.index("--") + 1 :]
    assert ns[0] == "splatfacto"
    assert ns[ns.index("--vis") + 1] == "tensorboard"
    assert ns[ns.index("--max-num-iterations") + 1] == "3000"
    # Scaled schedule: splitting stops at half the run, LR decays to its end.
    assert ns[ns.index("--pipeline.model.stop-split-at") + 1] == "1500"
    assert ns[ns.index("--optimizers.means.scheduler.max-steps") + 1] == "3000"
    assert ns[ns.index("--steps-per-eval-all-images") + 1] == "0"
    parser = ns.index("colmap")
    assert ns[parser + 1 :].count("--images-path") == 1
    assert ns[ns.index("--images-path") + 1] == str((tmp_path / "images").resolve())
    assert finish[finish.index("--load-config") + 1].endswith("run/config.yml")
    assert finish[finish.index("--budget") + 1] == "7"
    assert "--eval" in finish
    assert model.splat_count == 7
    assert model.metrics["psnr"] == 31.2346
    assert model.metrics["ssim"] == 0.912
    assert model.metrics["eval_views"] == 3
    assert model.metrics["trained_splats"] == 9
    assert model.metrics["growth"]["limited_steps"] == 2
    assert "fps" not in model.metrics
    assert {"train_s", "finish_s", "profile", "iterations"} <= set(model.metrics)
    assert model.preview_image.name == "eval_img_0001.png"


def test_eval_failure_never_fails_training(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls, fail_eval=True))
    model = GsplatTrainer().train(_poses(tmp_path), tmp_path, ReconstructionConfig())
    assert model.splat_count == 7
    assert "eval_error" in model.metrics
    assert model.preview_image is None
    # The export is retried without eval.
    assert "--eval" in calls[1] and "--eval" not in calls[2]


def test_a_splat_count_over_the_budget_fails_the_run(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls, vertices=8))
    with pytest.raises(TrainerError, match="splat cap violated"):
        GsplatTrainer().train(_poses(tmp_path), tmp_path, ReconstructionConfig(splat_budget=7))


def test_named_profiles():
    assert DEFAULT_PROFILE in PROFILES
    up = PROFILES["upstream-15k"]
    assert up.in_training_eval and up.ns_train_args() == ["--max-num-iterations", "15000"]
    s = TrainProfile.scaled(10_000).ns_train_args()
    assert s[s.index("--pipeline.model.resolution-schedule") + 1] == "1000"
    assert s[s.index("--pipeline.model.sh-degree-interval") + 1] == "333"
    assert s[s.index("--steps-per-save") + 1] == "0"
    trainer = GsplatTrainer(profile="scaled-10k")
    assert trainer.profile_for(ReconstructionConfig(train_iters=500)).iterations == 10_000
    # No explicit profile: the default recipe, rescaled to other lengths.
    assert GsplatTrainer().profile_for(ReconstructionConfig()) == PROFILES[DEFAULT_PROFILE]
    other = GsplatTrainer().profile_for(ReconstructionConfig(train_iters=4000)).ns_train_args()
    assert other[other.index("--pipeline.model.densify-grad-thresh") + 1] == "0.0006"
    with pytest.raises(TrainerError):
        GsplatTrainer(profile="nope")


def test_without_growth_limit_only_the_post_train_cap_applies(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    config = ReconstructionConfig(splat_budget=7)
    GsplatTrainer(growth_limit=False).train(_poses(tmp_path), tmp_path, config)
    train, finish = calls
    assert int(train[train.index("--budget") + 1]) > 10**12
    assert finish[finish.index("--budget") + 1] == "7"


def test_mcmc_profile_trains_at_the_budget(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    # Quality recipes pass antialiased on the config (no longer baked into QUALITY_ARGS).
    config = ReconstructionConfig(splat_budget=7, rasterize_mode="antialiased")
    model = GsplatTrainer(profile="quality-30k-mcmc").train(_poses(tmp_path), tmp_path, config)
    train, finish = calls
    own = train[: train.index("--")]
    assert own[own.index("--mcmc-cap") + 1] == "7"
    ns = train[train.index("--") + 1 :]
    assert ns[ns.index("--max-num-iterations") + 1] == "30000"
    assert ns[ns.index("--pipeline.model.rasterize-mode") + 1] == "antialiased"
    assert model.metrics["strategy"] == "mcmc"
    # The default-strategy profiles never ask for MCMC.
    calls.clear()
    out = tmp_path / "gsplat"
    import shutil

    shutil.rmtree(out)
    GsplatTrainer(profile="quality-30k").train(_poses(tmp_path), tmp_path, config)
    assert "--mcmc-cap" not in calls[0]
    assert "--depth-prior-dir" not in calls[0]  # depth/normal losses off by default


def test_config_quality_args_and_densify_strategy_wire_into_ns_train_capped(tmp_path, monkeypatch):
    """Item 1: splatfacto_quality_args + densify_strategy=mcmc → ns_train_capped."""
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    config = ReconstructionConfig(
        splat_budget=7, rasterize_mode="antialiased", densify_strategy="mcmc"
    )
    model = GsplatTrainer(profile="quality-30k").train(_poses(tmp_path), tmp_path, config)
    train = calls[0]
    own = train[: train.index("--")]
    assert own[own.index("--mcmc-cap") + 1] == "7"
    ns = train[train.index("--") + 1 :]
    assert ns[ns.index("--pipeline.model.rasterize-mode") + 1] == "antialiased"
    assert "--pipeline.model.strategy" not in ns  # not a nerfstudio 1.1.5 flag
    assert model.metrics["strategy"] == "mcmc"
    assert model.metrics["rasterize_mode"] == "antialiased"
    assert model.metrics["densify_strategy"] == "mcmc"


def test_score_plys_are_passed_to_finish_and_reported(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    scored = {"shipped-v1-400k": {"splats": 4, "psnr": 22.0}}
    fake = _fake_run(tmp_path, calls, finish_extra={"scored_plys": scored})
    monkeypatch.setattr(subprocess, "run", fake)
    trainer = GsplatTrainer(score_plys=(("shipped-v1-400k", tmp_path / "old.ply"),))
    model = trainer.train(_poses(tmp_path), tmp_path, ReconstructionConfig())
    finish = calls[1]
    assert finish[finish.index("--score-ply") + 1] == f"shipped-v1-400k={tmp_path / 'old.ply'}"
    assert model.metrics["scored_plys"] == scored


def test_measured_quality_recipes_keep_antialiased_via_config():
    """QUALITY_ARGS no longer pins rasterize-mode; callers use recipe_rasterize_mode."""
    from reconstruction.trainer import QUALITY_ARGS, recipe_rasterize_mode

    assert "--pipeline.model.rasterize-mode" not in QUALITY_ARGS
    for name in ("quality-30k", "quality-30k-camopt", "quality-30k-mcmc"):
        assert recipe_rasterize_mode(name) == "antialiased"
        assert recipe_rasterize_mode(PROFILES[name]) == "antialiased"
    for name in (DEFAULT_PROFILE, "upstream-15k", "", None):
        assert recipe_rasterize_mode(name) == "classic"


def test_rasterize_flag_is_emitted_once_from_the_config(tmp_path, monkeypatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    config = ReconstructionConfig(splat_budget=7)
    GsplatTrainer(profile="quality-30k").train(_poses(tmp_path), tmp_path, config)
    ns = calls[0][calls[0].index("--") + 1 :]
    assert ns.count("--pipeline.model.rasterize-mode") == 1
    assert ns[ns.index("--pipeline.model.rasterize-mode") + 1] == "classic"
    assert "--mcmc-cap" not in calls[0]


def test_depth_prior_wires_the_dn_losses_into_ns_train_capped(tmp_path, monkeypatch):
    """Items 2+3: depth_prior → --depth-prior-dir on the own-args half (before ``--``)."""
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", _fake_run(tmp_path, calls))
    (tmp_path / "depth_prior").mkdir()
    (tmp_path / "depth_prior" / "prior.json").write_text("{}")
    config = ReconstructionConfig(splat_budget=7, depth_prior="depth-anything-v2-small")
    model = GsplatTrainer(profile="quality-30k").train(_poses(tmp_path), tmp_path, config)
    own = calls[0][: calls[0].index("--")]
    assert own[own.index("--depth-prior-dir") + 1] == str(tmp_path / "depth_prior")
    assert model.metrics["depth_prior"] == "depth-anything-v2-small"


def test_pick_views_spreads_geometry_panels():
    from reconstruction.ns_finish import pick_views

    assert pick_views(29, 3) == [0, 14, 28]
    assert pick_views(29, 1) == [14]
    assert pick_views(0, 3) == [] and pick_views(2, 5) == [0, 1]
