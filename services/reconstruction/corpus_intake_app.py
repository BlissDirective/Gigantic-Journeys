"""Modal app for the reconstruction corpus intake (M0-CAPT-01).

Everything stays on project infrastructure (ADR-0005, SECURITY_CHECKLIST §6.3/§6.5):
the Owner uploads straight into the private ``gj-corpus`` Modal volume through a
signed, expiring link; stripping and verification run in a Modal container, so
raw media never touches the Bot VM, git, or a third-party share. Operator CLI:
``services/reconstruction/tools/corpus_intake.py`` (see ``corpus/README.md``).

    modal deploy services/reconstruction/corpus_intake_app.py

Volume layout (``gj-corpus``, Modal Volumes v2):
    /inbox/<upload-id>/owner.json      the Owner's form (mode, lighting, objects, check)
    /inbox/<upload-id>/upload.<ext>    the raw upload (deleted as soon as it is stripped)
    /corpus/<id>/<id>.<mov|mp4>        stripped, verified video (what reconstruction reads)
    /corpus/<id>/capture.json          the manifest row written at intake

Functions:
    web            upload page + chunked upload API (tools/intake_web.py); one container
    make_token     signs an upload link (the key lives only in the Modal secret)
    process_inbox  strip -> verify -> store -> manifest row; deletes the raw upload;
                   purges unfinished uploads older than 7 days (SECURITY_CHECKLIST §6.1)
    list_state     inbox counts + every capture.json (no media, no metadata values)
    delete_capture removes a capture (Owner-requested deletion); the id is never reused
"""

from __future__ import annotations

import sys
from pathlib import Path

import modal

_HERE = Path(__file__).parent
APP_NAME = "gj-corpus-intake"
VOLUME_NAME = "gj-corpus"
SECRET_NAME = "gj-corpus-intake"  # noqa: S105 -- a Modal secret NAME; holds CORPUS_INTAKE_KEY (random, never printed)
VOL = "/vol"
STALE_DAYS = 7

volume = modal.Volume.from_name(VOLUME_NAME, create_if_missing=True, version=2)
secret = modal.Secret.from_name(SECRET_NAME, required_keys=["CORPUS_INTAKE_KEY"])

# Only the tools/ package is mounted: nothing else from the repo (.env.local,
# .secrets-local/) can enter an image.
web_image = modal.Image.debian_slim(python_version="3.12").add_local_dir(
    _HERE / "tools", "/root/tools", ignore=["__pycache__"]
)
media_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg", "libimage-exiftool-perl")
    .add_local_dir(_HERE / "tools", "/root/tools", ignore=["__pycache__"])
)

app = modal.App(APP_NAME)


def _tools():
    if "/root" not in sys.path:
        sys.path.insert(0, "/root")
    from tools import corpus_manifest, intake_web, strip_metadata

    return corpus_manifest, intake_web, strip_metadata


@app.function(
    image=web_image,
    volumes={VOL: volume},
    secrets=[secret],
    max_containers=1,  # one writer: chunk appends stay ordered
    scaledown_window=300,
    timeout=900,
    cpu=0.5,
    memory=512,
)
@modal.concurrent(max_inputs=8)
@modal.asgi_app(label="gj-corpus-upload")
def web():
    import os

    _, intake_web, _ = _tools()
    inbox = Path(VOL) / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    return intake_web.IntakeApp(
        inbox, os.environ["CORPUS_INTAKE_KEY"].encode(), on_change=volume.commit.aio
    )


@app.function(image=web_image, secrets=[secret], timeout=60)
def make_token(hours: float = 72.0) -> str:
    import os

    _, intake_web, _ = _tools()
    return intake_web.make_token(os.environ["CORPUS_INTAKE_KEY"].encode(), hours)


def _captures(root: Path) -> list[dict]:
    import json

    rows = []
    for f in sorted((root / "corpus").glob("*/capture.json")):
        rows.append(json.loads(f.read_text()))
    return rows


@app.function(image=web_image, volumes={VOL: volume}, timeout=120)
def list_state() -> dict:
    import json
    import time

    volume.reload()
    root = Path(VOL)
    pending = []
    for d in sorted((root / "inbox").glob("*/")):
        meta_f = d / "owner.json"
        if not meta_f.exists():
            continue
        meta = json.loads(meta_f.read_text())
        part = d / "upload.part"
        pending.append(
            {
                "upload": d.name,
                "mode": meta.get("mode"),
                "size": meta.get("size"),
                "received": part.stat().st_size if part.exists() else meta.get("size"),
                "complete": "completed_at" in meta,
                "age_h": round((time.time() - meta.get("started_at", time.time())) / 3600, 1),
            }
        )
    return {"inbox": pending, "captures": _captures(root)}


@app.function(image=media_image, volumes={VOL: volume}, timeout=3600, cpu=2.0, memory=2048)
def process_inbox(dry_run: bool = False, keep_audio: bool = False) -> dict:
    import json
    import shutil
    import time

    corpus_manifest, _, strip_metadata = _tools()
    volume.reload()
    root = Path(VOL)
    inbox, corpus = root / "inbox", root / "corpus"
    corpus.mkdir(parents=True, exist_ok=True)
    taken = {p.name for p in corpus.iterdir() if p.is_dir()}
    done, failed, purged = [], [], []
    today = time.strftime("%Y-%m-%d", time.gmtime())
    for d in sorted(inbox.glob("*/")) if inbox.exists() else []:
        meta_f = d / "owner.json"
        meta = json.loads(meta_f.read_text()) if meta_f.exists() else {}
        if "completed_at" not in meta:
            if time.time() - meta.get("started_at", 0) > STALE_DAYS * 86400:
                purged.append(d.name)
                if not dry_run:
                    shutil.rmtree(d)
            continue
        raw = d / f"upload{meta['ext']}"
        if strip_metadata.kind_of(raw) != "video":
            failed.append({"upload": d.name, "error": "photos are not part of the M0 corpus"})
            continue
        cid = corpus_manifest.next_id(meta["mode"], taken)
        work = root / "work" / d.name
        work.mkdir(parents=True, exist_ok=True)
        out = work / f"{cid}{raw.suffix.lower()}"
        try:
            res = strip_metadata.strip_file(raw, out, keep_audio=keep_audio)
            video, duration = strip_metadata.video_info(out)
            video["sha256"] = res.sha256
            row = corpus_manifest.build_row(
                capture_id=cid,
                owner=meta,
                video=video,
                duration_s=duration,
                device_model=res.device_model,
                captured_on=res.captured_on,
                received_on=time.strftime("%Y-%m-%d", time.gmtime(meta["completed_at"])),
                strip_tool=strip_metadata.TOOL_ID,
                verified_with=res.verified_with,
                location_found=res.location_found,
            )
        except (strip_metadata.StripError, StopIteration, KeyError, ValueError) as exc:
            failed.append({"upload": d.name, "error": str(exc)[:300]})
            shutil.rmtree(work, ignore_errors=True)
            continue
        if dry_run:
            done.append(row)
            shutil.rmtree(work, ignore_errors=True)
            continue
        dest = corpus / cid
        dest.mkdir(parents=True)
        shutil.move(str(out), dest / out.name)
        (dest / "capture.json").write_text(json.dumps(row, indent=2) + "\n")
        shutil.rmtree(d)  # the raw upload (with any GPS) is gone once the clean copy exists
        shutil.rmtree(work, ignore_errors=True)
        taken.add(cid)
        done.append(row)
        volume.commit()
    shutil.rmtree(root / "work", ignore_errors=True)
    if not dry_run:
        volume.commit()
    return {"processed": done, "failed": failed, "purged_stale": purged, "day": today}


@app.function(image=web_image, volumes={VOL: volume}, timeout=300)
def delete_capture(capture_id: str) -> bool:
    import re
    import shutil
    import time

    if not re.fullmatch(r"(room|tabletop)-[0-9]{2,3}", capture_id):
        raise ValueError("bad capture id")
    volume.reload()
    d = Path(VOL) / "corpus" / capture_id
    if not (d / "capture.json").exists():
        return False
    shutil.rmtree(d)
    # Tombstone: the id is never reused, so manifest history stays unambiguous.
    d.mkdir()
    (d / "DELETED").write_text(time.strftime("%Y-%m-%d\n", time.gmtime()))
    volume.commit()
    return True
