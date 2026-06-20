# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Load payment rows from a tiny .xlsx fixture.

Builds a two-row Excel workbook on the fly, hands it to
:class:`pain001_loader_xlsx.XlsxLoader`, and verifies the loader
returns a :class:`pain001.plugins.LoaderResult` carrying the
expected records.

Run from the repository root::

    python examples/01_load_xlsx.py
"""

import tempfile
from pathlib import Path

import openpyxl
from pain001.plugins import LoaderResult

from pain001_loader_xlsx import XlsxLoader


def _fixture(tmpdir: Path) -> str:
    """Write a two-row Excel workbook into ``tmpdir`` and return its path."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["id", "amount", "debtor_account_IBAN"])
    sheet.append(["MSG-0001", 100.00, "DE89370400440532013000"])
    sheet.append(["MSG-0002", 250.50, "FR1420041010050500013M02606"])
    path = tmpdir / "payments.xlsx"
    workbook.save(path)
    return str(path)


def main() -> None:
    """Round-trip the fixture through XlsxLoader and print the rows."""
    with tempfile.TemporaryDirectory() as raw:
        tmpdir = Path(raw)
        xlsx_path = _fixture(tmpdir)

        loader = XlsxLoader()
        result = loader.load(xlsx_path)

        assert isinstance(result, LoaderResult)
        assert result.source_hint == xlsx_path
        assert len(result.rows) == 2

        print(f"source_hint: {result.source_hint}")
        print(f"rows loaded: {len(result.rows)}")
        for row in result.rows:
            iban = row["debtor_account_IBAN"]
            print(f"  - {row['id']}  {row['amount']:.2f}  {iban}")
        # -> source_hint: /tmp/.../payments.xlsx
        # -> rows loaded: 2
        # -> MSG-0001  100.00  DE89370400440532013000
        # -> MSG-0002  250.50  FR1420041010050500013M02606
    print("xlsx loader example completed.")


if __name__ == "__main__":
    main()
