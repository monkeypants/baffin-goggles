.PHONY: check build serve clean

# Unified quality gate: lint, format, architecture, types, tests.
check:
	uv run ruff check .
	uv run ruff format --check .
	uv run lint-imports
	uv run mypy
	uv run pytest -m "not manual and not wip"

# Placeholders wired up in later phases (CLI).
build:
	@echo "build: not implemented yet"

serve:
	@echo "serve: not implemented yet"

clean:
	@echo "clean: not implemented yet"
