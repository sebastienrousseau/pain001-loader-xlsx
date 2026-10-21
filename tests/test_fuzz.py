# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The fuzz corpus replays as a regression suite, without Atheris.

``fuzz/fuzz_load_xlsx.py`` holds the loader to one contract: every text
cell comes back as the text Excel stores for it, or ``ValueError`` when
XML cannot carry it. Atheris only runs on Linux x86_64 in CI; the
committed corpus runs here on every platform, and the harness is shown
to catch the bug its regression files record.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
CORPUS = sorted((ROOT / "fuzz" / "corpus").iterdir())


@pytest.fixture(scope="module")
def harness() -> ModuleType:
    """The harness module, loaded from its file."""
    spec = importlib.util.spec_from_file_location(
        "fuzz_load_xlsx", ROOT / "fuzz" / "fuzz_load_xlsx.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", CORPUS, ids=[p.name for p in CORPUS])
def test_corpus_holds_the_contract(harness: ModuleType, seed: Path) -> None:
    """Every committed input passes the harness's own checks."""
    harness.test_one_input(seed.read_bytes())


def test_the_escape_matches_excel(harness: ModuleType) -> None:
    """The oracle stores text the way ECMA-376 says Excel does."""
    assert harness.ooxml_escape("a\r\nb") == "a_x000D_\nb"
    assert harness.ooxml_escape("_x0041_") == "_x005F_x0041_"
    assert harness.ooxml_escape("bell\x07") == "bell_x0007_"


def test_the_harness_catches_undecoded_escapes(
    harness: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With decoding switched off, as before 0.0.74, the oracle fails."""
    monkeypatch.setattr(
        "pain001_loader_xlsx._normalise.decode_escapes", lambda text: text
    )
    with pytest.raises(AssertionError, match="x000D"):
        harness.test_one_input(b"Line1\r\nLine2")


def test_the_harness_catches_an_unrefused_character(
    harness: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the guard switched off, the oracle fails."""
    monkeypatch.setattr(
        "pain001_loader_xlsx.loader.XlsxLoader._guard_text_cells",
        lambda *args: None,
    )
    with pytest.raises(AssertionError, match="not refused"):
        harness.test_one_input(b"ACME\x07Ltd")
