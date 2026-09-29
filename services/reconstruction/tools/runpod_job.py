"""In-pod benchmark job for Runpod Secure Cloud pods (M1-RES-01 validation).

Runs INSIDE a pod prepared by ``runpod_setup.sh`` (driven by ``runpod_bench.py``);
stdlib + the ``reconstruction`` package only, Python >= 3.10.

- ``--room``: the Mip-NeRF 360 ``room`` benchmark (``images_4``, 311 images), fetched
  from its public archive with HTTP range requests (only ``room/images_4/`` is
  read out of the 12 GB zip), run with the Modal defaults of
  ``modal_app.reconstruct`` (CUDA COLMAP, GPU SIFT, ``--matcher auto``, incremental
  mapper, profile ``scaled-10k-dense``, 2M splat cap).
- ``--clip <id>=<frames dir>``: an open-video corpus clip from frames already
  extracted by the Modal ``--corpus`` mode (``extract_clip_frames``: the same
  frames), run with the ``reconstruct_clip`` defaults (GLOMAP global mapper,
  sequential matching, 4096 SIFT features).

Only ``public`` / ``corpus`` sources can run (``require_offsite_source``). Cost is
pipeline wall x the pod's all-in $/h (Runpod prices GPU + vCPU + RAM together),
so no separate CPU / memory line.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import time
import urllib.request
import zipfile
from pathlib import Path

MIPNERF360_URL = "https://storage.googleapis.com/gresearch/refraw360/360_v2.zip"
ROOM_PREFIX = "room/images_4/"
CORPUS_SFM, CORPUS_MATCHER, CORPUS_MAX_FEATURES = "glomap", "sequential", 4096


class HttpRangeFile(io.RawIOBase):
    """Read-only, seekable view of a remote file over HTTP Range requests."""

    def __init__(self, url: str, chunk: int = 4 << 20) -> None:
        self.url, self.chunk, self.pos = url, chunk, 0
        head = urllib.request.Request(url, method="HEAD")  # noqa: S310 - fixed https URL
        with urllib.request.urlopen(head, timeout=60) as resp:  # noqa: S310
            self.size = int(resp.headers["Content-Length"])
        self._buf_start, self._buf = 0, b""
        self.requests = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = 0) -> int:
        base = {0: 0, 1: self.pos, 2: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def _fetch(self, start: int, length: int) -> bytes:
        end = min(self.size, start + length) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end}"})  # noqa: S310
        self.requests += 1
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310
            return resp.read()

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if n <= 0:
            return b""
        lo, hi = self._buf_start, self._buf_start + len(self._buf)
        if not (lo <= self.pos and self.pos + n <= hi):
            self._buf_start, self._buf = self.pos, self._fetch(self.pos, max(n, self.chunk))
            lo = self._buf_start
        out = self._buf[self.pos - lo : self.pos - lo + n]
        self.pos += len(out)
        return out


COLMAP_SHIM = """#!/usr/bin/env bash
# Pod-only shim (runpod_job.limit_threads): COLMAP sizes its thread pools from
# the HOST core count (128 on Runpod hosts) while the pod's cgroup allows ~14,
# so every stage thrashes the CFS quota. Append --<Section>.num_threads N for
# each num_threads option the subcommand accepts, then exec the real binary.
real="{real}"
extra=()
if [ $# -gt 0 ]; then
  for opt in $("$real" "$1" -h 2>&1 | grep -oE -- '--[A-Za-z]+\\.num_threads' | sort -u); do
    extra+=("$opt" "{n}")
  done
fi
exec "$real" "$@" "${{extra[@]}}"
"""


def cgroup_cpus(root: Path = Path("/sys/fs/cgroup")) -> float:
    """CPU quota of this container (cgroup v2 ``cpu.max`` or v1 CFS), else the CPU count.

    Runpod hosts differ: some expose cgroup v2, some v1 (seen 2026-09-28).
    """
    try:
        quota, period = (root / "cpu.max").read_text().split()[:2]
        if quota != "max":
            return int(quota) / int(period)
    except (OSError, ValueError):
        pass
    for v1 in (root / "cpu", root / "cpu,cpuacct"):
        try:
            quota_us = int((v1 / "cpu.cfs_quota_us").read_text())
            period_us = int((v1 / "cpu.cfs_period_us").read_text())
        except (OSError, ValueError):
            continue
        if quota_us > 0 and period_us > 0:
            return quota_us / period_us
    return float(os.cpu_count() or 1)


def limit_threads(bin_dir: Path) -> dict:
    """Size every thread pool to the pod's CPU quota instead of the host's cores.

    Pins this process (and so every child: COLMAP, ns-train, Open3D) to the first
    N CPUs, sets the OpenMP/BLAS env vars, and puts a ``colmap`` shim that adds
    ``num_threads`` first on PATH. No-op when the quota already covers the host.
    """
    import shutil

    host = os.cpu_count() or 1
    n = max(1, int(cgroup_cpus()))
    info = {"host_cpus": host, "cgroup_cpus": round(cgroup_cpus(), 2), "threads": n}
    if n >= host:
        return info
    os.sched_setaffinity(0, range(n))
    for var in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_MAX_THREADS",
    ):
        os.environ[var] = str(n)
    real = shutil.which("colmap")
    if real:
        bin_dir.mkdir(parents=True, exist_ok=True)
        shim = bin_dir / "colmap"
        shim.write_text(COLMAP_SHIM.format(real=real, n=n))
        shim.chmod(0o755)
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ['PATH']}"
        info["colmap_shim"] = str(shim)
    return info


def fetch_room(dest: Path, url: str = MIPNERF360_URL) -> dict:
    """Extract only ``room/images_4/*`` from the public Mip-NeRF 360 zip into ``dest``."""
    started = time.monotonic()
    dest.mkdir(parents=True, exist_ok=True)
    remote = HttpRangeFile(url)
    total = 0
    with zipfile.ZipFile(remote) as zf:
        members = [m for m in zf.infolist() if m.filename.startswith(ROOM_PREFIX)]
        for m in members:
            name = Path(m.filename).name
            if m.is_dir() or not name:
                continue
            data = zf.read(m)
            (dest / name).write_bytes(data)
            total += len(data)
    count = sum(1 for p in dest.iterdir() if p.is_file())
    return {
        "url": url,
        "images": count,
        "bytes": total,
        "http_requests": remote.requests,
        "wall_s": round(time.monotonic() - started, 1),
    }


def run_scene(
    scan_id: str,
    image_dir: Path,
    source: str,
    work: Path,
    rate: float,
    sfm: str,
    matcher: str,
    max_features: int = 0,
) -> dict:
    """One full pipeline run (SfM -> train -> compress -> mesh) with the Modal defaults."""
    import shutil
    import traceback

    from reconstruction import (
        CostLedger,
        GsplatTrainer,
        Open3DMesher,
        ReconstructionConfig,
        ScanInput,
        SplatTransformCompressor,
        require_offsite_source,
        run_pipeline,
        select_sfm,
    )
    from reconstruction.spike import cost_sheet

    scan_source = require_offsite_source(source)
    count = sum(1 for p in image_dir.iterdir() if p.is_file())
    use_gpu = os.environ.get("GJ_COLMAP_CUDA") == "1"
    record: dict = {
        "scan_id": scan_id,
        "source": source,
        "images": count,
        "config": {"sfm": sfm, "matcher": matcher, "max_features": max_features},
    }
    started = time.monotonic()
    try:
        run = run_pipeline(
            ScanInput(scan_id, image_dir, count, scan_source),
            ReconstructionConfig(sfm=sfm),
            sfm=select_sfm(sfm, use_gpu=use_gpu, matcher=matcher, max_features=max_features),
            trainer=GsplatTrainer(),
            compressor=SplatTransformCompressor(),
            mesher=Open3DMesher(),
            work_dir=work / scan_id,
            ledger=CostLedger(),
            gpu_rate_per_hour_usd=rate,
        )
        sheet = cost_sheet(run)
        registered = run.poses.registered_images if run.poses else 0
        record.update(
            status="ok",
            registered_images=registered,
            registration_pct=round(100 * registered / max(count, 1), 1),
            pipeline=sheet,
        )
    except Exception as exc:  # noqa: BLE001 - record the failure, keep the batch going
        record.update(status="fail", error=f"{type(exc).__name__}: {exc}"[:500])
        record["traceback"] = traceback.format_exc()[-2000:]
    wall = time.monotonic() - started
    record["wall_s"] = round(wall, 1)
    record["usd"] = round(wall / 3600 * rate, 4)
    shutil.rmtree(work / scan_id, ignore_errors=True)
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="results JSON path")
    parser.add_argument("--rate", type=float, required=True, help="pod all-in $/h")
    parser.add_argument("--gpu", default="")
    parser.add_argument("--work", default="/root/gj-work")
    parser.add_argument("--room", action="store_true", help="run the Mip-NeRF 360 room")
    parser.add_argument("--clip", action="append", default=[], help="<clip id>=<frames dir>")
    parser.add_argument(
        "--deadline", type=float, default=0.0, help="epoch s; skip jobs that start after it"
    )
    args = parser.parse_args(argv)
    work = Path(args.work)
    out = Path(args.out)
    results: dict = {"gpu": args.gpu, "rate_per_hour_usd": args.rate, "runs": []}
    results["threads"] = limit_threads(work / "bin")

    def save() -> None:
        out.write_text(json.dumps(results, indent=2) + "\n")

    jobs: list[tuple[str, str, Path, str, str, int]] = []
    if args.room:
        room_dir = work / "data" / "room-images_4"
        if not room_dir.is_dir() or not any(room_dir.iterdir()):
            results["room_fetch"] = fetch_room(room_dir)
            save()
        jobs.append(("room", "public", room_dir, "colmap", "auto", 0))
    for spec in args.clip:
        clip_id, frames = spec.split("=", 1)
        slug = clip_id.split("/", 1)[1]
        jobs.append((slug, "corpus", Path(frames), CORPUS_SFM, CORPUS_MATCHER, CORPUS_MAX_FEATURES))
    for scan_id, source, image_dir, sfm, matcher, max_features in jobs:
        if args.deadline and time.time() > args.deadline:
            results["runs"].append({"scan_id": scan_id, "status": "skipped (deadline)"})
            save()
            continue
        rec = run_scene(scan_id, image_dir, source, work, args.rate, sfm, matcher, max_features)
        results["runs"].append(rec)
        save()
        print(json.dumps({k: rec.get(k) for k in ("scan_id", "status", "wall_s", "usd")}))
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
