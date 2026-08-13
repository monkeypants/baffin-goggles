"""Test-support package: in-memory port fakes.

Shipped so mypy checks the fakes against the Protocols, but fenced off from
production code by an import-linter forbidden contract; nothing under
domain/application/adapters/interface may import ``baffin.testing``.
"""
