Contributing
============

baffin is small and strict.
This chapter is the workflow around the code:
the gate that must stay green, where code lives, and the conventions.
The code's *shape* is :doc:`architecture`.

The gate
--------

One command gates every change:

.. code-block:: sh

   make check

Each step, and what it guards.
All must pass before pushing:

.. list-table::
   :header-rows: 1

   * - Step
     - What it guards
   * - ``ruff check``
     - Lint (pyflakes, imports, bugbears, pyupgrade).
   * - ``ruff format --check``
     - Formatting is enforced.
   * - ``lint-imports``
     - The dependency rule from :doc:`architecture`, enforced.
   * - ``mypy`` (strict)
     - Types on the whole of ``baffin``, including the fakes conforming to the ports.
   * - ``pytest`` + ``--doctest-modules``
     - The unit/integration suite and the doctests embedded in the core.

When a change touches docstrings, public signatures, a module-level type alias, or anything under ``docs/``,
also build the docs (CI does, under ``-W``):

.. code-block:: sh

   make docs

The pinned toolchain
--------------------

``make check`` uses whatever libvips your machine has,
which is the fast path and usually what you want.
CI does not:
it runs the same gate inside the image built from the repo's ``Dockerfile``,
which pins libvips and ffmpeg.

That matters because a derivative's cache key is
``hash(content_hash + spec)`` and does **not** include the toolchain
(:doc:`lazy-build`).
Identical keys therefore promise identical *inputs*, not identical output bytes:
upgrading libvips changes what a thumbnail looks like
while every key — and so every cache hit — stays exactly the same.
Pinning is what makes "all hits" mean the same thing on two machines.

.. code-block:: sh

   make check-docker                                    # the gate, pinned
   make build-docker SOURCE=~/photos OUTPUT=~/site      # a gallery, pinned

The container is also the only place the pooled build is exercised on Linux,
which is not a detail:
``ProcessPoolExecutor`` defaults to *spawn* on macOS and *fork* on Linux,
and forking a process that has initialised libvips deadlocks.
``baffin.adapters.generation`` therefore selects spawn explicitly
rather than inheriting the platform default.

Where things live
-----------------

The package mirrors the layers,
and the tests mirror the package:

.. code-block:: text

   baffin/
     domain/        frozen dataclasses + the cache key      (:doc:`domain`)
     application/   pure core, ports, use cases              (:doc:`functional-core`, :doc:`use-cases`)
     adapters/      the imperative shell (I/O)               (:doc:`architecture`)
     interface/cli/ the Typer surface                        (:doc:`cli`)
     testing/       in-memory fakes + builders (shipped, so mypy checks them)
   tests/           mirrors baffin/; the specification

Tests are the specification:
the curated ones are doctests and the examples pulled into these chapters;
the rest live in ``tests/`` and are browsable in the :doc:`API reference <reference>`.

Conventions
-----------

- **Commits** follow the Linux-kernel style:
  imperative summary (~50 chars), a blank line, then a body that explains *why* when it isn't obvious.
  No conventional-commit prefixes;
  no AI attribution (the author is accountable).
- **Branches** are feature branches with plain descriptive names;
  work never lands directly on ``master``.
- **New native dependency?** Add it to the docs and the CI install step,
  not just ``pyproject.toml`` (:doc:`getting-started`).

The decisions behind these choices, and the open questions, are recorded in :doc:`rationale`.
