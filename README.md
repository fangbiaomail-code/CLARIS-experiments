# CLARIS Experiments

Public research workspace for reproducing and extending the CLARIS evaluation.

## Current execution status

See [EXPERIMENT_STATUS.md](EXPERIMENT_STATUS.md) for the live experiment ledger, completed runs, parameters, and remaining work.

- Upstream VOLEitH 128-bit baseline: completed for N = 16, 64, 256, 1024 (one sample per ring size).
- Local CLARIS N=64 ordinary-proof measurements: completed with 30 samples and 3 warm-ups for report, claim, Anchor, and Bridge at s = 2, 3, 5.
- Primitive microbenchmarks: 50,000 repetitions each for AES-256 key schedule, one-block AES-256 CTR, and SHAKE256.
- Full CLARIS matrix N ∈ {16, 64, 256, 1024}, s ∈ {2, 3, 5, 10, 20}: running.
- Security-level-matched 256-bit upstream baseline: GitHub Actions run in progress.

## Important reproducibility note

The CLARIS-specific source package is currently being maintained in a separate working copy and is not yet committed as a complete source tree in this repository. The results committed here are explicitly labelled by their source/build provenance. Do not treat this workspace as fully self-contained until the source package and matrix runner are committed.

## What is reported in the manuscript

- Ordinary claim/link proof size: 49,208 bytes.
- Three-report link core proof size: 98,416 bytes.
- Ordinary-certificate functional checks: 27/27 at ring sizes 64 and 1024.
- Fresh public joint-verifier checks: 10/10 at both ring sizes.
- Fresh identity-free link-verifier checks: 9/9 at both ring sizes.
- Anchor-versus-bridge ablation: three measured runs per cell after one warm-up, for N = 64 and 1024 and s = 2, 3, 5.

The manuscript explicitly distinguishes measured proof objects from analytical communication costs and does not claim a measured end-to-end service latency.

## Repository layout

- `CHAPTER_VII_EXPERIMENTS.md`: Chapter VII experimental targets and acceptance checklist.
- `EXPERIMENT_STATUS.md`: actual run status and limitations.
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
5. Never combine Anchor/Bridge timings from the repeated-OR ablation with ordinary-pair timings.
6. Do not label analytical byte counts as measured network traffic.
7. External schemes must be compared only when implementation, security target, and measured operation are sufficiently matched. Otherwise report construction-level properties separately.

## Upstream reference

Chiang et al., *PQ-Threshold-Ring-Sigs-from-VOLEitH*, pinned source revision:
`fa540fa152303a23b55a0a63efe20977076a6e15`.

The upstream implementation is a dependency/reference point; it is not by itself the CLARIS implementation.
