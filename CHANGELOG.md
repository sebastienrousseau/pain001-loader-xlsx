# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every package in the
[`pain001`](https://github.com/sebastienrousseau/pain001) suite ships
the **same version number** — the core, `pain001-mcp`, `pain001-lsp`,
`pain001-loader-xlsx` and `pain001-loader-mt101`. If the core is at
`0.0.60` then so is this package, so there is no compatibility table to
consult. Versions advance in `0.0.1` steps along the `0.0.x` line;
`0.1.0` follows `0.0.999`.

`PAIN001_API_VERSION` still guards the plugin contract at load time — a
plugin built against a newer contract than its host raises rather than
misbehaving — but it is a safety net, not the versioning rule. See
`pain001.suite`, which a daily job checks against PyPI.

## [Unreleased]

## [0.0.62] - 2026-08-21

### Added

- **Benchmarks for streaming throughput and value normalisation.** The
  0.0.61 set measured a full load, its scaling, and that
  `load_streaming` does not hold every row. Two gaps remained.

  Streaming should also cost roughly what a full load costs, and does:
  0.94x, 1.13x and 1.25x across chunk sizes. The guard is against
  chunking becoming expensive in its own right — re-opening the workbook
  per chunk, say — which would keep every row correct and leave the
  memory assertion passing while making the API pointless for the large
  files it exists for.

  `to_text` runs once per cell, so it scales with the sheet rather than
  the row count: ~1.67us per cell, roughly 30ms of a ~156ms 2000-row
  load. Not dominant — openpyxl's parsing is — but the largest piece
  this package owns.

## [0.0.61] - 2026-08-20

Suite release with `pain001` 0.0.61. No change in this package.

The core's 0.0.61 is a performance release — libxml2 XSD validation and
a fix for quadratic CSV diagnostics — and neither touches this loader,
which reads spreadsheets and goes through neither path. The version
moves because every member of the suite ships the same number.

Note that 0.0.60 was never published for this package. It was prepared
and tagged, but the tag failed before the publish step and the suite had
moved to 0.0.61 by the time it was corrected, so 0.0.60 is skipped and
this release carries its contents: values normalised to text, and
temporal cells refused. See the 0.0.60 entry below for the detail.

## [0.0.60] - 2026-08-20

Joins the suite's version line. The previous number said this package
"targets the `0.0.X` release of `pain001`" while `0.0.54` required
`pain001>=0.0.56` — a version claiming to belong to a release it
predates.

An earlier draft resolved that by moving to `0.1.0` and declaring the
loaders independently versioned. That was the wrong way round: the rule
was right and the metadata was wrong. `0.0.60` matches the core and
every other member, and carries the breaking change below.


### Fixed

- **Cell values are strings, matching `csv.DictReader`.** pain001
  renders XML from whatever a loader returns, and its CSV loader yields
  strings. This loader returned Excel's native types, so a cell
  displaying `100.00` — stored as the float `100.0` — reached the XML
  as `100.0` where the CSV path produced `100.00`. Same spreadsheet,
  two different amounts, depending on which container it arrived in.

  Numeric cells are now rendered through the cell's `number_format`,
  which is the only record of the intended precision, so `100.0` with
  format `0.00` emits `"100.00"`.

  **Breaking:** callers reading `result.rows[...]` now receive `str`
  where they previously received `int` / `float`. That is the shape
  pain001 has always consumed.

- **Excel date/time cells are refused.** They previously passed through
  untouched, so a `datetime` object reached pain001 and stringified as
  `2026-03-01 00:00:00` — a value no ISO 20022 date field accepts.
  Excel stores dates as offsets against a workbook epoch and the 1900
  and 1904 systems differ by four years, so the loader will not guess.
  The error names the sheet, column and row, and says to format the
  column as Text and use ISO-8601 — completing the date-handling
  requirement of pain001#180.

## [0.0.54] - 2026-07-18

### Changed

- Require `pain001 >= 0.0.56` — the release that ships the `pain001.plugins`
  substrate this loader auto-discovers through. (The substrate landed on PyPI
  in pain001 0.0.56, alongside the 0.0.55 path-injection hardening; the CI
  git-branch fallback used while it was in flight is removed.)

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
