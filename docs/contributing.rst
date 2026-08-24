Contributing
============

The gate that must stay green, where code lives, and the conventions.
The code's structure is in :doc:`architecture`.

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
     - Formatting.
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

``make check`` uses the host's libvips.
CI runs the same gate inside the image built from ``Dockerfile``,
which pins libvips and ffmpeg.

A derivative's cache key is ``hash(content_hash + spec)``
and does not include the toolchain (:doc:`lazy-build`).
Upgrading libvips changes the output bytes without changing any key,
so two machines can both report all-hits over derivatives that differ.
Pinning the toolchain removes that variable.

.. code-block:: sh

   make check-docker                                    # the gate, pinned
   make build-docker SOURCE=~/photos OUTPUT=~/site      # a gallery, pinned

The container is also where the pooled build gets exercised on Linux.
``ProcessPoolExecutor`` defaults to spawn on macOS and fork on Linux,
and forking a process that has initialised libvips deadlocks,
so ``baffin.adapters.generation`` sets the start method explicitly.

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
   tests/           mirrors baffin/

The tests specify the behaviour:
the curated ones are doctests and the examples pulled into these chapters;
the rest live in ``tests/`` and are browsable in the :doc:`API reference <reference>`.

Conventions
-----------

- Commits follow the Linux-kernel style:
  imperative summary (~50 chars), a blank line, then a body that explains why when it isn't obvious.
  No conventional-commit prefixes;
  no AI attribution (the author is accountable).
- Branches are feature branches with plain descriptive names;
  work never lands directly on ``master``.
- A new native dependency goes in the docs and the CI install step,
  not just ``pyproject.toml`` (:doc:`getting-started`).

The decisions behind these choices, and the open questions, are recorded in :doc:`rationale`.
