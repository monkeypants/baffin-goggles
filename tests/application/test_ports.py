"""The ports are importable typing.Protocols (real conformance is via mypy)."""

from baffin.application import ports


def test_all_ports_are_protocols() -> None:
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
