<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

The single entry point for working on `pain001-loader-xlsx`: toolchain,
how to reproduce every CI gate locally, where tests live, and how a
release happens. [CONTRIBUTING.md](CONTRIBUTING.md) covers the etiquette
(DCO, commit format, review); this file covers the mechanics.

## Toolchain

| Tool | Version | Where it is pinned |
| :--- | :--- | :--- |
| Python | 3.11 is the floor; CI tests 3.11 to 3.14 | `pyproject.toml` `requires-python`, the `ci.yml` matrix, [toolchain policy](docs/POLICIES.md) |
| Python packages | exact versions with hashes | `requirements/*.txt`, compiled from `requirements/*.in` by `make pip-compile` (needs [uv](https://docs.astral.sh/uv/)) |
| Node | any current LTS | only for `markdownlint-cli2` in the docs-lint job |
| pre-commit | any | optional; hooks pinned by commit SHA in `.pre-commit-config.yaml` |

```bash
git clone https://github.com/sebastienrousseau/pain001-loader-xlsx
cd pain001-loader-xlsx
python -m venv .venv && . .venv/bin/activate
python -m pip install --require-hashes -r requirements/dev.txt
python -m pip install --no-deps -e .
pre-commit install        # optional: ruff, codespell and hygiene hooks
make check
```

`requirements/dev.txt` is one resolved tree holding everything
`make check` runs. CI installs one file per job instead
(`requirements/test.txt`, `lint.txt`, `complexity.txt`, `docs.txt`,
`docs-lint.txt`, `audit.txt`, `fuzz.txt`, `mutation.txt`).

The [devcontainer](.devcontainer/devcontainer.json) does the same in a
Codespace or VS Code container and finishes by running `make check`.

## Reproducing every CI gate

| Gate | Local command | CI workflow and job |
| :--- | :--- | :--- |
| Lint and format (ruff) | `make lint` | `ci.yml` Lint & Type Check |
| Types (mypy `--strict`, package and gate scripts) | `make type-check` | `ci.yml` Lint & Type Check |
| Complexity (cyclomatic 10, cognitive 15, Halstead 30, 60 lines per function, 500 per file) against `complexity-baseline.json`, which only shrinks | `make complexity` | `ci.yml` Complexity |
| Tests with the 100% line and branch coverage floor | `make test` | `ci.yml` Test (matrix), Test (all) |
| README rendered from its sources, Quick Start run verbatim | `python scripts/render_readme.py --check` and `make test` | `ci.yml` Test |
| Docstring coverage 100% | `make doc-coverage` | `ci.yml` Test |
| Benchmarks (kept running, not asserted) | `python benches/bench_load_xlsx.py --quick` | `ci.yml` Test |
| Release notes present for the current version | `test -f releases/v$(python -c 'import pain001_loader_xlsx as p; print(p.__version__)').md` | `ci.yml` Release Notes Present |
| Advisory audit of every requirements file | `make audit` (needs `requirements/audit.txt`) | `ci.yml` Dependency audit |
| Docs lint (codespell, markdownlint) | `make docs-lint` | `docs-lint.yml` |
| Docs build, warnings as errors, every page links the author | `make docs` (needs `requirements/docs.txt`) | `docs.yml` build |
| External links in the manual (network) | `make linkcheck` (needs `requirements/docs.txt`) | `docs.yml` Link check |
| Repository-relative links in every Markdown file | `make test` (`tests/test_docs_links.py`) | `ci.yml` Test |
| Fuzzing (Atheris, Linux x86_64 only) | `make fuzz` (needs `requirements/fuzz.txt`) | `fuzz.yml` |
| Mutation score floor | `make mutate` (needs `requirements/mutation.txt`) | `mutation.yml` |
| Static analysis | none locally | `codeql.yml` |
| Signed-off-by on every commit | `git commit -s` | `dco.yml` |
| Suite versions agree with PyPI | `python scripts/check_suite_consistency.py` (network) | `suite-consistency.yml` (daily) |
| All of the above that run offline without extra trees | `make check` | |

The coverage floor is 100% line and branch and is stated once, in
`pyproject.toml` `[tool.coverage.report]`. The package is a few hundred
lines, and the branches a lower floor would leave untested are the
malformed-input ones. `# pragma: no cover` marks three defensive
guards a test cannot reach, each with its reason on the line; a new one
needs the same.

## Test layout

```text
tests/
  test_loader.py                 the parse: valid and malformed workbooks, streaming
  test_value_normalisation.py    cell value to text, honouring number formats
  test_guard_messages.py         exact wording, row and column of every refusal
  test_ooxml_escapes.py          _xHHHH_ escapes and characters XML cannot carry
  test_raw_values.py             cells starting with =, +, - or @ reach the payment as written
  test_csv_equivalence.py        an xlsx and the equivalent CSV render byte-identical XML
  test_workbook_cleanup.py       rejected workbooks do not leak open file handles
  test_examples.py               runs every examples/[0-9]*.py
  test_readme.py                 README section order, tokens, links; Quick Start run verbatim
  test_docs_links.py             every relative link in the Markdown sources resolves
  test_fuzz.py                   replays fuzz/corpus without Atheris
  test_benchmarks.py             scaling and memory guards (pytest-benchmark)
  test_check_*.py, test_release_notes.py   the gate and release scripts
  test_suite_conformance.py      family-wide rules; vendored, byte-identical, do not edit
examples/                        numbered, self-checking scripts
benches/                         throughput as workbooks grow
fuzz/                            Atheris harness and its regression corpus
```

Workbooks used by tests and examples are synthetic and built in the
test itself; no real account data is committed.

## README

`README.md` is generated. Edit `docs/readme-template.md` (a copy of the
portfolio's canonical layout) or `docs/readme-values.json`, then run
`python scripts/render_readme.py`. CI fails when the committed README
differs from the rendered one, when a `{{TOKEN}}` is left unresolved,
when a relative link points at a missing file, or when the `##`
sections depart from the canonical order (`tests/test_readme.py`).

## Release model

The version is `0.0.x`, moves in `0.0.1` steps, and ships in lockstep
with the other `pain001` suite members. Work for the next version
happens on `feat/v<next-version>`, the only pull request into `main`.
The maintainer opens and cuts releases; [RELEASING.md](RELEASING.md)
has the checklist and what the tag-triggered `release.yml` does.
