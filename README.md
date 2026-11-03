# CLARIS Experiments

Public research workspace for reproducing and extending the CLARIS evaluation.

## Current execution status

See [EXPERIMENT_STATUS.md](EXPERIMENT_STATUS.md) for the experiment ledger, completed runs, parameters, and remaining work.

- Upstream VOLEitH baseline: 128-bit and matched 256-bit profiles completed for N = 16, 64, 256, 1024; each cell is a one-shot measurement.
- Full-matrix CLARIS source build: successful for N = 16, 64, 256, 1024.
- Functional smoke checks: all four ring sizes passed (27 joint checks, 10 fresh public-verifier checks, 9 identity-free link-verifier checks per N).
- AES-byte, batching-algebra, opening-bound, and transcript-namespace checks: passed.
- Full CLARIS matrix N ∈ {16, 64, 256, 1024}, s ∈ {2, 3, 5, 10, 20}: running with 3 warm-ups and 30 measured repetitions per cell. Anchor and Bridge are measured separately.
- Earlier N=16 and N=64 measurements remain archived separately because they use a different host/source run; do not mix them with the current full-matrix run.

## Important reproducibility note

The matrix-extension source is currently maintained in a local working copy and is not yet committed as a complete source tree in this repository. The committed results are labelled by source/build provenance. Do not treat this repository as fully self-contained until the source package and matrix runner are committed.

## Experimental comparison

[SECURITY_PROPERTY_COMPARISON.md](docs/SECURITY_PROPERTY_COMPARISON.md) distinguishes claimability, user-controlled linking, tag-based linkability, accountable opening, and CLARIS's selected post-hoc association. It also states the conditional security scope and which external implementations have not been benchmarked.

## Manuscript-reported construction costs

- Ordinary claim/link proof size: 49,208 bytes.
- Three-report link core proof size: 98,416 bytes.
- The manuscript distinguishes measured proof objects from analytical communication costs and does not claim measured end-to-end network traffic or service latency.

## Repository layout

- `CHAPTER_VII_EXPERIMENTS.md`: Chapter VII experimental targets and acceptance checklist.
- `EXPERIMENT_STATUS.md`: actual run status and limitations.
- `docs/SECURITY_PROPERTY_COMPARISON.md`: source-grounded comparison of related constructions and security scopes.
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
