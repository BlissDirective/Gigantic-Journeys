"""Depth-prior cache: licence gate (AUTH #049) + stdlib map round trip."""

import json

import pytest
from reconstruction.depth_prior import MockDepthPrior
from reconstruction.depth_prior_cache import (
    DEPTH_MODELS,
    build_cache,
    model_repo,
    read_map_grid,
    write_map,
)
from reconstruction.licenses import LicenseError


def test_only_the_small_checkpoint_is_allowed():
    assert model_repo("depth-anything-v2-small") == "depth-anything/Depth-Anything-V2-Small-hf"
    assert set(DEPTH_MODELS) == {"depth-anything-v2-small"}
    for nc in (
        "depth-anything-v2-base",
        "depth-anything-v2-large",
        "depth-anything-v2-giant",
        "depth-anything/Depth-Anything-V2-Large-hf",
        "unidepth",
        "my-Large-variant",
    ):
        with pytest.raises(LicenseError):
            model_repo(nc)


def test_map_round_trip(tmp_path):
    grid = [[0.5, 1.25, 2.0], [3.0, 0.0, -1.5]]
    write_map(tmp_path, "frame_0001", grid)
    assert read_map_grid(tmp_path, "frame_0001") == grid
    assert read_map_grid(tmp_path, "missing") is None
    with pytest.raises(ValueError):
        write_map(tmp_path, "bad", [[1.0, 2.0], [3.0]])


def test_build_cache_writes_one_map_per_frame_and_a_manifest(tmp_path):
    images = [tmp_path / f"f{i}.jpg" for i in (2, 0, 1)]
    out = tmp_path / "prior"
    manifest = build_cache(images, out, MockDepthPrior(), lambda p: [[0.0] * 4 for _ in range(3)])
    assert manifest["frames"] == ["f0", "f1", "f2"]
    assert manifest["license"] == "Apache-2.0" and manifest["kind"] == "disparity"
    assert json.loads((out / "prior.json").read_text())["model"] == "depth-anything-v2-small"
    g = read_map_grid(out, "f1")
    assert len(g) == 3 and len(g[0]) == 4
    with pytest.raises(LicenseError):
        build_cache(
            images, out, MockDepthPrior(), lambda p: [[0.0]], model="depth-anything-v2-large"
        )


def test_config_values_and_licence_manifest_stay_in_sync():
    from reconstruction.depth_prior_cache import DEPTH_MODEL_REVISIONS
    from reconstruction.licenses import MANIFEST, assert_commercial_safe
    from reconstruction.models import DEPTH_PRIORS

    assert set(DEPTH_PRIORS) == {"none", *DEPTH_MODELS}
    assert set(DEPTH_MODEL_REVISIONS) == set(DEPTH_MODELS)
    names = {c.name for c in assert_commercial_safe()}
    assert {"transformers", "Depth Anything V2 Small"} <= names
    assert len(MANIFEST) == len(names)
