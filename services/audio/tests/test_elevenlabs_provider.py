"""ElevenLabs provider (M1-GAME-04, AUTH #048) -- payload shape, env-key handling, no network."""

import json

import pytest
import sources
from elevenlabs_provider import MAX_DURATION_S, MODEL_ID, ElevenLabsProvider


def _request(**kw):
    base = dict(
        id="walk__wood",
        event="walk",
        material="wood",
        prompt="impact one-shot, short-decay, 1:12 miniature scale, light footstep on wood",
        kind="object-impact",
        loop=False,
        count=1,
        duration_s=0.6,
        bus="movement",
        weight="light",
        post_process=sources.PostProcess(
            leave_raw=False, trim_silence=True, normalize=True, target_lufs=-16.0
        ),
    )
    base.update(kw)
    return sources.GenerationRequest(**base)


def test_payload_shape():
    body = ElevenLabsProvider().payload(_request())
    assert body["text"].startswith("impact one-shot")
    assert body["model_id"] == MODEL_ID
    assert body["loop"] is False
    assert 0.0 <= body["prompt_influence"] <= 1.0
    assert body["output_format"].startswith("mp3")
    assert body["duration_seconds"] == 0.6


def test_duration_is_clamped_to_the_api_cap():
    body = ElevenLabsProvider().payload(_request(duration_s=99.0))
    assert body["duration_seconds"] == MAX_DURATION_S


def test_loop_flag_passes_through():
    assert ElevenLabsProvider().payload(_request(loop=True))["loop"] is True


def test_generate_calls_count_times_with_the_env_key(monkeypatch):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "secret-key")
    seen = []

    def fake_post(url, body, headers):
        seen.append((url, json.loads(body), headers))
        return b"FAKE_MP3"

    provider = ElevenLabsProvider(http_post=fake_post)
    clips = provider.generate(_request(count=3))
    assert clips == [b"FAKE_MP3"] * 3
    assert len(seen) == 3
    url, body, headers = seen[0]
    assert url.endswith("/v1/sound-generation")
    assert headers["xi-api-key"] == "secret-key"
    assert body["text"].startswith("impact one-shot")


def test_missing_key_raises_and_never_calls(monkeypatch):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    called = []
    provider = ElevenLabsProvider(http_post=lambda *a: called.append(1) or b"")
    with pytest.raises(RuntimeError, match="ELEVENLABS_API_KEY"):
        provider.generate(_request())
    assert called == []  # the key is checked before any HTTP call / spend
