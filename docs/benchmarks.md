# Benchmarks

`XlsxLoader` has two entry points and the difference between them is
entirely about memory. `load` returns every row at once;
`load_streaming` yields fixed-size chunks so a caller can process a large
file without holding all of it. Time is nearly identical either way —
openpyxl's parsing dominates both — so the only question worth measuring
is whether streaming actually bounds the peak.

```sh
python benches/bench_load_xlsx.py           # full run
python benches/bench_load_xlsx.py --quick   # what CI runs
python benches/bench_load_xlsx.py --json    # machine-readable
```

## Measured (chunk size 500)

| rows | eager ms | stream ms | eager MB | streamed MB | materialised MB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 42.6 | 43.7 | 0.85 | 0.77 | 0.85 |
| 2,000 | 145.6 | 135.6 | 2.02 | 1.30 | 2.02 |
| 10,000 | 850.7 | 811.8 | 8.73 | **1.96** | 8.73 |

At 10,000 rows, streaming and releasing each chunk peaks **4.5× lower**
than loading everything, and stays roughly flat as the file grows. Time
is unchanged.

## The third column

`materialised MB` is `list(loader.load_streaming(path, 500))` — streamed
and then kept. It costs **exactly** what `load()` costs, because it
retains every chunk, which is the one thing streaming exists to avoid.

It is in the table because the first version of this benchmark measured
the streaming path that way and reported "streaming saves nothing" — a
wrong number that looked plausible enough to quote. Callers make the same
mistake in real code.

**The saving comes from consuming a chunk and letting it go**, not from
calling `load_streaming` instead of `load`.

## One honest limit

Peak comes from `tracemalloc`, which sees Python-level allocations only.
Whatever openpyxl's XML parsing allocates in C is not counted. Read these
as a floor, and as a comparison between the three paths — not as a
budget.
