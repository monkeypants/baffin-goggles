Contributing
============

baffin is small, strict, and test-driven. This chapter orients a contributor:
the one gate that must stay green, where code lives, and the conventions the
history follows. The *shape* of the code is :doc:`architecture`; this is the
workflow around it.

The gate
--------

One command decides whether a change is sound:

.. code-block:: sh

   make check

It runs, and all of it must pass, before anything is pushed:

.. list-table::
   :header-rows: 1

   * - Step
     - What it guards
   * - ``ruff check``
     - Lint (pyflakes, imports, bugbears, pyupgrade).
   * - ``ruff format --check``
     - Formatting is not a matter of opinion.
   * - ``lint-imports``
     - The dependency rule — the layering in :doc:`architecture` is enforced, not aspirational.
   * - ``mypy`` (strict)
     - Types on the whole of ``baffin``, including the fakes conforming to the ports.
   * - ``pytest`` + ``--doctest-modules``
     - The unit/integration suite and the doctests embedded in the core.

When a change touches docstrings, public signatures, a module-level type alias,
or anything under ``docs/``, also build the docs — CI does, under ``-W``:

.. code-block:: sh

   make docs

Where things live
-----------------

The package mirrors the layers, and the tests mirror the package:

.. code-block:: text

   baffin/
     domain/        frozen dataclasses + the cache key      (:doc:`domain`)
     application/   pure core, ports, use cases              (:doc:`functional-core`, :doc:`use-cases`)
     adapters/      the imperative shell (I/O)               (:doc:`architecture`)
     interface/cli/ the Typer surface                        (:doc:`cli`)
     testing/       in-memory fakes + builders (shipped, so mypy checks them)
   tests/           mirrors baffin/; the executable specification

Tests are the specification: the curated, pedagogic ones are doctests and the
examples pulled into these chapters; the rigorous ones live in ``tests/`` and are
browsable in the :doc:`API reference <reference>`.

Conventions
-----------

- **Commits** follow the Linux-kernel style: imperative summary (~50 chars), a
  blank line, then a body that explains *why* when it isn't obvious. No
  conventional-commit prefixes; no AI attribution — the author is accountable.
- **Branches** are feature branches with plain descriptive names; work never
  lands directly on ``master``.
- **New native dependency?** Add it to the docs and the CI install step, not just
  ``pyproject.toml`` — see :doc:`getting-started`.

The decisions behind these choices, and the open questions, are recorded in
:doc:`rationale`.
