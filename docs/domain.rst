The domain
==========

The domain is frozen dataclasses with no I/O and one method.
The central type is :py:class:`~baffin.domain.models.Asset`:
a source item plus its **content hash**.
The hash is its identity,
so a renamed or duplicated file is the same asset.

Two metadata types stay distinct.
:py:class:`~baffin.domain.models.RawMetadata` is the technical read from an original (dimensions, EXIF, GPS);
:py:class:`~baffin.domain.models.AssetMeta` is authored sidecar text (title, caption, credit, alt).

The cache key
-------------

The domain's one method is :py:meth:`~baffin.domain.models.DerivativeSpec.cache_key`.
It must be stable across runs and machines,
so it is a SHA-256 over the content hash and the spec rather than the salted builtin ``hash``.
This is what makes the :doc:`lazy build <lazy-build>` content-addressed:

.. doctest::

   >>> from baffin.domain import DerivativeSpec
   >>> from baffin.testing.builders import an_asset
   >>> thumb = DerivativeSpec("thumb", 300, 80)
   >>> thumb.cache_key(an_asset("deadbeef")) == thumb.cache_key(an_asset("deadbeef"))
   True

The digest below is pinned as a literal,
so any change to the formula is caught:

.. literalinclude:: ../tests/domain/test_derivative_spec.py
   :pyobject: test_cache_key_is_stable_across_runs
