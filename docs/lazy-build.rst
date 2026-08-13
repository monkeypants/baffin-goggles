The lazy build
==============

The headline promise: expensive image work happens once, and template iteration
is effectively free. Two cache layers plus always-on rendering (see the sequence
diagram in :doc:`architecture`) make it so — a ``stat``\ →hash memo, a
content-addressed derivative cache, and HTML that always re-renders.

The whole promise is verified end to end, through the real CLI, against real
image bytes on disk. This one test is the specification of the lazy build:

.. literalinclude:: ../tests/interface/test_lazy_build.py
   :pyobject: test_second_run_is_all_hits_and_template_edit_rewrites_no_image_bytes
   :caption: tests/interface/test_lazy_build.py

Two claims are pinned here at once: a second build **generates nothing** and
leaves every derivative byte-for-byte identical, and editing a template
**re-renders the HTML while rewriting zero image bytes**.
