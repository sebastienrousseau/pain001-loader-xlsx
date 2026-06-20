# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Run every script in ``examples/`` and require a zero exit code.

Keeps the example suite honest: if the loader API or the pain001
plugin contract shifts under our feet, the matching example fails
loudly in CI instead of silently rotting on disk.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((REPO_ROOT / "examples").glob("[0-9]*.py"))


def test_examples_discovered() -> None:
    """The glob must find every example (guards against renames)."""
    assert len(EXAMPLES) >= 2, EXAMPLES


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.name)
def test_example_runs_cleanly(example: Path) -> None:
    """Each example exits 0 when run from the repository root."""
    result = subprocess.run(
        [sys.executable, str(example)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, (
        f"{example.name} failed with exit code {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
