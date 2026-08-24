Ports and use cases
===================

The application orchestrates the pure core over ``typing.Protocol`` ports.
Each port is a swappable seam with a real adapter and an in-memory fake (drawn in :doc:`architecture`),
so the use cases test with no I/O:
:py:class:`~baffin.application.scan.ScanGallery`,
:py:class:`~baffin.application.clean.CleanGallery`, and
:py:class:`~baffin.application.editmeta.EditAssetMeta`.

The build is the exception.
Planning is pure (:py:func:`~baffin.application.planning.plan_derivatives`,
:py:func:`~baffin.application.planning.diff_plan`),
but executing the plan fans out across a process pool over the
:py:class:`~baffin.adapters.processor.AssetProcessor` composite,
so its orchestration lives in the shell as
:py:func:`~baffin.interface.cli.pipeline.run_build`.

Skip and report
---------------

Protocols cannot type their exceptions, so the policy is stated here and
enforced by tests:
a port failure on one asset is recorded and skipped so the run continues,
unless ``--strict`` makes it fatal.
Real bugs always propagate.

The policy holds on both generation paths.
In the pooled one, a worker's exception re-raises inside the same guard:

.. literalinclude:: ../tests/adapters/test_generation.py
   :pyobject: test_generate_skips_and_reports_a_failing_asset

.. literalinclude:: ../tests/adapters/test_generation.py
   :pyobject: test_generate_skips_in_the_process_pool_too

.. literalinclude:: ../tests/adapters/test_generation.py
   :pyobject: test_generate_strict_makes_a_failing_asset_fatal

Authoring is a use case
-----------------------

:py:class:`~baffin.application.editmeta.EditAssetMeta` reads, merges, and writes one sidecar.
It depends on nothing but the sidecar store,
so it cannot touch a photo's bytes.
The CLI drives it now;
a v2 web form would drive the same use case.
Merge semantics: set fields overwrite, unset fields are left alone.

.. literalinclude:: ../tests/application/test_edit_asset_meta.py
   :pyobject: test_merge_overlays_set_fields_and_keeps_the_rest
