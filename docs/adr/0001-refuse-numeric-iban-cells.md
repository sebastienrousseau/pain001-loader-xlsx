<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0001. Refuse numeric IBAN cells

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

Excel converts anything that looks like a number into a number. An
IBAN pasted into a `General` cell loses its structure before any
export, and a corrupted debtor account is the failure a bank cannot
detect.

## Options considered

1. Coerce: turn the number back into text and carry on. Fast, and
   silently wrong whenever the coercion is lossy.
2. Refuse: stop the load with an error naming the row when any IBAN
   column cell arrives as a numeric type.

## Decision

Option 2. The type guard at load time and the mod-97 checksum in the
core afterwards are two independent layers; the first exists because
the second cannot see what Excel already destroyed.

## Consequences

`load` and `load_streaming` raise before any record is produced. The
guard is tested with workbooks whose IBAN cells are numeric, and the
README states the behaviour in its first section.
