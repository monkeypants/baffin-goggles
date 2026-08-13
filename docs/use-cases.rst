Ports and use cases
===================

The application orchestrates the pure core over ``typing.Protocol`` **ports**. Each
port is a swappable seam with a real adapter and an in-memory fake (the seam is
drawn in :doc:`architecture`), so the use cases —
:py:class:`~baffin.application.scan.ScanGallery`,
:py:class:`~baffin.application.build.BuildGallery`,
:py:class:`~baffin.application.clean.CleanGallery`,
:py:class:`~baffin.application.editmeta.EditAssetMeta` — are tested with no I/O.

Skip and report
---------------

Protocols cannot type their exceptions, so the error policy is a prose contract
made executable: a port failure on one asset is recorded and skipped so the run
continues, unless ``--strict`` makes it fatal. Real bugs always propagate.

.. literalinclude:: ../tests/application/test_build_gallery.py
   :pyobject: test_skip_and_report_survives_a_failing_asset

.. literalinclude:: ../tests/application/test_build_gallery.py
   :pyobject: test_strict_makes_a_failing_asset_fatal

Authoring is a use case
-----------------------

:py:class:`~baffin.application.editmeta.EditAssetMeta` reads, merges, and writes
one sidecar — and depends on nothing but the sidecar store, so it *cannot* touch
a photo's bytes. The CLI drives it now; a v2 web form would drive the same use
case. Merge semantics: set fields overwrite, unset fields are left alone.

.. literalinclude:: ../tests/application/test_edit_asset_meta.py
   :pyobject: test_merge_overlays_set_fields_and_keeps_the_rest
