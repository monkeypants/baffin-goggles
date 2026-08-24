The lazy build
==============

Expensive image work happens once;
editing a template regenerates no images.
Two caches and always-on rendering do it (see the sequence diagram in :doc:`architecture`):
a ``stat``\ →hash memo in the :py:class:`~baffin.application.ports.Hasher`,
a content-addressed derivative cache keyed by :py:meth:`~baffin.domain.models.DerivativeSpec.cache_key` behind the :py:class:`~baffin.application.ports.DerivativeStore`,
and HTML that re-renders every build.

One test verifies this end to end, through the real CLI against real image bytes:

.. literalinclude:: ../tests/interface/test_lazy_build.py
   :pyobject: test_second_run_is_all_hits_and_template_edit_rewrites_no_image_bytes
   :caption: tests/interface/test_lazy_build.py

The test asserts that a second build generates nothing
and leaves every derivative byte-for-byte identical,
and that editing a template re-renders the HTML while rewriting zero image bytes.
