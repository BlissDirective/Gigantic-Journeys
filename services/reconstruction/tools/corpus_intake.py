#!/usr/bin/env python3
"""Operator CLI for the corpus intake (M0-CAPT-01). Runs on the Operator VM.

The media never comes here: uploads land in the private ``gj-corpus`` Modal volume
and are stripped + verified in a Modal container (``corpus_intake_app.py``). This
CLI only signs links, triggers processing, and writes manifest rows to
``services/reconstruction/corpus/manifest.json`` (text, no media).

Setup once (Modal token from .env.local: MODAL_TOKEN_ID / MODAL_TOKEN_SECRET):
    python services/reconstruction/tools/corpus_intake.py setup     # creates the signing secret
    modal deploy services/reconstruction/corpus_intake_app.py

Then:
    python services/reconstruction/tools/corpus_intake.py link [--hours 72]   # send to the Owner
    python services/reconstruction/tools/corpus_intake.py status
    python services/reconstruction/tools/corpus_intake.py process [--dry-run]
    python services/reconstruction/tools/corpus_intake.py fetch room-01 --out ~/gj-corpus-work \
        [--frames 2]
    python services/reconstruction/tools/corpus_intake.py delete room-01

``link`` prints a capability URL: anyone holding it can upload (never download)
until it expires. Send it to the Owner privately; never paste it in git, tickets
or logs.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVICE = HERE.parent
REPO = SERVICE.parents[1]
sys.path.insert(0, str(SERVICE))

from tools import corpus_manifest  # noqa: E402

APP_NAME = "gj-corpus-intake"
VOLUME_NAME = "gj-corpus"
SECRET_NAME = "gj-corpus-intake"  # noqa: S105 -- a Modal secret name, not a value


def _modal():
    try:
        import modal
    except ImportError:
        sys.exit("the modal client is needed: use the repo .venv (pip install modal)")
    return modal


def _fn(name: str):
    return _modal().Function.from_name(APP_NAME, name)


def cmd_setup(_: argparse.Namespace) -> int:
    """Create the link-signing secret once. The key is random and never printed."""
    listing = subprocess.run(
        ["modal", "secret", "list", "--json"], capture_output=True, text=True, check=True
    ).stdout
    if any((s.get("name") or s.get("Name")) == SECRET_NAME for s in json.loads(listing or "[]")):
        print(f"secret {SECRET_NAME} already exists (rotate: modal secret delete, then setup)")
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "intake.json"
        src.touch(mode=0o600)
        src.write_text(json.dumps({"CORPUS_INTAKE_KEY": secrets.token_urlsafe(48)}))
        subprocess.run(
            ["modal", "secret", "create", SECRET_NAME, "--from-json", str(src)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    print(f"created Modal secret {SECRET_NAME} (value not shown)")
    return 0


def cmd_link(args: argparse.Namespace) -> int:
    token = _fn("make_token").remote(hours=args.hours)
    url = _fn("web").get_web_url().rstrip("/")
    print(f"Upload link (valid {args.hours:g} h; upload-only; send privately):")
    print(f"{url}/?t={token}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    state = _fn("list_state").remote()
    print(f"inbox: {len(state['inbox'])} upload(s)")
    for u in state["inbox"]:
        pct = 100 * (u["received"] or 0) / max(1, u["size"] or 1)
        flag = "complete" if u["complete"] else f"{pct:.0f}% received"
        size_mb = u["size"] / 1e6
        print(f"  {u['upload']}  {u['mode']:<8}  {size_mb:8.1f} MB  {flag}  ({u['age_h']} h old)")
    print(f"corpus: {len(state['captures'])} capture(s)")
    for r in state["captures"]:
        w = r.get("intake", {}).get("warnings", [])
        print(f"  {r['id']:<12} {r['duration_s']:6.1f} s  {len(w)} warning(s)")
    return 0


def _load_manifest() -> dict:
    return json.loads(corpus_manifest.MANIFEST.read_text(encoding="utf-8"))


def _write_manifest(manifest: dict) -> None:
    manifest["captures"].sort(key=lambda r: (r["mode"] != "room", r["id"]))
    errors = corpus_manifest.validate(manifest)
    if errors:
        for e in errors:
            print(f"ERROR {e}", file=sys.stderr)
        raise SystemExit("manifest not written: validation failed")
    corpus_manifest.MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def cmd_process(args: argparse.Namespace) -> int:
    result = _fn("process_inbox").remote(dry_run=args.dry_run, keep_audio=args.keep_audio)
    for f in result["failed"]:
        print(f"FAILED {f['upload']}: {f['error']}", file=sys.stderr)
    if result["purged_stale"]:
        print(f"purged {len(result['purged_stale'])} unfinished upload(s) older than 7 days")
    rows = result["processed"]
    if args.dry_run:
        print(json.dumps(rows, indent=2))
        return 1 if result["failed"] else 0
    # Rows already in git keep their (possibly hand-corrected) labels; new ones are
    # added, including any capture.json a previous interrupted run left behind.
    manifest = _load_manifest()
    have = {r["id"] for r in manifest["captures"]}
    fresh = [r for r in _fn("list_state").remote()["captures"] if r["id"] not in have]
    manifest["captures"].extend(fresh)
    _write_manifest(manifest)
    for r in fresh:
        loc = "; GPS was present and removed" if r["privacy"]["location_found_on_intake"] else ""
        print(f"added {r['id']} ({r['duration_s']:.0f} s{loc})")
        for w in r.get("intake", {}).get("warnings", []):
            print(f"    warning: {w}")
    print(json.dumps(corpus_manifest.summary(manifest), indent=2))
    return 1 if result["failed"] else 0


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO.resolve())
    except ValueError:
        return False
    return True


def cmd_fetch(args: argparse.Namespace) -> int:
    out = Path(args.out).expanduser()
    if _inside_repo(out):
        sys.exit(
            "refusing to write corpus media inside the git checkout; use e.g. ~/gj-corpus-work"
        )
    manifest = {r["id"]: r for r in _load_manifest()["captures"]}
    row = manifest.get(args.capture_id)
    if not row:
        sys.exit(f"{args.capture_id} is not in manifest.json (run process first)")
    vol = _modal().Volume.from_name(VOLUME_NAME, version=2)
    dest = out / args.capture_id
    dest.mkdir(parents=True, exist_ok=True, mode=0o700)
    video = dest / Path(row["storage"]["path"]).name
    with video.open("wb") as fh:
        for chunk in vol.read_file(row["storage"]["path"]):
            fh.write(chunk)
    print(f"fetched {video} ({video.stat().st_size / 1e6:.1f} MB)")
    if args.frames:
        images = dest / "images"
        images.mkdir(exist_ok=True)
        subprocess.run(
            [
                shutil.which("ffmpeg") or "ffmpeg",
                "-nostdin",
                "-loglevel",
                "error",
                "-i",
                str(video),
                "-vf",
                f"fps={args.frames}",
                "-map_metadata",
                "-1",
                "-q:v",
                "2",
                str(images / "%05d.jpg"),
            ],
            check=True,
        )
        n = len(list(images.glob("*.jpg")))
        print(f"extracted {n} frames -> {images}")
        print(
            "reconstruct: modal run services/reconstruction/modal_app.py "
            f"--images {images} --scan-id {args.capture_id} --source corpus"
        )
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    removed = _fn("delete_capture").remote(args.capture_id)
    manifest = _load_manifest()
    manifest["captures"] = [r for r in manifest["captures"] if r["id"] != args.capture_id]
    _write_manifest(manifest)
    where = "deleted from the volume" if removed else "not on the volume"
    print(f"{args.capture_id}: {where}; manifest row removed")
    return 0


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="create the link-signing Modal secret once")
    p = sub.add_parser("link", help="print a signed, expiring upload link for the Owner")
    p.add_argument("--hours", type=float, default=72.0)
    sub.add_parser("status", help="inbox and corpus counts")
    p = sub.add_parser("process", help="strip + verify + store new uploads; write manifest rows")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-audio", action="store_true")
    p = sub.add_parser("fetch", help="download a stripped capture (outside the repo)")
    p.add_argument("capture_id")
    p.add_argument("--out", required=True)
    p.add_argument("--frames", type=float, default=0, help="also extract N frames/s to images/")
    p = sub.add_parser("delete", help="delete a capture from the volume and the manifest")
    p.add_argument("capture_id")
    args = ap.parse_args(argv)
    return {
        "setup": cmd_setup,
        "link": cmd_link,
        "status": cmd_status,
        "process": cmd_process,
        "fetch": cmd_fetch,
        "delete": cmd_delete,
    }[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
