baffin
======

Point it at a folder of camera originals; get a chronological static gallery you
can share as a link. It never edits your photos, and needs no curation.

These docs are **literate and test-driven**: the behaviour of the system is
specified by its tests, the canonical examples are runnable doctests, and the
API reference is generated from the code and the test suite. Narrative chapters
tie them together.

How these docs are organized
----------------------------

Read top-to-bottom for a full tour, or jump to your entry point:

- **New here?** :doc:`getting-started` — install, then your first gallery.
- **Want to know why it's built this way?** :doc:`rationale` — vision,
  principles, and the decisions of record.
- **Contributing?** :doc:`contributing` for the workflow, :doc:`architecture`
  for the shape, and the :doc:`reference` (the test suite is the spec).
- **Reorienting?** :doc:`rationale` §20 (decisions) and :doc:`architecture` are
  the fastest way back in; the search box finds the rest.

The chapters run from *why* (rationale) through the *shape* (architecture) to the
*parts* (domain, functional core, ports) and the *surfaces* (lazy build, CLI).
The generated API Reference documents both the package and the test suite — the
tests are the executable specification.

.. toctree::
   :maxdepth: 2
   :caption: Chapters

   getting-started
   rationale
   architecture
   domain
   functional-core
   use-cases
   lazy-build
   cli
   contributing

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference
