Rationale & decisions
=====================

*Point it at a folder of camera originals; get a chronological static gallery you
can share as a link. It never edits your photos, and needs no curation.*

Named for the Akshayuk Pass traverse on Baffin Island, where the driving photo
collection was made.

This chapter keeps only the *why*: vision, principles, privacy, roadmap, and
decisions of record. The *what/how* — the domain model, the ports, the build
flow, the CLI — is the rest of these docs, generated from the code and its tests.
The original specification's section numbers are kept here as headings for
provenance. Code and tests no longer cite them; docstrings cross-reference the
owning chapter directly (e.g. :doc:`lazy-build`). The gaps (§4–13, §16–18) are
the sections now owned by the narrative chapters and the API reference:

- §4 domain model → :doc:`domain`
- §5 architecture & ports → :doc:`architecture`, :doc:`use-cases`
- §6–10 layout, derivatives, lazy build, grouping, rendering → :doc:`functional-core`, :doc:`lazy-build`
- §11–13 config, CLI, sidecars → :doc:`cli`, :doc:`use-cases`
- §16–18 dependencies, testing, Makefile → the README and the test suite itself

.. _rationale-vision:

1. Vision
---------

``baffin`` is the **raw-dump publisher**: it turns a folder of camera originals into
a **static website** — thumbnails and multiple resolutions, organised
chronologically — generated **lazily** so the expensive image work happens once and
template/HTML iteration is effectively free. Then you share the link.

It deliberately does **one** job (publish a gallery) and does not curate, caption
for you, sequence a narrative, or produce a book. Those are separate concerns for
separate tools.

The reason it's built on clean architecture is concrete, not aspirational:
**one application core, two delivery mechanisms.**

- **v1 — CLI** (``baffin …``, Typer). For the technical user, now.
- **v2 — FastAPI web UI.** Upload photos in a browser, generate + host the
  gallery, get a link — so travel companions who won't touch a Python CLI can use
  the exact same core.

Both are thin adapters over the same use cases. Designing the core to be
delivery-agnostic from day one is what makes the web UI an *addition*, not a
rewrite — and is the entire justification for the layering.

.. _rationale-scope:

2. Scope
--------

In scope — v1 (CLI)
~~~~~~~~~~~~~~~~~~~~~

- Read-only ingest of a source tree of **JPEG** photos and **MP4/MOV** videos.
- Lazy generation of JPEG derivatives: ``thumb``, ``low``, ``med``, ``full``.
- Video: extract a poster frame + copy the clip (no transcode yet).
- **Adaptive** chronological grouping (per-day for short spans, Year→Month for long
  archives), overridable in config.
- Jinja2-rendered static HTML/CSS, portable relative URLs, social/OpenGraph +
  sitemap using a configured ``base_url``.
- Progressive enhancement: complete, navigable HTML with **no JS**; a tiny
  vanilla-JS layer adds a lightbox + keyboard nav when available.
- Content-hash-based lazy rebuild that never regenerates unchanged derivatives.
- Typer CLI + Makefile.
- **Optional** per-image metadata sidecars — never required — both **read and
  authored** via ``baffin meta``. Authoring writes sidecars only, never the
  originals.

Reserved — v2 (FastAPI web UI), designed for but not built
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Browser upload of photos into a server-managed source store.
- Trigger a build and host the resulting static gallery; return a shareable link.
- A **graphical** authoring surface over the *same* ``EditAssetMeta`` use case the
  v1 CLI already exposes — a friendlier front-end, not a new capability.
- Multi-user / accounts / auth — flagged as a real question, not solved here.

Explicitly out of scope
~~~~~~~~~~~~~~~~~~~~~~~~~

- **Narrative / story composition** (sequencing photos into prose) — a separate
  downstream tool, never baffin.
- Print / PDF / coffee-table book.
- Any mutation or curation of the originals.
- RAW ``.ARW`` ingest, video transcoding, GPS maps — named extension points, off by
  default.

.. _rationale-principles:

3. Principles & invariants
--------------------------

1. **The application core is delivery-agnostic.** It knows nothing about a
   terminal or HTTP. CLI and web are interchangeable adapters over the same use
   cases. This is the load-bearing principle.
2. **Originals are immutable; sidecars are a separate annotation layer.** baffin
   never modifies, moves, renames, or deletes the image/video **originals** — and
   by default never writes into the source tree at all. Per-image metadata lives in
   a separate ``meta/`` tree; creating/updating a ``.md`` sidecar there never touches a
   photo's bytes. (In v2, "source" is the uploaded set, still immutable once landed.)
3. **Originals are never mutated, even for privacy.** GPS stripping and IPTC
   embedding happen only on *derivative copies* in the output dir.
4. **Every published tier is a derivative**, including ``full`` — default
   GPS-stripping makes ``full`` a *scrubbed copy*, not the literal original.
5. **Derivatives are expensive and cached; HTML is cheap and always re-rendered.**
   The core of the lazy-build promise: editing a template touches zero image bytes.
6. **Words in, metadata out.** Optional human-authored sidecars are the source of
   truth for per-image text (editable, git-diffable). The build *writes* that text
   into output JPEG IPTC/XMP so shared files are self-describing — it never treats
   generated artifacts as the source of truth.
7. **Framework-free core.** Domain = plain dataclasses. Seams = ``typing.Protocol``.
   Pydantic only at I/O edges (config, sidecar parsing, manifest records, and later
   the web request/response DTOs). Not every layer needs serialisation.
8. **Functional core, imperative shell.** Planning, grouping, URL building, and
   cache-diffing are pure functions over the model. All I/O (filesystem, pyvips,
   ffmpeg, hashing, Jinja writes, HTTP) lives in adapters at the edge.

.. _rationale-privacy:

14. Privacy / EXIF
------------------

- ``captured_at`` and optional camera settings read from originals.
- **GPS stripped from all derivatives by default** (``strip_gps = true``); ``full`` is
  therefore a scrubbed re-write, never the literal original.
- Retaining GPS + rendering a route/pin map is an opt-in future extension —
  off by default because these are shared publicly.

.. _rationale-peers:

15. Peers / cross-linking (reserved)
------------------------------------

``[[peers]]`` renders a "fellow travellers" nav of absolute links to other people's
galleries. It only becomes meaningful once more than one person is publishing —
i.e. once the **v2 web UI** lets non-CLI users generate their own galleries. The
field is reserved now so v1 output can link out by hand in the meantime.

.. _rationale-roadmap:

19. Roadmap
-----------

.. list-table::
   :header-rows: 1

   * - Phase
     - Adds
     - Seam it plugs into
   * - v1
     - CLI raw-dump gallery, lazy build, optional sidecars **read + authored** (``baffin meta``)
     - ``EditAssetMeta`` + ``SidecarStore``
   * - v2
     - **FastAPI web UI**: browser upload → generate → host → link; **graphical** metadata authoring over the same ``EditAssetMeta``
     - new ``interface/web`` + ``UploadAssetRepository``; same use cases
   * - later
     - RAW ``.ARW``, video transcode, GPS map
     - ``MetadataReader``, ``VideoProcessor``, config flags

Everything additive: a new adapter or a config flag, never a core rewrite. The
whole reason for the layering is that v2's web UI is a new ``interface/``, not a
second application.

.. _rationale-decisions:

20. Decisions of record & open questions
----------------------------------------

**Decided:**

- **Manifest:** flat ``manifest.json`` (diffable, zero-dep; SQLite only if v2 brings
  concurrent writers — a ``DerivativeStore`` swap).
- **EXIF/metadata:** ``pyexiv2`` (in-process, wheels bundle libexiv2) for read +
  write; exiftool-subprocess kept as a fallback adapter behind the port.
- **``full`` tier:** opt-in per build (``include_full``, default off).
- **Parallelism:** process pool over assets, ``VIPS_CONCURRENCY=1`` per worker.
- **Sidecar location:** separate ``meta/`` tree by default (source stays pristine);
  co-location beside originals configurable.
- **Read seam:** ``SourceRef.path`` is always a readable local handle; v2 lands
  uploads to a local staging tree before discovery rather than introducing a
  stream/object-store port. Landing is the adapter's job; reading is uniform.
- **Cache-state boundary:** ``DerivativeStore.snapshot() -> StoreState`` (manifest
  read + existence check) feeds the pure ``diff_plan``; no per-key ``is_current`` I/O
  interleaves with planning.
- **Stat→hash memo owner:** the ``Hasher`` adapter, injected with a ``.baffin/`` memo
  handle — not a separate port.
- **Per-asset unit:** an ``AssetProcessor`` shell-side composite (not a port) is the
  process-pool submission unit; adapters must be picklable / worker-constructable.
- **Port DTO:** ``MetadataReader`` returns ``RawMetadata`` (raw read: dims/kind/EXIF),
  distinct from the authored ``AssetMeta`` sidecar.

**Deferred (not a blocker for v1):**

1. **v2 auth / multi-user** — explicitly not being decided now. When v2 is real,
   choose single-tenant (one deploy per person, share links) vs accounts; keeping
   the web layer a thin adapter preserves both options at zero cost today.
