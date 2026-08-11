"""group_timeline: adaptive/day/month boundaries, labelling, ordering, edges."""

from datetime import date, datetime
from pathlib import Path

from baffin.application.grouping import GroupingPolicy, group_timeline
from baffin.domain import Asset, SourceRef


def _asset(when: datetime, tag: str) -> Asset:
    return Asset(
        ref=SourceRef(path=Path(f"photos/{tag}.jpg"), size=1, mtime_ns=1),
        content_hash=tag,
        kind="photo",
        captured_at=when,
        width=100,
        height=100,
        orientation=1,
    )


def test_empty_input_yields_no_groups() -> None:
    assert group_timeline([], GroupingPolicy()) == ()


def test_flat_mode_is_one_bucket() -> None:
    assets = [
        _asset(datetime(2025, 7, 14, 9), "a"),
        _asset(datetime(2025, 9, 1, 9), "b"),
    ]
    (group,) = group_timeline(assets, GroupingPolicy(mode="flat"))
    assert group.key == "all"
    assert len(group.assets) == 2
    assert group.span == (datetime(2025, 7, 14, 9), datetime(2025, 9, 1, 9))


def test_adaptive_short_trip_groups_by_day_with_trip_labels() -> None:
    assets = [
        _asset(datetime(2025, 7, 12, 8), "a"),  # Day 1
        _asset(datetime(2025, 7, 12, 18), "b"),  # Day 1
        _asset(datetime(2025, 7, 14, 10), "c"),  # Day 3
    ]
    groups = group_timeline(assets, GroupingPolicy(mode="adaptive"))
    assert [g.key for g in groups] == ["day-01", "day-03"]
    assert groups[0].label == "Day 1 — 12 Jul"
    assert groups[1].label == "Day 3 — 14 Jul"
    assert len(groups[0].assets) == 2


def test_day1_anchor_shifts_trip_numbering() -> None:
    assets = [_asset(datetime(2025, 7, 14, 10), "c")]
    groups = group_timeline(
        assets, GroupingPolicy(mode="day", day1_anchor=date(2025, 7, 12))
    )
    assert groups[0].key == "day-03"
    assert groups[0].label == "Day 3 — 14 Jul"


def test_adaptive_boundary_30_days_is_still_by_day() -> None:
    assets = [
        _asset(datetime(2025, 7, 1, 9), "a"),
        _asset(datetime(2025, 7, 31, 9), "b"),  # 30-day span
    ]
    groups = group_timeline(assets, GroupingPolicy(mode="adaptive"))
    assert all(g.key.startswith("day-") for g in groups)


def test_adaptive_long_archive_groups_by_year_month() -> None:
    assets = [
        _asset(datetime(2025, 7, 1, 9), "a"),
        _asset(datetime(2025, 9, 1, 9), "b"),  # 62-day span → year→month
    ]
    groups = group_timeline(assets, GroupingPolicy(mode="adaptive"))
    assert [g.key for g in groups] == ["2025/07", "2025/09"]
    assert groups[0].label == "July 2025"


def test_month_mode_uses_flat_key_year_month_uses_path() -> None:
    assets = [_asset(datetime(2025, 7, 14, 9), "a")]
    (flat,) = group_timeline(assets, GroupingPolicy(mode="month"))
    (nested,) = group_timeline(assets, GroupingPolicy(mode="year-month"))
    assert flat.key == "2025-07"
    assert nested.key == "2025/07"
    assert flat.label == nested.label == "July 2025"


def test_newest_first_reverses_group_order() -> None:
    assets = [
        _asset(datetime(2025, 7, 12, 9), "a"),
        _asset(datetime(2025, 7, 14, 9), "c"),
    ]
    oldest = group_timeline(assets, GroupingPolicy(mode="day", order="oldest-first"))
    newest = group_timeline(assets, GroupingPolicy(mode="day", order="newest-first"))
    assert [g.key for g in oldest] == ["day-01", "day-03"]
    assert [g.key for g in newest] == ["day-03", "day-01"]
