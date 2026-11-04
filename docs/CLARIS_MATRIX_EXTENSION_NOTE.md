# CLARIS benchmark-matrix extension

Status: **completed and published** (2026-11-04). The earlier version of this note described a
planned extension that existed only in a local working copy. The extension and its outputs are
now part of this repository.

## What was extended

Harness-only changes; the vendor AES/VOLE implementation, the Q-v2 batching patch, the G-v1
ordinary relation and the transcript domains are unchanged.

1. `experiments/validate.c`: NR 7 → 20, so up to 20 distinct reports can be selected.
2. `experiments/benchmark/ordinary_worker.c`: ordinary batch bound 31 (supports Bridge s=20).
3. `experiments/benchmark/ordinary_benchmark.c`: selection sizes 1,2,3,5,10,20; original-report
   validation is timed for every selected-set size (including s=10 and s=20); the driver's peak
   RSS is written to `reports.json`.

The three modified files are recorded in `artifact/source/provenance/benchmark_revision.json`
with their previous and current SHA-256 values, and the source inventory is refreshed for
exactly those files.

## What was run

- One build, one host: N ∈ {16, 64, 256, 1024}, s ∈ {2, 3, 5, 10, 20}, plus the s = 1 claim baseline.
- 3 warm-ups and 30 measured samples per cell; raw per-sample timings kept.
- Anchor and Bridge measured for every s ≥ 2; original-report validation timed separately.
- Fresh public-only reconstruction after each ring size.
- Primitive microbenchmarks and functional/adversarial checks at all four ring sizes.

The complete source package and harness are in `artifact/`; aggregated data, raw CSVs, figures,
tables and environment records are under `results/` and `docs/`.

## Scope that still does not change

The benchmark remains in-memory proof generation/verification and original-report validation.
It does not produce a single end-to-end full-verification timer and it does not measure network
transfer. External schemes still have no matched executable benchmark beyond the pinned
Chiang et al. baseline.
