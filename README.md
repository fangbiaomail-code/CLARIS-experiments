# CLARIS Experiments

Public research workspace for reproducing and extending the CLARIS evaluation.

## Current execution status

See [EXPERIMENT_STATUS.md](EXPERIMENT_STATUS.md) for the experiment ledger, completed runs, parameters, and remaining work.

- Upstream VOLEitH baseline: 128-bit and matched 256-bit profiles completed for N = 16, 64, 256, 1024; each cell is a one-shot measurement.
- Earlier CLARIS prototype benchmark: N = 64 and 1024, s = 2, 3, 5; 30 samples and 3 warm-ups per configuration in the archived dataset.
- Anchor/Common Bridge controlled comparison and proof-size tables are archived under `results/processed/`.
- Full-matrix build and additional functional checks are described in [EXPERIMENT_STATUS.md](EXPERIMENT_STATUS.md); do not confuse these checks with a completed 30-run full N × s matrix.

## Chapter VII draft and data

- [Chinese Chapter VII draft](docs/VII_performance_evaluation_CN.md)
- [Benchmark scope and reproduction limitations](docs/experiment_limitations_and_reproduction_notes.md)
- [Benchmark-matrix extension note](docs/CLARIS_MATRIX_EXTENSION_NOTE.md)
- [Security/property comparison of related constructions](docs/SECURITY_PROPERTY_COMPARISON.md)
- [Report performance data](results/processed/report_performance.csv)
- [Claim/Anchor/Bridge performance data](results/processed/certificate_performance.csv)
- [Chapter VII benchmark provenance](results/metadata/claris_chapter_vii_benchmark_metadata.json)

## Important interpretation limits

The Chapter VII draft uses archived 2026-10-02 benchmark measurements. It does not claim those values were measured on the current hosted runner. The formal performance dataset covers N = 64, 1024 and s = 2, 3, 5 only. It does not contain measured N = 16, 256 or s = 10, 20 CLARIS performance cells.

External schemes have a source-grounded feature/construction comparison, but matched executable benchmarks against Park–Sealfon, Fiore et al., DualRing-PRF, SPRING, and other external schemes are not complete. The Chiang et al. upstream baseline is retained as a separate reference and is not a matched Claim/Link benchmark.

The full-matrix source extension and full raw per-sample matrix outputs are not currently committed as a self-contained source package in this repository. The matrix-extension note describes the intended harness changes and must not be mistaken for a completed full-matrix result.

## Repository layout

- `CHAPTER_VII_EXPERIMENTS.md`: Chapter VII experimental targets and acceptance checklist.
- `EXPERIMENT_STATUS.md`: actual run status and limitations.
- `docs/`: chapter draft, reproduction notes, and related-work comparison.
- `configs/`: benchmark matrix.
- `scripts/`: data aggregation utilities.
- `results/raw/`: raw or source-reported observations, clearly labelled by provenance.
- `results/processed/`: derived summaries.
- `results/metadata/`: host, compiler, source revision, and parameter records.

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
