Getting started
===============

Point ``baffin`` at a folder of camera originals;
get a chronological static gallery you can share as a link.
This chapter gets you from checkout to a served gallery.
For *why* it works this way, read :doc:`rationale`.

System dependencies
-------------------

baffin leans on a few native libraries that aren't Python packages.
Install them before ``uv sync``.

macOS (Homebrew)
~~~~~~~~~~~~~~~~~

.. code-block:: sh

   brew install vips ffmpeg inih
   brew install plantuml   # only to build the docs

- **vips** (libvips): the default ``pyvips`` thumbnailer.
  Without it, only the Pillow fallback works.
- **ffmpeg**: video poster frames and clip copies.
  Must be on ``PATH``.
- **inih**: provides ``libINIReader``,
  which the ``pyexiv2`` wheel's bundled ``libexiv2`` links against on macOS.
  Without it, ``import pyexiv2`` fails to load its dylib.
- **plantuml**: renders the architecture diagrams.
  Only needed for ``make docs``.

Linux (Debian/Ubuntu)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sh

   sudo apt-get install -y libvips-dev ffmpeg plantuml

The ``pyexiv2`` manylinux wheel bundles its own libraries,
so no ``inih`` equivalent is needed.
This is what CI installs.

First gallery
-------------

.. code-block:: sh

   uv sync                                   # create the environment
   uv run baffin doctor                      # check libvips/ffmpeg + config
   uv run baffin build --source photos --output site
   uv run baffin serve --source photos --output site --watch

``build`` is lazy:
a second run regenerates nothing,
and editing a template rewrites zero image bytes (:doc:`lazy-build`).
``serve --watch`` re-renders templates on change without touching images.

Put the recurring settings in ``baffin.toml``
(``source``, ``output``, ``include_full``; see :doc:`cli`).
The Makefile targets then need no arguments:

.. code-block:: sh

   make build ARGS="--full --jobs 8"   # any CLI flag via ARGS
   make serve                          # foreground; dies with the terminal
   make up                             # login agent: survives crashes and reboots
   make status                         # is the agent running, and as what pid
   make down                           # stop and remove it

``make up`` installs a launchd agent (macOS only) that runs ``baffin serve``
from the repo root with ``RunAtLoad`` and ``KeepAlive``,
so it restarts after a crash and returns after a reboot.
Logs go to ``~/Library/Logs/baffin-gallery.log``.
Per-image captions are optional (:doc:`use-cases`):

.. code-block:: sh

   uv run baffin meta set photos/2025/DSC1.JPG --title "River crossing" --credit "Chris"

The full command surface is :doc:`cli`.

Configuration: ``baffin.toml``
-------------------------------

Resolution order: CLI flag > env var (``BAFFIN_*``) > ``baffin.toml`` > default.

.. code-block:: toml

   title    = "Akshayuk Pass — Chris"
   base_url = "https://chris.example.com/baffin/"
   source   = "photos/"
   output   = "site/"
   grouping = "adaptive"          # adaptive | day | month | year-month | flat
   strip_gps = true
   include_full = false           # publish full-res scrubbed copies? (~5 GB) default off

   [[derivatives]]
   name = "thumb"
   max_edge = 300
   quality = 80

The CLI suite parses this exact sample, in ``test_documented_sample_config_parses``.
To contribute, see :doc:`contributing`.
