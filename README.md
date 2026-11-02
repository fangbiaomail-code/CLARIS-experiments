# CLARIS Experiments

Public research workspace for reproducing and extending the CLARIS evaluation.

## Current implementation status

This repository is being initialized as the experiment workspace. The manuscript currently available to the project describes a prototype built on the VOLE-in-the-head ring-signature implementation by Chiang et al., pinned at commit `fa540fa152303a23b55a0a63efe20977076a6e15`.

**Important:** the CLARIS-specific source changes and executable are not yet present in this repository. Therefore, this repository does not claim that the benchmark matrix below has been run. Existing manuscript measurements are recorded as prior reported results, not as newly reproduced results.

## What is already reported in the manuscript

- Ordinary claim/link proof size: 49,208 bytes.
- Three-report link core proof size: 98,416 bytes.
- Ordinary-certificate functional checks: 27/27 at ring sizes 64 and 1024.
- Fresh public joint-verifier checks: 10/10 at both ring sizes.
- Fresh identity-free link-verifier checks: 9/9 at both ring sizes.
- Anchor-versus-bridge ablation: three measured runs per cell after one warm-up, for N = 64 and 1024 and s = 2, 3, 5.
- The manuscript explicitly identifies ordinary-pair latency, peak memory, native ARM measurements, matched external compiler implementations, and end-to-end service measurements as not yet measured.

See [CHAPTER_VII_EXPERIMENTS.md](CHAPTER_VII_EXPERIMENTS.md) for the consolidated Chapter VII experiment plan and [results/README.md](results/README.md) for data conventions.

## Repository layout

- `docs/`: experimental protocol and comparison methodology.
- `configs/`: benchmark matrix.
- `scripts/`: data aggregation utilities.
- `results/raw/`: unmodified per-run measurements (CSV).
- `results/processed/`: aggregated tables and plots.

## Reproducibility rules

1. Record the source commit, compiler, flags, CPU, OS, and dependency versions for every run.
2. Keep raw samples; do not store only averages.
3. Separate report signing, report verification, claim generation/verification, link generation/verification, and full verification.
4. Distinguish additional-certificate verification from full verification including original reports.
5. Never combine Anchor/Bridge timings from the repeated-OR ablation with ordinary-pair timings.
6. Do not label analytical byte counts as measured network traffic.
7. External schemes must be compared only when the implementation, security target, and measured operation are sufficiently matched. Otherwise report construction-level properties separately.

## Upstream reference

Chiang et al., *PQ-Threshold-Ring-Sigs-from-VOLEitH*, pinned source revision:
`fa540fa152303a23b55a0a63efe20977076a6e15`.

The upstream implementation is a dependency/reference point; it is not by itself the CLARIS implementation.
