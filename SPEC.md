# baffin — specification

*Point it at a folder of camera originals; get a chronological static gallery you
can share as a link. It never edits your photos, and needs no curation.*

Named for the Akshayuk Pass traverse on Baffin Island, where the driving photo
collection was made.

---

## 1. Vision

`baffin` is the **raw-dump publisher**: it turns a folder of camera originals into
a **static website** — thumbnails and multiple resolutions, organised
chronologically — generated **lazily** so the expensive image work happens once and
template/HTML iteration is effectively free. Then you share the link.

It deliberately does **one** job (publish a gallery) and does not curate, caption
for you, sequence a narrative, or produce a book. Those are separate concerns for
separate tools.

The reason it's built on clean architecture is concrete, not aspirational:
**one application core, two delivery mechanisms.**

- **v1 — CLI** (`baffin …`, Typer). For the technical user, now.
- **v2 — FastAPI web UI.** Upload photos in a browser, generate + host the
  gallery, get a link — so travel companions who won't touch a Python CLI can use
  the exact same core.

Both are thin adapters over the same use cases. Designing the core to be
delivery-agnostic from day one is what makes the web UI an *addition*, not a
rewrite — and is the entire justification for the layering below.

---

## 2. Scope

### In scope — v1 (CLI)
- Read-only ingest of a source tree of **JPEG** photos and **MP4/MOV** videos.
- Lazy generation of JPEG derivatives: `thumb`, `low`, `med`, `full`.
- Video: extract a poster frame + copy the clip (no transcode yet).
- **Adaptive** chronological grouping (per-day for short spans, Year→Month for long
  archives), overridable in config.
- Jinja2-rendered static HTML/CSS, portable relative URLs, social/OpenGraph +
  sitemap using a configured `base_url`.
- Progressive enhancement: complete, navigable HTML with **no JS**; a tiny
  vanilla-JS layer adds a lightbox + keyboard nav when available.
- Content-hash-based lazy rebuild that never regenerates unchanged derivatives.
- Typer CLI + Makefile.
- **Optional** per-image metadata sidecars (§13) — never required — both **read
  and authored** via `baffin meta` (§12). Authoring writes sidecars only, never
  the originals.

### Reserved — v2 (FastAPI web UI), designed for but not built
- Browser upload of photos into a server-managed source store.
- Trigger a build and host the resulting static gallery; return a shareable link.
- A **graphical** authoring surface over the *same* `EditAssetMeta` use case the
  v1 CLI already exposes — a friendlier front-end, not a new capability.
- Multi-user / accounts / auth — flagged as a real question, not solved here.

### Explicitly out of scope
- **Narrative / story composition** (sequencing photos into prose) — a separate
  downstream tool, never baffin.
- Print / PDF / coffee-table book.
- Any mutation or curation of the originals.
- RAW `.ARW` ingest, video transcoding, GPS maps — named extension points, off by
  default.

---

## 3. Principles & invariants

1. **The application core is delivery-agnostic.** It knows nothing about a
   terminal or HTTP. CLI and web are interchangeable adapters over the same use
   cases. This is the load-bearing principle.
2. **Originals are immutable; sidecars are a separate annotation layer.** baffin
   never modifies, moves, renames, or deletes the image/video **originals** — and
   by default never writes into the source tree at all. Per-image metadata lives in
   a separate `meta/` tree (§13); creating/updating a `.md` sidecar there never
   touches a photo's bytes. (Co-location beside originals is available via config,
   but the camera folder stays byte-for-byte pristine by default. In v2, "source"
   is the uploaded set, still immutable once landed.)
3. **Originals are never mutated, even for privacy.** GPS stripping and IPTC
   embedding happen only on *derivative copies* in the output dir.
4. **Every published tier is a derivative**, including `full` — default
   GPS-stripping makes `full` a *scrubbed copy*, not the literal original.
5. **Derivatives are expensive and cached; HTML is cheap and always re-rendered.**
   The core of the lazy-build promise (§8): editing a template touches zero image
   bytes.
6. **Words in, metadata out.** Optional human-authored sidecars are the source of
   truth for per-image text (editable, git-diffable). The build *writes* that text
   into output JPEG IPTC/XMP so shared files are self-describing — it never treats
   generated artifacts as the source of truth.
7. **Framework-free core.** Domain = plain dataclasses. Seams = `typing.Protocol`.
   Pydantic only at I/O edges (config, sidecar parsing, manifest records, and later
   the web request/response DTOs). Not every layer needs serialisation.
8. **Functional core, imperative shell.** Planning, grouping, URL building, and
   cache-diffing are pure functions over the model. All I/O (filesystem, pyvips,
   ffmpeg, hashing, Jinja writes, HTTP) lives in adapters at the edge.

---

## 4. Domain model (`baffin.domain`)

Plain frozen dataclasses; no I/O, no framework imports.

```python
AssetKind = Literal["photo", "video"]

@dataclass(frozen=True)
class SourceRef:
    path: Path            # location in the read-only source
    size: int
    mtime_ns: int         # fast prefilter only, never truth

@dataclass(frozen=True)
class Asset:
    ref: SourceRef
    content_hash: str     # xxhash of bytes — the durable identity
    kind: AssetKind
    captured_at: datetime # EXIF DateTimeOriginal (falls back to mtime)
    width: int
    height: int
    orientation: int
    camera: CameraInfo | None      # iso, shutter, aperture, focal_len, lens, model
    gps: GpsFix | None             # read from original; stripped from outputs by default

@dataclass(frozen=True)
class AssetMeta:                   # per-image metadata from a sidecar (§13); all optional
    title: str | None
    caption: str | None
    credit: str | None
    alt: str | None                # NOT narrative/story data — just describes one image

@dataclass(frozen=True)
class RawMetadata:                 # the raw read from an original (§5 MetadataReader)
    kind: AssetKind                # NOT the sidecar — this is what EXIF/probe yields:
    captured_at: datetime          # everything needed to build an Asset except ref +
    width: int                     # content_hash. Distinct from AssetMeta (authored text).
    height: int
    orientation: int
    camera: CameraInfo | None
    gps: GpsFix | None

@dataclass(frozen=True)
class DerivativeSpec:
    name: Literal["thumb", "low", "med", "full"]
    max_edge: int | None           # longest-edge px; None = original size (full)
    quality: int
    def cache_key(self, asset: Asset) -> str: ...   # hash(content_hash + spec)

@dataclass(frozen=True)
class Derivative:
    asset_hash: str
    spec_name: str
    rel_path: Path                 # path within the output site
    width: int
    height: int

@dataclass(frozen=True)
class StoreState:                  # immutable snapshot the pure diff consumes (§5, §8)
    present: frozenset[str]        # cache keys that are BOTH recorded in the manifest
                                   # AND whose file exists on disk (existence pre-checked
                                   # by the shell during snapshot(); diff stays pure)

@dataclass(frozen=True)
class Group:                       # a chronological bucket in the timeline
    key: str                       # "2025-07-14" | "day-03" | "2025/07"
    label: str                     # "Day 3 — 14 Jul"
    span: tuple[datetime, datetime]
    assets: tuple[Asset, ...]

@dataclass(frozen=True)
class Site:
    title: str
    base_url: str
    peers: tuple[Peer, ...]        # reserved; see §15
    groups: tuple[Group, ...]
```

---

## 5. Architecture

Clean architecture with a strict inward dependency rule, enforced by
`import-linter` (§17). Four layers:

```
baffin/
  domain/         # dataclasses + pure logic. Imports nothing outward.
  application/    # use cases + Protocol ports. Imports domain only.
  adapters/       # concrete port implementations (the imperative shell).
  interface/      # delivery mechanisms — thin, swappable:
    cli/          #   v1: Typer
    web/          #   v2: FastAPI  (reserved, plugs into the SAME use cases)
```

The **money shot**: `interface/cli` and `interface/web` both do nothing but
translate their input (argv / HTTP request) into a use-case call and translate the
result back out. Neither leaks into `application` or `domain`.

### Application use cases (`baffin.application`)
- `BuildGallery` — scan → plan → generate misses → render. The one CLI `build` and
  a web "generate" endpoint both invoke this.
- `ScanGallery` — discover + report the model and cache HIT/MISS plan (dry run).
- `CleanGallery` — prune orphaned derivatives.
- `EditAssetMeta` — read → merge → write one asset's sidecar metadata. The CLI
  `meta` command drives it now; the v2 web authoring form drives the *same* use
  case later. A second use case, and the clearest proof the core is
  delivery-agnostic: two front-ends, one authoring path.

### Ports (`typing.Protocol`)

The **identity currency** across ports is `SourceRef` for the source side and
`Path` for the *output* side. `SourceRef.path` is always a **readable local
handle**: v1 points it at the camera folder; v2's `UploadAssetRepository` lands
each upload to a local staging tree *before* `discover()` yields it, so no port
needs an object-store or stream abstraction and the "no core change for v2" claim
holds by making landing (not reading) the adapter's job.

```python
class AssetRepository(Protocol):
    """Where photos come from. v1: a local read-only folder.
       v2: an uploaded set, landed to a local staging path before discovery.
       Both read-only after landing; SourceRef.path is a readable local handle."""
    def discover(self, root: Path) -> Iterable[SourceRef]: ...

class MetadataReader(Protocol):
    def read(self, ref: SourceRef) -> RawMetadata: ...        # EXIF/probe: dims, kind, …

class SidecarStore(Protocol):
    """Optional per-image metadata beside the original. The ONLY place baffin
       writes into the source tree — sidecar files only, never the photo bytes.
       Constructed with source_root + meta_root to resolve the mirrored path."""
    def read(self, ref: SourceRef) -> AssetMeta | None: ...
    def write(self, ref: SourceRef, meta: AssetMeta) -> None: ...   # never touches the image

class Hasher(Protocol):
    """xxhash of bytes. Owns the stat→hash memo (§8.1): constructed with a memo
       persistence handle (a table in .baffin/); consults/updates it internally
       so the Protocol stays a single call. Unchanged (path,size,mtime_ns) ⇒
       memoised hash; changed stat ⇒ re-hash."""
    def hash_file(self, ref: SourceRef) -> str: ...

class Thumbnailer(Protocol):
    """One image derivative. Default adapter: pyvips; fallback: Pillow."""
    def render(self, src: SourceRef, spec: DerivativeSpec, dst: Path,
               *, strip_gps: bool, embed: AssetMeta | None) -> Derivative: ...

class VideoProcessor(Protocol):
    def poster(self, src: SourceRef, spec: DerivativeSpec, dst: Path) -> Derivative: ...
    def publish_clip(self, src: SourceRef, dst: Path, *, strip_gps: bool) -> Path: ...

class DerivativeStore(Protocol):
    """Output dir + manifest. Records results; hands the pure diff a snapshot.
       snapshot() reads the manifest AND pre-checks file existence, returning the
       immutable StoreState that diff_plan() consumes — so HIT/MISS stays a pure
       function and no per-key is_current() I/O is interleaved with planning."""
    def snapshot(self) -> StoreState: ...
    def record(self, key: str, deriv: Derivative) -> None: ...
    def orphans(self, live_keys: set[str]) -> Iterable[Path]: ...

class SiteRenderer(Protocol):
    """Jinja2 → HTML/CSS/JS. Always runs; cheap."""
    def render(self, site: Site, out: Path) -> None: ...
```

**Contract notes (beyond the signatures).**
- *Errors.* Read/generate ports raise a small defined hierarchy
  (`SourceUnreadable`, `MetadataUnreadable`, `DerivativeFailed`). `BuildGallery`'s
  default policy is **skip-and-report per asset**; `--strict` turns any such error
  fatal. Protocols can't type exceptions, so this is the contract in prose.
- *Parallelism.* The process pool (§8) fans out over a coarse **per-asset**
  unit, not these fine-grained calls. Adapters are therefore required to be
  **picklable or re-constructable in a worker**, and each worker composes
  hash→read→render for one asset. See the `AssetProcessor` seam in §8.

### Functional core (pure)
`group_timeline(assets, policy)`, `plan_derivatives(assets, specs)`,
`diff_plan(plan, store_state: StoreState) -> BuildPlan`, `url_for(...)`. The
`store_state` is the immutable snapshot from `DerivativeStore.snapshot()` — the
shell does the manifest read + file-existence check, the diff stays pure.

### Imperative shell (adapters)
`FsAssetRepository`, `ExifMetadataReader`, `MarkdownSidecarStore`, `XxHasher`,
`VipsThumbnailer` (+ `PillowThumbnailer` fallback), `FfmpegVideo`,
`FileDerivativeStore` (+ JSON/SQLite manifest), `Jinja2Renderer`. v2 adds an
`UploadAssetRepository` and a FastAPI app — no core change.

---

## 6. Source & output layout

**Source (read-only) + metadata (separate):**
```
photos/                   # originals — baffin NEVER writes here
  2025/DSC04512.JPG
  2025/C0003.MP4
meta/                     # per-image sidecars, mirroring the source layout
  2025/DSC04512.md        # optional; authored by `baffin meta` or by hand
```

**Output (publishable site == the derivative cache):**
```
site/
  index.html                      # timeline overview
  <group>/index.html              # e.g. day-03/  or 2025/07/
  thumb|low|med|full/<hash>.jpg
  video/<hash>.mp4   poster/<hash>.jpg
  assets/app.css  assets/app.js   # progressive-enhancement layer
  sitemap.xml
  .baffin/manifest.json           # cache index; not served
```

Derivatives are named by **content hash**: rename/move of a source is a cache
**hit**, identical bytes are stored once.

---

## 7. Derivatives

| Tier  | Longest edge | Format | Notes |
|-------|--------------|--------|-------|
| thumb | ~300 px      | JPEG   | grid; `loading="lazy"` |
| low   | ~800 px      | JPEG   | lightbox default / slow links |
| med   | ~1600 px     | JPEG   | lightbox zoom / large screens |
| full  | original     | JPEG   | scrubbed copy (GPS removed); **opt-in, default off** — see below |

**`full` is opt-in per build** (`include_full`, default `false`; `--full` on the
CLI). It roughly duplicates the source volume in `site/` (~5 GB), and `med` covers
almost all on-screen viewing, so it's off unless you want downloadable originals.
It's just another `DerivativeSpec`: turning it on later generates only the missing
copies; `clean` prunes them if turned off.

Sizes/qualities configurable. pyvips does downscale + auto-orient + sharpen in one
pass. Videos yield `poster/<hash>.jpg` (mid-frame via ffmpeg) + a copied clip;
transcode is a reserved extension.

---

## 8. The lazy build (the crown jewel)

Two independent cache layers plus always-on rendering:

1. **Stat→hash memo.** Re-hashing 5 GB every run is wasteful, so
   `(path, size, mtime_ns)` maps to a previously computed `content_hash`. Unchanged
   stat ⇒ trust the cached hash; changed ⇒ re-hash. (Prefilter only.)
2. **Derivative cache.** Key = `hash(content_hash + spec)`. Manifest has the key
   **and** the file exists ⇒ **skip generation**. Renames/moves/duplicate bytes ⇒
   hits. Changing a spec (thumb 300→320) changes only that key ⇒ only that tier
   regenerates.
3. **HTML/CSS/JS always re-render.** Cheap; depend on the templates you iterate on.
   **Editing a `.j2` and re-running touches zero image bytes** — the whole point.

```
scan → (memo?) hash → read EXIF + optional sidecar → build Asset model
     → group_timeline → plan_derivatives → diff vs manifest
     → generate MISSES only (parallel)      # expensive, cached
     → render site templates (always)       # cheap
     → prune orphans (opt-in) → write manifest + sitemap
```

`--force` bypasses caches; `clean` removes orphaned derivatives.

**Parallelism.** Generation of misses runs on a **process pool over assets**
(`ProcessPoolExecutor`, workers ≈ CPU count, `--jobs`), with libvips pinned to one
thread per worker (`VIPS_CONCURRENCY=1`) to avoid CPU oversubscription. Processes
parallelize the *whole* per-image pipeline (hash + EXIF + resize + IPTC write), not
just the resize, and give pyexiv2's non-thread-safe writes a private interpreter
each. Planning stays pure in the functional core; only the shell fans work out.

That per-asset unit is the **`AssetProcessor` seam**: a shell-side composite that
runs `Hasher` → `MetadataReader` → `Thumbnailer`/`VideoProcessor` for one asset and
returns its `Derivative`s. It is what the pool submits, so its inputs and outputs
are picklable and its adapters are re-constructable per worker (§5 contract notes).
It is deliberately *not* an application port — the core plans; the shell executes.

---

## 9. Chronological grouping

`captured_at` (EXIF `DateTimeOriginal`, fallback mtime) drives an **adaptive**
policy:

- **Span ≤ ~30 days** → **by day**, labelled by trip-day (`Day 3 — 14 Jul`).
- **Longer** → **Year → Month**.
- Config pins `grouping = "day" | "month" | "year-month" | "flat" | "adaptive"`,
  plus day-1 anchor and ordering (newest/oldest-first).

`index.html` is the timeline overview; each group is its own page.

---

## 10. Templates & rendering

- Jinja2, no bundler, no Node. `site/assets/app.{css,js}` hand-written, copied
  verbatim.
- **Progressive enhancement.** Server-rendered HTML is fully functional and
  crawlable (works in `lynx`/`wget`): every thumb links to a real photo/full page;
  groups are real pages. `app.js` *enhances* into a lightbox with `←/→/Esc` and
  lazy-loads; JS off breaks nothing.
- Responsive `srcset` across thumb/low/med; `full` reachable via link.
- OpenGraph/Twitter meta + `sitemap.xml` use `base_url`; in-site links are
  **relative** so the site is portable across domain root, `/baffin/` subpath, or
  `file://`.

---

## 11. Configuration — `baffin.toml`

```toml
title    = "Akshayuk Pass — Chris"
base_url = "https://chris.example.com/baffin/"
source   = "photos/"
output   = "site/"
meta     = "meta/"             # per-image sidecar tree (mirrors source); "beside" to co-locate
grouping = "adaptive"          # adaptive | day | month | year-month | flat
strip_gps = true
show_camera_settings = false
include_full = false           # publish full-res scrubbed copies? (~5 GB) default off

[[derivatives]]
name = "thumb"; max_edge = 300; quality = 80
# low / med / full follow…

[[peers]]                       # reserved (§15)
name = "Dana"; url = "https://dana.example.com/baffin/"
```

Parsed/validated with a Pydantic `Settings` model at the edge, handed inward as a
plain config object. The same `Settings` is reused by the v2 web layer.

---

## 12. CLI — `baffin` (Typer)

Type-hint / `Annotated`-driven, congruent with the user's FastAPI habits. Each
command is a one-liner that builds adapters and invokes a use case.

| Command | Purpose |
|---------|---------|
| `baffin build`  | Full lazy build. `--force`, `--jobs N`, `--source`, `--output`. |
| `baffin scan`   | Dry run: report assets, groups, cache HIT/MISS plan. |
| `baffin serve`  | Build then serve `output/` locally; `--watch` re-renders templates on change (the iteration loop). |
| `baffin clean`  | Remove orphaned derivatives / stale manifest entries; `--all` wipes cache. |
| `baffin meta`   | Read/write per-image metadata sidecars (never the photo). `meta show <photo>`; `meta edit <photo>` opens `$EDITOR` on the sidecar (created from a template if absent); `meta set <photo> --title/--caption/--credit/--alt …` for scripted/structured edits; bulk e.g. `meta set --credit "Chris Gough" --all`. All routed through `EditAssetMeta`. |
| `baffin doctor` | Check system deps (libvips, ffmpeg) + config sanity. |

Config resolution: CLI flag > env var > `baffin.toml` > default.

---

## 13. Per-image metadata sidecars (optional; authored via CLI in v1)

Per-image metadata **only** — describing a single photo. **Not** narrative or story
composition (that's a separate downstream tool).

- **Location:** a separate `meta/` tree mirroring the source layout —
  `meta/2025/DSC04512.md` pairs with `photos/2025/DSC04512.JPG` by relative path
  (robust against stem collisions across folders). Keeps the camera folder
  byte-for-byte pristine. Co-location beside originals is a config option
  (`meta = "beside"`). baffin writes *these* files; never the image originals (§3.2).
- **Format:** Markdown with optional YAML front-matter:
  ```markdown
  ---
  title: River crossing
  credit: Chris Gough
  alt: A hiker fording a braided glacial river
  ---
  Short caption text for this one photo.
  ```
- **Authoring is a use case, exposed by every front-end.** In v1 the CLI writes
  sidecars via `baffin meta …` (`EditAssetMeta`); you can equally hand-edit the
  `.md`. Entirely optional — the raw dump requires none.
- If present, fields are used in HTML and **embedded into the output JPEG
  IPTC/XMP** (self-describing shares).
- **v2:** the web UI is a graphical form over the *same* `EditAssetMeta` use case —
  not a new capability, just a friendlier surface.

---

## 14. Privacy / EXIF

- `captured_at` and optional camera settings read from originals.
- **GPS stripped from all derivatives by default** (`strip_gps = true`); `full` is
  therefore a scrubbed re-write, never the literal original.
- Retaining GPS + rendering a route/pin map is an opt-in future extension —
  off by default because these are shared publicly.

---

## 15. Peers / cross-linking (reserved)

`[[peers]]` renders a "fellow travellers" nav of absolute links to other people's
galleries. It only becomes meaningful once more than one person is publishing —
i.e. once the **v2 web UI** lets non-CLI users generate their own galleries. The
field is reserved now so v1 output can link out by hand in the meantime.

---

## 16. Dependencies & system requirements

- **Runtime:** Python 3.12+, `typer`, `jinja2`, `pyvips` (⇒ system `libvips`),
  `pydantic`, `pyexiv2` (EXIF/IPTC/XMP read+write; wheels bundle
  libexiv2, so usually no system dep), an xxhash binding. `ffmpeg` on PATH for
  video.
- `Thumbnailer` Protocol keeps **Pillow** a drop-in fallback (no libvips); the
  `MetadataReader`/`SidecarStore` ports keep an **exiftool-subprocess** adapter as
  a documented fallback if Exiv2 ever fumbles a file (not the default).
- **v2 adds** `fastapi` + an ASGI server (`uvicorn`) — in `interface/web` only.
- `baffin doctor` verifies libvips/ffmpeg presence and versions.

---

## 17. Testing & quality gates

Mirrors the user's global conventions; `make check` is the gate.

- **`import-linter`** contracts enforce the dependency rule and, crucially, that
  **neither `interface/cli` nor `interface/web` is importable by `application` or
  `domain`** — proving the core is delivery-agnostic.
- **mypy --strict** across the package.
- **ruff** lint + format.
- **pytest**: the functional core (grouping, planning, cache-diffing, URL building)
  is unit-tested with no I/O; adapters get focused integration tests (tiny fixture
  images, temp source/output tree) asserting HIT/MISS behaviour, the read-only
  source invariant, and GPS-strip on outputs.
- Tests double as living documentation of the domain, aligned with
  functional-core / imperative-shell seams.

---

## 18. Makefile targets

```
make build      # baffin build
make serve      # baffin serve --watch (template iteration loop)
make clean      # baffin clean
make check      # ruff + ruff format --check + lint-imports + mypy + pytest
make docs       # (when public API/docstrings change)
```

---

## 19. Roadmap

| Phase | Adds | Seam it plugs into |
|-------|------|--------------------|
| v1    | CLI raw-dump gallery, lazy build, optional sidecars **read + authored** (`baffin meta`) | `EditAssetMeta` + `SidecarStore` |
| v2    | **FastAPI web UI**: browser upload → generate → host → link; **graphical** metadata authoring over the same `EditAssetMeta` | new `interface/web` + `UploadAssetRepository`; same use cases |
| later | RAW `.ARW`, video transcode, GPS map | `MetadataReader`, `VideoProcessor`, config flags |

Everything additive: a new adapter or a config flag, never a core rewrite. The
whole reason for the layering is that v2's web UI is a new `interface/`, not a
second application.

---

## 20. Decisions of record & open questions

**Decided:**
- **Manifest:** flat `manifest.json` (diffable, zero-dep; SQLite only if v2 brings
  concurrent writers — a `DerivativeStore` swap).
- **EXIF/metadata:** `pyexiv2` (in-process, wheels bundle libexiv2) for read +
  write; exiftool-subprocess kept as a fallback adapter behind the port.
- **`full` tier:** opt-in per build (`include_full`, default off).
- **Parallelism:** process pool over assets, `VIPS_CONCURRENCY=1` per worker.
- **Sidecar location:** separate `meta/` tree by default (source stays pristine);
  co-location beside originals configurable.
- **Read seam:** `SourceRef.path` is always a readable local handle; v2 lands
  uploads to a local staging tree before discovery rather than introducing a
  stream/object-store port. Landing is the adapter's job; reading is uniform.
- **Cache-state boundary:** `DerivativeStore.snapshot() -> StoreState` (manifest
  read + existence check) feeds the pure `diff_plan`; no per-key `is_current` I/O
  interleaves with planning.
- **Stat→hash memo owner:** the `Hasher` adapter, injected with a `.baffin/` memo
  handle — not a separate port.
- **Per-asset unit:** an `AssetProcessor` shell-side composite (not a port) is the
  process-pool submission unit; adapters must be picklable / worker-constructable.
- **Port DTO:** `MetadataReader` returns `RawMetadata` (raw read: dims/kind/EXIF),
  distinct from the authored `AssetMeta` sidecar.

**Deferred (not a blocker for v1):**
1. **v2 auth / multi-user** — explicitly not being decided now. When v2 is real,
   choose single-tenant (one deploy per person, share links) vs accounts; keeping
   the web layer a thin adapter preserves both options at zero cost today.
```
