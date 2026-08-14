.PHONY: check build serve clean docs e2e

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

# Placeholders wired up in later phases (CLI).
build:
	@echo "build: not implemented yet"

serve:
	@echo "serve: not implemented yet"

clean:
	@echo "clean: not implemented yet"

docs:
	uv run --group docs sphinx-build -b doctest -W --keep-going docs docs/_build/doctest
	uv run --group docs sphinx-build -b html -W --keep-going docs docs/_build/html
