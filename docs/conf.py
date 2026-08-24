"""Sphinx configuration for baffin's docs.

The docs are literate and test-driven:
AutoAPI renders the code and tests,
and the doctest builder runs the examples embedded in the functional core.
"""

from __future__ import annotations

project = "Baffin Goggles"
author = "Chris Gough"

extensions = [
    "autoapi.extension",
    "sphinx.ext.doctest",
    "sphinxcontrib.plantuml",
]

# --- AutoAPI: document both the package and the tests (the executable spec) ---
autoapi_dirs = ["../baffin", "../tests"]
autoapi_type = "python"
autoapi_root = "reference"
autoapi_keep_files = False
# We curate the reference landing (docs/reference.rst) instead of AutoAPI's flat
# alphabetical index: the package is presented by layer, the test suite under its
# own caption. So suppress the auto toctree entry and exclude the generated flat
# index from the build (it would otherwise be an orphan under -W, and would drag
# the phone-book listing back into the sidebar).
autoapi_add_toctree_entry = False
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_python_class_content = "both"
autodoc_typehints = "description"
# Don't inline a base class's docstring into an undocumented subclass: our
# pydantic models would otherwise dump pydantic's BaseModel docstring (Google
# "Attributes:" sections + Markdown) into the reference. With Napoleon gone,
# that raw text no longer parses cleanly; and it was never our content to show.
autodoc_inherit_docstrings = False

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "reference/index.rst"]

# --- Theme ---
html_theme = "furo"
html_title = "Baffin Goggles"

# Where the built docs live, so canonical links resolve to the published site
# rather than to whatever host served the page (see the Docs workflow).
html_baseurl = "https://monkeypants.github.io/baffin-goggles/"

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
