"""The ports are importable typing.Protocols (real conformance is via mypy)."""

from baffin.application import ports


def test_all_ports_are_protocols() -> None:
    """The ports are swappable seams, not concrete classes. This asserts only
    that they are Protocols — structural conformance of adapters and fakes is
    mypy's job (see the TYPE_CHECKING block in baffin.testing.fakes), not this
    test's."""
    names = [
        "AssetRepository",
        "MetadataReader",
        "SidecarStore",
        "Hasher",
        "Thumbnailer",
        "VideoProcessor",
        "DerivativeStore",
        "SiteRenderer",
    ]
    for name in names:
        port = getattr(ports, name)
        assert getattr(port, "_is_protocol", False), f"{name} is not a Protocol"
