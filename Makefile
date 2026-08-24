.PHONY: check build serve clean docs e2e up down status

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
	uv run --group e2e pytest -m browser -q

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
