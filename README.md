# CLARIS Experiments

Public research workspace for reproducing and extending the CLARIS evaluation.

## Current execution status

See [EXPERIMENT_STATUS.md](EXPERIMENT_STATUS.md) for the experiment ledger, parameters and remaining work.

- **Full Chapter VII matrix completed on 2026-11-04.** N ∈ {16, 64, 256, 1024} × s ∈ {2, 3, 5, 10, 20}, plus the s = 1 claim baseline; Anchor and Common Bridge measured separately; 3 warm-ups and 30 measured samples per cell (44 certificate cells, 4 report cells, 1,440 raw samples); one build and one host.
- Primitive microbenchmarks (6 operations, 50 samples each), counter-derived primitive call counts, functional checks at all four ring sizes, peak-RSS and byte-accounting tables are complete.
- The exact source package and harness used for the run are published in [`artifact/`](artifact/README.md).
- External schemes still have no matched executable benchmark; the pinned Chiang et al. baseline remains descriptive reference data.

## Chapter VII draft and data

- [Chinese Chapter VII draft](docs/VII_performance_evaluation_CN.md)
- [Full-matrix tables (Chinese)](docs/chapter_vii_tables_CN.md) / [English](docs/chapter_vii_tables_EN.md)
- [Benchmark scope and reproduction limitations](docs/experiment_limitations_and_reproduction_notes.md)
- [Benchmark-matrix extension note](docs/CLARIS_MATRIX_EXTENSION_NOTE.md)
- [Security/property comparison of related constructions](docs/SECURITY_PROPERTY_COMPARISON.md)
- [Full-matrix index](results/processed/full_matrix_index.json)
- [Ring-size results](results/processed/full_matrix_ring_scalability.csv)
- [Claim/Anchor/Bridge results](results/processed/full_matrix_certificate_scalability.csv)
- [Anchor/Bridge ablation](results/processed/full_matrix_anchor_bridge_ablation.csv)
- [Communication accounting](results/processed/full_matrix_communication_overhead.csv)
- [Primitive operations](results/processed/full_matrix_basic_operations.csv)
- [Primitive call counts](results/processed/full_matrix_operation_counts.csv)
- [Environment](results/metadata/full_matrix_environment.json) and [build summary](results/metadata/full_matrix_build_summary.json)

## Important interpretation limits

- The 2026-11-04 matrix is one build and one host: Apple M1, macOS 15.3, Apple Clang 16.0, x86_64 AVX2/AES/PCLMUL executed through Rosetta 2. Absolute times include translation overhead and are not native x86_64 or ARM values.
- `complete_verify_median_ms` is the sum of two separately measured medians (original-report validation and core proof verification), not one end-to-end timer.
- Anchor/Bridge timing differences at large s are comparable to the ~10% cell-to-cell variation of the fanless host; ablation conclusions therefore rest on proof counts, proof sizes and the proof-count linear fit (R² > 0.9996).
- External schemes have a source-grounded feature/construction comparison, but no matched executable benchmark. The Chiang et al. baseline is not a matched Claim/Link benchmark.
- Communication sizes are byte accounting, not measured network traffic.
- The first N=16 run was affected by a preceding functional suite; N=16 was re-measured and the provenance is recorded in `results/aggregate_full_matrix.json`.

## Repository layout

- `artifact/`: source package, harness extension, run scripts and counter diagnostics used for the 2026-11-04 matrix.
- `CHAPTER_VII_EXPERIMENTS.md`: Chapter VII experimental targets and acceptance checklist.
- `EXPERIMENT_STATUS.md`: actual run status and limitations.
- `docs/`: chapter draft, tables, figures, reproduction notes, related-work comparison.
- `configs/`: benchmark matrix.
- `scripts/`: data aggregation utilities.
- `results/raw/`: raw or source-reported observations, clearly labelled by provenance.
- `results/processed/`: derived summaries.
- `results/metadata/`: host, compiler, source revision, parameter records.

## Reproducibility rules

1. Record source revision, compiler, flags, CPU, OS, and dependency versions for every run.
2. Keep raw samples; do not store only averages.
3. Separate report signing, report verification, claim generation/verification, link generation/verification, and full verification.
4. Distinguish additional-certificate verification from full verification including original reports.
5. Never combine Anchor/Bridge timings from different benchmark profiles or hosts.
6. Do not label analytical byte counts as measured network traffic.
7. External schemes must be compared only when implementation, security target, and measured operation are sufficiently matched. Otherwise report construction-level properties separately.

## Upstream reference

Chiang et al., *PQ-Threshold-Ring-Sigs-from-VOLEitH*, pinned source revision:
`fa540fa152303a23b55a0a63efe20977076a6e15`.

The upstream implementation is a dependency/reference point; it is not by itself the CLARIS implementation.
