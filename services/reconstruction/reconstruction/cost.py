"""Per-scan compute cost accounting and spend-cap enforcement.

Implements the M1-CAPT-02 AT-2 cost/cap requirement and the AUTH #031 spike
cap. All spend is the Owner's to authorize; these caps are hard stops, not
suggestions. ``guard`` is called before any GPU work so a run that would cross a
cap never starts.

A scan's cost is GPU + CPU + memory. Serverless hosts (Modal) bill CPU and
memory per second as ``max(reserved, used)``, so a CPU-heavy step that bursts
past its reservation costs more than the reservation suggests (the 2026-09-25
smoke run's CPU COLMAP averaged ~20 cores against 8 reserved: CPU cost ~ GPU
cost). ``ResourceMeter`` samples the container's actual CPU and memory use so
the cost sheet prices that burst instead of guessing.
"""

from __future__ import annotations

import datetime as dt
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .models import ReconstructionError

DAILY_CAP_USD = 50.0  # SECURITY_CHECKLIST §8.5 / kit §7
SPIKE_CAP_USD = 100.0  # AUTH #031 (one-time self-host spike)
# Conservative single-scan GPU-box estimate for the pre-run cap check
# (analysis: ~0.5-0.75 GPU-box-hr/scan; take the worst case).
ESTIMATE_HOURS = 0.75

# Modal list prices (`modal billing rates`, 2026-09-26). CPU is per PHYSICAL core
# (= 2 vCPU); memory per GiB. The GPU rate is passed per run (--rate).
MODAL_CPU_CORE_HOUR_USD = 0.0473
MODAL_MEMORY_GIB_HOUR_USD = 0.008
GIB = 1024**3


class SpendCapError(ReconstructionError):
    """Raised before running work that would cross a spend cap."""


@dataclass(frozen=True)
class ResourceUsage:
    """Billable CPU/memory for one run, as ``max(reserved, used)`` per sample."""

    wall_seconds: float
    billed_core_seconds: float  # physical cores x s
    used_core_seconds: float
    billed_gib_seconds: float
    peak_memory_gib: float
    source: str  # which counters were read (cgroup-v2 / cgroup-v1 / proc / reserved-only)

    def cpu_usd(self, rate_per_core_hour: float = MODAL_CPU_CORE_HOUR_USD) -> float:
        return self.billed_core_seconds / 3600.0 * rate_per_core_hour

    def memory_usd(self, rate_per_gib_hour: float = MODAL_MEMORY_GIB_HOUR_USD) -> float:
        return self.billed_gib_seconds / 3600.0 * rate_per_gib_hour


def reserved_only_usage(wall_seconds: float, cores: float, memory_gib: float) -> ResourceUsage:
    """Usage when no counters are readable: bill the reservation (a lower bound)."""
    return ResourceUsage(
        wall_seconds=wall_seconds,
        billed_core_seconds=cores * wall_seconds,
        used_core_seconds=0.0,
        billed_gib_seconds=memory_gib * wall_seconds,
        peak_memory_gib=0.0,
        source="reserved-only",
    )


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _cgroup_cpu_seconds(root: Path = Path("/sys/fs/cgroup")) -> tuple[float, str] | None:
    """Total vCPU-seconds used by this container's cgroup (v2, then v1), else /proc."""
    try:
        for line in (root / "cpu.stat").read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition(" ")
            if key == "usage_usec":
                return int(value) / 1e6, "cgroup-v2"
    except (OSError, ValueError):
        pass
    for rel in ("cpuacct/cpuacct.usage", "cpu,cpuacct/cpuacct.usage", "cpuacct.usage"):
        ns = _read_int(root / rel)
        if ns is not None:
            return ns / 1e9, "cgroup-v1"
    try:  # sandbox-wide jiffies (gVisor exposes the sandbox's own /proc/stat)
        fields = Path("/proc/stat").read_text(encoding="utf-8").splitlines()[0].split()
        user, nice, system = (int(fields[i]) for i in (1, 2, 3))
        return (user + nice + system) / 100.0, "proc"
    except (OSError, ValueError, IndexError):
        return None


def _memory_bytes(root: Path = Path("/sys/fs/cgroup")) -> int | None:
    """Current memory use (cgroup v2 / v1), else MemTotal - MemAvailable."""
    for rel in ("memory.current", "memory/memory.usage_in_bytes", "memory.usage_in_bytes"):
        value = _read_int(root / rel)
        if value is not None:
            return value
    try:
        info = {}
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            key, _, rest = line.partition(":")
            info[key] = int(rest.split()[0]) * 1024
        return info["MemTotal"] - info["MemAvailable"]
    except (OSError, ValueError, KeyError, IndexError):
        return None


class ResourceMeter:
    """Background sampler of container CPU + memory, priced like Modal bills it.

    Each interval bills ``max(reserved, used)`` cores and GiB. Start it when the
    container starts work and stop it at the end; ``stop()`` returns the usage.
    The readers are injectable for tests.
    """

    def __init__(
        self,
        cores: float,
        memory_gib: float,
        interval: float = 1.0,
        cpu_reader: Callable[[], tuple[float, str] | None] = _cgroup_cpu_seconds,
        mem_reader: Callable[[], int | None] = _memory_bytes,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.cores = cores
        self.memory_gib = memory_gib
        self.interval = interval
        self._cpu_reader = cpu_reader
        self._mem_reader = mem_reader
        self._clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._source = "reserved-only"
        self._billed_core_s = 0.0
        self._used_core_s = 0.0
        self._billed_gib_s = 0.0
        self._peak_gib = 0.0
        self._started = 0.0
        self._last_t = 0.0
        self._last_cpu: float | None = None

    def start(self) -> ResourceMeter:
        self._started = self._last_t = self._clock()
        first = self._cpu_reader()
        if first is not None:
            self._last_cpu, self._source = first
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def sample(self) -> None:
        """Account the interval since the previous sample."""
        now = self._clock()
        dt_s = now - self._last_t
        if dt_s <= 0:
            return
        used_cores = 0.0
        reading = self._cpu_reader()
        if reading is not None and self._last_cpu is not None:
            vcpu_s = max(0.0, reading[0] - self._last_cpu)
            used_cores = vcpu_s / 2.0 / dt_s  # 1 billed physical core = 2 vCPU
            self._last_cpu = reading[0]
        mem = self._mem_reader()
        used_gib = (mem or 0) / GIB
        self._peak_gib = max(self._peak_gib, used_gib)
        self._used_core_s += used_cores * dt_s
        self._billed_core_s += max(self.cores, used_cores) * dt_s
        self._billed_gib_s += max(self.memory_gib, used_gib) * dt_s
        self._last_t = now

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            self.sample()

    def stop(self) -> ResourceUsage:
        self._stop.set()
        if self._thread is not None:
            self._thread.join()
        self.sample()
        return ResourceUsage(
            wall_seconds=self._last_t - self._started,
            billed_core_seconds=self._billed_core_s,
            used_core_seconds=self._used_core_s,
            billed_gib_seconds=self._billed_gib_s,
            peak_memory_gib=self._peak_gib,
            source=self._source if self._last_cpu is not None else "reserved-only",
        )


@dataclass(frozen=True)
class ScanCost:
    """The recorded cost of one reconstructed scan (GPU + CPU + memory)."""

    scan_id: str
    gpu_seconds: float
    rate_per_hour_usd: float
    day: dt.date
    cpu_usd: float = 0.0
    memory_usd: float = 0.0

    @property
    def gpu_usd(self) -> float:
        return self.gpu_seconds / 3600.0 * self.rate_per_hour_usd

    @property
    def usd(self) -> float:
        return self.gpu_usd + self.cpu_usd + self.memory_usd


def estimate_usd(rate_per_hour_usd: float, hours: float = ESTIMATE_HOURS) -> float:
    """Conservative pre-run cost estimate for the cap guard."""
    return rate_per_hour_usd * hours


@dataclass
class CostLedger:
    """Accumulates scan costs and enforces the spike and daily caps."""

    spike_cap_usd: float = SPIKE_CAP_USD
    daily_cap_usd: float = DAILY_CAP_USD
    _records: list[ScanCost] = field(default_factory=list)

    def records(self) -> tuple[ScanCost, ...]:
        return tuple(self._records)

    def spike_total_usd(self) -> float:
        return sum(r.usd for r in self._records)

    def daily_total_usd(self, day: dt.date) -> float:
        return sum(r.usd for r in self._records if r.day == day)

    def guard(self, estimated_usd: float, day: dt.date) -> None:
        """Raise SpendCapError if adding ``estimated_usd`` would cross a cap."""
        spike = self.spike_total_usd()
        if spike + estimated_usd > self.spike_cap_usd:
            raise SpendCapError(
                f"spike cap ${self.spike_cap_usd:.2f} would be exceeded "
                f"(spent ${spike:.2f} + est ${estimated_usd:.2f})"
            )
        daily = self.daily_total_usd(day)
        if daily + estimated_usd > self.daily_cap_usd:
            raise SpendCapError(
                f"daily cap ${self.daily_cap_usd:.2f} would be exceeded on {day} "
                f"(spent ${daily:.2f} + est ${estimated_usd:.2f})"
            )

    def record(
        self,
        scan_id: str,
        gpu_seconds: float,
        rate_per_hour_usd: float,
        day: dt.date | None = None,
        cpu_usd: float = 0.0,
        memory_usd: float = 0.0,
    ) -> ScanCost:
        cost = ScanCost(
            scan_id=scan_id,
            gpu_seconds=gpu_seconds,
            rate_per_hour_usd=rate_per_hour_usd,
            day=day or dt.date.today(),
            cpu_usd=cpu_usd,
            memory_usd=memory_usd,
        )
        self._records.append(cost)
        return cost
