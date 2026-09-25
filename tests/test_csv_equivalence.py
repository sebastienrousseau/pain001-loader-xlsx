# SPDX-License-Identifier: Apache-2.0 OR MIT
"""XLSX and equivalent CSV inputs must render byte-identical payments."""

import csv

import openpyxl
from pain001.constants import TEMPLATES_DIR
from pain001.data.loader import load_payment_data
from pain001.plugins.registry import registry
from pain001.xml.generate_xml import generate_xml_string


def test_registered_xlsx_matches_csv(tmp_path, monkeypatch):
    """Discover the installed plugin and compare real rendered XML bytes."""
    assets = TEMPLATES_DIR / "pain.001.001.03"
    with (assets / "template.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.reader(stream))
    workbook = openpyxl.Workbook()
    for row in records:
        workbook.active.append(row)
    xlsx = tmp_path / "payments.xlsx"
    workbook.save(xlsx)
    workbook.close()
    equivalent = tmp_path / "payments.csv"
    with equivalent.open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows(records)
    monkeypatch.chdir(tmp_path)
    registry.reset()
    rows_csv = load_payment_data(str(equivalent))
    rows_xlsx = load_payment_data(str(xlsx))
    assert rows_csv == rows_xlsx
    args = (
        "pain.001.001.03",
        str(assets / "template.xml"),
        str(assets / "pain.001.001.03.xsd"),
    )
    assert (
        generate_xml_string(rows_xlsx, *args).encode()
        == generate_xml_string(rows_csv, *args).encode()
    )
    assert registry.get_loader("xlsx").meta.source.startswith(
        "pain001-loader-xlsx=="
    )
