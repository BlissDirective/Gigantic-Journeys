#!/usr/bin/env python3
"""Validate every tickets/*.json against tickets/SCHEMA.json plus cross-ticket rules.

Usage:
  python tickets/validate.py            # exit 1 on any problem (CI: governance.yml)
  python tickets/validate.py --summary  # print the status counts and ticket table for PROGRESS.md

Cross-ticket rules beyond the schema:
  - filename equals <id>.json; the AREA token of the id equals `area`; the M-token equals
    `milestone`
  - depends_on references exist, are not self-references, and form no cycle
  - in-progress / in-review / changes-requested require `branch`; merged requires `pr`;
    blocked requires a non-empty `blocked_by`
  - an approved auth_required entry carries its `auth_id`
  - acceptance test ids are unique within a ticket
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

try:
    import jsonschema
except ImportError:  # pragma: no cover
    print("missing dependency: pip install jsonschema==4.26.0")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent
STATUS_ORDER = [
    "open",
    "in-progress",
    "in-review",
    "changes-requested",
    "blocked",
    "merged",
    "done",
    "cancelled",
]
NEEDS_BRANCH = {"in-progress", "in-review", "changes-requested"}


def load() -> tuple[dict, dict[str, dict], list[str]]:
    schema = json.loads((ROOT / "SCHEMA.json").read_text(encoding="utf-8"))
    tickets: dict[str, dict] = {}
    errors: list[str] = []
    for path in sorted(ROOT.glob("*.json")):
        if path.name == "SCHEMA.json":
            continue
        try:
            tickets[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
    return schema, tickets, errors


def check(schema: dict, tickets: dict[str, dict], errors: list[str]) -> None:
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    ids = {t.get("id") for t in tickets.values()}
    for name, t in tickets.items():
        for err in validator.iter_errors(t):
            where = "/".join(str(x) for x in err.path) or "<root>"
            errors.append(f"{name}: {where}: {err.message}")
        tid = t.get("id")
        if not isinstance(tid, str) or tid.count("-") != 2:
            continue
        m_token, area_token, _ = tid.split("-")
        if name != f"{tid}.json":
            errors.append(f"{name}: filename must be {tid}.json")
        if t.get("area") and area_token != t["area"]:
            errors.append(f"{name}: area {t['area']} does not match id {tid}")
        if t.get("milestone") and m_token != t["milestone"]:
            errors.append(f"{name}: milestone {t['milestone']} does not match id {tid}")
        for dep in t.get("depends_on", []):
            if dep == tid:
                errors.append(f"{name}: depends on itself")
            elif dep not in ids:
                errors.append(f"{name}: depends_on unknown ticket {dep}")
        status = t.get("status")
        if status in NEEDS_BRANCH and not t.get("branch"):
            errors.append(f"{name}: status {status} requires a branch")
        if status == "merged" and not t.get("pr"):
            errors.append(f"{name}: status merged requires a pr link")
        if status == "blocked" and not t.get("blocked_by"):
            errors.append(f"{name}: status blocked requires blocked_by")
        if status == "cancelled" and not t.get("notes"):
            errors.append(f"{name}: status cancelled requires notes")
        for auth in t.get("auth_required", []):
            if auth.get("status") == "approved" and not auth.get("auth_id"):
                errors.append(f"{name}: approved auth_required entry needs auth_id")
        at_ids = [a.get("id") for a in t.get("acceptance_tests", []) if isinstance(a, dict)]
        if len(at_ids) != len(set(at_ids)):
            errors.append(f"{name}: duplicate acceptance test ids")
        for a in t.get("acceptance_tests", []):
            if isinstance(a, dict) and not a.get("level"):
                errors.append(f"{name}: {a.get('id')} needs a level (required | suggested)")

    graph = {
        t["id"]: t.get("depends_on", []) for t in tickets.values() if isinstance(t.get("id"), str)
    }
    state: dict[str, int] = {}

    def visit(node: str, stack: list[str]) -> None:
        if state.get(node) == 1:
            errors.append(f"dependency cycle: {' -> '.join([*stack, node])}")
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        for dep in graph.get(node, []):
            visit(dep, [*stack, node])
        state[node] = 2

    for node in graph:
        visit(node, [])


def summary(tickets: dict[str, dict]) -> None:
    counts = collections.Counter(t.get("status", "?") for t in tickets.values())
    print("| Status | Count |")
    print("|---|---|")
    for status in STATUS_ORDER:
        print(f"| {status} | {counts.get(status, 0)} |")
    print(f"| **total** | **{len(tickets)}** |")
    print()
    print("| ID | Title | Owner | Pri | Status | Depends on | Branch / PR |")
    print("|---|---|---|---|---|---|---|")
    for t in sorted(tickets.values(), key=lambda t: (t.get("priority", "P9"), t.get("id", ""))):
        link = t.get("pr") or t.get("branch") or "—"
        deps = ", ".join(t.get("depends_on", [])) or "—"
        print(
            f"| {t.get('id')} | {t.get('title')} | {t.get('owner')} | {t.get('priority')} | "
            f"{t.get('status')} | {deps} | {link} |"
        )


def main() -> int:
    schema, tickets, errors = load()
    check(schema, tickets, errors)
    if "--summary" in sys.argv:
        summary(tickets)
        return 0
    if errors:
        for err in errors:
            print(f"::error::{err}")
        print(f"{len(errors)} problem(s) across {len(tickets)} ticket(s)")
        return 1
    print(f"tickets: {len(tickets)} valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
