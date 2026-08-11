"""GroupingPolicy: construction and defaults."""

from datetime import date

from baffin.application.grouping import GroupingPolicy


def test_defaults_are_adaptive_oldest_first_no_anchor() -> None:
    policy = GroupingPolicy()
    assert policy.mode == "adaptive"
    assert policy.order == "oldest-first"
    assert policy.day1_anchor is None


def test_explicit_construction() -> None:
    policy = GroupingPolicy(
        mode="day", day1_anchor=date(2025, 7, 12), order="newest-first"
    )
    assert policy.mode == "day"
    assert policy.day1_anchor == date(2025, 7, 12)
    assert policy.order == "newest-first"
