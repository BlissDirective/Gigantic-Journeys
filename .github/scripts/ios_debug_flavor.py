#!/usr/bin/env python3
"""iOS build flavors for the ios-build workflow (ticket M0-UNITY-04 AT-1 device check).

The debug overlay's assembly compiles only under
``UNITY_EDITOR || DEVELOPMENT_BUILD || GJ_DEBUG``. Release builds (every push and the
default dispatch) must not contain it; the ``internal-debug`` flavor (workflow_dispatch
``flavor: internal-debug``) adds ``GJ_DEBUG`` to the iOS scripting defines **in the CI
runner's checkout only**, so the committed ProjectSettings stay release-clean (EditMode
test ``DebugOverlayReleaseExclusionTests.ReleaseDefines_DoNotForceGjDebug``), and the
testflight job exports that build as TestFlight internal-testing-only.

Device-test splat room (ticket M1-UNITY-01 AT-2/AT-3): the internal-debug flavor also
appends ``Assets/Scenes/DeviceTest/SplatRoom.unity`` to the build list (committed build
settings keep only the release scenes) and, when the dispatch passes a short-lived signed
URL, fetches the converted splat package from the private staging bucket, verifies its
SHA-256 against ``splat-room.json`` and unpacks it into a gitignored Resources folder. The
corpus splat never enters git (public repo; repo-hygiene bans scan files).

Commands:
    add-define <ProjectSettings.asset>          add GJ_DEBUG to the iPhone defines
    add-scene <EditorBuildSettings.asset> <Assets/...unity>
        append an enabled scene (guid from its .meta) to the build list
    fetch-splat --manifest <splat-room.json> --dest <dir> [--file <package>]
        verify a downloaded package (or download $SPLAT_URL, never printed): size +
        SHA-256 against the manifest, then unpack only <slug>*.asset/.bytes/.meta
    check <xcode project dir> --expect present|absent
        fail unless the overlay's IL2CPP output and the share-sheet plugin are
        present (internal-debug) or absent (release) in the exported Xcode project
    check-device-test <xcode project dir> --scene present|absent --splat present|absent
        fail unless the SplatRoom scene / the splat resource are present or absent
        in the exported player data
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

DEFINE = "GJ_DEBUG"
OVERLAY_ASSEMBLY = "GiganticJourneys.DebugOverlay"
SHARE_PLUGIN = "GJShareSheet.mm"
DEVICE_TEST_SCENE = "Assets/Scenes/DeviceTest/SplatRoom.unity"
SPLAT_SUFFIXES = (".asset", ".bytes", ".meta")
MAX_PACKAGE_BYTES = 64 * 1024 * 1024


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


def add_scene(settings: Path, scene: str, project_dir: Path | None = None) -> None:
    """Append ``scene`` (enabled) to EditorBuildSettings.asset; idempotent."""
    project_dir = project_dir or settings.parent.parent
    meta = project_dir / f"{scene}.meta"
    m = re.search(r"^guid: ([0-9a-f]{32})\s*$", meta.read_text(), re.M) if meta.is_file() else None
    if not m:
        sys.exit(f"no guid in {meta}")
    text = settings.read_text()
    if re.search(rf"^\s*path: {re.escape(scene)}\s*$", text, re.M):
        print(f"[GJ-FLAVOR] {scene} already in the build list")
        return
    block = re.search(r"^  m_Scenes:\s*\n((?:  - .*\n(?:    .*\n)*)*)", text, re.M)
    if not block:
        sys.exit(f"m_Scenes not found in {settings}")
    entry = f"  - enabled: 1\n    path: {scene}\n    guid: {m.group(1)}\n"
    end = block.end()
    settings.write_text(text[:end] + entry + text[end:])
    print(f"[GJ-FLAVOR] internal-debug: build list now includes {scene}")


def _safe_member(member: tarfile.TarInfo, slug: str) -> bool:
    name = member.name
    return (
        member.isfile()
        and "/" not in name
        and "\\" not in name
        and ".." not in name
        and name.startswith(slug)
        and name.endswith(SPLAT_SUFFIXES)
    )


def unpack_splat(data: bytes, manifest: dict, dest: Path) -> list[str]:
    """Verify ``data`` against the manifest and unpack it into ``dest``; return the file names."""
    want_sha = manifest["packageSha256"].lower()
    want_bytes = int(manifest["packageBytes"])
    got_sha = hashlib.sha256(data).hexdigest()
    if len(data) != want_bytes or got_sha != want_sha:
        raise ValueError(
            f"splat package mismatch: {len(data)} bytes sha256 {got_sha}, "
            f"manifest says {want_bytes} bytes sha256 {want_sha}"
        )
    slug = manifest["slug"]
    names = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        members = tar.getmembers()
        bad = [m.name for m in members if not _safe_member(m, slug)]
        if bad:
            raise ValueError(f"unexpected entries in the splat package: {bad}")
        dest.mkdir(parents=True, exist_ok=True)
        for m in members:
            src = tar.extractfile(m)
            (dest / m.name).write_bytes(src.read() if src else b"")
            names.append(m.name)
    asset = f"{Path(manifest['resource']).name}.asset"
    if asset not in names:
        raise ValueError(f"splat package has no {asset}")
    return sorted(names)


def fetch_splat(manifest_path: Path, dest: Path, url: str = "", file: Path | None = None) -> int:
    manifest = json.loads(manifest_path.read_text())
    if file is not None:
        data = file.read_bytes()
    else:
        if not url.startswith("https://"):
            print("::error::splat URL must be https (a short-lived signed URL)")
            return 1
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310 (https enforced above)
            data = resp.read(MAX_PACKAGE_BYTES + 1)
    if len(data) > MAX_PACKAGE_BYTES:
        print(f"::error::splat package exceeds {MAX_PACKAGE_BYTES} bytes")
        return 1
    try:
        names = unpack_splat(data, manifest, dest)
    except (ValueError, tarfile.TarError) as e:
        print(f"::error::{e}")
        return 1
    print(
        f"[GJ-FLAVOR] internal-debug: device-test splat {manifest['slug']} "
        f"({manifest['splatCount']} splats, {len(data)} bytes, sha256 verified) "
        f"-> {dest} ({len(names)} files)"
    )
    return 0


def _player_data(project: Path) -> Path:
    return project / "Data"


def _data_contains(data_dir: Path, needle: bytes) -> bool:
    needle = needle.lower()
    for f in data_dir.rglob("*"):
        if f.is_file() and needle in f.read_bytes().lower():
            return True
    return False


def check_device_test(project: Path, scene: str, splat: str, slug: str) -> int:
    data = _player_data(project)
    if not data.is_dir():
        print(f"::error::{data} missing: not a Unity iOS Xcode export")
        return 1
    has_scene = _data_contains(data, DEVICE_TEST_SCENE.encode())
    # The converted position data's TextAsset name; the descriptor JSON (scene-referenced,
    # present in every internal-debug build) names the slug but never this file.
    has_splat = _data_contains(data, f"{slug}_pos".encode())
    print(
        f"[GJ-FLAVOR] {project}: SplatRoom scene {'present' if has_scene else 'absent'} "
        f"(expected {scene}), splat {slug} {'present' if has_splat else 'absent'} "
        f"(expected {splat})"
    )
    ok = has_scene == (scene == "present") and has_splat == (splat == "present")
    if not ok:
        print(
            "::error::device-test scene/splat presence does not match the flavor "
            "(release builds must contain neither; M1-UNITY-01, SECURITY_CHECKLIST 9.8)"
        )
        return 1
    return 0


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
    s = sub.add_parser("add-scene")
    s.add_argument("settings", type=Path)
    s.add_argument("scene")
    f = sub.add_parser("fetch-splat")
    f.add_argument("--manifest", type=Path, required=True)
    f.add_argument("--dest", type=Path, required=True)
    f.add_argument("--file", type=Path, help="an already-downloaded package (else $SPLAT_URL)")
    c = sub.add_parser("check")
    c.add_argument("project", type=Path)
    c.add_argument("--expect", choices=["present", "absent"], required=True)
    d = sub.add_parser("check-device-test")
    d.add_argument("project", type=Path)
    d.add_argument("--scene", choices=["present", "absent"], required=True)
    d.add_argument("--splat", choices=["present", "absent"], required=True)
    d.add_argument("--slug", default="medieval-great-hall-winchester")
    args = ap.parse_args()
    if args.cmd == "add-define":
        add_define(args.settings)
        return 0
    if args.cmd == "add-scene":
        add_scene(args.settings, args.scene)
        return 0
    if args.cmd == "fetch-splat":
        if args.file is not None:
            return fetch_splat(args.manifest, args.dest, file=args.file)
        url = os.environ.get("SPLAT_URL", "")
        if not url:
            print("::error::SPLAT_URL is empty")
            return 1
        return fetch_splat(args.manifest, args.dest, url)
    if args.cmd == "check-device-test":
        return check_device_test(args.project, args.scene, args.splat, args.slug)
    return check(args.project, args.expect)


if __name__ == "__main__":
    sys.exit(main())
