Rationale & decisions
=====================

Point it at a folder of camera originals;
get a chronological static gallery you can share as a link.
It never edits your photos, and needs no curation.

Named for the Akshayuk Pass traverse on Baffin Island,
where the driving photo collection was made.

This chapter records why the design is what it is:
vision, scope, principles, privacy, roadmap, and decisions of record.
The domain model, ports, build flow and CLI are covered by the other chapters,
generated from the code and its tests.

.. _rationale-vision:

Vision
------

``baffin`` turns a folder of camera originals into a static website:
thumbnails and several resolutions, organised chronologically,
generated lazily so the image work happens once
and HTML iteration is cheap.

It does one job, publishing a gallery.
It does not curate, caption, sequence a narrative, or produce a book.
Those are separate tools.

The layering exists for one reason: one application core, two delivery mechanisms.

- v1 — CLI (``baffin …``, Typer), for the technical user.
- v2 — FastAPI web UI: upload photos in a browser, generate and host the gallery,
  return a link, so travel companions who will not use a Python CLI
  can drive the same core.

Both are thin adapters over the same use cases,
so v2 is a new ``interface/`` package rather than a second application.

.. _rationale-scope:

Scope
-----

In scope — v1 (CLI)
~~~~~~~~~~~~~~~~~~~~

- Read-only ingest of a source tree of JPEG photos and MP4/MOV videos.
- Lazy generation of JPEG derivatives: ``thumb``, ``low``, ``med``, ``full``.
- Video: extract a poster frame and copy the clip (no transcode).
- Adaptive chronological grouping (per-day for short spans, Year→Month for long
  archives), overridable in config.
- Jinja2-rendered static HTML/CSS, portable relative URLs,
  OpenGraph tags and a sitemap from a configured ``base_url``.
- Complete, navigable HTML with no JavaScript;
  a small vanilla-JS layer adds a lightbox and keyboard navigation when available.
- Content-hash-based rebuild that never regenerates unchanged derivatives.
- Typer CLI and Makefile.
- Optional per-image metadata sidecars, read and authored via ``baffin meta``.
  Authoring writes sidecars only.

Reserved — v2 (FastAPI web UI), designed for but not built
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Browser upload of photos into a server-managed source store.
- Trigger a build, host the resulting static gallery, return a shareable link.
- A graphical authoring surface over the same ``EditAssetMeta`` use case
  the v1 CLI exposes.
- Multi-user, accounts and auth: an open question, not solved here.

Out of scope
~~~~~~~~~~~~~~~~~~~~~~~~~

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
   In v2, "source" is the uploaded set, still immutable once landed.
3. **Originals are never mutated, even for privacy.**
   GPS stripping and IPTC embedding happen on derivative copies in the output
   directory.
4. **Every published tier is a derivative**, including ``full``.
   Default GPS-stripping makes ``full`` a scrubbed copy rather than the
   literal original.
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
   config, sidecar parsing, manifest records, and later the web DTOs.
8. **Functional core, imperative shell.**
   Planning, grouping, URL building and cache-diffing are pure functions over
   the model.
   All I/O (filesystem, pyvips, ffmpeg, hashing, Jinja writes, HTTP) lives in
   adapters at the edge.

.. _rationale-privacy:

Privacy / EXIF
--------------

- ``captured_at`` and optional camera settings are read from the originals.
- GPS is stripped from all derivatives by default (``strip_gps = true``),
  so ``full`` is a scrubbed re-write rather than the literal original.
- Retaining GPS and rendering a route map is an opt-in extension,
  off by default because galleries are shared publicly.

.. _rationale-peers:

Peers / cross-linking (reserved)
--------------------------------

``[[peers]]`` renders a "fellow travellers" nav of absolute links to other
people's galleries.
It becomes useful once more than one person is publishing,
which in practice means once the v2 web UI lets non-CLI users generate galleries.
The field is reserved now so v1 output can link out by hand.

.. _rationale-roadmap:

Roadmap
-------

.. list-table::
   :header-rows: 1

   * - Phase
     - Adds
     - Seam it plugs into
   * - v1
     - CLI raw-dump gallery, lazy build, optional sidecars read and authored (``baffin meta``)
     - ``EditAssetMeta`` + ``SidecarStore``
   * - v2
     - FastAPI web UI: browser upload → generate → host → link; graphical metadata authoring over the same ``EditAssetMeta``
     - new ``interface/web`` + ``UploadAssetRepository``; same use cases
   * - later
     - RAW ``.ARW``, video transcode, GPS map
     - ``MetadataReader``, ``VideoProcessor``, config flags

Each phase adds an adapter or a config flag; none requires a core change.

.. _rationale-decisions:

Decisions of record & open questions
------------------------------------

Decided:

- **Manifest:** flat ``manifest.json``, diffable and zero-dependency.
  SQLite only if v2 brings concurrent writers, which is a ``DerivativeStore`` swap.
- **EXIF/metadata:** ``pyexiv2`` (in-process; wheels bundle libexiv2) for read
  and write, with an exiftool-subprocess fallback adapter behind the port.
- **``full`` tier:** opt-in per build (``include_full``, default off).
- **Parallelism:** process pool over assets, ``VIPS_CONCURRENCY=1`` per worker,
  workers started by spawn rather than fork
  (forking an initialised libvips deadlocks).
- **Sidecar location:** a separate ``meta/`` tree by default,
  leaving the source untouched; co-location beside the originals is configurable.
- **Read seam:** ``SourceRef.path`` is always a readable local handle.
  v2 lands uploads to a local staging tree before discovery
  instead of introducing a stream or object-store port:
  landing is the adapter's job, reading is uniform.
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

Deferred:

- **v2 auth and multi-user.**
  When v2 is real, choose between single-tenant (one deploy per person, shared
  links) and accounts.
  Keeping the web layer a thin adapter preserves both options.
