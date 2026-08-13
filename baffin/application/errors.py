"""Port error hierarchy (see :doc:`/use-cases`).

Protocols can't type their exceptions, so the contract lives here in prose and
types. Read/generate ports raise one of these; ``BuildGallery`` catches them
per-asset under the skip-and-report policy (see :mod:`baffin.application.reporting`),
unless ``--strict`` makes any failure fatal.
"""

from __future__ import annotations


class BaffinError(Exception):
    """Base for all baffin domain/port errors."""


class SourceUnreadable(BaffinError):
    """A source item could not be read (missing, permissions, corrupt)."""


class MetadataUnreadable(BaffinError):
    """EXIF / container metadata could not be read from an original."""


class DerivativeFailed(BaffinError):
    """A derivative (thumbnail, poster, clip) could not be generated."""
