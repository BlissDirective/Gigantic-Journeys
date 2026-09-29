"""Runpod Secure Cloud benchmark launcher (M1-RES-01 validation; not the migration).

Runs from the Operator VM. For each GPU type it creates ONE Secure Cloud pod in a
US datacenter, bootstraps the reconstruction stack (``runpod_setup.sh``), runs
``runpod_job.py`` (Mip-NeRF 360 room + optional corpus clips from already
extracted frames), copies the results back and TERMINATES the pod.

    set -a; . ./.env.local; set +a      # RUNPOD_API_KEY (never printed)
    python services/reconstruction/tools/runpod_bench.py \
        --gpu "NVIDIA A40" --gpu "NVIDIA GeForce RTX 4090" --room \
        --clip tabletop/lego-paranal-observatory=/tmp/gj-frames/lego/frames \
        --budget 6 --out ./out/runpod

Safeguards:
- Secure Cloud only (``cloudType=SECURE``), US datacenters only; the job refuses
  anything but ``public`` / ``corpus`` sources.
- Pre-flight: projected worst case (sum of pod $/h x ``--max-minutes``) must fit
  ``--budget``; otherwise nothing is created.
- Every pod is terminated in a ``finally`` (plus atexit / SIGINT / SIGTERM), and
  the end verifies via the API that none of its pods remain (other pods on the
  account are reported, never touched) and records the account spend rate.
- Each pod also self-terminates after ``--max-minutes`` (watchdog in the start
  command) and right after its job, and a detached local watchdog deletes the
  launched pods after ``--max-minutes`` + 5 in case this process dies.
- Pod access is an ephemeral SSH key generated per run (deleted afterwards).
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

REST = "https://rest.runpod.io/v1"
GRAPHQL = "https://api.runpod.io/graphql"
IMAGE = "nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04"
US_DATACENTERS = [
    "US-IL-1", "US-TX-3", "US-KS-2", "US-GA-2", "US-WA-1", "US-TX-1", "US-TX-4",
    "US-CA-2", "US-NC-1", "US-DE-1", "US-KS-3", "US-GA-1", "US-MD-1",
]  # fmt: skip
# NOTE: an ``allowedCudaVersions`` filter made every Secure request fail with "no
# instances available" (2026-09-28), so the driver is checked in the pod instead
# (torch cu124 needs a driver >= 550; run_pod records nvidia-smi).
HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "reconstruction"

# Container start command: sshd for the launcher, curl, and a hard max-runtime
# watchdog that terminates the pod itself (runpodctl if present, else the REST
# API with the pod-scoped key Runpod injects as RUNPOD_API_KEY).
SELF_TERMINATE = (
    '(command -v runpodctl >/dev/null && runpodctl remove pod "$RUNPOD_POD_ID") || '
    'curl -fsS -X DELETE -H "Authorization: Bearer $RUNPOD_API_KEY" '
    '"https://rest.runpod.io/v1/pods/$RUNPOD_POD_ID"'
)
# After the job: idle auto-shutdown 5 min later unless the launcher already
# terminated the pod (sshd sessions do not inherit the container env, so read
# RUNPOD_POD_ID / RUNPOD_API_KEY from PID 1).
IDLE_SHUTDOWN = (
    'nohup bash -c \'export $(tr "\\\\0" "\\\\n" < /proc/1/environ | grep -E ^RUNPOD_); '
    f"sleep 300; {SELF_TERMINATE.replace(chr(39), '')}' > /root/idle.log 2>&1 < /dev/null &"
)
START_CMD = (
    f"(sleep $GJ_MAX_RUNTIME_S; {SELF_TERMINATE}) > /root/watchdog.log 2>&1 & "
    "apt-get update -qq && apt-get install -y -qq --no-install-recommends "
    "openssh-server curl ca-certificates > /dev/null; "
    'mkdir -p /root/.ssh /run/sshd && echo "$PUBLIC_KEY" > /root/.ssh/authorized_keys && '
    "chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys && /usr/sbin/sshd; "
    "sleep infinity"
)

_created: list[str] = []
_lock = threading.Lock()


def _key() -> str:
    key = os.environ.get("RUNPOD_API_KEY", "")
    if not key:
        raise SystemExit("RUNPOD_API_KEY is not set (source .env.local)")
    return key


def _headers() -> dict[str, str]:
    # Runpod's edge rejects the default Python-urllib User-Agent (HTTP 403).
    return {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
        "User-Agent": "gj-runpod-bench/1.0",
    }


def rest(method: str, path: str, body: dict | None = None) -> dict | list | None:
    req = urllib.request.Request(  # noqa: S310 - fixed https host
        REST + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=_headers(),
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"{method} {path}: HTTP {exc.code} {detail}") from None
    return json.loads(raw) if raw.strip() else None


def account() -> dict:
    query = "{ myself { clientBalance currentSpendPerHr spendLimit } }"
    req = urllib.request.Request(  # noqa: S310 - fixed https host
        GRAPHQL,
        data=json.dumps({"query": query}).encode(),
        headers=_headers(),
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read())["data"]["myself"]


def _graphql(query: str) -> dict:
    req = urllib.request.Request(  # noqa: S310 - fixed https host
        GRAPHQL, data=json.dumps({"query": query}).encode(), headers=_headers()
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        return json.loads(resp.read())["data"]


def pod_location(pod_id: str) -> dict:
    """Datacenter + cloud type of a running pod (the REST pod object omits them)."""
    fields = "machine { dataCenterId secureCloud location }"
    q = f'{{ pod(input:{{podId:"{pod_id}"}}) {{ {fields} }} }}'
    try:
        return (_graphql(q).get("pod") or {}).get("machine") or {}
    except Exception as exc:  # noqa: BLE001 - informational only
        return {"error": str(exc)[:200]}


def secure_price(gpu_type: str) -> float:
    query = (
        f'{{ gpuTypes(input:{{id:"{gpu_type}"}}) {{ id securePrice '
        "lowestPrice(input:{gpuCount:1, secureCloud:true}) { uninterruptablePrice stockStatus } } }"
    )
    req = urllib.request.Request(  # noqa: S310 - fixed https host
        GRAPHQL,
        data=json.dumps({"query": query}).encode(),
        headers=_headers(),
    )
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
        row = json.loads(resp.read())["data"]["gpuTypes"][0]
    return float(row["lowestPrice"]["uninterruptablePrice"] or row["securePrice"])


def terminate(pod_id: str) -> None:
    for attempt in range(5):
        try:
            rest("DELETE", f"/pods/{pod_id}")
            print(f"[pod {pod_id}] terminated", flush=True)
            return
        except RuntimeError as exc:
            if "404" in str(exc):
                return
            print(f"[pod {pod_id}] terminate attempt {attempt + 1} failed: {exc}", flush=True)
            time.sleep(5)


def terminate_all() -> None:
    with _lock:
        ids = list(_created)
    for pod_id in ids:
        terminate(pod_id)


def _on_signal(signum, _frame) -> None:
    terminate_all()
    raise SystemExit(128 + signum)


def local_watchdog(pod_ids: list[str], minutes: float) -> None:
    """Detached process: delete these pods after ``minutes`` even if we die."""
    code = (
        "import os,time,urllib.request\n"
        f"time.sleep({minutes * 60:.0f})\n"
        f"for p in {pod_ids!r}:\n"
        "    r=urllib.request.Request('https://rest.runpod.io/v1/pods/'+p,method='DELETE',"
        "headers={'Authorization':'Bearer '+os.environ['RUNPOD_API_KEY'],"
        "'User-Agent':'gj-runpod-bench/1.0'})\n"
        "    try: urllib.request.urlopen(r,timeout=60)\n"
        "    except Exception: pass\n"
    )
    subprocess.Popen(  # noqa: S603
        [sys.executable, "-c", code],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class Pod:
    def __init__(self, gpu_type: str, key_dir: Path, max_minutes: float, disk_gb: int) -> None:
        self.gpu_type, self.key_dir = gpu_type, key_dir
        slug = gpu_type.replace("NVIDIA ", "").replace("GeForce ", "").replace(" ", "-").lower()
        self.slug = slug
        body = {
            "name": f"gj-bench-{slug}",
            "imageName": IMAGE,
            "cloudType": "SECURE",
            "computeType": "GPU",
            "gpuTypeIds": [gpu_type],
            "gpuCount": 1,
            "interruptible": False,
            "dataCenterIds": US_DATACENTERS,
            "dataCenterPriority": "availability",
            "containerDiskInGb": disk_gb,
            "volumeInGb": 0,
            "ports": ["22/tcp"],
            "supportPublicIp": True,
            "minVCPUPerGPU": 8,
            "minRAMPerGPU": 16,
            "env": {
                "PUBLIC_KEY": (key_dir / "id.pub").read_text().strip(),
                "GJ_MAX_RUNTIME_S": str(int(max_minutes * 60)),
            },
            "dockerStartCmd": ["bash", "-c", START_CMD],
        }
        pod = rest("POST", "/pods", body)
        self.id = pod["id"]
        with _lock:
            _created.append(self.id)
        self.created = time.monotonic()
        self.info = pod
        print(f"[{slug}] pod {self.id} created", flush=True)

    def wait_ssh(self, timeout_s: float = 900) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            info = rest("GET", f"/pods/{self.id}")
            ip, ports = info.get("publicIp"), info.get("portMappings") or {}
            if ip and ports.get("22"):
                self.info, self.host, self.port = info, ip, int(ports["22"])
                probe = self.ssh("echo ok", check=False, timeout=20)
                if probe.returncode == 0:
                    self.ready = time.monotonic()
                    return
            time.sleep(10)
        raise RuntimeError(f"pod {self.id}: SSH not reachable in {timeout_s:.0f} s")

    def _ssh_base(self) -> list[str]:
        return [
            "-i", str(self.key_dir / "id"), "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", "LogLevel=ERROR",
            "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=30",
        ]  # fmt: skip

    def ssh(self, cmd: str, check: bool = True, timeout: float | None = None):
        argv = ["ssh", *self._ssh_base(), "-p", str(self.port), f"root@{self.host}", cmd]
        res = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)  # noqa: S603
        if check and res.returncode != 0:
            raise RuntimeError(f"ssh {cmd[:60]!r} rc={res.returncode}: {res.stderr[-800:]}")
        return res

    def put(self, local: Path, remote: str) -> None:
        argv = ["scp", *self._ssh_base(), "-P", str(self.port), str(local)]
        subprocess.run([*argv, f"root@{self.host}:{remote}"], check=True, capture_output=True)  # noqa: S603

    def get(self, remote: str, local: Path) -> None:
        argv = ["scp", *self._ssh_base(), "-P", str(self.port)]
        subprocess.run([*argv, f"root@{self.host}:{remote}", str(local)], check=True)  # noqa: S603


def _bundle(clips: list[tuple[str, Path]], dest: Path) -> Path:
    """Tar the reconstruction package, the in-pod scripts and the clip frames."""
    path = dest / "bundle.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        tar.add(PKG, arcname="gj/reconstruction", filter=_no_cache)
        tar.add(HERE / "runpod_job.py", arcname="gj/runpod_job.py")
        tar.add(HERE / "runpod_setup.sh", arcname="gj/runpod_setup.sh")
        for clip_id, frames in clips:
            tar.add(frames, arcname=f"gj/frames/{clip_id.split('/', 1)[1]}")
    return path


def _no_cache(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
    return None if "__pycache__" in info.name or info.name.endswith(".pyc") else info


def run_pod(pod: Pod, args, bundle: Path, clips, out_dir: Path, results: dict) -> None:
    rec: dict = {"gpu_type": pod.gpu_type, "pod_id": pod.id}
    results[pod.gpu_type] = rec
    try:
        pod.wait_ssh()
        info = pod.info
        rate = float(info.get("costPerHr") or info.get("adjustedCostPerHr") or 0)
        rec.update(
            rate_per_hour_usd=rate,
            machine=pod_location(pod.id),
            vcpus=info.get("vcpuCount"),
            memory_gb=info.get("memoryInGb"),
            boot_to_ssh_s=round(pod.ready - pod.created, 1),
        )
        env = pod.ssh(
            "nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader; "
            "nproc; free -g | awk '/Mem/{print $2}'; "
            'echo "pod_key_injected=$(tr "\\0" "\\n" < /proc/1/environ | grep -c ^RUNPOD_API_KEY=) '
            'runpodctl=$(command -v runpodctl >/dev/null && echo yes || echo no)"'
        ).stdout.split("\n")
        rec["host"] = [line for line in env if line]
        print(f"[{pod.slug}] ready: {rec['host']}", flush=True)
        pod.put(bundle, "/root/bundle.tar.gz")
        t0 = time.monotonic()
        setup_cmd = "cd /root && tar -xzf bundle.tar.gz && bash gj/runpod_setup.sh"
        setup = pod.ssh(setup_cmd, check=False)
        rec["setup_s"] = round(time.monotonic() - t0, 1)
        rec["setup_tail"] = (setup.stdout + setup.stderr)[-1500:]
        print(f"[{pod.slug}] setup rc={setup.returncode} in {rec['setup_s']} s", flush=True)
        if setup.returncode != 0:
            raise RuntimeError("setup failed")
        remaining = args.max_minutes * 60 - (time.monotonic() - pod.created) - 120
        deadline = time.time() + remaining - args.min_job_minutes * 60
        clip_args = " ".join(f"--clip {c}=/root/gj/frames/{c.split('/', 1)[1]}" for c, _ in clips)
        cmd = (
            ". /root/gj-env.sh && cd /root/gj && python runpod_job.py --out /root/results.json "
            f"--rate {rate} --gpu '{pod.gpu_type}' {'--room' if args.room else ''} {clip_args} "
            f"--deadline {deadline:.0f} > /root/job.log 2>&1; rc=$?; {IDLE_SHUTDOWN} exit $rc"
        )
        t1 = time.monotonic()
        try:
            job_rc = pod.ssh(cmd, check=False, timeout=max(remaining, 60)).returncode
        except subprocess.TimeoutExpired:
            job_rc = -1
            rec["error"] = "job hit the pod max runtime; partial results"
        rec["job_s"] = round(time.monotonic() - t1, 1)
        rec["job_rc"] = job_rc
        rec["job_log_tail"] = pod.ssh("tail -c 3000 /root/job.log", check=False).stdout
        local = out_dir / f"{pod.slug}.json"
        pod.get("/root/results.json", local)
        rec["results"] = json.loads(local.read_text())
    except Exception as exc:  # noqa: BLE001 - always fall through to terminate
        rec["error"] = f"{type(exc).__name__}: {exc}"[:1500]
        print(f"[{pod.slug}] ERROR {rec['error']}", flush=True)
    finally:
        rec["pod_seconds"] = round(time.monotonic() - pod.created, 1)
        terminate(pod.id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gpu", action="append", required=True, help="Runpod gpuTypeId")
    parser.add_argument("--room", action="store_true")
    parser.add_argument("--clip", action="append", default=[], help="<clip id>=<frames dir>")
    parser.add_argument("--budget", type=float, default=6.0, help="hard $ cap for this run")
    parser.add_argument("--max-minutes", type=float, default=45.0, help="per-pod max runtime")
    parser.add_argument("--min-job-minutes", type=float, default=8.0)
    parser.add_argument("--disk-gb", type=int, default=60)
    parser.add_argument("--out", default="./out/runpod")
    args = parser.parse_args(argv)
    clips = [(c.split("=", 1)[0], Path(c.split("=", 1)[1])) for c in args.clip]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    prices = {g: secure_price(g) for g in args.gpu}
    projected = sum(p * args.max_minutes / 60 for p in prices.values())
    print(f"[plan] secure $/h {prices}; worst case ${projected:.2f} (cap ${args.budget})")
    if projected > args.budget:
        raise SystemExit(f"projected ${projected:.2f} exceeds the ${args.budget} cap; nothing run")
    before = account()
    print(f"[plan] balance ${before['clientBalance']:.2f}, spend ${before['currentSpendPerHr']}/h")

    atexit.register(terminate_all)
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)
    results: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        key_dir = Path(tmp)
        subprocess.run(  # noqa: S603
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key_dir / "id")],
            check=True,
        )
        bundle = _bundle(clips, key_dir)
        try:
            pods = [Pod(g, key_dir, args.max_minutes, args.disk_gb) for g in args.gpu]
            local_watchdog([p.id for p in pods], args.max_minutes + 5)
            threads = [
                threading.Thread(target=run_pod, args=(p, args, bundle, clips, out_dir, results))
                for p in pods
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            terminate_all()
    time.sleep(20)
    # Only OUR pods are this run's business: another launcher may be running
    # (2026-09-28: a sweep of "every pod" killed a concurrent run mid-job).
    with _lock:
        ours = set(_created)
    listed = rest("GET", "/pods") or []
    remaining = [p for p in listed if p.get("id") in ours]
    others = [p.get("id") for p in listed if p.get("id") not in ours]
    after = account()
    summary = {
        "results": results,
        "balance_before": before["clientBalance"],
        "balance_after": after["clientBalance"],
        "spend_per_hr_after": after["currentSpendPerHr"],
        "pods_remaining": [p.get("id") for p in remaining],
        "other_pods_on_account": others,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))
    if remaining:
        print("WARNING: pods of this run still exist; terminating", flush=True)
        for p in remaining:
            terminate(p["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
