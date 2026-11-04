# CLARIS matrix artifact (source + harness)

This directory publishes the exact source package and experiment harness used for the
Chapter VII full-matrix run recorded on 2026-11-04. It closes the earlier gap where the
matrix extension and its harness existed only in a local working copy.

## Contents

| Path | Purpose |
|---|---|
| `source/` | CLARIS source package (CLARIS-Q-v2-G-v1) plus the recorded harness extension. `python3 source/verify_sources.py` checks the 113-file inventory. |
| `source/provenance/benchmark_revision.json` | Exact harness-only changes applied for this matrix (see below). |
| `benchmark/run_full_matrix.py` | Runs N ∈ {16,64,256,1024} × s ∈ {1,2,3,5,10,20} with 3 warm-ups and 30 measured samples per cell, verifies every cell, runs the fresh public reconstruction, and records peak RSS. |
| `benchmark/run_functional.py` | Functional and adversarial checks at all four ring sizes, with two public verifier processes. |
| `benchmark/basic_benchmark_full.c` | Six primitive microbenchmarks, 50 samples × 3 warm-ups each. |
| `benchmark/analyze_full_matrix.py` | Produces the CSVs, linear fits, tables and Chapter VII figures. |
| `benchmark/export_to_repo.py` | Copies derived artifacts into this repository. |
| `diagnostics/make_counters.py` | Counter-instrumented diagnostic build (call counts only; its timings are not used). |
| `diagnostics/summarize_counts.py` | Turns the counter runs into the operation-count table. |

The vendor AES/VOLE implementation, the Q-v2 batching patch, the G-v1 ordinary relation
and the transcript domains are unchanged. All changes are confined to the benchmark
harness and are listed in `source/provenance/benchmark_revision.json`:

1. `experiments/validate.c`: NR 7 → 20 so up to 20 distinct reports can be selected.
2. `experiments/benchmark/ordinary_worker.c`: ordinary batch bound 31 (supports Bridge s=20).
3. `experiments/benchmark/ordinary_benchmark.c`: original-report validation is timed for
   every selected-set size (including s=10 and s=20), and the driver's peak RSS is written
   to `reports.json`.
4. `experiments/benchmark/ordinary_benchmark.c` selection sizes extended to 1,2,3,5,10,20.

Source integrity is refreshed in `source/provenance/source_inventory.json` for exactly these
three files; `benchmark_revision.json` records the previous and current hashes.

## Build

```sh
cd artifact
python3 source/verify_sources.py
python3 benchmark/build.py --output build --ring-sizes 16 64 256 1024
```

`build.py` must run from `benchmark/` (it resolves `../source`). On Apple Silicon it emits
x86_64 binaries that require Rosetta 2; the 2026-11-04 run used Rosetta translation, not a
native ARM backend. The build records compiler commands, source hashes and binary hashes in
`build/build_manifest.json`.

## Run

```sh
python3 benchmark/run_full_matrix.py --build build --output results/fullmatrix \
    --repeats 30 --warmups 3
```

The driver runs ring sizes sequentially, writes raw per-sample JSON for every cell, asserts
proof counts (`claim = 1`, `anchor = s-1`, `bridge = s`), and launches a fresh public-only
verifier for each ring size. `--resume` reuses completed cell files.

To rebuild the primitive table:

```sh
clang -arch x86_64 -O2 -march=x86-64 -mavx2 -maes -mpclmul -DNDEBUG \
  -D_bswap64=__builtin_bswap64 -std=c11 -I build/ordinary \
  benchmark/basic_benchmark_full.c build/ordinary/*.o -o build/basic_benchmark_full
./build/basic_benchmark_full > results/raw/basic_operations.json
```

## Important interpretation limits

- All timings are x86_64 binaries executed through Rosetta 2 on an Apple M1 host. Absolute
  values include translation overhead and must not be presented as native x86_64 hardware.
- Report timers and ordinary-proof timers have different scopes; the "combined" verification
  number is the sum of two separately measured medians, not one end-to-end timer.
- Communication numbers are byte accounting over measured fixtures and compiled constants;
  no network transfer was measured.
- Anchor and Bridge are compared inside this artifact. No matched executable benchmark
  against Park–Sealfon, Fiore et al., DualRing-PRF, SPRING or TalosLogic is included.
- The functional and timing experiments do not prove the conditional QROM security theorem.
