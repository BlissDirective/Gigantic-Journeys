#!/usr/bin/env python3
"""QA evidence standard (qa/VISUAL_QA.md §2, ticket M0-QA-02), made mechanical.

Checks every tracked file under qa/evidence/:
  - it sits in qa/evidence/<TICKET-ID>/ and tickets/<TICKET-ID>.json exists;
  - screenshots are PNG, named <nn>-<what>.png (two digits, lowercase kebab-case),
    placed directly in the ticket folder, and at most 2 MB (2 * 1024 * 1024 bytes);
  - no clips or other image formats (clips are attached to the PR, never committed);
  - every ticket folder that holds a PNG has a README.md with a "Privacy:" line.

Non-image sidecars (README.md, *.json, *.txt, *.csv) are allowed, also in subfolders.
Exit 1 on any violation. Run: python .github/scripts/check_qa_evidence.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = "qa/evidence/"
MAX_PNG_BYTES = 2 * 1024 * 1024
PNG_NAME = re.compile(r"^\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.png$")
TICKET_ID = re.compile(r"^M\d-[A-Z]+-\d{2}$")
CLIP_OR_IMAGE = {
    ".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv", ".gif",
    ".jpg", ".jpeg", ".heic", ".webp", ".bmp", ".tif", ".tiff",
}  # fmt: skip
SIDECARS = {".md", ".json", ".txt", ".csv"}
PRIVACY_LINE = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Privacy(?:\*\*)?\s*:", re.M | re.I)


def tracked(prefix: str) -> list[str]:
    """Tracked files under prefix; falls back to a directory walk outside a git checkout."""
    proc = subprocess.run(
        ["git", "ls-files", "--", prefix], cwd=REPO, capture_output=True, text=True
    )
    if proc.returncode == 0:
        return [line for line in proc.stdout.splitlines() if line]
    root = REPO / prefix
    return sorted(p.relative_to(REPO).as_posix() for p in root.rglob("*") if p.is_file())


def check(files: list[str]) -> list[str]:
    errors: list[str] = []
    png_dirs: set[str] = set()
    for f in files:
        parts = f[len(EVIDENCE) :].split("/")
        if len(parts) < 2:
            errors.append(f"{f}: evidence must live in qa/evidence/<TICKET-ID>/")
            continue
        ticket, name = parts[0], parts[-1]
        if not TICKET_ID.match(ticket) or not (REPO / "tickets" / f"{ticket}.json").exists():
            errors.append(f"{f}: '{ticket}' is not an existing ticket id (tickets/{ticket}.json)")
        suffix = Path(name).suffix.lower()
        if suffix == ".png":
            if len(parts) != 2:
                errors.append(f"{f}: screenshots go directly in qa/evidence/{ticket}/")
            if not PNG_NAME.match(name):
                errors.append(f"{f}: name must be <nn>-<what>.png, e.g. 01-overlay-bright-scan.png")
            size = (REPO / f).stat().st_size if (REPO / f).exists() else 0
            if size > MAX_PNG_BYTES:
                errors.append(f"{f}: {size / 1048576:.2f} MB exceeds the 2 MB limit")
            png_dirs.add(ticket)
        elif suffix in CLIP_OR_IMAGE:
            errors.append(
                f"{f}: clips and non-PNG images are never committed "
                "(attach clips of 30 s or less to the PR; screenshots are PNG)"
            )
        elif suffix not in SIDECARS:
            errors.append(
                f"{f}: unexpected file type in evidence (allowed: PNG + .md/.json/.txt/.csv)"
            )
    for ticket in sorted(png_dirs):
        readme = REPO / EVIDENCE / ticket / "README.md"
        if not readme.exists() or not PRIVACY_LINE.search(readme.read_text(encoding="utf-8")):
            errors.append(
                f"{EVIDENCE}{ticket}/: needs a README.md with a 'Privacy:' line "
                "(no faces, addresses, documents, or screens with personal data)"
            )
    return errors


def main() -> int:
    files = tracked(EVIDENCE)
    errors = check(files)
    for e in errors:
        print(f"::error::{e}")
    if errors:
        return 1
    print(f"qa-evidence: OK ({len(files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
