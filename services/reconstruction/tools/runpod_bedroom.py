"""Bedroom cleanup stage 2 launcher (M1-PIPE-02) on Runpod Secure Cloud under AUTH #051.

Retrains the Owner's bedroom capture (room-01, AUTH #046) with deblur + Splatfacto-W
appearance at the 400K phone budget (``runpod_bedroom_job.py``). AUTH #051's binding
conditions are enforced here, not left to the operator:

1. **Faces-blurred frames only**: ``--frames`` must be the ``blurred/`` staging folder
   next to its ``blur_log.json`` (the raw frames / video never leave the box).
2. **Secure Cloud, US only, no network volume** (``volumeInGb: 0``; container disk only),
   an **ephemeral per-run SSH key**, SSH/SCP transfer only (``runpod_bench.Pod``).
3. Pod **terminated** in ``finally`` (+ atexit / signals), in-pod max-runtime and idle
   self-terminate, a detached local watchdog; the pod's working data is deleted before
   termination; the end **verifies via the API** that the pod is gone (404) and no
   network volume exists. Only ``results.json`` (metrics) and the 400K ``splat.ply``
   come back, into ``--out`` (a ``chmod 700`` folder under the private staging root).
4. Spend: worst case (price x ``--max-minutes``) plus the bedroom-cleanup ledger must fit
   ``--hard-stop`` ($15, #051 (7)); the account balance is recorded before and after.
5. Refuses to run unless ``governance/AUTHORIZATION_LOG.md`` logs #051 as APPROVED.

    set -a; . ./.env.local; set +a      # RUNPOD_API_KEY (never printed)
    python services/reconstruction/tools/runpod_bedroom.py \\
        --frames /workspace/owner-capture/work/blurred \\
        --sparse /workspace/owner-capture/work/cleanup/sparse \\
        --out /workspace/owner-capture/work/cleanup/stage2
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import re
import shlex
import signal
import stat
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

try:  # run as a script from tools/
    import runpod_bench as rb
except ImportError:  # imported as tools.* (tests)
    from tools import runpod_bench as rb

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
STAGING_ROOT = Path("/workspace/owner-capture")
LEDGER = "runpod-ledger.json"  # per-run spend of the bedroom cleanup (#051 hard stop)
WIPE = "rm -rf /root/gj /root/gj-work /root/bundle.tar.gz /root/splat.ply /root/results.json; sync"


def auth_051_approved(log: Path) -> bool:
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.startswith("| #051 |"):
            return "**APPROVED**" in line and "Runpod Secure" in line.replace("RunPod", "Runpod")
    return False


def check_frames(frames: Path) -> int:
    """The faces-blurred set only: ``blurred/`` beside its ``blur_log.json``."""
    frames = frames.resolve()
    if frames.name != "blurred" or not (frames.parent / "blur_log.json").is_file():
        raise SystemExit(f"{frames}: not the faces-blurred staging folder (AUTH #051 (1))")
    n = sum(1 for p in frames.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if n == 0:
        raise SystemExit(f"{frames}: no frames")
    return n


def check_out(out: Path) -> Path:
    out = out.resolve()
    if STAGING_ROOT.resolve() not in out.parents:
        raise SystemExit(f"--out must be under {STAGING_ROOT} (private staging)")
    out.mkdir(parents=True, exist_ok=True)
    os.chmod(out, 0o700)
    return out


def ledger_spent(path: Path) -> float:
    if not path.is_file():
        return 0.0
    return round(sum(r.get("est_usd", 0.0) for r in json.loads(path.read_text())), 4)


def bundle(frames: Path, sparse: Path, dest: Path) -> Path:
    path = dest / "bundle.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        tar.add(rb.PKG, arcname="gj/reconstruction", filter=rb._no_cache)
        for name in ("runpod_bedroom_job.py", "runpod_setup.sh"):
            tar.add(HERE / name, arcname=f"gj/{name}")
        tar.add(frames, arcname="gj/data/frames")
        for part in ("cameras.bin", "images.bin", "points3D.bin"):
            tar.add(sparse / part, arcname=f"gj/data/sparse/{part}")
    return path


def verify_gone(pod_id: str) -> dict:
    """API check after termination: the pod is gone and no network volume exists."""
    try:
        info = rb.rest("GET", f"/pods/{pod_id}")
        gone = not info
    except RuntimeError as exc:
        gone, info = "404" in str(exc), None
    listed = [p.get("id") for p in (rb.rest("GET", "/pods") or [])]
    volumes = rb.rest("GET", "/networkvolumes") or []
    return {
        "pod_get_404": bool(gone),
        "pod_in_list": pod_id in listed,
        "pods_on_account": len(listed),
        "network_volumes": len(volumes),
        "status_if_listed": (info or {}).get("desiredStatus") if isinstance(info, dict) else None,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--frames", type=Path, required=True)
    p.add_argument("--sparse", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--gpu", default="NVIDIA L40S")
    p.add_argument("--max-minutes", type=float, default=150.0)
    p.add_argument("--hard-stop", type=float, default=15.0, help="#051 total $ cap")
    p.add_argument("--disk-gb", type=int, default=60)
    p.add_argument("--deblur-samples", type=int, default=5)
    p.add_argument("--appearance", default="splatfacto-w")
    p.add_argument("--smoke-steps", type=int, default=300)
    args = p.parse_args(argv)
    if not auth_051_approved(REPO / "governance" / "AUTHORIZATION_LOG.md"):
        raise SystemExit("AUTH #051 is not logged as APPROVED; nothing run")
    n_frames = check_frames(args.frames)
    out = check_out(args.out)
    ledger = out.parent / LEDGER
    spent = ledger_spent(ledger)
    price = rb.secure_price(args.gpu)
    worst = price * args.max_minutes / 60
    print(f"[plan] {args.gpu} secure ${price}/h; worst ${worst:.2f}; spent ${spent:.2f}")
    if spent + worst > args.hard_stop:
        raise SystemExit(f"spent + worst case ${spent + worst:.2f} > hard stop; nothing run")
    before = rb.account()
    print(f"[plan] balance before ${before['clientBalance']:.2f}", flush=True)
    atexit.register(rb.terminate_all)
    signal.signal(signal.SIGINT, rb._on_signal)
    signal.signal(signal.SIGTERM, rb._on_signal)
    rec: dict = {
        "auth": "AUTH #051 + #046 + #045",
        "gpu_type": args.gpu,
        "secure_price": price,
        "frames": n_frames,
        "frames_set": "faces-blurred",
        "volume_gb": 0,
    }
    pod = None
    with tempfile.TemporaryDirectory() as tmp:
        key_dir = Path(tmp)
        subprocess.run(  # noqa: S603
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_dir / "id")], check=True
        )
        tb = bundle(args.frames.resolve(), args.sparse.resolve(), key_dir)
        rec["bundle_bytes"] = tb.stat().st_size
        try:
            pod = rb.Pod(args.gpu, key_dir, args.max_minutes, args.disk_gb, name="gj-bedroom-s2")
            rb.local_watchdog([pod.id], args.max_minutes + 5)
            rec["pod_id"] = pod.id
            pod.wait_ssh()
            rate = float(pod.info.get("costPerHr") or pod.info.get("adjustedCostPerHr") or price)
            rec.update(rate_per_hour_usd=rate, machine=rb.pod_location(pod.id))
            loc = (rec["machine"] or {}).get("dataCenterId") or ""
            if not str(loc).startswith("US-") or rec["machine"].get("secureCloud") is False:
                raise RuntimeError(f"pod not in a US Secure datacenter: {rec['machine']}")
            rec["boot_to_ssh_s"] = round(pod.ready - pod.created, 1)
            pod.put(tb, "/root/bundle.tar.gz")
            t0 = time.monotonic()
            setup = pod.ssh(
                "cd /root && tar -xzf bundle.tar.gz && rm -f bundle.tar.gz && "
                "bash gj/runpod_setup.sh > /root/setup.log 2>&1; rc=$?; "
                "tail -c 1200 /root/setup.log; exit $rc",
                check=False,
            )
            rec["setup_s"] = round(time.monotonic() - t0, 1)
            rec["setup_tail"] = setup.stdout[-1200:]
            print(f"[pod] setup rc={setup.returncode} in {rec['setup_s']} s", flush=True)
            if setup.returncode != 0:
                raise RuntimeError("setup failed")
            remaining = args.max_minutes * 60 - (time.monotonic() - pod.created) - 300
            job = (
                ". /root/gj-env.sh && cd /root/gj && python runpod_bedroom_job.py "
                "--frames /root/gj/data/frames --sparse /root/gj/data/sparse "
                "--out /root/results.json --ply-out /root/splat.ply "
                f"--rate {rate} --deblur-samples {args.deblur_samples} "
                f"--appearance {args.appearance} --smoke-steps {args.smoke_steps} "
                f"--deadline {time.time() + remaining:.0f} > /root/job.log 2>&1; "
                "echo $? > /root/job.rc"
            )
            # Detached in the pod: a dropped SSH session (2026-10-18 first attempt, rc 255
            # at step 6.6k) no longer kills the run; the launcher polls for job.rc.
            pod.ssh(f"nohup bash -c {shlex.quote(job)} > /dev/null 2>&1 < /dev/null &")
            t1 = time.monotonic()
            rec["job_rc"], drops = None, 0
            while time.monotonic() - t1 < remaining:
                time.sleep(60)
                try:
                    r = pod.ssh("cat /root/job.rc 2>/dev/null", check=False, timeout=60)
                except subprocess.TimeoutExpired:
                    drops += 1
                    continue
                if r.returncode == 255:
                    drops += 1
                elif r.stdout.strip():
                    rec["job_rc"] = int(r.stdout.strip())
                    break
            rec["ssh_drops_while_polling"] = drops
            if rec["job_rc"] is None:
                rec["job_rc"], rec["error"] = -1, "hit the pod max runtime"
            pod.ssh(rb.IDLE_SHUTDOWN, check=False, timeout=60)
            rec["job_s"] = round(time.monotonic() - t1, 1)
            # Log tail: metrics / tracebacks only (numbers, paths), never images.
            tail = pod.ssh("tail -c 2500 /root/job.log", check=False).stdout
            rec["job_log_tail"] = re.sub(r"https?://\S+", "<url>", tail)
            pod.get("/root/results.json", out / "results.json")
            rec["results"] = json.loads((out / "results.json").read_text())
            if rec["results"].get("status") == "ok":
                pod.get("/root/splat.ply", out / "splat.ply")
        except Exception as exc:  # noqa: BLE001 - always fall through to wipe + terminate
            rec["error"] = f"{type(exc).__name__}: {exc}"[:1500]
            print(f"[pod] ERROR {rec['error']}", flush=True)
        finally:
            if pod is not None:
                try:
                    rec["wipe_rc"] = pod.ssh(WIPE, check=False, timeout=120).returncode
                except Exception as exc:  # noqa: BLE001
                    rec["wipe_rc"] = f"{type(exc).__name__}"
                rec["pod_seconds"] = round(time.monotonic() - pod.created, 1)
            rb.terminate_all()
    time.sleep(30)
    if pod is not None:
        rec["verify"] = verify_gone(pod.id)
        if not rec["verify"]["pod_get_404"] or rec["verify"]["pod_in_list"]:
            rb.terminate(pod.id)
            time.sleep(20)
            rec["verify_retry"] = verify_gone(pod.id)
    after = rb.account()
    rec.update(
        balance_before=before["clientBalance"],
        balance_after=after["clientBalance"],
        spend_per_hr_after=after["currentSpendPerHr"],
        est_usd=round(rec.get("pod_seconds", 0) / 3600 * rec.get("rate_per_hour_usd", price), 4),
    )
    for f in out.iterdir():
        os.chmod(f, stat.S_IRUSR | stat.S_IWUSR)
    (out / "summary.json").write_text(json.dumps(rec, indent=2) + "\n")
    os.chmod(out / "summary.json", 0o600)
    runs = json.loads(ledger.read_text()) if ledger.is_file() else []
    runs.append({"run": out.name, "pod_id": rec.get("pod_id"), "est_usd": rec["est_usd"]})
    ledger.write_text(json.dumps(runs, indent=2) + "\n")
    os.chmod(ledger, 0o600)
    print(json.dumps({k: v for k, v in rec.items() if k not in ("results", "setup_tail")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
