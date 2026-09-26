<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/pain001/v1/logos/pain001.svg" alt="pain001-loader-xlsx logo" width="128" />
</p>

<h1 align="center">pain001-loader-xlsx</h1>

<p align="center">
  Load Excel payment records through the pain001 plugin contract.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/pain001-loader-xlsx/actions"><img src="https://github.com/sebastienrousseau/pain001-loader-xlsx/workflows/ci/badge.svg?style=for-the-badge&logo=github" alt="Build" /></a>
  <a href="https://pypi.org/project/pain001-loader-xlsx/"><img src="https://img.shields.io/pypi/v/pain001-loader-xlsx?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" /></a>
  <a href="docs/index.md"><img src="https://img.shields.io/badge/docs-source?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/pain001-loader-xlsx"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/pain001-loader-xlsx?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-loader-xlsx/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.10%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.10 or newer" /></a>
</p>

---

## Contents

**Getting started**

- [Install](#install) — PyPI and source
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — use the installed companion

**The pain001-loader-xlsx ecosystem**

- [The pain001-loader-xlsx ecosystem](#the-pain001-loader-xlsx-ecosystem) — core and this companion

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use pain001-loader-xlsx](#when-not-to-use-pain001-loader-xlsx) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```bash
python -m pip install pain001-loader-xlsx
```

Published packages and development checkouts are distinct. Test unreleased
changes on this companion's development branches against the matching core
branch. Versions track core 0.0.x releases.

---

## Requirements

Python 3.10 or newer. CI tests 3.10–3.14 on Linux. See
[toolchain policy](docs/POLICIES.md); no distro-system-Python claim is made.

---

## Quick Start

```bash
pain001 plugins list --kind loader --json
pain001 -t pain.001.001.03 -d payments.xlsx -o output
```

Supply `payments.xlsx` with core template column names; [examples/](examples/)
creates synthetic workbooks. `-o` specifies an output directory, not a filename.

---

## The pain001-loader-xlsx ecosystem

This independently installed companion delegates payment behavior to core.
Coordinated versioning does not imply branch changes have been released.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [pain001](https://github.com/sebastienrousseau/pain001) | Generation and validation | Shared contracts and XML engine |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Integration | Excel loading and streaming | Test-gated companion package |

---

## Ecosystem comparison

This matrix describes the repository's scope, not an independently benchmarked
comparison with competitors.

| Project | Generate payment XML | Real settlement | Synthetic bank replies |
| :--- | :---: | :---: | :---: |
| **pain001-loader-xlsx** | Delegates to core | No | Not a bank service |

See [`docs/COMPARISON.md`](docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

CI smoke-runs benchmarks. No hardware-independent throughput or latency promise
is made; use the generated run report for measurements.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| Adapter operations | Run-specific | Python, hardware and dependency versions recorded per run |

See [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) for methodology and full results.

---

## Features

`XlsxLoader` implements `AbstractLoader` via the `pain001.loaders` entry point.
It reads `.xlsx`/`.xlsm`, first sheet only, row 1 as headers. Read-only, data-only
openpyxl access returns cached formula values, which can be stale or absent;
no formulas or macros are evaluated.

Numeric IBAN cells are rejected with column-specific Text-format guidance.
Text-valued IBAN cells are accepted even with General formatting. Excel date,
time and datetime objects are rejected; use ISO-8601 text. Formatting a damaged
identifier as Text cannot restore lost digits: recover the source value.
Streaming yields bounded chunks and workbooks close on errors.

---

## Configuration

Install alongside core for extension dispatch. `XlsxLoader.load(path)` returns
`LoaderResult`; `load_streaming(path, chunk_size)` yields chunks. Refer to
core's generated CLI help for generation flags.

---

## Examples

Run the self-checking scripts under [examples/](examples/). Tests cover valid
and malformed inputs and integration with the core contract.

---

## When not to use pain001-loader-xlsx

No legacy `.xls`, multi-sheet merging, formula evaluation or identifier repair.
Convert legacy files explicitly and preserve account values as text at source.
This is a payment-record adapter, not a general spreadsheet engine.

---

## Development

```bash
python -m pip install -e '.[dev]'
make check
python scripts/render_readme.py --check
python benches/bench_load_xlsx.py --quick
```

Coverage is gated at 100% line and branch. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [DEVELOPMENT.md](DEVELOPMENT.md). README is generated from the canonical
layout and `docs/readme-values.json`; CI rejects drift.

---

## Security

Read-only workbook loading does not run macros or evaluate formulas. Numeric
IBAN and temporal-cell guards reject known spreadsheet coercions. Loading a
workbook does not prove its accounts, amounts or bank rules are correct.

Report vulnerabilities according to [`SECURITY.md`](SECURITY.md).

---

## Documentation

[User manual](docs/index.md) · [API reference](docs/index.md) ·
[Developer guide](DEVELOPMENT.md) ·
[Family map](https://github.com/sebastienrousseau/pain001#the-pain001-ecosystem)

---

## Stability guarantees

Versions advance in coordinated `0.0.1` steps with core. The maintainer opens
releases. Contract and output changes need
compatibility review. No stronger platform or stability guarantee is implied.

---

## License

Dual-licensed under [Apache-2.0](LICENSE-APACHE) OR [MIT](LICENSE-MIT), at your
option. See [LICENSE](LICENSE). Dependencies retain their own licences.
