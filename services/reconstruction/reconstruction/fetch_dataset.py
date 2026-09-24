"""Fetch a public reconstruction dataset for the spike smoke test (before corpus).

Public data only — used to prove the pipeline before any consented corpus or
user scan. Run inside the container (needs ``curl``). URLs are validated during
the spike; if one 404s, download from the dataset's project page and point
``--images`` at the extracted folder.
"""

from __future__ import annotations

import subprocess  # noqa: S404 - fixed-argv CLI orchestration
import zipfile
from pathlib import Path

from .tools import require

# Name -> canonical archive URL. Mip-NeRF 360 (Google research data) is the
# default smoke-test set; add others as they are validated on the GPU box.
DATASETS = {
    "mipnerf360": "https://storage.googleapis.com/gresearch/refraw360/360_v2.zip",
}


def resolve_url(name: str) -> str:
    """Return the archive URL for a known dataset name (KeyError if unknown)."""
    return DATASETS[name]


def fetch(name: str, dest: Path) -> Path:
    """Download and extract a named dataset into ``dest``; return ``dest``."""
    url = resolve_url(name)
    curl = require("curl")
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / f"{name}.zip"
    subprocess.run([curl, "-fL", url, "-o", str(archive)], check=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    return dest
