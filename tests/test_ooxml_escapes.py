# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Cell text carries what Excel displays, not OOXML's escape sequences.

XML 1.0 cannot hold most control characters, and an XML parser folds a
raw carriage return into a line feed, so OOXML stores them as
``_xHHHH_`` (ECMA-376 Part 1, ST_Xstring) and writes a literal
``_xHHHH_`` typed by the user as ``_x005F_xHHHH_``. Excel shows the
decoded text. openpyxl hands the escapes back undecoded, so before
0.0.74 a cell holding ``Line1`` CR LF ``Line2`` reached the payment as
``Line1_x000D_`` LF ``Line2``, and a control character reached it as
six characters of escape text, where the CSV export of the same sheet
carries the real characters.
"""

from __future__ import annotations

import csv
import pathlib

import openpyxl
import pytest
from pain001.constants import TEMPLATES_DIR
from pain001.data.loader import load_payment_data
from pain001.plugins.registry import registry
from pain001.xml.generate_xml import generate_xml_string

from pain001_loader_xlsx._normalise import to_text
from pain001_loader_xlsx.loader import XlsxLoader


def _book(tmp_path: pathlib.Path, rows: list[list[object]]) -> str:
    """Write rows verbatim; openpyxl does not escape what it writes."""
    workbook = openpyxl.Workbook()
    for row in rows:
        workbook.active.append(row)
    target = tmp_path / "book.xlsx"
    workbook.save(target)
    workbook.close()
    return str(target)


class TestDecoding:
    """Escapes decode to the characters Excel displays."""

    @pytest.mark.parametrize(
        ("stored", "displayed"),
        [
            ("Line1_x000D_\nLine2", "Line1\r\nLine2"),
            ("Line1_x000d_\nLine2", "Line1\r\nLine2"),
            ("Tab_x0009_here", "Tab\there"),
            ("_x005F_x0041_", "_x0041_"),
            ("_xD83D__xDE00_", "\U0001f600"),
            ("ACME_x005f_x000D_Ltd", "ACME_x000D_Ltd"),
            ("no escape at all", "no escape at all"),
            ("_x41_ is not one", "_x41_ is not one"),
        ],
    )
    def test_to_text_decodes_st_xstring(
        self, stored: str, displayed: str
    ) -> None:
        """The ECMA-376 rule, including the escaped underscore."""
        assert to_text(stored, None) == displayed

    def test_the_loader_returns_the_displayed_text(
        self, tmp_path: pathlib.Path
    ) -> None:
        """A multi-line address cell keeps its carriage return."""
        book = _book(tmp_path, [["id", "note"], ["1", "Line1_x000D_\nLine2"]])

        row = XlsxLoader().load(book).rows[0]

        assert row["note"] == "Line1\r\nLine2"


class TestRefusal:
    """A character no XML payment can carry is refused, and located."""

    @pytest.mark.parametrize(
        ("stored", "code_point"),
        [
            ("ACME_x0007_Ltd", "U+0007"),
            ("_x000B_", "U+000B"),
            ("half_xD800_", "U+D800"),
            ("_xFFFE_", "U+FFFE"),
        ],
    )
    def test_an_escaped_illegal_character_is_refused(
        self, tmp_path: pathlib.Path, stored: str, code_point: str
    ) -> None:
        """Before 0.0.74 the escape text itself reached the payment."""
        book = _book(
            tmp_path,
            [["id", "creditor_name"], ["1", "ok"], ["2", stored]],
        )

        with pytest.raises(ValueError) as excinfo:
            XlsxLoader().load(book)

        message = str(excinfo.value)
        assert "column 'creditor_name' row 3" in message
        assert code_point in message

    def test_the_refusal_reads_in_full(self, tmp_path: pathlib.Path) -> None:
        """The whole message, after a numeric cell the guard must skip."""
        book = _book(
            tmp_path, [["amount", "creditor_name"], [100, "ACME_x0007_Ltd"]]
        )

        with pytest.raises(ValueError) as excinfo:
            XlsxLoader().load(book)

        assert str(excinfo.value) == (
            f"workbook {book!r} column 'creditor_name' row 2 holds the "
            "character U+0007, which XML cannot carry, so no payment "
            "message can include it. It is usually pasted in invisibly: "
            "retype the cell and re-save."
        )

    def test_rows_before_a_refusal_still_stream(
        self, tmp_path: pathlib.Path
    ) -> None:
        """Rows before the bad one still stream before the refusal."""
        book = _book(tmp_path, [["n"], ["fine"], ["bad_x0001_"]])
        chunks = XlsxLoader().load_streaming(book, chunk_size=1)

        assert next(iter(chunks)).rows == [{"n": "fine"}]
        with pytest.raises(ValueError, match="U\\+0001"):
            list(chunks)


def test_a_carriage_return_renders_as_the_csv_does(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The acceptance criterion: same rows, same XML bytes as the CSV."""
    assets = TEMPLATES_DIR / "pain.001.001.03"
    with (assets / "template.csv").open(newline="", encoding="utf-8") as fh:
        records = list(csv.reader(fh))
    column = records[0].index("remittance_information")
    as_csv = [list(r) for r in records]
    as_csv[1][column] = "Invoice 1\r\nInvoice 2"
    as_xlsx = [list(r) for r in records]
    as_xlsx[1][column] = "Invoice 1_x000D_\nInvoice 2"
    xlsx = _book(tmp_path, as_xlsx)
    equivalent = tmp_path / "payments.csv"
    with equivalent.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(as_csv)
    monkeypatch.chdir(tmp_path)
    registry.reset()

    rows_csv = load_payment_data(str(equivalent))
    rows_xlsx = load_payment_data(xlsx)

    assert rows_xlsx == rows_csv
    args = (
        "pain.001.001.03",
        str(assets / "template.xml"),
        str(assets / "pain.001.001.03.xsd"),
    )
    assert generate_xml_string(rows_xlsx, *args) == generate_xml_string(
        rows_csv, *args
    )
