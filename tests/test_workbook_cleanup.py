# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Rejected spreadsheets must not leak their open ZIP file handles."""

from unittest.mock import Mock

import pytest

from pain001_loader_xlsx.loader import XlsxLoader


@pytest.mark.parametrize(
    "mode", ["no-sheets", "empty", "numeric-iban", "valid"]
)
def test_workbook_always_closed(monkeypatch, mode):
    """Every success and rejection path releases the workbook."""
    workbook = Mock()
    workbook.sheetnames = [] if mode == "no-sheets" else ["Payments"]
    sheet = Mock()
    workbook.__getitem__ = Mock(return_value=sheet)
    header = Mock(value="debtor_account_IBAN")
    value = 12345 if mode == "numeric-iban" else "DE89370400440532013000"
    cell = Mock(
        value=value,
        number_format="General",
        data_type="n" if mode == "numeric-iban" else "s",
    )
    sheet.iter_rows.return_value = iter(
        [] if mode == "empty" else [(header,), (cell,)]
    )
    monkeypatch.setattr("openpyxl.load_workbook", Mock(return_value=workbook))
    if mode == "valid":
        assert XlsxLoader().load("synthetic.xlsx").rows == [
            {"debtor_account_IBAN": value}
        ]
    else:
        with pytest.raises(ValueError):
            XlsxLoader().load("synthetic.xlsx")
    workbook.close.assert_called_once_with()
