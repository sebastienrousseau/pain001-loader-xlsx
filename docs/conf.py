"""Sphinx configuration for pain001-loader-xlsx documentation."""

from __future__ import annotations

import importlib.metadata

project = "pain001-loader-xlsx"
author = "Sebastien Rousseau"
copyright = "2023-2026, Sebastien Rousseau"
try:
    release = importlib.metadata.version("pain001-loader-xlsx")
except importlib.metadata.PackageNotFoundError:
    release = "0.0.0+dev"
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "readme-template.md"]
# The README is included as a page: its repository-relative links,
# diagram fences and heading levels are right for GitHub, not for Sphinx.
suppress_warnings = [
    "myst.xref_missing",
    "myst.header",
    "misc.highlighting_failure",
]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
html_theme = "furo"
html_title = f"pain001-loader-xlsx {release}"
autodoc_member_order = "bysource"
autodoc_typehints = "description"
