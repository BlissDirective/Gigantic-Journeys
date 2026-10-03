"""M1-GAME-04: the data/audio -> Unity sync check passes on the current repo (AUTH #022)."""

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / ".github" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import check_audio_sync  # noqa: E402


def test_audio_sync_passes_on_the_repo():
    # internal consistency holds + no Unity mirror yet (or it is byte-identical)
    assert check_audio_sync.main() == 0
