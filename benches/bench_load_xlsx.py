#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What loading a payment spreadsheet costs, in time and in memory.

`XlsxLoader` offers two entry points, and the difference between them is
entirely about memory. `load` returns every row at once. `load_streaming`
yields fixed-size chunks, so a caller can process a large file without
holding all of it. Time is nearly identical either way -- openpyxl's
parsing dominates both -- so the only question worth measuring is whether
streaming actually bounds the peak.

It does, and the table shows by how much. But it shows something else
too, in a third column that exists because the first version of this
benchmark got it wrong.

Measuring the streaming path as ``list(loader.load_streaming(path, n))``
reports **exactly the eager peak**. That is not a flaw in the loader; it
is the measurement retaining every chunk it was handed, which is the one
thing streaming exists to avoid. The number was wrong in a way that
looked plausible -- "streaming saves nothing" -- and would have been
quoted.

It is kept as a column rather than deleted because callers make the same
mistake in real code. `list(load_streaming(...))` costs what `load()`
costs; the saving comes from consuming each chunk and letting it go.

Read:

* **eager peak** -- everything held at once.
* **streamed peak** -- chunks consumed and released, which is the
  intended use and roughly flat in file size.
* **materialised peak** -- streamed and then kept, the mistake.

Run::

    python benches/bench_load_xlsx.py
    python benches/bench_load_xlsx.py --json
    python benches/bench_load_xlsx.py --quick     # what CI runs

One honest limit: peak comes from :mod:`tracemalloc`, which sees
Python-level allocations only. Whatever openpyxl's XML parsing allocates
in C is not counted, so treat these as a floor and a way to compare the
three paths against each other, not as a budget.

Nothing here asserts a threshold: wall-clock and memory are not
comparable between machines. CI runs ``--quick`` so a benchmark that has
stopped compiling against the current API fails the build instead of
rotting into a file that reads as verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook  # noqa: E402

from pain001_loader_xlsx import XlsxLoader  # noqa: E402

COLUMNS = (
    "id",
    "date",
    "amount",
    "currency",
    "debtor_name",
    "creditor_name",
    "debtor_iban",
    "creditor_iban",
    "remittance_information",
)

CHUNK = 500


def build_sheet(path: Path, rows: int) -> Path:
    """Write a ``rows``-row flat-record sheet to ``path``."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(COLUMNS)
    for index in range(rows):
        sheet.append(
            [
                str(index),
                "2026-08-20",
                "100.00",
                "EUR",
                f"Debtor {index}",
                f"Creditor {index}",
                "DE89370400440532013000",
                "GB29NWBK60161331926819",
                f"INVOICE {index}",
            ]
        )
    workbook.save(path)
    return path


def _peak(call) -> int:
    """Peak Python-level bytes allocated during ``call``."""
    tracemalloc.start()
    call()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def _time(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up."""
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _consume_streaming(loader: XlsxLoader, path: str) -> int:
    """Stream and release: the intended use. Returns rows seen."""
    seen = 0
    for chunk in loader.load_streaming(path, CHUNK):
        seen += len(chunk.rows)
    return seen


def measure(rows: int, directory: Path, repeats: int) -> dict:
    """Time and peak for all three paths over a ``rows``-row sheet."""
    loader = XlsxLoader()
    path = str(build_sheet(directory / f"bench-{rows}.xlsx", rows))

    eager_ms = _time(lambda: loader.load(path), repeats) * 1e3
    streamed_ms = _time(lambda: _consume_streaming(loader, path), repeats)
    streamed_ms *= 1e3

    return {
        "rows": rows,
        "eager_ms": eager_ms,
        "streamed_ms": streamed_ms,
        "eager_peak_mb": _peak(lambda: loader.load(path)) / 1e6,
        "streamed_peak_mb": (
            _peak(lambda: _consume_streaming(loader, path)) / 1e6
        ),
        "materialised_peak_mb": (
            _peak(lambda: list(loader.load_streaming(path, CHUNK))) / 1e6
        ),
    }


def run(quick: bool) -> dict:
    """Measure across file sizes."""
    sizes = [500, 2_000] if quick else [500, 2_000, 10_000]
    repeats = 1 if quick else 3
    with tempfile.TemporaryDirectory() as directory:
        rows = [measure(n, Path(directory), repeats) for n in sizes]
    return {"chunk_size": CHUNK, "rows": rows}


def render(results: dict) -> None:
    """Print the table and the verdict."""
    print(
        f"  chunk size {results['chunk_size']}\n\n"
        f"  {'rows':>7}{'eager ms':>11}{'stream ms':>11}"
        f"{'eager MB':>11}{'streamed MB':>14}{'materialised MB':>18}"
    )
    for row in results["rows"]:
        print(
            f"  {row['rows']:>7}{row['eager_ms']:>11.1f}"
            f"{row['streamed_ms']:>11.1f}{row['eager_peak_mb']:>11.2f}"
            f"{row['streamed_peak_mb']:>14.2f}"
            f"{row['materialised_peak_mb']:>18.2f}"
        )

    last = results["rows"][-1]
    if last["streamed_peak_mb"]:
        saving = last["eager_peak_mb"] / last["streamed_peak_mb"]
        print(
            f"\n  At {last['rows']:,} rows, streaming and releasing each "
            f"chunk peaks {saving:.1f}x lower than\n  loading everything, "
            f"and stays roughly flat as the file grows. Time is "
            f"unchanged --\n  openpyxl's parsing dominates both paths."
        )
    print(
        "\n  The last column is the mistake worth knowing about. "
        "`list(load_streaming(...))` costs\n  what `load()` costs: it "
        "retains every chunk, which is the one thing streaming exists\n  "
        "to avoid. The saving comes from consuming a chunk and letting it "
        "go."
    )
    print(
        "\n  Peak is tracemalloc, which sees Python allocations only -- "
        "openpyxl's C-level XML\n  parsing is not counted. Read these as a "
        "floor and as a comparison between the three\n  paths, not as a "
        "budget."
    )


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
