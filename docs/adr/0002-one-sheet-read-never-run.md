<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0002. One sheet, one batch; read, never run

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

A workbook can hold several sheets, formulas and macros. A loader
could try to honour all of them.

## Options considered

1. Load every sheet, evaluate formulas, run macros where needed. More
   inputs accepted; an unauditable batch, and macro execution on a
   payments machine.
2. First sheet only, formulas as their last-saved values, macros never
   executed, read-only access, streaming chunks.

## Decision

Option 2. One sheet keeps the audit trail unambiguous; reading cached
values keeps the loader a reader; refusing to run macros is a security
boundary, not a limitation.

## Consequences

Multi-sheet workbooks are split upstream. `data_only=True` and
read-only mode are asserted by tests. The behaviour is stated on the
site's reference page under "Behaviour, precisely".
