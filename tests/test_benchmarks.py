"""Performance benchmarks for the XLSX loader.

Three things, guarding three different failures.

``test_load_1000_rows`` is the measurement: it records what loading a
realistic sheet costs so the number lands in a CI artifact and can be
compared release over release.

``test_loading_scales_linearly`` is the regression guard. An absolute
wall-clock threshold on a shared runner has to be loose enough to
survive a noisy neighbour, and by then it only catches catastrophes.
Comparing the loader against itself at two sizes is machine-independent:
a runner twice as slow scales both measurements equally and the ratio
holds. Measured here, loading is linear -- 4x the rows costs 4.21x the
time -- so the ceiling is 8, against ~16 for quadratic.

``test_streaming_does_not_hold_every_row`` guards the reason
``load_streaming`` exists. Its contract is bounded memory, and the way
that breaks is not a slowdown: someone materialises the sheet and then
slices it, which passes every correctness test and every timing check
while quietly using memory proportional to the file. Peak allocation is
the only thing that catches it.
"""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path

import pytest
from openpyxl import Workbook

from pain001_loader_xlsx._normalise import to_text
from pain001_loader_xlsx.loader import XlsxLoader

COLUMNS = [
    "id",
    "date",
    "amount",
    "currency",
    "debtor_name",
    "creditor_name",
    "debtor_account_IBAN",
    "creditor_account_IBAN",
    "remittance_information",
]

#: Ratio ceiling for a 4x increase in row count. Linear is ~4,
#: quadratic is ~16.
MAX_SCALING_RATIO = 8.0


def build_sheet(path: Path, rows: int) -> Path:
    """Write an ``rows``-row flat-record sheet to ``path``."""
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


def _best_of(loader: XlsxLoader, path: Path, rounds: int = 3) -> float:
    """Fastest load of ``path`` in seconds.

    The minimum rather than the mean: least disturbed by an unrelated
    process getting the CPU.
    """
    loader.load(str(path))
    timings = []
    for _ in range(rounds):
        started = time.perf_counter()
        loader.load(str(path))
        timings.append(time.perf_counter() - started)
    return min(timings)


@pytest.mark.benchmark
def test_load_1000_rows(benchmark, tmp_path) -> None:
    """Benchmark loading a 1000-row sheet."""
    path = build_sheet(tmp_path / "bench.xlsx", 1000)
    loader = XlsxLoader()

    result = benchmark(loader.load, str(path))

    # A benchmark that silently loaded nothing would still look fast.
    assert len(result.rows) == 1000
    assert result.rows[0]["amount"] == "100.00"


@pytest.mark.benchmark
def test_loading_scales_linearly(tmp_path) -> None:
    """Loading 4x the rows must not cost ~16x the time."""
    loader = XlsxLoader()
    small = _best_of(loader, build_sheet(tmp_path / "small.xlsx", 1000))
    large = _best_of(loader, build_sheet(tmp_path / "large.xlsx", 4000))

    ratio = large / small
    assert ratio < MAX_SCALING_RATIO, (
        f"loading 4000 rows took {ratio:.1f}x loading 1000 "
        f"({large * 1000:.0f}ms vs {small * 1000:.0f}ms); linear is ~4x "
        f"and quadratic is ~16x"
    )


@pytest.mark.benchmark
def test_streaming_does_not_hold_every_row(tmp_path) -> None:
    """Streaming must not allocate in proportion to the file.

    The failure guarded here is someone re-implementing
    ``load_streaming`` as ``load`` plus slicing. That keeps every row
    correct and every timing unchanged, so only peak allocation
    distinguishes it.
    """
    path = build_sheet(tmp_path / "stream.xlsx", 4000)
    loader = XlsxLoader()

    tracemalloc.start()
    try:
        seen = 0
        for chunk in loader.load_streaming(str(path), chunk_size=100):
            seen += len(chunk.rows)
        _, streaming_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert seen == 4000

    tracemalloc.start()
    try:
        loader.load(str(path))
        _, full_peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    # Deliberately not `streaming_peak < full_peak`. A naive
    # implementation measures a hair *under* a full load (3642 KiB vs
    # 3628 KiB here) because it is a full load plus slicing, so that
    # comparison flips on noise. Requiring a real margin does not: true
    # streaming peaks at ~885 KiB against ~3628 KiB, a 4x gap.
    budget = full_peak / 2
    assert streaming_peak < budget, (
        f"streaming peaked at {streaming_peak / 1024:.0f} KiB against a "
        f"budget of {budget / 1024:.0f} KiB (half the {full_peak / 1024:.0f} "
        f"KiB a full load takes) — load_streaming looks like it is "
        f"materialising the sheet and slicing it rather than streaming"
    )


#: Ceiling on streaming cost relative to a full load. Measured 0.94-1.25x.
MAX_STREAMING_OVERHEAD = 2.0


class TestStreamingThroughput:
    """Streaming buys bounded memory, not speed.

    ``test_streaming_does_not_hold_every_row`` pins the memory property.
    This pins the other half of the trade, which is easy to lose sight
    of: streaming should cost roughly what a full load costs. Measured
    across chunk sizes it lands at 0.94x, 1.13x and 1.25x of a full
    load, so the cost of chunking is noise rather than a tax.

    The regression this guards is chunking becoming expensive in its own
    right -- re-opening the workbook per chunk, say -- which would keep
    every row correct and every memory assertion passing while making
    the API pointless for the large files it exists for.
    """

    @pytest.mark.benchmark
    def test_streaming_costs_about_the_same_as_loading(self, tmp_path) -> None:
        """Chunking must not add meaningful overhead."""
        path = build_sheet(tmp_path / "throughput.xlsx", 2000)
        loader = XlsxLoader()

        def stream() -> int:
            seen = 0
            for chunk in loader.load_streaming(str(path), chunk_size=500):
                seen += len(chunk.rows)
            return seen

        full = _best_of(loader, path)
        stream()
        timings = []
        for _ in range(3):
            started = time.perf_counter()
            assert stream() == 2000
            timings.append(time.perf_counter() - started)
        streaming = min(timings)

        overhead = streaming / full
        assert overhead < MAX_STREAMING_OVERHEAD, (
            f"streaming 2000 rows cost {overhead:.2f}x a full load "
            f"({streaming * 1000:.0f}ms vs {full * 1000:.0f}ms); chunking "
            f"should be close to free, so this suggests per-chunk work "
            f"that belongs outside the loop"
        )


class TestValueNormalisation:
    """The per-cell conversion added when values became text.

    ``to_text`` runs once per cell, so it scales with the whole sheet
    rather than the row count: at ~1.67us per cell and nine columns, a
    2000-row sheet spends roughly 30ms of its ~156ms load here. Not the
    dominant cost -- openpyxl's parsing is -- but the largest piece this
    package actually owns, and the one most likely to grow if the
    formatting rules get richer.
    """

    @pytest.mark.benchmark
    def test_to_text_on_a_formatted_number(self, benchmark) -> None:
        """Benchmark the common case: a currency-formatted float."""
        result = benchmark(to_text, 100.0, "0.00")

        # Trailing zeros are the whole point of consulting the format.
        assert result == "100.00"
