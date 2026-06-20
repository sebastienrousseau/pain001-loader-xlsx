<!-- SPDX-License-Identifier: Apache-2.0 -->

<h1 align="center">pain001-loader-xlsx</h1>

<p align="center">
  <b>Excel (.xlsx / .xlsm) loader plugin for the pain001 ISO 20022 library.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/v/pain001-loader-xlsx?style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/pyversions/pain001-loader-xlsx.svg?style=for-the-badge" alt="Python versions" /></a>
  <a href="#license"><img src="https://img.shields.io/pypi/l/pain001-loader-xlsx?style=for-the-badge" alt="License" /></a>
</p>

---

`pain001-loader-xlsx` is a third-party loader plugin for
[`pain001`](https://github.com/sebastienrousseau/pain001) that
teaches it to read payment data directly from Excel `.xlsx` /
`.xlsm` files - no "Save As CSV" step.

Drop-in: install both packages and `.xlsx` files dispatch
automatically; nothing else changes about how you use pain001.

---

## Install

```bash
pip install pain001 pain001-loader-xlsx
```

Requires Python 3.10+, `pain001 >= 0.0.54`, and `openpyxl >= 3.1`.

## Quick start

```bash
# An ordinary pain001 invocation - the .xlsx extension is dispatched
# to this plugin automatically.
pain001 -t pain.001.001.03 -d payments.xlsx -o out.xml

# Confirm pain001 sees the plugin.
pain001 plugins list --kind loader
# loader  xlsx  pain001-loader-xlsx==0.0.54  Read flat-record payment data from Excel .xlsx / .xlsm files.
```

From Python:

```python
from pain001 import process_files

# pain001's universal loader dispatches .xlsx through this plugin.
output_path = process_files(
    xml_message_type="pain.001.001.03",
    xml_template_file_path="template.xml",
    xsd_schema_file_path="schema.xsd",
    data_file_path="payments.xlsx",
)
print(output_path)  # -> "pain.001.001.03.xml" - validated and on disk
```

## Layout

The first sheet of the workbook is read. Row 1 is the header (column
names become dict keys); rows 2..N are the data records.

| Concern | How the loader handles it |
| :--- | :--- |
| Multi-sheet workbooks | First sheet wins. Consolidate before invocation. |
| Excel formulas | Cached value is read (`data_only=True`) - what you see in Excel is what pain001 gets. |
| IBAN columns | **Refused** when the cell type is `General` (Excel silently strips leading zeros). Re-type as `Text` and re-export. |
| Date cells | Cached value is passed through; ISO-8601 strings work, Excel datetime objects depend on the underlying spreadsheet. |
| Blank header cells | Stay in the dict under key `""`; downstream consumers can ignore or strip. |
| Streaming | `load_streaming(path, chunk_size)` honours pain001's `--streaming` mode. |

## Why a separate package?

`pain001` v0.0.54 introduced a formal plugin contract
([`pain001.plugins`](https://github.com/sebastienrousseau/pain001/blob/main/docs/plugins.md)).
External loaders that ride that contract publish on their own
cadence and don't bloat `pain001`'s dependency graph. `openpyxl`
in particular pulls in a non-trivial transitive tree that
operators who only need CSV / SQLite / JSON would rightly object
to as part of the core install.

This package is the canonical worked example. The implementation
([`pain001_loader_xlsx/loader.py`](pain001_loader_xlsx/loader.py))
is ~150 lines; the entry-point declaration is one line in
[`pyproject.toml`](pyproject.toml):

```toml
[project.entry-points."pain001.loaders"]
xlsx = "pain001_loader_xlsx.loader:XlsxLoader"
```

## Development

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-xlsx.git
cd pain001-loader-xlsx
pip install -e ".[dev]"
pytest                                # full suite
pytest --cov=pain001_loader_xlsx --cov-branch --cov-fail-under=100
ruff check . && ruff format --check .
mypy pain001_loader_xlsx
interrogate -c pyproject.toml pain001_loader_xlsx
```

## License

Apache License, Version 2.0. Built on
[`openpyxl`](https://foss.heptapod.net/openpyxl/openpyxl) and the
[`pain001`](https://github.com/sebastienrousseau/pain001) plugin
contract.
