# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The exact wording, row and column of every refusal, and what a cell yields.

Mutation testing showed the guards' messages were matched only by a
fragment: a mutant that named the wrong column, dropped the row number,
or reported the wrong cell type passed every test. An analyst fixing a
workbook reads that message; it has to be exact. The workbook-reading
options (cached values, read-only) are pinned the same way.
"""

from __future__ import annotations

import datetime as dt

import openpyxl
import pytest

from pain001_loader_xlsx import XlsxLoader
from pain001_loader_xlsx._normalise import decimals_in, to_text


def _workbook(tmp_path, name, rows, formats=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    for (r, c), fmt in (formats or {}).items():
        ws.cell(row=r, column=c).number_format = fmt
    path = tmp_path / name
    wb.save(path)
    return str(path)


class TestIbanGuard:
    """A numeric IBAN stops the load with the column, the value and the fix."""

    def test_message_is_exact(self, tmp_path):
        path = _workbook(
            tmp_path,
            "bad.xlsx",
            [["id", "creditor_account_IBAN"], ["MSG-1", 12345678]],
        )
        with pytest.raises(ValueError) as exc:
            XlsxLoader().load(path)
        assert str(exc.value) == (
            f"workbook {path!r} column 'creditor_account_IBAN' contains a "
            "numeric value (12345678) where an IBAN string is "
            "expected. Excel's 'General' cell format silently "
            "strips leading zeros from IBANs; re-type the column "
            "as 'Text' (in Excel: select the column, "
            "Format Cells -> Number -> Text) and re-export."
        )

    def test_a_float_iban_is_refused_too(self, tmp_path):
        path = _workbook(
            tmp_path,
            "bad.xlsx",
            [["id", "debtor_account_IBAN"], ["MSG-1", 1.5]],
        )
        with pytest.raises(ValueError, match=r"numeric value \(1\.5\)"):
            XlsxLoader().load(path)

    def test_the_header_match_is_case_insensitive(self, tmp_path):
        path = _workbook(
            tmp_path,
            "bad.xlsx",
            [["id", "Debtor_Account_IBAN"], ["MSG-1", 12345678]],
        )
        with pytest.raises(ValueError, match="column 'Debtor_Account_IBAN'"):
            XlsxLoader().load(path)

    def test_a_later_bad_row_is_still_refused(self, tmp_path):
        path = _workbook(
            tmp_path,
            "bad.xlsx",
            [
                ["id", "debtor_account_IBAN"],
                ["MSG-1", "DE89370400440532013000"],
                ["MSG-2", 42],
            ],
        )
        with pytest.raises(ValueError, match=r"numeric value \(42\)"):
            list(XlsxLoader().load_streaming(path, chunk_size=1))


class TestTemporalGuard:
    """A date-typed cell stops the load, naming column, row and cell type."""

    def test_message_is_exact_with_row_number_and_type(self, tmp_path):
        path = _workbook(
            tmp_path,
            "dates.xlsx",
            [
                ["id", "requested_execution_date"],
                ["MSG-1", "2026-09-19"],
                ["MSG-2", dt.datetime(2026, 9, 19, 9, 0)],
            ],
        )
        with pytest.raises(ValueError) as exc:
            XlsxLoader().load(path)
        assert str(exc.value) == (
            f"workbook {path!r} column 'requested_execution_date' row "
            "3 is an Excel "
            "datetime cell. Excel stores dates "
            "against a workbook epoch (the 1900 and 1904 systems "
            "differ by four years), which this loader will not "
            "guess at. Re-type the column as 'Text' (in Excel: "
            "select the column, Format Cells -> Number -> Text) "
            "and write dates as ISO-8601 (YYYY-MM-DD)."
        )

    @pytest.mark.parametrize(
        ("value", "type_name"),
        [
            # openpyxl reads a date cell back as a datetime.
            (dt.date(2026, 9, 19), "datetime"),
            (dt.time(9, 30), "time"),
            (dt.timedelta(days=1), "timedelta"),
        ],
    )
    def test_every_temporal_type_is_named(self, tmp_path, value, type_name):
        path = _workbook(tmp_path, "t.xlsx", [["id", "when"], ["MSG-1", value]])
        with pytest.raises(
            ValueError, match=f"row 2 is an Excel {type_name} cell"
        ):
            XlsxLoader().load(path)

    def test_a_cell_under_an_empty_header_is_named_by_that_header(
        self, tmp_path
    ):
        # openpyxl pads the header row to the widest row, so the unnamed
        # column reads as '' rather than falling back to its index.
        path = _workbook(
            tmp_path,
            "wide.xlsx",
            [["id"], ["MSG-1", dt.date(2026, 9, 19)]],
        )
        with pytest.raises(
            ValueError, match="column '' row 2 is an Excel datetime cell"
        ):
            XlsxLoader().load(path)


class TestReadingOptions:
    """Formulas resolve to their cached value; the workbook is read, not run."""

    def test_a_formula_cell_yields_its_cached_value_not_the_formula(
        self, tmp_path
    ):
        path = _workbook(
            tmp_path,
            "formula.xlsx",
            [["id", "amount"], ["MSG-1", "=1+1"]],
        )
        result = XlsxLoader().load(path)
        # openpyxl writes no cached value, so data_only yields None -> "".
        # A loader that read the formula text would yield "=1+1".
        assert result.rows == [{"id": "MSG-1", "amount": ""}]

    def test_rows_are_text_keyed_by_the_header_in_order(self, tmp_path):
        path = _workbook(
            tmp_path,
            "ok.xlsx",
            [["id", "amount", "note"], ["MSG-1", 100, None]],
        )
        result = XlsxLoader().load(path)
        assert result.rows == [{"id": "MSG-1", "amount": "100", "note": ""}]
        assert result.source_hint == path

    def test_streaming_chunks_have_the_requested_size(self, tmp_path):
        rows = [["id"]] + [[f"MSG-{i}"] for i in range(5)]
        path = _workbook(tmp_path, "many.xlsx", rows)
        chunks = list(XlsxLoader().load_streaming(path, chunk_size=2))
        assert [len(c.rows) for c in chunks] == [2, 2, 1]
        assert chunks[0].rows[0] == {"id": "MSG-0"}
        assert chunks[2].rows[0] == {"id": "MSG-4"}


class TestNumberFormats:
    """Decimal places come from the first section of the format only."""

    @pytest.mark.parametrize(
        ("fmt", "expected"),
        [
            ("0.00;[Red]-0.00", 2),
            ("0.0;0.000", 1),
            ("#,##0.000;(#,##0.000)", 3),
            ("0", None),
            ("General", None),
            (None, None),
        ],
    )
    def test_decimals_in(self, fmt, expected):
        assert decimals_in(fmt) == expected

    def test_a_pinned_format_renders_trailing_zeros(self):
        assert to_text(1.1, "0.00") == "1.10"
        assert to_text(1.1, "General") == "1.1"
