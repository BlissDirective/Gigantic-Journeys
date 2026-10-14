"""Item-6 phase-1 launcher: MapAnything vs COLMAP+GLOMAP on Runpod Secure Cloud.

Owner go-ahead 2026-10-06 (phase 1 on Runpod, ~$1.2, under AUTH #039). Reuses the
``runpod_bench`` pod plumbing (Secure Cloud, US only, ephemeral SSH key, in-pod
max-runtime self-terminate, detached local watchdog, terminate in ``finally``).
Corpus rooms only: each ``--room`` dir holds ``frames/``, the GLOMAP ``sparse/`` and
``run.json`` of the existing corpus recon. No training, no bedroom data, no Modal.

    set -a; . ./.env.local; set +a      # RUNPOD_API_KEY (never printed)
    python services/reconstruction/tools/runpod_mapanything.py \
        --room /workspace/gj-pipe03/ma-ab/medieval-great-hall-winchester ... \
        --budget 1.5 --max-minutes 75 --out ./out/ma-phase1
"""

from __future__ import annotations

import argparse
import atexit
import json
import signal
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

try:  # run as a script from tools/
    import runpod_bench as rb
    from runpod_mapanything_job import CLIP_ID_RE
except ImportError:  # imported as tools.* (tests)
    from tools import runpod_bench as rb
    from tools.runpod_mapanything_job import CLIP_ID_RE

HERE = Path(__file__).resolve().parent
MA_CODE = "3d10cf7a3016fc0f9bb13a071ee66c47b10be0d9"  # == mapanything_ab_app
MA_REV = "00f9c245bbcb60522d1ed7f9e9d88462c6e3f38a"


def room_clip_id(room: Path) -> str:
    import re

    clip_id = json.loads((room / "run.json").read_text(encoding="utf-8"))["clip_id"]
    if not re.match(CLIP_ID_RE, clip_id):
        raise SystemExit(f"{room}: not a corpus clip id {clip_id!r} (corpus rooms only)")
    if not (room / "frames").is_dir() or not (room / "sparse").is_dir():
        raise SystemExit(f"{room}: needs frames/ and sparse/")
    return clip_id


def bundle(rooms: list[Path], dest: Path) -> Path:
    path = dest / "bundle.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        tar.add(rb.PKG, arcname="gj/reconstruction", filter=rb._no_cache)
        for name in ("runpod_mapanything_job.py", "runpod_mapanything_setup.sh"):
            tar.add(HERE / name, arcname=f"gj/{name}")
        for room in rooms:
            for part in ("frames", "sparse", "run.json"):
                tar.add(room / part, arcname=f"gj/rooms/{room.name}/{part}")
    return path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--room", action="append", required=True, type=Path)
    p.add_argument("--gpu", default="NVIDIA L40S")
    p.add_argument("--budget", type=float, default=1.5, help="hard $ cap")
    p.add_argument("--max-minutes", type=float, default=75.0)
    p.add_argument("--disk-gb", type=int, default=60)
    p.add_argument("--out", type=Path, default=Path("./out/ma-phase1"))
    args = p.parse_args(argv)
    rooms = [(room_clip_id(r), r) for r in args.room]
    args.out.mkdir(parents=True, exist_ok=True)
    price = rb.secure_price(args.gpu)
    worst = price * args.max_minutes / 60
    print(f"[plan] {args.gpu} secure ${price}/h; worst case ${worst:.2f} (cap ${args.budget})")
    if worst > args.budget:
        raise SystemExit("worst case exceeds the cap; nothing run")
    before = rb.account()
    atexit.register(rb.terminate_all)
    signal.signal(signal.SIGINT, rb._on_signal)
    signal.signal(signal.SIGTERM, rb._on_signal)
    rec: dict = {"gpu_type": args.gpu, "secure_price": price, "rooms": [c for c, _ in rooms]}
    with tempfile.TemporaryDirectory() as tmp:
        key_dir = Path(tmp)
        subprocess.run(  # noqa: S603
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_dir / "id")], check=True
        )
        tb = bundle([r for _, r in rooms], key_dir)
        pod = None
        try:
            pod = rb.Pod(args.gpu, key_dir, args.max_minutes, args.disk_gb)
            rb.local_watchdog([pod.id], args.max_minutes + 5)
            rec["pod_id"] = pod.id
            pod.wait_ssh()
            rate = float(pod.info.get("costPerHr") or pod.info.get("adjustedCostPerHr") or price)
            rec.update(rate_per_hour_usd=rate, machine=rb.pod_location(pod.id))
            rec["boot_to_ssh_s"] = round(pod.ready - pod.created, 1)
            pod.put(tb, "/root/bundle.tar.gz")
            t0 = time.monotonic()
            setup = pod.ssh(
                "cd /root && tar -xzf bundle.tar.gz && "
                f"MA_CODE={MA_CODE} MA_REV={MA_REV} bash gj/runpod_mapanything_setup.sh "
                "> /root/setup.log 2>&1; rc=$?; tail -c 1500 /root/setup.log; exit $rc",
                check=False,
            )
            rec["setup_s"] = round(time.monotonic() - t0, 1)
            rec["setup_tail"] = setup.stdout[-1500:]
            print(f"[pod] setup rc={setup.returncode} in {rec['setup_s']} s", flush=True)
            if setup.returncode != 0:
                raise RuntimeError("setup failed")
            remaining = args.max_minutes * 60 - (time.monotonic() - pod.created) - 120
            rooms_arg = " ".join(f"--room {c}=/root/gj/rooms/{r.name}" for c, r in rooms)
            cmd = (
                ". /root/gj-env.sh && cd /root/gj && python runpod_mapanything_job.py "
                f"--out /root/results.json --rate {rate} {rooms_arg} "
                f"--deadline {time.time() + remaining - 300:.0f} > /root/job.log 2>&1"
            )
            t1 = time.monotonic()
            try:
                rec["job_rc"] = pod.ssh(cmd, check=False, timeout=max(remaining, 60)).returncode
            except subprocess.TimeoutExpired:
                rec["job_rc"], rec["error"] = -1, "hit pod max runtime"
            rec["job_s"] = round(time.monotonic() - t1, 1)
            rec["job_log_tail"] = pod.ssh("tail -c 3000 /root/job.log", check=False).stdout
            pod.get("/root/results.json", args.out / "results.json")
            rec["results"] = json.loads((args.out / "results.json").read_text())
        except Exception as exc:  # noqa: BLE001 - always fall through to terminate
            rec["error"] = f"{type(exc).__name__}: {exc}"[:1500]
            print(f"[pod] ERROR {rec['error']}", flush=True)
        finally:
            if pod is not None:
                rec["pod_seconds"] = round(time.monotonic() - pod.created, 1)
            rb.terminate_all()
    time.sleep(30)
    ours = set(rb._created)
    left = [x.get("id") for x in (rb.rest("GET", "/pods") or []) if x.get("id") in ours]
    for pod_id in left:
        rb.terminate(pod_id)
    after = rb.account()
    rec.update(
        balance_before=before["clientBalance"],
        balance_after=after["clientBalance"],
        spend_per_hr_after=after["currentSpendPerHr"],
        pods_remaining=left,
        est_usd=round(rec.get("pod_seconds", 0) / 3600 * rec.get("rate_per_hour_usd", price), 4),
    )
    (args.out / "summary.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k not in ("results", "setup_tail")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
