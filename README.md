# baffin

Point it at a folder of camera originals; get a chronological static gallery you
can share as a link. It never edits your photos, and needs no curation.

**[Documentation](https://monkeypants.github.io/baffin-goggles/)**

```sh
uv sync
uv run baffin doctor
uv run baffin build --source photos --output site
```

Native prerequisites (libvips, ffmpeg, and inih on macOS) and the full
walkthrough are in the **Getting started** chapter of the docs.

## Docs

The docs are the specification, generated from the code and its test suite.
They are published from `master` to
<https://monkeypants.github.io/baffin-goggles/> by the `Docs` workflow, built
with the same pinned toolchain as the tests.

To build them locally:

```sh
make docs   # then open docs/_build/html/index.html
```

They cover getting started, the architecture, and how to contribute. Start at
`index.html`; `AGENTS.md` is the quick orientation for coding agents.

## Develop

```sh
make check   # ruff + format + import-linter + mypy + pytest + doctests
make up      # serve the gallery as a login agent (survives crash + reboot)
```
