# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Keep the README canonical and its runnable claims true.

The README is rendered from ``docs/readme-template.md`` and
``docs/readme-values.json``; these tests hold the result to the
portfolio's canonical section order, refuse unresolved ``{{TOKEN}}``
placeholders and dangling repository links, and execute the Quick Start
verbatim, so a change to the pain001 CLI or to this loader's entry point
fails here rather than in a reader's terminal.
"""

from __future__ import annotations

import csv
import importlib.resources
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

# The second-level headings of ~/Code/README-TEMPLATE.md, in order.
CANONICAL_SECTIONS = [
    "Contents",
    "Install",
    "Requirements",
    "Quick Start",
    "The pain001-loader-xlsx ecosystem",
    "Capabilities at a glance",
    "Ecosystem comparison",
    "Benchmarks",
    "Features",
    "Configuration",
    "Examples",
    "When not to use pain001-loader-xlsx",
    "Development",
    "Security",
    "Documentation",
    "Stability guarantees",
    "License",
]


def _rendered_readme() -> str:
    """Render the README with ``scripts/render_readme.py``."""
    path = ROOT / "scripts" / "render_readme.py"
    spec = importlib.util.spec_from_file_location("render_readme", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rendered: str = module.render()
    return rendered


def _section(title: str) -> str:
    """Return the body of the ``## title`` section of the README."""
    return README.split(f"\n## {title}\n", 1)[1].split("\n---", 1)[0]


def _quick_start_commands() -> list[list[str]]:
    """Return each Quick Start command, split into words."""
    block = re.search(r"```bash\n(.*?)\n```", _section("Quick Start"), re.S)
    assert block is not None, "Quick Start has no bash block"
    return [line.split() for line in block[1].splitlines()]


def _write_template_workbook(path: Path) -> None:
    """Write core's pain.001.001.03 sample rows into an .xlsx at ``path``.

    The README tells the reader to supply a workbook with core's
    template column names; this builds that workbook from the template
    CSV the installed core ships, so the test tracks core's columns.
    """
    template = (
        importlib.resources.files("pain001")
        / "templates"
        / "pain.001.001.03"
        / "template.csv"
    )
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in csv.reader(template.read_text(encoding="utf-8").splitlines()):
        sheet.append(row)
    workbook.save(path)


def test_quick_start_runs_verbatim(tmp_path: Path) -> None:
    """Every Quick Start command succeeds and produces XML."""
    _write_template_workbook(tmp_path / "payments.xlsx")
    outputs = []
    for words in _quick_start_commands():
        assert words[0] == "pain001", words
        result = subprocess.run(
            [sys.executable, "-m", "pain001", *words[1:]],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(result.stdout)
    loaders = json.loads(outputs[0])
    assert "xlsx" in {entry["name"] for entry in loaders}
    assert list((tmp_path / "output").glob("*.xml"))


def test_readme_matches_its_sources() -> None:
    """The committed README is exactly what the renderer produces."""
    assert _rendered_readme() == README


def test_readme_has_no_unresolved_tokens() -> None:
    """Every template placeholder was filled from readme-values.json."""
    assert not re.findall(r"\{\{[A-Z_]+\}\}", README)


def test_readme_sections_follow_the_canonical_order() -> None:
    """The README keeps the canonical headings, in order, and no others."""
    assert re.findall(r"^## (.+)$", README, re.M) == CANONICAL_SECTIONS


def test_readme_repository_links_resolve() -> None:
    """Every relative link and image in the README points at a file."""
    targets = re.findall(r"\]\(([^)]+)\)", README)
    targets += re.findall(r'(?:src|href)="([^"]+)"', README)
    local = [t for t in targets if "://" not in t and not t.startswith("#")]
    assert local
    missing = [t for t in local if not (ROOT / t.split("#")[0]).exists()]
    assert not missing, missing
