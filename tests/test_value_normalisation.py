# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Cell values become the strings a CSV would have carried.

pain001 renders XML from whatever a loader returns, and its CSV loader
is :class:`csv.DictReader`, which yields strings. Returning a float
here is not a cosmetic difference: a cell displaying ``100.00`` is the
float ``100.0``, which stringifies to ``"100.0"`` and reaches the
``InstdAmt`` element as a different number of decimals than the CSV
path produces for the same spreadsheet.
"""

from __future__ import annotations

import datetime as dt
import pathlib

import pytest
from openpyxl import Workbook

from pain001_loader_xlsx._normalise import decimals_in, to_text
from pain001_loader_xlsx.loader import XlsxLoader


def _book(
    tmp_path: pathlib.Path,
    rows: list[list[object]],
    formats: dict[tuple[int, int], str] | None = None,
) -> str:
    """Write a single-sheet workbook and return its path."""
    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(row)
    for (r, c), fmt in (formats or {}).items():
        sheet.cell(row=r, column=c).number_format = fmt
    target = tmp_path / "book.xlsx"
    workbook.save(target)
    return str(target)


class TestNumberFormat:
    """The cell format is the only record of the intended precision."""

    @pytest.mark.parametrize(
        ("fmt", "expected"),
        [
            ("0.00", 2),
            ("#,##0.000", 3),
            ("0.00;[Red]-0.00", 2),
            ("General", None),
            ("@", None),
            ("", None),
            (None, None),
            ("0", None),
        ],
    )
    def test_decimals_are_read_from_the_format(
        self, fmt: str | None, expected: int | None
    ) -> None:
        """Only the positive-form section governs an ordinary value."""
        assert decimals_in(fmt) == expected

    @pytest.mark.parametrize(
        ("value", "fmt", "expected"),
        [
            ("already text", "@", "already text"),
            (None, None, ""),
            (True, None, "TRUE"),
            (False, None, "FALSE"),
            (100, "General", "100"),
            (100.0, "General", "100"),
            (100.5, "General", "100.5"),
            (100.0, "0.00", "100.00"),
            (100.456, "0.00", "100.46"),
            (1234.5, "#,##0.000", "1234.500"),
        ],
    )
    def test_cells_render_as_the_displayed_text(
        self, value: object, fmt: str | None, expected: str
    ) -> None:
        """Each row here is a shape real finance exports produce."""
        assert to_text(value, fmt) == expected

    def test_unexpected_types_still_produce_a_string(self) -> None:
        """A type openpyxl grows later must not leak a non-string out."""
        assert to_text(complex(1, 2), None) == "(1+2j)"


class TestLoadedValues:
    """The same guarantee, observed through the loader."""

    def test_amount_keeps_its_displayed_precision(
        self, tmp_path: pathlib.Path
    ) -> None:
        """`100.00` in Excel must not reach the XML as `100.0`."""
        book = _book(
            tmp_path,
            [["amount"], [100.0]],
            formats={(2, 1): "0.00"},
        )

        assert XlsxLoader().load(book).rows[0]["amount"] == "100.00"

    def test_every_value_is_a_string(self, tmp_path: pathlib.Path) -> None:
        """Matching csv.DictReader is the whole point."""
        book = _book(tmp_path, [["a", "b"], [1, "x"]])

        row = XlsxLoader().load(book).rows[0]

        assert all(isinstance(v, str) for v in row.values()), row


class TestTemporalCells:
    """Excel dates are refused rather than guessed at."""

    @pytest.mark.parametrize(
        "value",
        [
            dt.datetime(2026, 3, 1, 12, 0),
            dt.date(2026, 3, 1),
            dt.time(12, 0),
            dt.timedelta(days=1),
        ],
    )
    def test_temporal_cells_are_refused(
        self, value: object, tmp_path: pathlib.Path
    ) -> None:
        """The 1900 and 1904 epochs differ by four years."""
        book = _book(tmp_path, [["payment_date"], [value]])

        with pytest.raises(ValueError, match="ISO-8601"):
            XlsxLoader().load(book)

    def test_refusal_names_the_column_and_row(
        self, tmp_path: pathlib.Path
    ) -> None:
        """The user has to find the cell, so the message must locate it."""
        book = _book(
            tmp_path,
            [["id", "payment_date"], ["1", "2026-03-01"], ["2", dt.date(2026, 3, 1)]],
        )

        with pytest.raises(ValueError) as excinfo:
            XlsxLoader().load(book)

        message = str(excinfo.value)
        assert "'payment_date'" in message
        assert "row 3" in message
        assert "'Text'" in message

    def test_iso_dates_written_as_text_are_accepted(
        self, tmp_path: pathlib.Path
    ) -> None:
        """The documented workaround has to work."""
        book = _book(
            tmp_path,
            [["payment_date"], ["2026-03-01"]],
            formats={(2, 1): "@"},
        )

        row = XlsxLoader().load(book).rows[0]

        assert row["payment_date"] == "2026-03-01"
