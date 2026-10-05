"""Audio-source generation recipe (M1-GAME-04 / AUTH #022) -- vendor-agnostic plan over the bank."""

import json
from pathlib import Path

import sources

_REPO = Path(__file__).resolve().parents[3]


def test_materials_are_the_scene_graph_enum_minus_unknown():
    mats = sources.scene_graph_materials()
    schema = json.loads(
        (_REPO / "data" / "schemas" / "environment" / "scene_graph.json").read_text()
    )
    enum = schema["$defs"]["surface"]["properties"]["material"]["enum"]
    assert mats == [m for m in enum if m != "unknown"]
    assert "unknown" not in mats
    assert len(mats) == 10


def test_manifest_covers_every_bank_event_and_validates():
    specs = sources.build_manifest()
    bank = sources.load_bank()
    assert {s.event for s in specs} == set(bank["events"])
    assert sources.validate_manifest(specs) == []


def test_committed_manifest_is_in_sync_with_the_bank():
    """Drift guard: data/audio/source_manifest.json == build_manifest(bank). Regenerate with
    `python services/audio/sources.py` after any bank change."""
    committed = json.loads((_REPO / "data" / "audio" / "source_manifest.json").read_text())
    assert committed == sources.manifest_dict()


def test_material_varying_events_carry_materials_and_a_slot():
    by = {s.event: s for s in sources.build_manifest()}
    walk = by["walk"]  # varies_by_material
    assert walk.materials and "{material}" in walk.prompt_template
    assert walk.count == 8  # round_robin from the bank
    grapple = by["grapple-swing"]  # tools, varies_by_material false
    assert grapple.materials is None and "{material}" not in grapple.prompt_template


def test_expand_produces_one_request_per_material_with_unique_ids():
    walk = {s.event: s for s in sources.build_manifest()}["walk"]
    reqs = walk.expand()
    assert len(reqs) == len(sources.scene_graph_materials())
    assert len({r.id for r in reqs}) == len(reqs)
    wood = next(r for r in reqs if r.material == "wood")
    assert "on wood" in wood.prompt and "{material}" not in wood.prompt
    assert wood.count == 8

    fixed = {s.event: s for s in sources.build_manifest()}["ui-publish"].expand()
    assert len(fixed) == 1 and fixed[0].material is None


def test_loops_are_left_raw_oneshots_are_cleaned():
    by = {s.event: s for s in sources.build_manifest()}
    bed = by["ambience-bed"]
    assert bed.loop and bed.post_process.leave_raw and bed.duration_s == 10.0
    walk = by["walk"]
    assert not walk.loop and walk.post_process.trim_silence and walk.post_process.normalize


def test_ffmpeg_filters_recipe():
    raw = sources.PostProcess(leave_raw=True, trim_silence=False, normalize=False, target_lufs=None)
    assert sources.ffmpeg_filters(raw) == []
    oneshot = sources.PostProcess(
        leave_raw=False, trim_silence=True, normalize=True, target_lufs=-16.0
    )
    chain = sources.ffmpeg_filters(oneshot)
    joined = " ".join(chain)
    assert "silenceremove" in joined and "areverse" in joined
    assert "loudnorm=I=-16.0" in joined


def test_durations_stay_in_the_provider_range():
    lo, hi = sources.ELEVENLABS_DURATION_RANGE
    for s in sources.build_manifest():
        assert lo <= s.duration_s <= hi


def test_prompt_shapes():
    # object impact mentions the surface material and the miniature scale
    p = sources.build_prompt("walk", "movement", "light", loop=False, material="wood")
    assert "on wood" in p and "miniature" in p and "impact one-shot" in p
    # world ambience is a loop prompt
    a = sources.build_prompt("ambience-bed", "world", "light", loop=True, material="wood")
    assert a.startswith("ambient loop") and "wood space" in a
    # ui / music have their own shapes, no material surface clause
    assert sources.build_prompt("ui-publish", "ui", "light", loop=False).startswith("clean UI")
    assert "musical sting" in sources.build_prompt("sting-summit", "music", "medium", loop=False)


def test_dry_run_provider_records_without_spending():
    provider = sources.DryRunProvider()
    reqs = {s.event: s for s in sources.build_manifest()}["walk"].expand()
    for r in reqs:
        assert provider.generate(r) == []
    assert provider.requested == [r.id for r in reqs]


def test_every_verb_has_a_plan_via_bank_coverage():
    """The bank already enforces verb coverage; the plan covers the whole bank, so every v1 verb
    has a generation spec too."""
    import bank as bank_mod

    specs = {s.event for s in sources.build_manifest()}
    assert bank_mod.verb_set() <= specs
