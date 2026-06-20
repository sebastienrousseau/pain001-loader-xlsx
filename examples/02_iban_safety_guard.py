# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Demonstrate the loader's IBAN-typed-as-number safety guard.

Excel's "General" cell format silently strips leading zeros from
numeric-looking strings - a known data-corruption mode in SAP /
Oracle / Workday exports. The loader catches this by refusing any
row whose ``debtor_account_IBAN`` / ``creditor_account_IBAN`` /
``charge_account_IBAN`` cell is typed as a number, surfacing a
clear remediation rather than silently wiring a wrong IBAN to a
bank.

Run from the repository root::

    python examples/02_iban_safety_guard.py
"""

import tempfile
from pathlib import Path

import openpyxl

from pain001_loader_xlsx import XlsxLoader


def _bad_fixture(tmpdir: Path) -> str:
    """Write an .xlsx whose IBAN column is numeric (the bad case)."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["id", "amount", "debtor_account_IBAN"])
    # 89370400440532013000 is a number in Excel's "General" format -
    # Excel will silently strip any leading zero on the way in/out.
    sheet.append(["MSG-0001", 100.00, 89370400440532013000])
    path = tmpdir / "broken-payments.xlsx"
    workbook.save(path)
    return str(path)


def main() -> None:
    """Demonstrate that the loader rejects numeric-typed IBAN cells."""
    with tempfile.TemporaryDirectory() as raw:
        tmpdir = Path(raw)
        xlsx_path = _bad_fixture(tmpdir)

        loader = XlsxLoader()
        try:
            loader.load(xlsx_path)
        except ValueError as exc:
            assert "Excel's 'General' cell format" in str(exc)
            print("IBAN safety guard fired - the loader refused the file.")
            print()
            print("Error message:")
            print(f"  {exc}")
            return

        raise AssertionError(
            "expected the loader to raise on a numeric IBAN cell"
        )


if __name__ == "__main__":
    main()
