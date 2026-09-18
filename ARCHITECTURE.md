<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# pain001-loader-xlsx Architecture

A map of the codebase for new contributors and maintainers.

## The pipeline

```
payments.xlsx / .xlsm  (first worksheet; row 1 is the header)
        |
        v
pain001_loader_xlsx.loader.XlsxLoader        registered under the pain001.loaders entry point
        |  load(path) / load_streaming(path, chunk_size)
        |  cell values normalised to the text the CSV pipeline would carry
        v
pain001  (SchemaValidator, scheme rulebooks, official XSD, XML generation)
        |
        v
ISO 20022 pain.001 XML
```

The loader teaches the core to read workbooks directly, so no "Save As
CSV" step exists to lose leading zeros or reformat an IBAN. It registers
itself through the `pain001.loaders` entry point and the core dispatches
`.xlsx` and `.xlsm` paths to it at process start; `pain001 -t ... -d
payments.xlsx -o out/` needs no configuration.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Public API** | `pain001_loader_xlsx/__init__.py` | Exports `XlsxLoader` and `__version__` |
| **Loader** | `pain001_loader_xlsx/loader.py` | `XlsxLoader`: read-only workbook access, header row, streaming chunks, the numeric-IBAN guard, the plugin API version it declares |
| **Normalisation** | `pain001_loader_xlsx/_normalise.py` | Cell value to text, honouring the cell's number format so `1.10` stays `1.10` |
| **Tests** | `tests/` | Loading, streaming, the guard, malformed workbooks, examples, the suite conformance file |
| **Examples** | `examples/` | Runnable scripts, executed by the tests |
| **Benchmarks** | `benches/` | Load throughput, scaling and memory guards |
| **Suite** | `scripts/check_suite_consistency.py`, `tests/test_suite_conformance.py` | The shared checks every suite member carries |

## Key design decisions

- **The IBAN guard.** Excel turns anything numeric-looking into a number.
  If any cell in an IBAN column arrives as a numeric type, the load stops
  with an error naming the row; a corrupted debtor account is the failure
  a bank cannot detect.
- **Read, never run.** Formulas resolve to their last-saved values
  (`data_only=True`); macros in `.xlsm` files are never executed.
- **One sheet, one batch.** Multi-sheet workbooks are out of scope by
  design; the audit trail stays unambiguous.
- **Streaming.** Workbooks open read-only and `load_streaming` yields
  fixed-size chunks, so a batch of hundreds of thousands of rows never has
  to fit in memory.
- **Structural conformance to the core's `AbstractLoader` protocol,** no
  subclassing, with the plugin API version declared so the core can refuse
  an incompatible pair.

## Extension points

- **A new cell type or format:** extend `_normalise.py` and add a workbook
  fixture that exercises it.
- **A new file format:** a separate loader package on the same entry
  point; this one stays Excel-only.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`pain001`](https://github.com/sebastienrousseau/pain001)
