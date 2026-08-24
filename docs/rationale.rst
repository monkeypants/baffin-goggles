Rationale & decisions
=====================

Named for the Akshayuk Pass traverse on Baffin Island,
where the driving photo collection was made.

This chapter records what was decided and why.
What the software does is documented in the other chapters,
generated from the code and its tests.

.. _rationale-vision:

Why the layering exists
-----------------------

baffin publishes a gallery and does nothing else.
It does not curate, caption, sequence a narrative, or produce a book.

The constraint that shapes the code is that the CLI is not meant to be the only
delivery mechanism.
A FastAPI web UI would let travel companions who will not use a Python CLI
drive the same use cases,
so the application core is delivery-agnostic
and each surface is a thin adapter over it.
That is what the layer boundaries in :doc:`architecture` are for,
and why adding the web UI would mean adding an ``interface/`` package
rather than a second application.

.. _rationale-scope:

Out of scope
------------

- Narrative composition (sequencing photos into prose): a downstream tool.
- Print, PDF, coffee-table book.
- Any mutation or curation of the originals.
- RAW ``.ARW`` ingest, video transcoding, GPS maps:
  extension points, off by default.

.. _rationale-principles:

Principles & invariants
-----------------------

1. **The application core is delivery-agnostic.**
   It knows nothing about a terminal or HTTP.
   CLI and web are interchangeable adapters over the same use cases.
2. **Originals are immutable; sidecars are a separate annotation layer.**
   baffin never modifies, moves, renames or deletes the originals,
   and by default never writes into the source tree at all.
   Per-image metadata lives in a separate ``meta/`` tree;
   writing a ``.md`` sidecar there never touches a photo's bytes.
   Under a web UI, "source" would be the uploaded set, still immutable once
   landed.
3. **Originals are never mutated, even for privacy.**
   Scrubbing and metadata embedding happen on derivative copies in the output
   directory.
4. **Every published tier is a derivative**, including ``full``
   (see :ref:`rationale-privacy`).
5. **Derivatives are expensive and cached; HTML is cheap and always re-rendered.**
   Editing a template touches zero image bytes.
6. **Words in, metadata out.**
   Optional human-authored sidecars are the source of truth for per-image text,
   editable and git-diffable.
   The build writes that text into the output JPEG's IPTC/XMP so shared files
   are self-describing, and never reads generated artifacts back as source.
7. **Framework-free core.**
   Domain is plain dataclasses, seams are ``typing.Protocol``,
   and Pydantic appears only at I/O edges:
   config, sidecar parsing and manifest records.
8. **Functional core, imperative shell.**
   Planning, grouping, URL building and cache-diffing are pure functions over
   the model.
   All I/O (filesystem, pyvips, ffmpeg, hashing, Jinja writes) lives in
   adapters at the edge.

.. _rationale-privacy:

Privacy
-------

``captured_at`` and optional camera settings are read from the originals.
GPS is stripped from every derivative by default (``strip_gps = true``),
so ``full`` is a scrubbed re-encode rather than the original bytes.
Retaining GPS and rendering a route map is an opt-in extension,
off by default because galleries are shared publicly.

.. _rationale-peers:

Peers (reserved)
----------------

``[[peers]]`` renders a "fellow travellers" nav of absolute links to other
people's galleries.
The field is reserved and currently rendered by hand-written config;
it becomes useful once more than one person is publishing.

.. _rationale-roadmap:

Roadmap
-------

Each phase adds an adapter or a config flag; none requires a core change.

.. list-table::
   :header-rows: 1

   * - Phase
     - Adds
     - Seam it plugs into
   * - v1
     - CLI gallery, lazy build, sidecars read and authored (``baffin meta``)
     - ``EditAssetMeta`` + ``SidecarStore``
   * - v2
     - Web UI: browser upload, generate, host, link
     - new ``interface/web`` + ``UploadAssetRepository``; same use cases
   * - later
     - RAW ``.ARW``, video transcode, GPS map
     - ``MetadataReader``, ``VideoProcessor``, config flags

.. _rationale-decisions:

Decisions of record
-------------------

- **Manifest:** flat ``manifest.json``, diffable and zero-dependency.
  SQLite only if concurrent writers arrive, which is a ``DerivativeStore`` swap.
- **EXIF/metadata:** ``pyexiv2`` (in-process; wheels bundle libexiv2) for read
  and write, with an exiftool-subprocess fallback adapter behind the port.
- **``full`` tier:** opt-in per build (``include_full``, default off).
- **Parallelism:** process pool over assets, ``VIPS_CONCURRENCY=1`` per worker,
  workers started by spawn rather than fork
  (forking an initialised libvips deadlocks).
- **Sidecar location:** a separate ``meta/`` tree by default,
  leaving the source untouched; co-location beside the originals is configurable.
- **Read seam:** ``SourceRef.path`` is always a readable local handle.
  Uploads would land in a local staging tree before discovery
  instead of introducing a stream or object-store port,
  keeping landing an adapter concern and reading uniform.
- **Cache-state boundary:** ``DerivativeStore.snapshot() -> StoreState``
  (manifest read plus existence check) feeds the pure ``diff_plan``,
  so no per-key I/O interleaves with planning.
- **Stat→hash memo owner:** the ``Hasher`` adapter, injected with a ``.baffin/``
  memo handle, rather than a separate port.
- **Per-asset unit:** an ``AssetProcessor`` shell-side composite, not a port,
  is the process-pool submission unit;
  its adapters must be picklable and constructable in a worker.
- **Port DTO:** ``MetadataReader`` returns ``RawMetadata`` (dims, kind, EXIF),
  distinct from the authored ``AssetMeta`` sidecar.
- **Toolchain:** libvips and ffmpeg are pinned in ``Dockerfile`` for CI,
  because a derivative's cache key does not include them
  (see :doc:`contributing`).

Open questions
--------------

- **Auth and multi-user**, if the web UI is built.
  The choice is between single-tenant (one deploy per person, shared links)
  and accounts.
  Keeping the web layer a thin adapter preserves both options.
- **Toolchain in the cache key.**
  Two machines with different libvips versions produce different bytes under
  identical keys, and each reports all-hits over the other's output.
  Either the key includes a toolchain fingerprint, at the cost of invalidating
  every derivative on an upgrade, or the pinned image is the only sanctioned
  builder.
