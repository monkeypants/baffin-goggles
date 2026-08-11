"""Skip-and-report build policy (SPEC §5 contract notes).

The default build policy is per-asset **skip-and-report**: a port error on one
asset records the failure and moves on, so one bad file can't sink the whole
run. ``--strict`` flips it — any port error becomes fatal. Non-port exceptions
(real bugs) always propagate regardless.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

from baffin.application.errors import BaffinError


@dataclass
class BuildReport:
    """Accumulated per-asset skips over a build run."""

    skipped: list[tuple[str, BaffinError]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when nothing was skipped."""
        return not self.skipped


@contextmanager
def per_asset(report: BuildReport, label: str, *, strict: bool) -> Iterator[None]:
    """Guard one asset's work: record and continue, or (strict) re-raise.

    Only :class:`BaffinError` is treated as a skippable port failure; any other
    exception is a bug and propagates.
    """
    try:
        yield
    except BaffinError as exc:
        if strict:
            raise
        report.skipped.append((label, exc))
