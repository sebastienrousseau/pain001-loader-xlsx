<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

`pain001-loader-xlsx` reads flat-record payment data from Excel `.xlsx`
files for `pain001`, registered as a `pain001.loaders` entry point, and
nothing else. These are the rules an automated change is most likely to
break; humans follow them too. Read [CONTRIBUTING.md](CONTRIBUTING.md)
and [DEVELOPMENT.md](DEVELOPMENT.md) first.

## Versioning

- The version is `0.0.x`, moves by `0.0.1`, and ships in lockstep with
  the other eight `pain001` suite repositories. Never bump it as a side
  effect of a change.
- It is restated in `pyproject.toml`, `pain001_loader_xlsx/__init__.py`
  and `CITATION.cff`, with a `## [0.0.N]` heading in `CHANGELOG.md`;
  `tests/test_suite_conformance.py` checks that the package and the
  changelog agree.
- Work for the next version happens on `feat/v<next-version>`, the only
  pull request into `main`.

## Commits

- Conventional commits with a body that says why.
- Every commit is signed off (`git commit -s`, see [DCO.txt](DCO.txt))
  and SSH-signed. Never rewrite pushed history.

## The gate

- `make check` runs lint, strict mypy, complexity, tests with **100%
  line and branch coverage** and docstring coverage. "It compiles" is
  not done.
- `README.md` is rendered from `docs/readme-template.md` and
  `docs/readme-values.json` by `scripts/render_readme.py`; edit those and
  re-render, never the README itself. CI fails on drift.
- Complexity ceilings are held against `complexity-baseline.json`, which
  may only shrink.
- `requirements/*.txt` are hash-pinned; regenerate them with
  `make pip-compile`, never by hand.

## Data

- No real account numbers, personal data or bank-restricted material in
  the repository. Workbooks used in tests and examples are synthetic.

## Leave alone

- `tests/test_suite_conformance.py` is a byte-identical copy shared
  across the suite; change it upstream, not here.
