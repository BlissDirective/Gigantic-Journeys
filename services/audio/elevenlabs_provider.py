"""ElevenLabs Sound Generation provider for the audio-source recipe (M1-GAME-04, AUTH #048).

Implements the ``sources.AudioProvider`` port against the ElevenLabs Sound Generation API
(``POST https://api.elevenlabs.io/v1/sound-generation``). The API key is read from the environment
(``ELEVENLABS_API_KEY``) and is **never** stored in the repo. Standard library only (urllib); the
HTTP call is injectable so tests run with no network and no spend.

Running this spends on the Owner's own ElevenLabs account, so the batch runner (``generate_audio``)
defaults to a dry run and never bulk-generates without an explicit limit/confirm.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from sources import GenerationRequest

ENDPOINT = "https://api.elevenlabs.io/v1/sound-generation"
MODEL_ID = "eleven_text_to_sound_v2"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
MAX_DURATION_S = 30.0  # ElevenLabs sound-generation hard cap

# (url, json_body_bytes, headers) -> response bytes. Injectable so tests never hit the network.
HttpPost = Callable[[str, bytes, dict], bytes]


def _urllib_post(url: str, body: bytes, headers: dict) -> bytes:
    if not url.startswith("https://"):
        raise ValueError("refusing to POST to a non-HTTPS URL")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (https-guarded above)
            return resp.read()
    except urllib.error.HTTPError as exc:  # surface 422 validation errors etc.
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {detail}") from exc


@dataclass
class ElevenLabsProvider:
    """A ``sources.AudioProvider`` backed by ElevenLabs. No key is held in the repo."""

    name: str = "elevenlabs"
    api_key_env: str = "ELEVENLABS_API_KEY"
    output_format: str = DEFAULT_OUTPUT_FORMAT
    prompt_influence: float = 0.3
    http_post: HttpPost = _urllib_post

    def _api_key(self) -> str:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(
                f"{self.api_key_env} is not set. Export it as an environment variable / CI secret; "
                "never commit it to the repo."
            )
        return key

    def payload(self, request: GenerationRequest) -> dict:
        """The request body for one clip. ``loop`` and ``duration_seconds`` come from the recipe."""
        body: dict = {
            "text": request.prompt,
            "model_id": MODEL_ID,
            "prompt_influence": self.prompt_influence,
            "output_format": self.output_format,
            "loop": bool(request.loop),
        }
        if request.duration_s:
            body["duration_seconds"] = min(float(request.duration_s), MAX_DURATION_S)
        return body

    def generate(self, request: GenerationRequest) -> list[bytes]:
        """Generate ``request.count`` round-robin variants (one API call each; each call spends)."""
        headers = {
            "xi-api-key": self._api_key(),
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        clips: list[bytes] = []
        for _ in range(max(1, request.count)):
            body = json.dumps(self.payload(request)).encode("utf-8")
            clips.append(self.http_post(ENDPOINT, body, headers))
        return clips
