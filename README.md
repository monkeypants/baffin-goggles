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
```

- **vips** (libvips) — the default `pyvips` thumbnailer. Without it, only the
  Pillow fallback works.
- **ffmpeg** — video poster frames and clip copies. Must be on `PATH`.
- **inih** — provides `libINIReader`, which the `pyexiv2` wheel's bundled
  `libexiv2` links against on macOS. Without it, `import pyexiv2` fails to load
  its dylib.

### Linux (Debian/Ubuntu)

```sh
sudo apt-get install -y libvips-dev ffmpeg
```

The `pyexiv2` manylinux wheel bundles its own libraries, so no `inih` equivalent
is needed. This is what CI installs.

## Development

```sh
uv sync          # create the environment
make check       # ruff + format + import-linter + mypy + pytest
```
