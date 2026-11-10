<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing

Thanks for looking. This package is small on purpose: it turns an XLSX
input into the flat `pain.001` records the rest of the `pain001` suite
already understands, and nothing else.

## Before you open a pull request

Everything CI checks, you can run locally. [DEVELOPMENT.md](DEVELOPMENT.md)
has the setup and maps each CI job to its command; the short version:

```sh
python -m pip install --require-hashes -r requirements/dev.txt
python -m pip install --no-deps -e .
make check          # lint, types, complexity, tests + coverage, docstrings
make docs-lint      # codespell and markdownlint (needs Node)
python benches/bench_load_xlsx.py --quick   # the benchmark still runs
```

`make test` fails below **100% line and branch coverage**. That is not a
stretch goal here: the package is a few hundred lines, and the branches
that go untested are the malformed-input ones, which is exactly where a
workbook loader earns its keep.

Commits are signed off (`git commit -s`, see [DCO.txt](DCO.txt)) and use
conventional-commit subjects with a body that says why.

## What the tests are for

- `tests/test_loader.py`: the parse itself, valid and malformed.
- `tests/test_benchmarks.py`: scaling and memory guards that compare the
  loader against itself, so they do not depend on the machine.
- `tests/test_examples.py` and `tests/test_readme.py`: every example and
  the README Quick Start run as written.
- `tests/test_suite_conformance.py`: shared across the suite. **Do not
  edit it here.** It is generated from one canonical copy, and a local
  edit fails `test_this_file_is_the_canonical_copy` by design; the point
  is that no repository can quietly weaken a shared gate.

[DEVELOPMENT.md](DEVELOPMENT.md#test-layout) lists the rest.

## Benchmarks

`benches/` measures throughput as workbooks grow. It asserts nothing:
wall-clock numbers are not comparable between machines, but CI runs it
with `--quick` so a benchmark that has stopped working against the
current API fails the build rather than rotting unnoticed.

Divide each time by its row count. Flat across sizes means linear. A
per-row time that climbs with size means the loader has gone
superlinear, which no unit test will tell you and a month-end payment
batch will.

## Versioning

The maintainer opens each version; a pull request does not bump it. When
it moves, it is restated in `pyproject.toml`,
`pain001_loader_xlsx/__init__.py` and `CITATION.cff`, with a
`CHANGELOG.md` entry, and the conformance tests confirm they agree. They
exist because the suite has already published a release whose
`__version__` reported the previous one.

**Versions increment by 0.0.1.** `0.1.0` follows `0.0.999`, not `0.0.9`.

## Licence

Apache-2.0 OR MIT, at your option. By contributing you agree your work is
released under the same dual grant.
