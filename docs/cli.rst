The CLI
=======

The ``baffin`` command is a thin Typer adapter:
each command translates argv into a :doc:`use-case <use-cases>` call and translates the result back out.
Nothing in :py:mod:`baffin.interface.cli.app` leaks into the core.

.. list-table::
   :header-rows: 1

   * - Command
     - Purpose
   * - ``baffin build``
     - Lazy build. ``--source --output --full --force --jobs``.
   * - ``baffin scan``
     - Dry run: assets, groups, and the HIT/MISS plan.
   * - ``baffin serve``
     - Build then serve locally. ``--source --output --full --jobs``; ``--watch`` re-renders templates.
   * - ``baffin clean``
     - Prune orphaned derivatives; ``--all`` wipes the cache.
   * - ``baffin meta``
     - Read/write sidecars: ``show`` / ``edit`` / ``set``.
   * - ``baffin origin``
     - Map gallery images (hash / URL / derivative) back to their originals.
   * - ``baffin doctor``
     - Check libvips/ffmpeg and the resolved config.

``serve`` rebuilds before it serves, so it takes the build options too.
``--full`` affects the output: the tier drives the lightbox's Full switcher
entry and its download button, so serving without it re-renders a
``build --full`` gallery without them.
Set ``include_full = true`` in ``baffin.toml`` rather than relying on the flag.
``--jobs`` affects only speed;
both commands default to one worker,
and a cold cache generates every tier of every photo before the first page is served.

Configuration resolves CLI flag > env var > ``baffin.toml`` > default
(parsed by :py:class:`~baffin.adapters.settings.BaffinSettings` at the edge,
handed inward as a plain :py:class:`~baffin.application.config.GalleryConfig`).

Derivatives are content-addressed, so gallery URLs carry a content hash, not the
source name.
``baffin origin`` recovers the original path, for editing a picked shot
elsewhere (e.g. ``open -a Hugin $(baffin origin full/069f10b0a11b9961.jpg ...)``).
Setting ``show_filenames = true`` also prints each original's name in the
lightbox while browsing;
it is off by default so shared galleries don't leak source names.

Assembling the real adapters and running the build end to end:

.. literalinclude:: ../tests/interface/test_build_cli.py
   :pyobject: test_build_emits_the_expected_site_layout
