# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This package's version follows the [`pain001`](https://github.com/sebastienrousseau/pain001)
suite (`pain001`, `pain001-mcp`, `pain001-lsp`); a `0.0.X` release of
this package targets the `0.0.X` release of `pain001`.

## [0.0.53] - 2026-06-20

### Added

Initial release of `pain001-loader-xlsx`, a third-party loader
plugin that teaches the [`pain001`](https://github.com/sebastienrousseau/pain001)
ISO 20022 payment library to read payment data directly from Excel
`.xlsx` / `.xlsm` files. Drop-in: install both packages and `.xlsx`
files dispatch automatically.

- **`XlsxLoader`** — implements the structural
  `pain001.plugins.AbstractLoader` Protocol without subclassing.
  Just exposes `meta`, `extensions`, `load`, and `load_streaming`.
- **First-sheet header dispatch** — row 1 becomes the dict keys,
  rows 2..N become the records. Cells are read with `openpyxl`'s
  `data_only=True` so formulas resolve to their cached last-saved
  value.
- **Streaming variant** — `load_streaming(path, chunk_size)`
  honours pain001's `--streaming` mode.
- **IBAN safety guard** — refuses any row whose
  `debtor_account_IBAN` / `creditor_account_IBAN` /
  `charge_account_IBAN` cell is typed as a number, surfacing a
  clear remediation pointing at Excel's "Format Cells > Number >
  Text" workflow. Protects against the silent leading-zero-stripping
  that breaks SAP / Oracle / Workday exports.
- **Entry-point auto-discovery** — registered via the standard
  `pain001.loaders` entry-point group in `pyproject.toml`; pain001
  picks the loader up at process start with no manual wiring.
- **Two runnable examples** at `examples/` that double as
  integration tests in CI.

### Requirements

- Python 3.10 or later.
- `pain001 >= 0.0.54, < 1` — the plugin substrate
  (`pain001.plugins`) ships in pain001 v0.0.54. The package metadata
  declares this dependency explicitly; `pip` will pull a compatible
  pain001 automatically.
- `openpyxl >= 3.1, < 4`.

### Quality gates

| Gate | Status |
| :--- | :--- |
| pytest | 12 tests passing |
| Line + branch coverage | **100%** (enforced via `--cov-fail-under=100`) |
| Docstring coverage (interrogate) | **100%** |
| ruff lint + format | clean |
| mypy `--strict` | clean |
| Examples in CI | 2/2 run as integration tests |

### Suite alignment

| Package | Version |
| :--- | :--- |
| [`pain001`](https://pypi.org/project/pain001/) | 0.0.53 |
| [`pain001-mcp`](https://pypi.org/project/pain001-mcp/) | 0.0.53 |
| [`pain001-lsp`](https://pypi.org/project/pain001-lsp/) | 0.0.53 |
| `pain001-loader-xlsx` (this release) | **0.0.53** |
