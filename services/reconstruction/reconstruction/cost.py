"""Per-scan GPU cost accounting and spend-cap enforcement.

Implements the M1-CAPT-02 AT-2 cost/cap requirement and the AUTH #031 spike
cap. All spend is the Owner's to authorize; these caps are hard stops, not
suggestions. ``guard`` is called before any GPU work so a run that would cross a
cap never starts.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .models import ReconstructionError

DAILY_CAP_USD = 50.0  # SECURITY_CHECKLIST §8.5 / kit §7
SPIKE_CAP_USD = 100.0  # AUTH #031 (one-time self-host spike)
# Conservative single-scan GPU-box estimate for the pre-run cap check
# (analysis: ~0.5-0.75 GPU-box-hr/scan; take the worst case).
ESTIMATE_HOURS = 0.75


class SpendCapError(ReconstructionError):
    """Raised before running work that would cross a spend cap."""


@dataclass(frozen=True)
class ScanCost:
    """The recorded cost of one reconstructed scan."""

    scan_id: str
    gpu_seconds: float
    rate_per_hour_usd: float
    day: dt.date

    @property
    def usd(self) -> float:
        return self.gpu_seconds / 3600.0 * self.rate_per_hour_usd


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
    ) -> ScanCost:
        cost = ScanCost(
            scan_id=scan_id,
            gpu_seconds=gpu_seconds,
            rate_per_hour_usd=rate_per_hour_usd,
            day=day or dt.date.today(),
        )
        self._records.append(cost)
        return cost
