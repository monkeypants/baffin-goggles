API reference
=============

Generated from the source and the test suite;
nothing here is written by hand.

The package's public surface is the tree below, grouped by layer (:doc:`architecture`).
Curated examples from the test suite appear inline in the chapters as doctests and ``literalinclude``\ s;
the full suite is browsable here, under its own heading rather than mixed into the API.

.. toctree::
   :caption: The package, by layer
   :maxdepth: 3

   reference/baffin/index

.. toctree::
   :caption: Test suite
   :maxdepth: 1
   :glob:

   reference/conftest/index
   reference/test_*/index
