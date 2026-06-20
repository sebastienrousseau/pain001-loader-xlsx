<!-- SPDX-License-Identifier: Apache-2.0 -->

# pain001-loader-xlsx Examples

Runnable, self-checking examples covering every feature this loader
exposes. Each script exits `0` on success and is executed in CI by
`tests/test_examples.py`, so they cannot silently drift out of date.

Run them from the repository root:

```bash
python examples/01_load_xlsx.py
```

| Example | Feature shown |
| :--- | :--- |
| `01_load_xlsx.py` | The happy path: build a tiny `.xlsx` fixture, load it through `XlsxLoader`, verify `LoaderResult.rows` |
| `02_iban_safety_guard.py` | The IBAN-typed-as-number refusal that protects against Excel's leading-zero-stripping data-corruption mode |

Together these scripts exercise the full public surface of the
loader (`XlsxLoader.load`, the structural Protocol conformance, the
defensive IBAN guard) — i.e. everything an external integrator can
reach.

Each example creates its fixture in a temporary directory and
cleans up after itself; the scripts leave no on-disk artefacts.
