#!/usr/bin/env python3
"""Fail if a migration creates a table without RLS + a policy in the same file.

SECURITY_CHECKLIST §2.1 / supabase/README.md: every table created in a migration
must `enable row level security` and have at least one `create policy`, in the
same migration. This is the mechanical first line; the Coordinator's review is
the real gate.

Storage policies (`create policy ... on storage.objects`) are a bonus, not
required here — `storage.objects` is a Supabase system table this repo does not
create, so it never appears in the created-tables set. Quoted identifiers that
contain spaces are not parsed (the repo uses plain snake_case identifiers).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"

_CREATE_TABLE = re.compile(r'create\s+table\s+(?:if\s+not\s+exists\s+)?([\w."]+)', re.IGNORECASE)
_ENABLE_RLS = re.compile(
    r'alter\s+table\s+(?:only\s+)?([\w."]+)\s+enable\s+row\s+level\s+security',
    re.IGNORECASE,
)
_CREATE_POLICY = re.compile(r'create\s+policy\s+\S+\s+on\s+([\w."]+)', re.IGNORECASE)


def _strip_comments(sql: str) -> str:
    """Drop -- line comments and /* */ block comments so prose never matches."""
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", sql)


def _base(name: str) -> str:
    """Normalize a possibly schema-qualified, quoted name to its base table name."""
    return name.split(".")[-1].strip('"').lower()


def violations(sql: str) -> list[str]:
    """Base names of tables created in `sql` that lack RLS-enable or a policy."""
    sql = _strip_comments(sql)
    created = {_base(m) for m in _CREATE_TABLE.findall(sql)}
    rls = {_base(m) for m in _ENABLE_RLS.findall(sql)}
    policied = {_base(m) for m in _CREATE_POLICY.findall(sql)}
    bad: list[str] = []
    for table in sorted(created):
        missing = []
        if table not in rls:
            missing.append("enable row level security")
        if table not in policied:
            missing.append("create policy")
        if missing:
            bad.append(f"{table}: missing {' + '.join(missing)}")
    return bad


def _display(path: Path) -> str:
    """Repo-relative path for GitHub annotations when possible."""
    root = Path(__file__).resolve().parents[2]
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: list[str] | None = None) -> int:
    """Scan supabase/migrations (or the directory given as the only argument)."""
    args = sys.argv[1:] if argv is None else argv
    migrations = Path(args[0]).resolve() if args else MIGRATIONS
    if not migrations.is_dir():
        print(f"check_rls: no migrations dir at {migrations}")
        return 0
    files = sorted(migrations.glob("*.sql"))
    failed = False
    for path in files:
        for bad in violations(path.read_text(encoding="utf-8")):
            failed = True
            print(f"::error file={_display(path)}::RLS — {bad}")
    if failed:
        print(
            "Every table created in a migration needs `enable row level security` "
            "+ at least one `create policy` in the same migration (SECURITY_CHECKLIST §2.1)."
        )
        return 1
    print(f"check_rls: {len(files)} migration(s) OK — every created table has RLS + a policy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
