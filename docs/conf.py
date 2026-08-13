"""Sphinx configuration for baffin's docs.

The docs are literate and test-driven: AutoAPI renders code and tests, Napoleon
reads the docstrings, and the doctest builder runs the examples embedded in the
functional core.
"""

from __future__ import annotations

project = "baffin"
author = "Chris Gough"

extensions = [
    "autoapi.extension",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinxcontrib.plantuml",
]

# --- AutoAPI: document both the package and the tests (the executable spec) ---
autoapi_dirs = ["../baffin", "../tests"]
autoapi_type = "python"
autoapi_root = "reference"
autoapi_keep_files = False
autoapi_add_toctree_entry = True
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_python_class_content = "both"
autodoc_typehints = "description"

# --- Theme ---
html_theme = "furo"
html_title = "baffin"

# --- PlantUML (diagrams render into the build; requires plantuml on PATH) ---
plantuml = "plantuml"
plantuml_output_format = "svg"

# --- Nitpicky: every cross-reference must resolve ---
nitpicky = True
# External libraries (pydantic, PIL, typer, stdlib, …) are not our concern.
nitpick_ignore_regex = [
    ("py:.*", r"^(?!baffin\.).+"),
    # Domain types are re-exported from baffin.domain but AutoAPI documents them
    # at their definition site (baffin.domain.models); ignore the re-export path.
    ("py:class", r"^baffin\.domain\.[A-Z]\w+$"),
]
# Module-level Literal aliases: AutoAPI emits them as py:data, annotations
# reference them as py:class. Ignore the four canonical aliases.
nitpick_ignore = [
    ("py:class", "baffin.domain.models.AssetKind"),
    ("py:class", "baffin.domain.models.SpecName"),
    ("py:class", "baffin.application.grouping.GroupMode"),
    ("py:class", "baffin.application.grouping.Order"),
]
