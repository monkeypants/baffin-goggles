API reference
=============

Generated from the source and the test suite — nothing here is written by hand.

The package's public surface is the tree below, grouped the way the code is: by
layer (:doc:`architecture`). The **test suite is the executable specification** —
the curated, pedagogic examples appear inline in the chapters (as doctests and
``literalinclude``\ s), while the full, rigorous suite is browsable here under its
own heading rather than intermixed with the API.

.. toctree::
   :caption: The package, by layer
   :maxdepth: 3

   reference/baffin/index

.. toctree::
   :caption: Test suite (the executable specification)
   :maxdepth: 1
   :glob:

   reference/conftest/index
   reference/test_*/index
