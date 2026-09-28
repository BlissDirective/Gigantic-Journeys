#!/usr/bin/env python3
"""iOS build flavors for the ios-build workflow (ticket M0-UNITY-04 AT-1 device check).

The debug overlay's assembly compiles only under
``UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG``. Release builds (every push and the
default dispatch) must not contain it; the ``internal-debug`` flavor (workflow_dispatch
``flavor: internal-debug``) adds ``GJ_DEBUG`` to the iOS scripting defines **in the CI
runner's checkout only**, so the committed ProjectSettings stay release-clean (EditMode
test ``DebugOverlayReleaseExclusionTests.ReleaseDefines_DoNotForceGjDebug``), and the
testflight job exports that build as TestFlight internal-testing-only.

Commands:
    add-define <ProjectSettings.asset>          add GJ_DEBUG to the iPhone defines
    check <xcode project dir> --expect present|absent
        fail unless the overlay's IL2CPP output and the share-sheet plugin are
        present (internal-debug) or absent (release) in the exported Xcode project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFINE = "GJ_DEBUG"
OVERLAY_ASSEMBLY = "GiganticJourneys.DebugOverlay"
SHARE_PLUGIN = "GJShareSheet.mm"


def add_define(settings: Path) -> None:
    text = settings.read_text()
    empty = re.search(r"^(\s*)scriptingDefineSymbols: \{\}\s*$", text, re.M)
    if empty:
        indent = empty.group(1)
        text = text.replace(
            empty.group(0),
            f"{indent}scriptingDefineSymbols:\n{indent}  iPhone: {DEFINE}",
            1,
        )
    else:
        block = re.search(r"^(\s*)scriptingDefineSymbols:\s*\n((?:\1  .*\n)*)", text, re.M)
        if not block:
            sys.exit(f"scriptingDefineSymbols not found in {settings}")
        indent, body = block.group(1), block.group(2)
        iphone = re.search(rf"^{indent}  iPhone: ?(.*)$", body, re.M)
        if iphone:
            current = [d for d in re.split(r"[;,]", iphone.group(1).strip()) if d]
            if DEFINE in current:
                print(f"{DEFINE} already set for iPhone")
                return
            new_line = f"{indent}  iPhone: {';'.join(current + [DEFINE])}"
            body_new = body.replace(iphone.group(0), new_line, 1)
        else:
            body_new = body + f"{indent}  iPhone: {DEFINE}\n"
        text = text.replace(block.group(0), f"{indent}scriptingDefineSymbols:\n{body_new}", 1)
    settings.write_text(text)
    print(f"[GJ-FLAVOR] internal-debug: iPhone scripting defines now include {DEFINE}")


def overlay_present(project: Path) -> tuple[bool, bool]:
    cpp = project / "Il2CppOutputProject" / "Source" / "il2cppOutput"
    assembly = cpp.is_dir() and any(p.name.startswith(OVERLAY_ASSEMBLY) for p in cpp.glob("*.cpp"))
    plugin = any(project.rglob(SHARE_PLUGIN))
    return assembly, plugin


def check(project: Path, expect: str) -> int:
    if not project.is_dir():
        print(f"::error::{project} is not a directory")
        return 1
    cpp = project / "Il2CppOutputProject" / "Source" / "il2cppOutput"
    if not cpp.is_dir():
        print(f"::error::{cpp} missing: not an IL2CPP Xcode export, cannot check the overlay")
        return 1
    assembly, plugin = overlay_present(project)
    want = expect == "present"
    print(
        f"[GJ-FLAVOR] {project}: overlay IL2CPP output {'present' if assembly else 'absent'}, "
        f"{SHARE_PLUGIN} {'present' if plugin else 'absent'} (expected {expect})"
    )
    if assembly != want or plugin != want:
        print(
            f"::error::debug overlay expected {expect} in this Xcode project "
            f"(assembly={assembly}, share plugin={plugin}); SECURITY_CHECKLIST 9.7/9.8"
        )
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add-define")
    a.add_argument("settings", type=Path)
    c = sub.add_parser("check")
    c.add_argument("project", type=Path)
    c.add_argument("--expect", choices=["present", "absent"], required=True)
    args = ap.parse_args()
    if args.cmd == "add-define":
        add_define(args.settings)
        return 0
    return check(args.project, args.expect)


if __name__ == "__main__":
    sys.exit(main())
