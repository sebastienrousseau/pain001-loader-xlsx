<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# pain001-loader-xlsx Governance

This document describes how pain001-loader-xlsx is run, how decisions are made, and how
to take on responsibility for it. It exists to make the project legible and
sustainable, and to reduce its dependence on any single person.

## Mission and scope

pain001-loader-xlsx is a loader plugin for the
[`pain001`](https://github.com/sebastienrousseau/pain001) ISO 20022
library. It reads payment batches straight from Excel workbooks, so the
core can validate and generate `pain.001` XML from them without a CSV
export in between.

Changes are weighed against that scope: correctness, security and clarity
over feature breadth. Anything that belongs to the core library's public
API is proposed there, not here.

## Roles

| Role | Who | Can |
| :--- | :--- | :--- |
| **Maintainer** | Listed in [`MAINTAINERS.md`](MAINTAINERS.md) | Merge PRs, cut releases, triage, set direction |
| **Contributor** | Anyone with a merged PR | Propose changes, review, discuss |
| **User** | Everyone | File issues, ask questions, request features |

## Decision making

- **Day-to-day changes** (fixes, docs, tests, additive features within
  scope) proceed by **lazy consensus**: open a PR; if no maintainer objects
  and CI is green, a maintainer merges it.
- **Significant changes** (new public names, a change to the records a
  loader emits, new dependencies, a raised `pain001` floor) need explicit
  approval from a maintainer in the PR, and should start as an issue.
- **Disagreement** is resolved by discussion aiming for consensus; if none
  is reached, the lead maintainer decides and records the rationale.

Every change must pass the full gate (100% line and branch coverage, 100%
docstring coverage, mypy, ruff, CodeQL, the suite conformance test) before
merge, enforced in CI, not by trust. Commits carry a Developer Certificate
of Origin sign-off (`git commit -s`; see `DCO.txt`).

## Releases

Releases follow [`RELEASING.md`](RELEASING.md). Every member of the pain001
suite ships the same version number as the core; the `pain001` floor this
loader declares is the oldest core whose plugin contract it needs, recorded
in the core's `pain001.suite` table and checked against PyPI daily. Only
maintainers publish to PyPI.

## Becoming a maintainer

More maintainers is the single biggest thing that would de-risk the
project.

1. Contribute a few reviewed PRs ([`ARCHITECTURE.md`](ARCHITECTURE.md) is
   the map; good first areas: a cell format the normaliser does not yet cover, a workbook fixture, a benchmark).
2. Help triage issues and review others' PRs.
3. Open a discussion or email the lead maintainer expressing interest.

A maintainer proposes you; with no objection from existing maintainers
within a week, you are added to `MAINTAINERS.md`.

## Sustainability (bus factor)

pain001-loader-xlsx has **one** maintainer today. The mitigations in place:

- **The work is legible:** [`ARCHITECTURE.md`](ARCHITECTURE.md) maps the
  codebase and [`RELEASING.md`](RELEASING.md) documents the release
  process; the examples are executed by the test suite.
- **Quality is enforced by CI,** not by one person's memory.
- **The goal is two or more maintainers** with independent release
  authority.

## Code of conduct and security

Security issues follow the private disclosure process in
[`SECURITY.md`](SECURITY.md); please do not open public issues for
vulnerabilities.
