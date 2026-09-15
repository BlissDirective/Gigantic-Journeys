#!/usr/bin/env python3
"""Governance gate: PRs that touch protected paths must cite an APPROVED AUTH number.

Protected paths (kit §0, "Authorization protocol"): SPEC.md, ADRs, data schemas, the design
system and the locked design docs, design tokens, the ticket schema, and the movement
constants (Movement Bible §10). The only change allowed without authorization is an append
under the "Field notes" heading of a locked design doc (the docs themselves permit it).

Inputs from the environment: BASE_SHA, HEAD_SHA, PR_BODY. Exit 1 on a violation.
This is the first line of defense; the Coordinator's review is the real gate.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

PROTECTED: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^SPEC\.md$"), "product spec"),
    (re.compile(r"^ADRs/(?!README\.md$|0000-template\.md$).+\.md$"), "ADR"),
    (re.compile(r"^data/schemas/"), "data schema"),
    (re.compile(r"^design/DESIGN_SYSTEM\.md$"), "design system"),
    (re.compile(r"^design/MOVEMENT_BIBLE\.md$"), "Movement Bible (locked)"),
    (re.compile(r"^design/Gigantic-Journey-Design-Skills\.md$"), "Design Skills (locked)"),
    (re.compile(r"^design/tokens/"), "design tokens (locked design system)"),
    (re.compile(r"^tickets/SCHEMA\.json$"), "ticket schema"),
    (re.compile(r"^config/movement(\.schema)?\.json$"), "movement constants (Bible §10)"),
]
FIELD_NOTES_OK = {
    "design/MOVEMENT_BIBLE.md",
    "design/Gigantic-Journey-Design-Skills.md",
    "design/DESIGN_SYSTEM.md",
}
FIELD_NOTES_HEADING = re.compile(r"^#{1,6}\s+(?:\d+\.\s+)?Field notes\b")
APPROVED_RE = re.compile(r"APPROVED\s*#\s*0*(\d+)")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def changed_files(base: str, head: str) -> list[str]:
    return [line for line in git("diff", "--name-only", f"{base}...{head}").splitlines() if line]


def only_field_note_appends(path: str, base: str, head: str) -> bool:
    """True when every hunk is a pure addition placed after the Field notes heading."""
    try:
        content = git("show", f"{head}:{path}")
    except subprocess.CalledProcessError:
        return False  # deleted or renamed away
    heading_line = None
    for i, line in enumerate(content.splitlines(), start=1):
        if FIELD_NOTES_HEADING.match(line):
            heading_line = i
            break
    if heading_line is None:
        return False
    diff = git("diff", "-U0", base, head, "--", path)
    hunks = list(HUNK_RE.finditer(diff))
    if not hunks:
        return False
    for m in hunks:
        old_count = int(m.group(2)) if m.group(2) is not None else 1
        new_start = int(m.group(3))
        if old_count != 0:
            return False  # something was removed or replaced
        if new_start <= heading_line:
            return False  # addition above or at the heading
    return True


def main() -> int:
    base = os.environ.get("BASE_SHA", "")
    head = os.environ.get("HEAD_SHA", "")
    body = os.environ.get("PR_BODY") or ""
    if not base or not head:
        print("auth-gate: not a pull request context; nothing to check")
        return 0

    hits: list[tuple[str, str]] = []
    for path in changed_files(base, head):
        for pattern, label in PROTECTED:
            if pattern.search(path):
                if path in FIELD_NOTES_OK and only_field_note_appends(path, base, head):
                    print(f"ok: {path} — Field notes append only (allowed without AUTH)")
                else:
                    hits.append((path, label))
                break

    if not hits:
        print("auth-gate: no protected paths touched")
        return 0

    print("Protected paths changed in this PR:")
    for path, label in hits:
        print(f"  - {path}  ({label})")

    match = APPROVED_RE.search(body)
    if not match:
        print(
            "::error::This PR changes protected paths but its description does not cite an "
            "`APPROVED #n`. File an AUTH REQUEST (agents/grok/README.md §6), wait for the Owner's "
            "reply, then add the exact reference to the PR body."
        )
        return 1

    tag = f"#{int(match.group(1)):03d}"
    try:
        log = git("show", f"{head}:governance/AUTHORIZATION_LOG.md")
    except subprocess.CalledProcessError:
        log = ""
    if any(tag in line and "APPROVED" in line for line in log.splitlines()):
        print(f"ok: PR cites APPROVED {tag}, present in governance/AUTHORIZATION_LOG.md")
    else:
        print(
            f"::warning::PR cites APPROVED {tag} but governance/AUTHORIZATION_LOG.md at HEAD has "
            f"no APPROVED row for {tag}. The Coordinator verifies the Owner's reply on the "
            "auth-request issue before merging."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
