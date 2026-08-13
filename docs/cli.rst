The CLI
=======

The ``baffin`` command is a thin Typer adapter: each command translates argv into
a :doc:`use-case <use-cases>` call and translates the result back out. Nothing in
:py:mod:`baffin.interface.cli.app` leaks into the core.

.. list-table::
   :header-rows: 1

   * - Command
     - Purpose
   * - ``baffin build``
     - Lazy build. ``--source --output --full --force --jobs``.
   * - ``baffin scan``
     - Dry run: assets, groups, and the HIT/MISS plan.
   * - ``baffin serve``
     - Build then serve locally; ``--watch`` re-renders templates.
   * - ``baffin clean``
     - Prune orphaned derivatives; ``--all`` wipes the cache.
   * - ``baffin meta``
     - Read/write sidecars: ``show`` / ``edit`` / ``set``.
   * - ``baffin doctor``
     - Check libvips/ffmpeg and the resolved config.

Configuration resolves CLI flag > env var > ``baffin.toml`` > default (parsed by
:py:class:`~baffin.adapters.settings.BaffinSettings` at the edge, handed inward
as a plain :py:class:`~baffin.application.config.GalleryConfig`).

Assembling the real adapters and running the plan-then-generate build in the
shell is covered end to end:

.. literalinclude:: ../tests/interface/test_build_cli.py
   :pyobject: test_build_emits_the_expected_site_layout
