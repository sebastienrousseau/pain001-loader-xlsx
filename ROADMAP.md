# pain001-loader-xlsx Roadmap

The loader ships with the pain001 suite, at the suite's version. Items
here are candidates; a release ships when the gates pass, not on a
calendar, and the maintainer decides what opens.

## Shipped

- `XlsxLoader` on the `pain001.loaders` entry point: `.xlsx` and `.xlsm`,
  first worksheet, header row, formulas as cached values, macros never
  executed, read-only streaming in fixed-size chunks.
- The numeric-IBAN guard: a load stops with the row named when Excel has
  turned an account identifier into a number.
- 100% line and branch coverage, docstring gate, benchmarks with scaling
  and memory guards, examples run by the tests; CodeQL, Dependabot, DCO
  and Scorecard; releases attested, signed and shipped with SBOMs.

## Candidates

- **Column-name aliases** from common treasury templates to the core's
  vocabulary, declared in one table, so a workbook exported from an ERP
  loads without renaming headers. Needs the core's alias rules first.
- **A workbook sample in the browser demo**, once the demo accepts a file
  upload beyond CSV.
- **Mutation testing** on the loader and the normaliser on the pattern the
  MCP and LSP servers use.

## Out of scope

- Multi-sheet workbooks: one sheet, one batch, by design.
- Legacy `.xls` (BIFF).
- Generating or validating XML: the core does both.
