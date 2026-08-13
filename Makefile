.PHONY: check build serve clean docs

# Unified quality gate: lint, format, architecture, types, tests.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports
	uv run mypy
	uv run pytest -m "not manual and not wip"
	uv run pytest --doctest-modules baffin -q

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
