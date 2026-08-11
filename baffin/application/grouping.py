"""Chronological grouping: policy + the pure ``group_timeline`` (SPEC §9).

Pure functional core — imports domain types only, does no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

GroupMode = Literal["adaptive", "day", "month", "year-month", "flat"]
Order = Literal["oldest-first", "newest-first"]


@dataclass(frozen=True)
class GroupingPolicy:
    """How the timeline is bucketed (SPEC §9).

    ``adaptive`` picks by-day for short trips and year→month for long archives.
    ``day1_anchor`` fixes which calendar day counts as "Day 1" for trip-day
    labels; when ``None`` the earliest asset's day anchors it.
    """

    mode: GroupMode = "adaptive"
    day1_anchor: date | None = None
    order: Order = "oldest-first"
