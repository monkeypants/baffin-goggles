.PHONY: check build serve clean docs e2e e2e-tests up down status image check-docker build-docker

# Port for `serve` and the login agent; override with `make serve PORT=8000`.
PORT ?= 8753
# Extra CLI flags, e.g. `make build ARGS="--full --jobs 8"`.
ARGS ?=

# Unified quality gate: lint, format, architecture, types, tests.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports
	uv run mypy
	uv run pytest -m "not manual and not wip and not browser"
	uv run pytest --doctest-modules baffin -q

# End-to-end browser tests (Playwright). Kept out of `check` — they need a
# browser binary and are slower. Run explicitly.
e2e:
	uv run --group e2e python -m playwright install chromium
	$(MAKE) e2e-tests

# Collect only tests/e2e. The `browser` marker deselects the rest, but pytest
# imports every module before it deselects anything, and tests/adapters imports
# pyvips — so a wider collection needs libvips present just to throw it away.
# CI runs this target directly, after installing the browser with --with-deps,
# so the command cannot drift from the one used here.
e2e-tests:
	uv run --group e2e pytest tests/e2e -m browser -q

# Source and output come from baffin.toml (or BAFFIN_* / the defaults); pass
# anything else through ARGS.
build:
	uv run baffin build $(ARGS)

# Foreground: dies with the terminal. For a gallery that outlives the shell and
# comes back after a reboot, use `make up`.
serve:
	uv run baffin serve --port $(PORT) $(ARGS)

clean:
	uv run baffin clean $(ARGS)

# --- Pinned toolchain (see Dockerfile) -------------------------------------
#
# The host's libvips decides what a derivative looks like, but the cache key
# does not include it. These targets run the same work against one pinned
# libvips/ffmpeg, which is what CI uses too.

IMAGE ?= baffin-builder
DOCKER_RUN = docker run --rm --user "$$(id -u):$$(id -g)" \
	-v "$(CURDIR):/work" -w /work $(IMAGE)

image:
	docker build -t $(IMAGE) .

# The gate, on the pinned toolchain instead of whatever this machine has.
check-docker: image
	$(DOCKER_RUN) make check

# Build a gallery with the pinned libvips, so its bytes match CI's. SOURCE is
# mounted read-only: baffin never writes to originals, and the mount enforces
# it. BAFFIN_* env beats baffin.toml, so the container's paths win.
build-docker: image
	@test -n "$(SOURCE)" || { echo "set SOURCE=/path/to/originals" >&2; exit 64; }
	@test -n "$(OUTPUT)" || { echo "set OUTPUT=/path/to/site" >&2; exit 64; }
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-v "$(CURDIR):/work" -w /work \
		-v "$(SOURCE):/photos:ro" -v "$(OUTPUT):/site" \
		-e BAFFIN_SOURCE=/photos -e BAFFIN_OUTPUT=/site \
		$(IMAGE) make build ARGS="$(ARGS)"

# Run the gallery as a login agent: restarted if it crashes, back after a
# reboot. `make status` reports it, `make down` removes it.
up:
	./scripts/gallery-agent install $(PORT)

down:
	./scripts/gallery-agent uninstall

status:
	./scripts/gallery-agent status

docs:
	uv run --group docs sphinx-build -b doctest -W --keep-going docs docs/_build/doctest
	uv run --group docs sphinx-build -b html -W --keep-going docs docs/_build/html
