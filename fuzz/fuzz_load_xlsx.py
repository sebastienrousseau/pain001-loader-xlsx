# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of ``XlsxLoader`` text cells with Atheris.

Each input is a small sheet: its bytes decode (UTF-8, with undecodable
bytes kept as lone surrogates) into rows split on U+001D and cells split
on U+001E. Every cell is written the way Excel stores text: characters
XML cannot hold, and the carriage return, as ``_xHHHH_``, and a literal
``_xHHHH_`` with its underscore escaped as ``_x005F_``. The sheet is
saved with openpyxl and read back through ``XlsxLoader.load``.

The contract: when every cell's text is something XML 1.0 can carry,
each one comes back as that exact text, a leading ``=``, ``+``, ``-``
or ``@`` included; when any is not, ``ValueError`` is raised. Any
other exception, or a value that differs, is a crash libFuzzer reports
and minimises. ``tests/test_fuzz.py`` replays ``fuzz/corpus/`` through
the same function without Atheris, so the corpus is a regression suite
on every platform.

Run (Linux x86_64, Python 3.12 to 3.14)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_load_xlsx.py fuzz/corpus -max_total_time=60
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import openpyxl

ROWS, CELLS = "\x1d", "\x1e"
MAX_ROWS, MAX_CELLS = 8, 6

#: A complete escape, as the decoder reads it.
_ESCAPE = re.compile(r"_x[0-9A-Fa-f]{4}_")
#: What Excel escapes: XML-illegal characters, plus the carriage return.
_STORED_ESCAPED = re.compile(
    "[\x00-\x08\x0b\x0c\x0d\x0e-\x1f\ud800-\udfff\ufffe\uffff]"
)
_WORKDIR = Path(tempfile.mkdtemp(prefix="fuzz-xlsx-"))


def ooxml_escape(text: str) -> str:
    """Encode ``text`` as ECMA-376 ST_Xstring, the way Excel stores it.

    A literal underscore is escaped when the *stored* text would read as
    an escape from it, which can depend on an escape written after it:
    ``_x005F`` followed by U+DC9A stores as ``_x005F`` then ``_xDC9A_``,
    and the decoder would take ``_x005F_`` first. Escaping an underscore
    never changes whether another one matches, so one pass decides all.
    """
    parts = [
        f"_x{ord(c):04X}_" if _STORED_ESCAPED.match(c) else c for c in text
    ]
    stored = "".join(parts)
    offset = 0
    for i, part in enumerate(parts):
        if part == "_" and _ESCAPE.match(stored, offset):
            parts[i] = "_x005F_"
        offset += len(part)
    return "".join(parts)


def sheet(data: bytes) -> list[list[str]]:
    """The rows of text this input encodes."""
    text = data.decode("utf-8", "surrogateescape")
    rows = [row.split(CELLS)[:MAX_CELLS] for row in text.split(ROWS)]
    return rows[:MAX_ROWS]


def _write(rows: list[list[str]]) -> str:
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    width = max(len(row) for row in rows)
    worksheet.append([f"c{i}" for i in range(width)])
    for r, row in enumerate(rows, start=2):
        for c, text in enumerate(row, start=1):
            cell = worksheet.cell(row=r, column=c, value=ooxml_escape(text))
            cell.data_type = "s"  # never a formula, whatever it starts with
    target = _WORKDIR / "fuzz.xlsx"
    workbook.save(target)
    workbook.close()
    return str(target)


def test_one_input(data: bytes) -> None:
    """Write one sheet, load it, and hold the result to the contract."""
    # Imported here so main() can import the package instrumented first.
    from pain001_loader_xlsx._normalise import not_xml
    from pain001_loader_xlsx.loader import XlsxLoader

    rows = sheet(data)
    path = _write(rows)
    legal = all(not_xml(text) is None for row in rows for text in row)
    try:
        loaded = XlsxLoader().load(path).rows
    except ValueError:
        if legal:
            raise
        return
    if not legal:
        raise AssertionError("a cell XML cannot carry was not refused")
    for row, record in zip(rows, loaded, strict=False):
        for c, text in enumerate(row):
            got = record.get(f"c{c}", "")
            if got != text:
                raise AssertionError(f"cell c{c}: {got!r} != {text!r}")


def main() -> None:  # pragma: no cover - needs Atheris (Linux x86_64)
    """Hand the harness to libFuzzer."""
    import atheris

    # Only the package is instrumented: instrumenting openpyxl and the
    # pain001 core as well costs more time than the coverage it buys.
    with atheris.instrument_imports(include=["pain001_loader_xlsx"]):
        import pain001_loader_xlsx.loader  # noqa: F401
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":  # pragma: no cover
    main()
