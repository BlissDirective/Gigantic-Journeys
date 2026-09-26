#!/usr/bin/env python3
"""Scripted, unattended Unity editor smoke task (ticket M0-QA-01).

Runs the pinned Unity Editor in -batchmode with a graphics device (a virtual X
display via xvfb-run when no DISPLAY is set) and the editor script
unity/Assets/Editor/QA/EditorSmoke.cs, which opens the project, imports the
sample splat, opens the sample scene and renders the scene camera to
qa/evidence/M0-QA-01/editor-smoke.png. This script then writes
qa/reports/M0-editor-smoke.md (versions, timings, results, privacy line) and a
sanitized run log under qa/reports/M0-QA-01/.

The raw Unity Editor log is never committed: it can carry licensing details.
Only the smoke task's own [GJ-SMOKE] lines and error lines are kept, after
redaction.

Usage:
    python qa/scripts/editor_smoke.py [--runs 2] [--unity PATH] [--timeout 1800]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROJECT = REPO / "unity"
EVIDENCE = REPO / "qa" / "evidence" / "M0-QA-01"
LOGS = REPO / "qa" / "reports" / "M0-QA-01"
REPORT = REPO / "qa" / "reports" / "M0-editor-smoke.md"
METHOD = "GiganticJourneys.EditorTools.QA.EditorSmoke.Run"

# Environment-only Editor log noise on a headless box (not project issues).
ENV_NOISE = (
    "FMOD failed to initialize",
    "[Licensing::Module]",
    "Curl error",
    "dbus",
    "AT-SPI",
)
REDACT = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"),
    (
        re.compile(r"\b[A-Z0-9]{2}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}\b"),
        "<serial>",
    ),
    (re.compile(r"(?i)(token|password|serial|license)[^\n]*"), r"\1 <redacted>"),
    (re.compile(re.escape(str(Path.home()))), "~"),
]


def pinned_version() -> tuple[str, str]:
    text = (PROJECT / "ProjectSettings" / "ProjectVersion.txt").read_text()
    version = re.search(r"m_EditorVersion:\s*(\S+)", text).group(1)
    rev = re.search(r"m_EditorVersionWithRevision:\s*\S+\s*\((\w+)\)", text)
    return version, rev.group(1) if rev else ""


def find_editor(version: str, override: str | None) -> Path:
    candidates = [override, os.environ.get("UNITY_PATH")]
    candidates += [
        str(Path.home() / "Unity" / "Hub" / "Editor" / version / "Editor" / "Unity"),
        f"/Applications/Unity/Hub/Editor/{version}/Unity.app/Contents/MacOS/Unity",
        rf"C:\Program Files\Unity\Hub\Editor\{version}\Editor\Unity.exe",
    ]
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    sys.exit(f"Unity {version} not found; install it with the Hub CLI or pass --unity")


def ios_module(editor: Path) -> bool:
    roots = [editor.parent / "Data" / "PlaybackEngines", editor.parent.parent / "PlaybackEngines"]
    return any((r / "iOSSupport").is_dir() for r in roots)


def sanitize(line: str) -> str:
    for pattern, repl in REDACT:
        line = pattern.sub(repl, line)
    return line


def run_once(editor: Path, n: int, timeout: int) -> dict:
    out_dir = EVIDENCE if n == 1 else EVIDENCE / f"run-{n}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "result.json").unlink(missing_ok=True)
    raw_log = Path(tempfile.gettempdir()) / f"gj-editor-smoke-{n}.log"
    cmd = [
        str(editor),
        "-batchmode",
        "-projectPath",
        str(PROJECT),
        "-executeMethod",
        METHOD,
        "-logFile",
        str(raw_log),
        "-gjSmokeOut",
        str(out_dir),
    ]
    if sys.platform.startswith("linux") and not os.environ.get("GJ_SMOKE_USE_DISPLAY"):
        if not shutil.which("xvfb-run"):
            sys.exit("xvfb-run is required on Linux (apt install xvfb)")
        cmd = ["xvfb-run", "-a", "-s", "-screen 0 1920x1080x24", *cmd]
    started = time.monotonic()
    proc = subprocess.run(cmd, timeout=timeout, check=False, capture_output=True, text=True)
    wall = time.monotonic() - started
    log = raw_log.read_text(errors="replace") if raw_log.exists() else ""
    raw_log.unlink(missing_ok=True)

    kept = [
        sanitize(line)
        for line in log.splitlines()
        if "[GJ-SMOKE]" in line
        or re.search(r"error CS\d+|Exception:|\bError\b", line)
        and not any(noise in line for noise in ENV_NOISE)
    ]
    compile_errors = [ln for ln in kept if re.search(r"error CS\d+", ln)]
    result_file = out_dir / "result.json"
    result = (
        json.loads(result_file.read_text())
        if result_file.exists()
        else {"passed": False, "steps": []}
    )
    result.update(
        run=n,
        exit_code=proc.returncode,
        wall_seconds=round(wall, 1),
        compile_errors=len(compile_errors),
    )
    result["passed"] = bool(result.get("passed")) and proc.returncode == 0 and not compile_errors
    if n != 1 and (out_dir / "editor-smoke.png").exists():
        # Keep one committed PNG (run 1); later runs only prove repeatability.
        (out_dir / "editor-smoke.png").unlink()
    result_file.write_text(json.dumps(result, indent=2) + "\n")

    LOGS.mkdir(parents=True, exist_ok=True)
    header = [
        f"# M0-QA-01 editor smoke run {n} ({dt.datetime.now().astimezone():%Y-%m-%d %H:%M %Z})",
        f"# exit_code={proc.returncode} wall={wall:.1f}s passed={result['passed']}",
        "# sanitized: only [GJ-SMOKE] and error lines of the Unity Editor log, secrets redacted",
    ]
    (LOGS / f"run-{n}.log").write_text("\n".join(header + kept) + "\n")
    return result


def signature(result: dict) -> list[tuple[str, str]]:
    return [(s["name"], s["status"]) for s in result.get("steps", [])]


def write_report(version: str, rev: str, editor: Path, results: list[dict]) -> None:
    first = results[0]
    identical = len({tuple(signature(r)) for r in results}) == 1
    textures = first.get("sceneTextures", [])
    splat = next((s for s in first.get("steps", []) if s["name"] == "import sample splat"), {})
    captured = splat.get("status") == "pass" or textures
    privacy = (
        "PASS (automated): the rendered scene references no captured imagery "
        "(no splat imported, 0 project textures), "
        "so no faces, documents or personal data can appear."
        if not captured
        else "MANUAL REVIEW REQUIRED: the scene contains captured imagery "
        f"({len(textures)} texture(s), splat step {splat.get('status')}); a reviewer must confirm "
        "no faces, documents or personal data before this report is committed."
    )
    rows = "\n".join(
        f"| {s['name']} | **{s['status']}** | {s['seconds']:.2f} | {s['detail']} |"
        for s in first.get("steps", [])
    )
    runs = "\n".join(
        f"| {r['run']} | {'PASS' if r['passed'] else 'FAIL'} | {r['exit_code']} | "
        f"{r['wall_seconds']} | {r.get('errorCount', '?')} / {r.get('exceptionCount', '?')} / "
        f"{r.get('compile_errors', '?')} | `qa/reports/M0-QA-01/run-{r['run']}.log` |"
        for r in results
    )
    pending = [s["name"] for s in first.get("steps", []) if s["status"] == "pending"]
    overall = all(r["passed"] for r in results)
    generated = f"{dt.datetime.now().astimezone():%Y-%m-%d %H:%M %Z}"
    versions_match = "yes" if first.get("unityVersion") == version else "NO"
    ios = "installed" if ios_module(editor) and first.get("iosModuleInstalled") else "MISSING"
    host = f"{platform.system()} {platform.release()} ({platform.machine()})"
    host += f"; {first.get('platform', '?')}"
    since_start = first.get("secondsSinceEditorStart", 0)
    shot = first.get("screenshotFile") or "(none)"
    size = f"{first.get('screenshotWidth', 0)}x{first.get('screenshotHeight', 0)}"
    verdict = "PASS" if overall else "FAIL"
    if pending:
        verdict += f" — pending steps: {', '.join(pending)} (need M0-UNITY-02)"
    text = f"""# M0-editor-smoke — scripted Unity editor smoke task (M0-QA-01)

Generated by `qa/scripts/editor_smoke.py` on {generated}. Do not edit by hand.

## Header (AT-1)
| | |
|---|---|
| Pinned version (`unity/ProjectSettings/ProjectVersion.txt`) | `{version}` (`{rev}`) |
| Installed Editor (reported by the Editor) | `{first.get("unityFullVersion", "?")}` |
| Versions match | **{versions_match}** |
| iOS Build Support module | **{ios}** |
| Host | {host} |
| Graphics device | {first.get("graphicsDevice", "?")} |
| Active build target | {first.get("activeBuildTarget", "?")} |

## Steps (run 1)
| Step | Status | Seconds | Detail |
|---|---|---|---|
{rows}

Editor start to smoke entry (project open + domain load): {since_start:.1f} s.
Scene: `{first.get("scenePath", "?")}`. Screenshot: `qa/evidence/M0-QA-01/{shot}`
({size}, the scene's Game-view camera rendered offscreen; batchmode has no Game-view window).

## Runs (AT-3)
| Run | Result | Exit | Wall s | Errors / exceptions / compile errors | Log |
|---|---|---|---|---|---|
{runs}

Identical step results across runs: **{"yes" if identical else "NO"}**.

## Privacy check (AT-4)
{privacy}

## Overall
**{verdict}**.
"""
    REPORT.write_text(text)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--runs", type=int, default=2, help="consecutive unattended runs (AT-3 asks for 2)"
    )
    ap.add_argument(
        "--unity",
        help="path to the Unity Editor binary (default: Hub install of the pinned version)",
    )
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per run")
    args = ap.parse_args()

    version, rev = pinned_version()
    editor = find_editor(version, args.unity)
    if not ios_module(editor):
        print(f"warning: iOS Build Support not found next to {editor}", file=sys.stderr)
    results = []
    for n in range(1, args.runs + 1):
        print(f"run {n}/{args.runs}: {editor} ...", flush=True)
        r = run_once(editor, n, args.timeout)
        print(f"run {n}: {'PASS' if r['passed'] else 'FAIL'} in {r['wall_seconds']} s", flush=True)
        results.append(r)
    write_report(version, rev, editor, results)
    print(f"report: {REPORT.relative_to(REPO)}")
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
