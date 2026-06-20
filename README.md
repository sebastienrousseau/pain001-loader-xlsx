<!-- SPDX-License-Identifier: Apache-2.0 -->

<p align="center">
  <img
    src="https://cloudcdn.pro/pain001/v1/logos/pain001.svg"
    alt="pain001-loader-xlsx logo"
    width="120"
    height="120"
  />
</p>

<h1 align="center">pain001-loader-xlsx</h1>

<p align="center">
  <b>Excel (.xlsx / .xlsm) loader plugin for the pain001 ISO 20022 payment library.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/v/pain001-loader-xlsx?style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/pyversions/pain001-loader-xlsx.svg?style=for-the-badge" alt="Python versions" /></a>
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/dm/pain001-loader-xlsx.svg?style=for-the-badge" alt="PyPI downloads" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-loader-xlsx/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/pain001-loader-xlsx/ci.yml?branch=main&label=Tests&style=for-the-badge" alt="Tests" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-loader-xlsx/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/pain001-loader-xlsx/ci.yml?branch=main&label=Coverage&style=for-the-badge" alt="Coverage" /></a>
  <a href="#license"><img src="https://img.shields.io/pypi/l/pain001-loader-xlsx?style=for-the-badge" alt="License" /></a>
</p>

---

## Contents

**Getting started**

- [What is pain001-loader-xlsx?](#what-is-pain001-loader-xlsx) — the problem it solves
- [Install](#install) — PyPI, virtualenv
- [Quick start](#quick-start) — one command from Excel to validated XML

**Library reference**

- [How it works](#how-it-works) — the plugin contract, in one diagram
- [Layout](#layout) — sheet selection, headers, the IBAN safety guard
- [Using the loader from Python](#using-the-loader-from-python) — bypass pain001 entirely
- [The pain001 suite](#the-pain001-suite) — core lib, MCP server, LSP server, this loader

**Operational**

- [When not to use pain001-loader-xlsx](#when-not-to-use-pain001-loader-xlsx) — honest boundaries
- [Development](#development) — gates, make targets
- [Security](#security) — defensive posture
- [Documentation](#documentation) — examples, guides
- [Contributing](#contributing) — how to get changes in
- [License](#license) — Apache-2.0

---

## What is pain001-loader-xlsx?

`pain001-loader-xlsx` is a third-party loader plugin for the
[`pain001`](https://github.com/sebastienrousseau/pain001) ISO 20022
payment library that teaches it to read payment data **directly from
Excel `.xlsx` / `.xlsm` files** — no "Save As CSV" step.

Drop-in: install both packages and `.xlsx` files dispatch
automatically. Nothing else changes about how you use pain001.

This package exists because `openpyxl` carries a non-trivial
transitive dependency tree that operators who only need CSV / SQLite
/ JSON would rightly object to as part of the core install. It is
also the canonical worked example of pain001's v0.0.54+ plugin
substrate — the same `AbstractLoader` Protocol any third-party
loader uses.

| Concern | How the loader handles it |
| :--- | :--- |
| Sheet selection | First sheet wins. Consolidate cross-sheet batches before invocation. |
| Excel formulas | Cached value is read (`data_only=True`) — what you see in Excel is what pain001 gets. |
| IBAN columns | **Refused** when the cell type is `General` (Excel silently strips leading zeros from numeric-looking strings). The error tells the user to re-type the column as `Text` and re-export. |
| Date cells | Cached value is passed through; ISO 8601 strings work, Excel datetime objects depend on the underlying spreadsheet. |
| Blank header cells | Stay in the dict under key `""`; downstream consumers can ignore or strip. |
| Streaming | `load_streaming(path, chunk_size)` honours pain001's `--streaming` mode. |
| Discovery | Registered via the standard `pain001.loaders` entry-point group; pain001 picks it up at process start. |
| Cross-platform | Pure Python (`openpyxl`); works wherever pain001 works. |

---

## Install

| Channel | Command | Notes |
| :--- | :--- | :--- |
| PyPI | `pip install pain001 pain001-loader-xlsx` | Pulls in `openpyxl >= 3.1` + a recent `pain001` |
| Source | `git clone https://github.com/sebastienrousseau/pain001-loader-xlsx && cd pain001-loader-xlsx && pip install -e ".[dev]"` | For development |

Requires Python 3.10 or later. Works on macOS, Linux, and Windows.

> **pain001 version requirement.** The plugin substrate
> (`pain001.plugins`) that powers auto-discovery is part of
> `pain001 >= 0.0.54`. The package metadata declares this dependency
> explicitly; `pip install pain001-loader-xlsx` will pull in a
> compatible `pain001` automatically.

<details>
<summary>Using an isolated virtual environment (recommended)</summary>

```sh
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
python -m pip install -U pain001 pain001-loader-xlsx
```

</details>

---

## Quick start

Install both packages and feed pain001 an `.xlsx` file:

```bash
pip install pain001 pain001-loader-xlsx

pain001 -t pain.001.001.03 -d payments.xlsx -o out.xml
# -> writes a validated pain.001.001.03 XML alongside out.xml
```

Confirm pain001 sees the loader:

```bash
pain001 plugins list --kind loader --json | python -m json.tool
# [
#   { "kind": "loader", "name": "xlsx",
#     "source": "pain001-loader-xlsx==0.0.53", ... },
#   ...
# ]
```

From Python:

```python
from pain001 import process_files

# pain001's universal loader dispatches .xlsx through this plugin.
output_path = process_files(
    xml_message_type="pain001.001.001.03",
    xml_template_file_path="template.xml",
    xsd_schema_file_path="schema.xsd",
    data_file_path="payments.xlsx",
)
print(output_path)  # -> "pain.001.001.03.xml" — validated and on disk
```

---

## How it works

```text
+--------------------------+        +--------------------------+
|  pain001 CLI / REST API  |        |  pain001-loader-xlsx     |
|                          |        |                          |
|  load_payment_data(path) |  -->   |  XlsxLoader.load(path)   |
|                          |        |  -> LoaderResult         |
+----------+---------------+        +----------+---------------+
           |                                   |
           | extension dispatch (.xlsx)         |
           v                                   v
    +------+-------+                    +------+-------+
    |  pain001     |                    |  openpyxl    |
    |  registry    |                    |  read_only   |
    +--------------+                    +--------------+
```

pain001 v0.0.54 ships a formal plugin contract; this package
exposes one Python class that satisfies it. Wired into pain001 via
a single line in this package's `pyproject.toml`:

```toml
[project.entry-points."pain001.loaders"]
xlsx = "pain001_loader_xlsx.loader:XlsxLoader"
```

That is all the integration there is. pain001 discovers the entry
point at process start via `importlib.metadata.entry_points` and
dispatches by extension. There is no global state, no central
registry to update, nothing to subclass.

---

## Layout

The first sheet of the workbook is read. Row 1 is the header (column
names become dict keys); rows 2..N are the data records. Cells are
read with `openpyxl`'s `data_only=True` so formulas resolve to their
cached last-saved value — what the user sees in Excel is what
pain001 gets.

### The IBAN guard, explained

Excel's "General" cell format silently coerces a numeric-looking
string like `0023012345...` into the integer `23012345...`,
**dropping the leading zeros**. This is a known data-corruption
mode in SAP / Oracle / Workday exports. To protect against it the
loader refuses any row whose `debtor_account_IBAN` /
`creditor_account_IBAN` / `charge_account_IBAN` cell is typed as a
number, and tells the user to re-type the column as `Text`:

```text
workbook 'payments.xlsx' column 'debtor_account_IBAN' contains
a numeric value (89370400440532013000) where an IBAN string is
expected. Excel's 'General' cell format silently strips leading
zeros from IBANs; re-type the column as 'Text' (in Excel: select
the column, Format Cells -> Number -> Text) and re-export.
```

Caught early, the warning saves the user from wiring an IBAN with a
missing digit to a bank.

---

## Using the loader from Python

For Lambdas, ETL pipelines, or just inspecting an Excel file's
records before generation, you can use `XlsxLoader` directly without
going through pain001's dispatch:

```python
from pain001_loader_xlsx import XlsxLoader

loader = XlsxLoader()
result = loader.load("payments.xlsx")

print(result.source_hint)        # -> "payments.xlsx"
print(len(result.rows))          # -> 42
print(result.rows[0]["id"])      # -> "MSG-0001"
```

Streaming variant for batches that don't fit in memory:

```python
for chunk in loader.load_streaming("big-payments.xlsx", chunk_size=1000):
    process(chunk.rows)
```

The runnable version of this snippet (and a couple of others) lives
in [`examples/`](examples/).

---

## The pain001 suite

`pain001-loader-xlsx` is part of a set of independently installable
packages built around the
[`pain001`](https://github.com/sebastienrousseau/pain001) library —
pick whichever ones your stack needs:

| Package | Role |
| :--- | :--- |
| [`pain001`](https://pypi.org/project/pain001/) | Core library + CLI + FastAPI REST API |
| [`pain001-mcp`](https://pypi.org/project/pain001-mcp/) | Model Context Protocol server (for AI agents) |
| [`pain001-lsp`](https://pypi.org/project/pain001-lsp/) | Language Server Protocol server (for editors) |
| [`pain001-loader-xlsx`](https://pypi.org/project/pain001-loader-xlsx/) | **Excel loader plugin (this package)** |

```mermaid
flowchart LR
    A["payments.xlsx"] -->|extension dispatch| B["pain001-loader-xlsx"]
    B -->|LoaderResult| C["pain001"]
    C -->|render + XSD validate| D["ISO 20022 pain.001 XML"]
```

---

## When not to use pain001-loader-xlsx

- **You can export CSV cleanly.** A `.csv` round-trip skips an
  entire transitive dependency tree (`openpyxl` + its handful of
  deps). pain001's built-in CSV loader is preferred when you have
  the choice.
- **You need multi-sheet support.** The first sheet wins; cross-sheet
  payment batches need to be consolidated first.
- **You need `.xls` (legacy binary format).** Out of scope.
  Convert to `.xlsx` first, or use a different loader.
- **Your data isn't payment-record-shaped.** This loader is a thin
  pain001 input adapter, not a general-purpose Excel reader.

---

## Development

`pain001-loader-xlsx` uses standard Python tooling — no Poetry, just
pip + pyproject.toml.

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-xlsx.git
cd pain001-loader-xlsx
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Quality gates (kept in lockstep with CI):

| Target | What it runs |
| :--- | :--- |
| `pytest` | Full test suite |
| `pytest --cov=pain001_loader_xlsx --cov-branch --cov-fail-under=100` | **100% line + branch** coverage gate |
| `interrogate -c pyproject.toml pain001_loader_xlsx` | **100% docstring** coverage gate |
| `ruff check pain001_loader_xlsx tests` | Lint |
| `ruff format --check pain001_loader_xlsx tests` | Format |
| `mypy pain001_loader_xlsx` | Type check |

Current state (v0.0.53): **12 tests passing, 100% line + branch
coverage**, ruff + mypy clean, interrogate 100% docstring coverage.

---

## Security

- **No filesystem writes.** The loader reads from an Excel file
  path and yields plain dicts; it does not create, modify, or
  delete files.
- **No code execution.** `openpyxl`'s `read_only=True` mode does
  not evaluate macros (Excel VBA is not executed). `data_only=True`
  returns the cached last-saved value of formulas — no formula
  engine runs.
- **IBAN safety**: the loader refuses any row whose IBAN cells are
  numeric (see [Layout](#layout)), avoiding the
  "Excel silently dropped a leading zero" data-corruption mode.
- **Dependencies** are pinned via `pyproject.toml` (`openpyxl >=
  3.1, < 4`) and audited by GitHub's Dependabot.

To report a vulnerability, please use
[GitHub private vulnerability reporting](https://github.com/sebastienrousseau/pain001-loader-xlsx/security)
rather than a public issue.

---

## Documentation

- **Runnable examples:** [`examples/`](https://github.com/sebastienrousseau/pain001-loader-xlsx/tree/main/examples)
- **Release history:** [CHANGELOG.md](https://github.com/sebastienrousseau/pain001-loader-xlsx/blob/main/CHANGELOG.md)
- **pain001 plugin contract:** [`docs/plugins.md` upstream](https://github.com/sebastienrousseau/pain001/blob/main/docs/plugins.md)
- **openpyxl docs:** [openpyxl.readthedocs.io](https://openpyxl.readthedocs.io)

---

## Contributing

Contributions are welcome — see the
[contributing guide](https://github.com/sebastienrousseau/pain001-loader-xlsx/blob/main/CONTRIBUTING.md)
(or the upstream pain001 contributing guide if a per-repo one has
not landed yet). Thanks to all the
[contributors](https://github.com/sebastienrousseau/pain001-loader-xlsx/graphs/contributors)
who have helped build `pain001-loader-xlsx`.

---

## License

Licensed under the [Apache License, Version 2.0](https://opensource.org/license/apache-2-0/).
Built on [`openpyxl`](https://foss.heptapod.net/openpyxl/openpyxl)
and the
[`pain001`](https://github.com/sebastienrousseau/pain001) plugin
contract.

Any contribution submitted for inclusion shall be licensed as above,
without additional terms.

---

<p align="center">
  <a href="https://pain001.com">pain001.com</a> ·
  <a href="https://pypi.org/project/pain001-loader-xlsx/">PyPI</a> ·
  <a href="https://github.com/sebastienrousseau/pain001-loader-xlsx">GitHub</a>
</p>
