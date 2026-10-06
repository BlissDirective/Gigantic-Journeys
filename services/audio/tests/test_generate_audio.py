"""Audio batch runner (M1-GAME-04, AUTH #048) -- dry-run safety, cost estimate, limit guard."""

import generate_audio as ga
import sources


class _FakeProvider:
    """Returns dummy bytes without spending; stands in for ElevenLabs in tests."""

    name = "fake"
    output_format = "mp3_44100_128"

    def generate(self, request):
        return [b"MP3"] * request.count


def test_resolve_filter_treats_all_and_blank_as_no_filter():
    # Dispatch can't send a blank event (GitHub swaps it to the default), so 'all' is the sentinel.
    assert ga._resolve_filter(None) is None
    assert ga._resolve_filter("") is None
    assert ga._resolve_filter("   ") is None
    assert ga._resolve_filter("all") is None
    assert ga._resolve_filter("ALL") is None
    assert ga._resolve_filter("walk") == "walk"
    assert ga._resolve_filter("  walk  ") == "walk"


def test_estimate_counts_the_whole_manifest():
    est = ga.estimate()
    assert est["events"] == 62
    assert est["families"] > est["events"]  # material-varying events expand
    assert est["calls"] >= est["families"]  # each family makes >= 1 call


def test_dry_run_plans_without_writing_or_spending(tmp_path):
    res = ga.run(sources.DryRunProvider(), tmp_path, dry_run=True)
    assert res["dry_run"] is True
    assert res["planned_families"] > 0
    assert res["written_files"] == 0
    assert res["provider_calls"] == 0
    assert not any(tmp_path.iterdir())  # nothing written to disk


def test_execute_writes_clips_and_respects_the_limit(tmp_path):
    # walk varies by material (10) x count 8; the per-family limit guard stops after one family.
    res = ga.run(_FakeProvider(), tmp_path, limit=2, dry_run=False, postprocess=False, event="walk")
    assert res["dry_run"] is False
    assert res["stopped_at_limit"] is True
    assert res["written_files"] == 8  # one family of 8 round-robin variants
    assert res["provider_calls"] == 8
    clips = list((tmp_path / "walk").glob("*.mp3"))
    assert len(clips) == 8
    assert clips[0].read_bytes() == b"MP3"


def test_execute_filters_to_one_event_and_material(tmp_path):
    res = ga.run(
        _FakeProvider(),
        tmp_path,
        dry_run=False,
        postprocess=False,
        event="ambience-bed",
        material="carpet-rug",
    )
    # ambience-bed is a loop (count 1), one material selected -> exactly one clip
    assert res["written_files"] == 1
    assert list((tmp_path / "ambience-bed").glob("*.mp3"))


class _FlakyProvider:
    """Raises for any request whose id starts with ``fail_prefix``; others succeed."""

    name = "flaky"
    output_format = "mp3_44100_128"

    def __init__(self, fail_prefix):
        self.fail_prefix = fail_prefix

    def generate(self, request):
        if request.id.startswith(self.fail_prefix):
            raise RuntimeError("boom")
        return [b"MP3"] * request.count


def test_a_failing_family_is_recorded_not_fatal(tmp_path):
    res = ga.run(
        _FlakyProvider("ui-publish"), tmp_path, dry_run=False, postprocess=False, event="ui-publish"
    )
    assert res["written_files"] == 0
    assert res["failed_families"] == 1
    assert res["failures"][0]["id"] == "ui-publish"


def test_batch_continues_past_a_failure(tmp_path):
    # In the walk event, fail only walk__glass; the other 9 materials still generate.
    res = ga.run(
        _FlakyProvider("walk__glass"), tmp_path, dry_run=False, postprocess=False, event="walk"
    )
    assert res["failed_families"] == 1
    assert res["failures"][0]["id"] == "walk__glass"
    assert res["written_files"] == 72  # 9 materials x 8 variants still produced
