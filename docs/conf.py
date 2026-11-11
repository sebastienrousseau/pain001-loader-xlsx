# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Sphinx configuration for pain001-loader-xlsx documentation."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from markupsafe import Markup

project = "pain001-loader-xlsx"
author = "Sebastien Rousseau"
copyright = "2023-2026 Sebastien Rousseau"
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

# `make linkcheck` and the docs.yml linkcheck job. GitHub renders heading
# anchors client-side (user-content-*), so linkcheck cannot see them.
linkcheck_anchors_ignore_for_url = [r"https://github\.com/.*"]
linkcheck_retries = 3
linkcheck_timeout = 30


def _link_author(
    app: Any,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
) -> None:
    """Link the author's name in every page footer.

    The theme escapes ``copyright``; a ``Markup`` value passes through
    unchanged, so the HTML footer carries the link and every other
    builder keeps the plain text above.
    """
    context["copyright"] = Markup(
        '2023-2026 <a href="https://sebastienrousseau.com/" rel="author">'
        "Sebastien Rousseau</a>"
    )


def setup(app: Any) -> None:
    """Register the footer hook."""
    app.connect("html-page-context", _link_author)
