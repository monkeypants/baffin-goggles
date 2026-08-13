# AGENTS.md

Orientation for coding agents. Tool-neutral; assumes no particular assistant.

## What this is

`baffin` is a raw-dump static photo-gallery generator: point it at camera
originals, get a chronological static site. Clean architecture, functional core /
imperative shell. The full narrative is in `docs/`: build it with `make docs`
and open `docs/_build/html/index.html`. Start with `architecture` and
`contributing`.

## The one gate

Every change must pass, before it is pushed:

```sh
make check     # ruff check · ruff format --check · lint-imports · mypy --strict · pytest + doctests
```

Also build the docs when you touch a docstring, a public signature, a
module-level type alias, or anything under `docs/`:

```sh
make docs      # sphinx-build -W (doctest + html); warnings are errors
```

Do not push, and do not consider a task done, on a red `make check`. Report
failures with their output rather than working around them.

## The dependency rule

Dependencies point inward only:

```
interface → adapters → application → domain
```

The domain imports nothing outward. `lint-imports` (an `import-linter` contract)
enforces this, so a violation fails `make check`. Keep the core (`domain`,
`application`) free of I/O and frameworks; all filesystem/pyvips/ffmpeg/HTTP work
lives in `adapters`.

## Where things live

```
baffin/
  domain/        frozen dataclasses + the content-hash cache key
  application/   pure core (grouping, planning, urls, diff), ports, use cases
  adapters/      the imperative shell (hashing, exif, thumbnails, store, render)
  interface/cli/ the Typer surface
  testing/       in-memory fakes + builders (shipped so mypy checks them)
tests/           mirrors baffin/; the specification
docs/            reStructuredText chapters + AutoAPI reference
```

Ports are `typing.Protocol`s in `application/ports.py`; each has a real adapter
and an in-memory fake in `baffin/testing/fakes.py`. Test doubles must never be
imported by production code; a forbidden-import contract enforces it.

## Conventions

- **Commits:** Linux-kernel style. Imperative summary (~50 chars), blank line,
  a body that says *why* when it isn't obvious. No conventional-commit prefixes
  (`feat:`/`fix:`). No AI attribution; the author is accountable.
- **Branches:** feature branches with plain descriptive names. Never commit
  directly to `master`.
- **New native dependency:** update `docs/getting-started.rst` and the CI install
  step, not just `pyproject.toml`.

## Gotchas

- The derivative cache key is a **SHA-256** over the content hash plus the spec
  (not the salted builtin `hash`); it must be stable across runs and machines.
- Parallel generation runs a process pool with `VIPS_CONCURRENCY=1` per worker.
- Native prerequisites: **libvips**, **ffmpeg**, and on macOS **inih** (for the
  `pyexiv2` dylib). `baffin doctor` checks the first two.
