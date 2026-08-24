Baffin Goggles
==============

Point it at a folder of camera originals;
get a chronological static gallery you can share as a link.
It never edits your photos, and needs no curation.

These docs are **literate and test-driven**:
tests specify the behaviour,
doctests are the runnable examples,
and the API reference is generated from the code and tests.
Narrative chapters tie them together.

How these docs are organized
----------------------------

Read top-to-bottom for a full tour,
or jump to your entry point:

- **New here?** :doc:`getting-started`: install, then your first gallery.
- **Why is it built this way?** :doc:`rationale`: vision, principles, decisions of record.
- **Contributing?** :doc:`contributing` for the workflow,
  :doc:`architecture` for the shape,
  the :doc:`reference` for the code.
- **Reorienting?** :doc:`rationale` §20 (decisions) and :doc:`architecture`;
  the search box finds the rest.

The chapters run from *why* (rationale) through the *shape* (architecture)
to the *parts* (domain, functional core, ports)
and the *surfaces* (lazy build, CLI).
The API Reference covers both the package and the test suite.

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
