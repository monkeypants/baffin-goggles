The domain
==========

The domain is plain frozen dataclasses and one piece of behaviour — no I/O, no
frameworks. The load-bearing type is :py:class:`~baffin.domain.models.Asset`: a
source item plus its **content hash**, the durable identity that makes the cache
content-addressed. A rename or a duplicate is the same asset.

Two metadata types are kept deliberately distinct:
:py:class:`~baffin.domain.models.RawMetadata` is the technical read from an
original (dimensions, EXIF, GPS), while
:py:class:`~baffin.domain.models.AssetMeta` is authored sidecar text (title,
caption, credit, alt). One is machine-read, the other human-written.

The cache key
-------------

The only behaviour in the domain is
:py:meth:`~baffin.domain.models.DerivativeSpec.cache_key`. It must be stable
across runs and machines — the salted builtin ``hash`` cannot back a cache — so it
is a SHA-256 over the content hash and the spec:

.. doctest::

   >>> from baffin.domain import DerivativeSpec
   >>> from baffin.testing.builders import an_asset
   >>> thumb = DerivativeSpec("thumb", 300, 80)
   >>> thumb.cache_key(an_asset("deadbeef")) == thumb.cache_key(an_asset("deadbeef"))
   True

That stability is pinned as a specification — the digest is a literal, so any
change to the key's formula is caught:

.. literalinclude:: ../tests/domain/test_derivative_spec.py
   :pyobject: test_cache_key_is_stable_across_runs
