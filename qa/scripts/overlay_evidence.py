#!/usr/bin/env python3
"""Debug-overlay evidence (ticket M0-UNITY-04), unattended.

1. Runs the pinned Unity Editor headless with
   unity/Assets/Editor/QA/OverlayEvidence.cs: builds a Development and a release
   Linux player of the splat sample scene (optionally iOS Xcode exports too, with
   --ios) and checks that only the Development builds contain the overlay
   (AT-2, build level).
2. Runs the Development player under a virtual X display with Vulkan on Mesa
   lavapipe in the overlay's QA capture mode (OverlayCapture.cs): the overlay over
   a bright and a dark exposure of the scene at 1280x720, and at 2556x1179 with the
   iPhone 15 Pro landscape safe-area insets simulated (AT-1, AT-3). The capture
   mode also presses the overlay's "Save report" handler, so the saved report is
   evidence that the action works (lavapipe numbers are not performance data).
3. Copies the PNGs to qa/evidence/M0-UNITY-04/ under the VISUAL_QA names and the
   machine results (builds.json, capture-*.json, the report) to its run/ subfolder,
   plus sanitized log excerpts to qa/reports/M0-UNITY-04/.

Raw Unity logs are never committed (they can carry licensing details); only the
tagged [GJ-...] lines and error lines are kept, after redaction.

Usage:
    python qa/scripts/overlay_evidence.py [--unity PATH] [--ios] [--skip-build]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROJECT = REPO / "unity"
TICKET = "M0-UNITY-04"
EVIDENCE = REPO / "qa" / "evidence" / TICKET
LOGS = REPO / "qa" / "reports" / TICKET
BUILD_ROOT = PROJECT / "Builds" / "overlay"
PLAYER = BUILD_ROOT / "linux-development" / "gj.x86_64"
METHOD = "GiganticJourneys.EditorTools.QA.OverlayEvidence.Run"
SHOTS = {
    "bright-scan.png": "01-overlay-bright-scan.png",
    "dark-scan.png": "02-overlay-dark-scan.png",
    "safe-area.png": "03-overlay-safe-area-iphone-15-pro.png",
}
KEEP = re.compile(r"\[GJ-[A-Z-]+\]|error CS\d+|Exception|\bError\b")
NOISE = ("FMOD", "[Licensing::", "Curl error", "dbus", "AT-SPI", "ALSA", "CopyFiles", "% Packages/")
REDACT = [(re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<email>"), (re.compile(r"/home/[^/\s]+"), "~")]


def editor(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    text = (PROJECT / "ProjectSettings" / "ProjectVersion.txt").read_text()
    version = re.search(r"m_EditorVersion:\s*(\S+)", text).group(1)
    path = Path.home() / "Unity" / "Hub" / "Editor" / version / "Editor" / "Unity"
    if not path.exists():
        sys.exit(f"Unity {version} not found at {path}; pass --unity")
    return path


def excerpt(log: Path, name: str) -> list[str]:
    lines = log.read_text(errors="replace").splitlines() if log.exists() else []
    kept = []
    for line in lines:
        if KEEP.search(line) and not any(n in line for n in NOISE):
            for pattern, repl in REDACT:
                line = pattern.sub(repl, line)
            kept.append(line)
    LOGS.mkdir(parents=True, exist_ok=True)
    (LOGS / f"{name}.txt").write_text(
        f"# {TICKET} {name}: sanitized excerpt ([GJ-*] and error lines only)\n"
        + "\n".join(kept)
        + "\n"
    )
    return kept


def build(unity: Path, out: Path, ios: bool) -> dict:
    log = out / "editor-build.log"
    cmd = [
        str(unity),
        "-batchmode",
        "-nographics",
        "-projectPath",
        str(PROJECT),
        "-executeMethod",
        METHOD,
        "-logFile",
        str(log),
        "-gjEvidenceOut",
        str(out),
        "-gjBuildRoot",
        str(BUILD_ROOT),
    ]
    if ios:
        cmd.append("-gjOverlayIos")
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=7200)
    excerpt(log, "build")
    result = json.loads((out / "builds.json").read_text()) if (out / "builds.json").exists() else {}
    result["exit_code"] = proc.returncode
    return result


def capture(out: Path, shot_set: str, width: int, height: int) -> dict:
    run_dir = out / shot_set
    run_dir.mkdir(parents=True, exist_ok=True)
    log = out / f"player-{shot_set}.log"
    screen = f"-screen 0 {width + 64}x{height + 64}x24"
    cmd = [
        "xvfb-run",
        "-a",
        "-s",
        screen,
        str(PLAYER),
        "-force-vulkan",
        "-force-device-index",
        "0",
        "-screen-fullscreen",
        "0",
        "-screen-width",
        str(width),
        "-screen-height",
        str(height),
        "-logFile",
        str(log),
        "-gjOverlayCapture",
        str(run_dir),
        "-gjOverlaySet",
        shot_set,
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=900)
    excerpt(log, f"capture-{shot_set}")
    result_file = run_dir / "capture.json"
    result = json.loads(result_file.read_text()) if result_file.exists() else {"shots": []}
    result["exit_code"] = proc.returncode
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument(
        "--unity", help="Unity Editor binary (default: Hub install of the pinned version)"
    )
    ap.add_argument("--ios", action="store_true", help="also export iOS Development + release")
    ap.add_argument("--skip-build", action="store_true", help="reuse the existing players")
    args = ap.parse_args()
    if not shutil.which("xvfb-run"):
        sys.exit("xvfb-run is required (apt install xvfb mesa-vulkan-drivers)")

    out = Path(tempfile.mkdtemp(prefix="gj-overlay-evidence-"))
    run_dir = EVIDENCE / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    ok = True
    if not args.skip_build:
        builds = build(editor(args.unity), out, args.ios)
        (run_dir / "builds.json").write_text(json.dumps(builds, indent=2) + "\n")
        print(f"builds: {'PASS' if builds.get('passed') else 'FAIL'}")
        ok &= bool(builds.get("passed"))

    for shot_set, w, h in (("scans", 1280, 720), ("safe-area", 2556, 1179)):
        result = capture(out, shot_set, w, h)
        for shot in result.get("shots", []):
            src = out / shot_set / shot["file"]
            dst = SHOTS.get(shot["file"])
            if dst and src.exists():
                shutil.copyfile(src, EVIDENCE / dst)
                shot["file"] = dst
        report = result.get("reportFile")
        if report and (out / shot_set / report).exists():
            shutil.copyfile(out / shot_set / report, run_dir / "perf-report-linux-lavapipe.txt")
            result["reportFile"] = "run/perf-report-linux-lavapipe.txt"
        (run_dir / f"capture-{shot_set}.json").write_text(json.dumps(result, indent=2) + "\n")
        good = result["exit_code"] == 0 and result.get("errorCount", 1) == 0 and result["shots"]
        good = good and all(
            s["insideSafeArea"] and s["overlayHeightFraction"] <= 0.08 for s in result["shots"]
        )
        print(f"capture {shot_set}: {'PASS' if good else 'FAIL'} ({len(result['shots'])} shot(s))")
        ok &= bool(good)

    shutil.rmtree(out, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
