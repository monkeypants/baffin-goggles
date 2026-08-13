"""The skip-vs-strict build policy contract (see :doc:`/use-cases`)."""

import pytest

from baffin.application.errors import (
    BaffinError,
    DerivativeFailed,
    MetadataUnreadable,
    SourceUnreadable,
)
from baffin.application.reporting import BuildReport, per_asset


def test_error_hierarchy_is_importable_and_rooted() -> None:
    for exc in (SourceUnreadable, MetadataUnreadable, DerivativeFailed):
        assert issubclass(exc, BaffinError)


def test_default_policy_skips_and_reports() -> None:
    report = BuildReport()
    assert report.ok

    for label, exc in [("a.jpg", SourceUnreadable), ("b.jpg", DerivativeFailed)]:
        with per_asset(report, label, strict=False):
            raise exc("boom")

    assert not report.ok
    assert [label for label, _ in report.skipped] == ["a.jpg", "b.jpg"]


def test_strict_policy_makes_the_first_error_fatal() -> None:
    report = BuildReport()
    with pytest.raises(MetadataUnreadable), per_asset(report, "a.jpg", strict=True):
        raise MetadataUnreadable("boom")
    assert report.skipped == []


def test_non_port_errors_always_propagate() -> None:
    report = BuildReport()
    with pytest.raises(ValueError), per_asset(report, "a.jpg", strict=False):
        raise ValueError("a real bug, not a skippable asset")
    assert report.skipped == []
