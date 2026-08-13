"""Chronological grouping: policy + the pure ``group_timeline`` (see
:doc:`/functional-core`).

Pure functional core — imports domain types only, does no I/O.
"""

from __future__ import annotations

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from baffin.domain import Asset, Group

GroupMode = Literal["adaptive", "day", "month", "year-month", "flat"]
Order = Literal["oldest-first", "newest-first"]

# Adaptive threshold: a trip spanning at most this many days groups by day;
# anything longer collapses to year→month (the "~30 days" rule; see the
# functional-core chapter).
ADAPTIVE_DAY_THRESHOLD = 30


@dataclass(frozen=True)
class GroupingPolicy:
    """How the timeline is bucketed (see :doc:`/functional-core`).

    ``adaptive`` picks by-day for short trips and year→month for long archives.
    ``day1_anchor`` fixes which calendar day counts as "Day 1" for trip-day
    labels; when ``None`` the earliest asset's day anchors it.
    """

    mode: GroupMode = "adaptive"
    day1_anchor: date | None = None
    order: Order = "oldest-first"


def group_timeline(
    assets: list[Asset] | tuple[Asset, ...], policy: GroupingPolicy
) -> tuple[Group, ...]:
    """Bucket assets into an ordered chronological timeline (see
    :doc:`/functional-core`).

    Pure: sorts by ``captured_at``, resolves the effective mode, buckets, and
    orders the resulting groups per ``policy.order``. Assets within a group stay
    oldest-first for stable reading regardless of group order.

    >>> from datetime import datetime
    >>> from baffin.application.grouping import GroupingPolicy, group_timeline
    >>> from baffin.testing.builders import an_asset
    >>> trip = [an_asset("a", captured_at=datetime(2025, 7, 12, 9)),
    ...         an_asset("b", captured_at=datetime(2025, 7, 14, 9))]
    >>> [g.key for g in group_timeline(trip, GroupingPolicy())]
    ['day-01', 'day-03']
    """
    items = sorted(assets, key=lambda a: a.captured_at)
    if not items:
        return ()

    mode = _resolve_mode(items, policy.mode)
    if mode == "flat":
        groups = [_flat_group(items)]
    elif mode == "day":
        groups = _by_day(items, policy.day1_anchor)
    else:  # "month" | "year-month"
        groups = _by_year_month(items, mode)

    if policy.order == "newest-first":
        groups.reverse()
    return tuple(groups)


def _resolve_mode(items: list[Asset], mode: GroupMode) -> GroupMode:
    if mode != "adaptive":
        return mode
    span_days = (items[-1].captured_at.date() - items[0].captured_at.date()).days
    return "day" if span_days <= ADAPTIVE_DAY_THRESHOLD else "year-month"


def _span(items: list[Asset]) -> tuple[datetime, datetime]:
    return (items[0].captured_at, items[-1].captured_at)


def _flat_group(items: list[Asset]) -> Group:
    return Group(key="all", label="All photos", span=_span(items), assets=tuple(items))


def _by_day(items: list[Asset], anchor: date | None) -> list[Group]:
    day1 = anchor if anchor is not None else items[0].captured_at.date()
    buckets: dict[date, list[Asset]] = defaultdict(list)
    for asset in items:
        buckets[asset.captured_at.date()].append(asset)

    groups: list[Group] = []
    for day, members in sorted(buckets.items()):
        n = (day - day1).days + 1
        label = f"Day {n} — {day.day} {day.strftime('%b')}"
        groups.append(
            Group(
                key=f"day-{n:02d}",
                label=label,
                span=_span(members),
                assets=tuple(members),
            )
        )
    return groups


def _by_year_month(items: list[Asset], mode: GroupMode) -> list[Group]:
    buckets: dict[tuple[int, int], list[Asset]] = defaultdict(list)
    for asset in items:
        stamp = asset.captured_at
        buckets[(stamp.year, stamp.month)].append(asset)

    groups: list[Group] = []
    for (year, month), members in sorted(buckets.items()):
        # "year-month" nests as 2025/07 (a URL path); "month" stays flat as 2025-07.
        sep = "/" if mode == "year-month" else "-"
        key = f"{year:04d}{sep}{month:02d}"
        label = f"{calendar.month_name[month]} {year}"
        groups.append(
            Group(key=key, label=label, span=_span(members), assets=tuple(members))
        )
    return groups
