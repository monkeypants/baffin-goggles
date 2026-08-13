# baffin

Point it at a folder of camera originals; get a chronological static gallery you
can share as a link. It never edits your photos, and needs no curation.

See the docs for the full design — `make docs`, then open
`docs/_build/html/index.html`. The tests are the executable specification.

## System dependencies

baffin leans on a few native libraries that aren't Python packages. Install
them before `uv sync`.

### macOS (Homebrew)

```sh
brew install vips ffmpeg inih
brew install plantuml   # only to build the docs
```

- **vips** (libvips) — the default `pyvips` thumbnailer. Without it, only the
  Pillow fallback works.
- **ffmpeg** — video poster frames and clip copies. Must be on `PATH`.
- **inih** — provides `libINIReader`, which the `pyexiv2` wheel's bundled
  `libexiv2` links against on macOS. Without it, `import pyexiv2` fails to load
  its dylib.
- **plantuml** — renders the architecture diagrams (pulls a JRE + graphviz).
  Only needed for `make docs`.

### Linux (Debian/Ubuntu)

```sh
sudo apt-get install -y libvips-dev ffmpeg plantuml
```

The `pyexiv2` manylinux wheel bundles its own libraries, so no `inih` equivalent
is needed. This is what CI installs.

## Quickstart

```sh
uv sync                                   # create the environment
uv run baffin doctor                      # check libvips/ffmpeg + config
uv run baffin build --source photos --output site
uv run baffin serve --source photos --output site --watch
```

`build` is lazy: a second run regenerates nothing, and editing a template
rewrites zero image bytes. `serve --watch` re-renders templates on change
without touching images. Per-image captions are optional:

```sh
uv run baffin meta set photos/2025/DSC1.JPG --title "River crossing" --credit "Chris"
```

## Commands

| Command | Purpose |
|---------|---------|
| `baffin build`  | Lazy build. `--source --output --full --force --jobs`. |
| `baffin scan`   | Dry run: assets, groups, and the HIT/MISS plan. |
| `baffin serve`  | Build then serve locally; `--watch` re-renders templates. |
| `baffin clean`  | Prune orphaned derivatives; `--all` wipes the cache. |
| `baffin meta`   | Read/write per-image sidecars: `show` / `edit` / `set`. |
| `baffin doctor` | Check libvips/ffmpeg and the resolved config. |

## Configuration — `baffin.toml`

Resolution order: CLI flag > env var (`BAFFIN_*`) > `baffin.toml` > default.

```toml
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
```

## Development

```sh
make check       # ruff + format + import-linter + mypy + pytest + doctests
make docs        # sphinx-build -W (doctest + html)
```
