# CLARIS experiment execution status

Last updated: 2026-11-03 (UTC)

This status is separate from the target list in [CHAPTER_VII_EXPERIMENTS.md](CHAPTER_VII_EXPERIMENTS.md). A check is marked complete only when a corresponding run record exists.

## Completed

### 1. Upstream VOLEitH baseline

Pinned upstream commit: `fa540fa152303a23b55a0a63efe20977076a6e15`.

Two successful GitHub Actions runs provide one-shot measurements at 128 bits; the newer workflow also provides the matched 256-bit profile:

- Earlier 128-bit run: [#41467761462](https://github.com/fangbiaomail-code/CLARIS-experiments/actions/runs/41467761462), raw data in `results/raw/upstream_baseline_128.csv`.
- Newer 128-bit rerun: [#41581088450](https://github.com/fangbiaomail-code/CLARIS-experiments/actions/runs/41581088450), raw data in `results/raw/upstream_baseline_128_run2.csv`.
- Matched 256-bit baseline: [#41581088450](https://github.com/fangbiaomail-code/CLARIS-experiments/actions/runs/41581088450), raw data in `results/raw/upstream_baseline_256.csv`.

| N | 128-bit signature B | 128-bit sign ms (run 2) | 128-bit verify ms (run 2) | 256-bit signature B | 256-bit sign ms | 256-bit verify ms |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 4,594 | 8.732900 | 12.880490 | 20,184 | 11,524.973270 | 61.005410 |
| 64 | 4,594 | 8.739430 | 12.780180 | 20,184 | 16,153.537580 | 71.249180 |
| 256 | 4,594 | 8.798258 | 12.799480 | 20,184 | 11,298.807750 | 61.676680 |
| 1024 | 4,594 | 8.706277 | 12.765945 | 20,184 | 10,603.059960 | 61.750140 |

Each cell is one benchmark sample. The older 128-bit run is retained separately because it used a different hosted runner and gave different timings. These are reference observations, not statistically robust performance rankings. The 128-bit profile must not be compared as a matched-security result against the AES-256 CLARIS prototype.

### 2. Full-matrix CLARIS source build

The archived source was extended in a separate working copy to support the Chapter VII matrix. The extension is limited to the experimental harness and does not alter the vendor AES/VOLE implementation, Q-v2 batching patch, G-v1 ordinary relation, or transcript domains.

- Source integrity: 114 inventoried files pass after refreshing the inventory for this matrix revision.
- Clean build: ordinary target plus ring targets N = 16, 64, 256, 1024.
- Compiler: Clang 17.0.0.
- Flags: `-O2 -march=x86-64 -mavx2 -maes -mpclmul -DNDEBUG` plus the recorded platform defines.
- Host: AMD EPYC 9V74 80-Core Processor, x86_64 Linux; 5 CPUs exposed to this container.
- The build manifest is retained with the local run outputs.

### 3. Functional and algebraic checks

All four ring sizes passed the functional smoke suite:

| N | Joint checks | Fresh public verifier | Identity-free link verifier |
|---:|---:|---:|---:|
| 16 | 27/27 | 10/10 | 9/9 |
| 64 | 27/27 | 10/10 | 9/9 |
| 256 | 27/27 | 10/10 | 9/9 |
| 1024 | 27/27 | 10/10 | 9/9 |

The fresh verifier processes loaded public reports/certificates without loading signing keys. These are functional tests, not a cryptographic security proof.

Additional checks passed:

- AES byte pseudoinverse relation: 65,536 byte pairs checked; 256 satisfying pairs.
- Transcript namespace separation: 180 scalar/vector/stage/lane checks.
- Batching/selector algebra checks.
- Opening-bound exact-counting check.

Low-level selector transcript diagnostics passed for N = 16, 64, 256. The N=1024 selector diagnostic is still pending; it was not counted as passed in this run.

### 4. Earlier local CLARIS measurements

The repository retains earlier measurements from a different host/source run:

- N=64 ordinary-proof subset: 30 samples and 3 warm-ups for report, claim, Anchor and Bridge at s = 2, 3, 5; see [claris_local_n64_summary.csv](results/processed/claris_local_n64_summary.csv).
- N=16 full selected-size matrix summary: see [claris_local_n16_summary.csv](results/processed/claris_local_n16_summary.csv).
- Primitive microbenchmarks: 50,000 repetitions each for AES-256 key schedule, one-block AES-256 CTR and SHAKE256; see [primitive_benchmark.csv](results/raw/primitive_benchmark.csv).

Do not combine these earlier measurements with the new AMD EPYC/Clang 17 full-matrix run. Their host and source/build provenance differ.

## In progress

### 5. Full CLARIS matrix on one host

The current full run is using one build and one host for all ring sizes:

- N ∈ {16, 64, 256, 1024}
- s ∈ {2, 3, 5, 10, 20}
- Claim baseline at s=1
- Anchor and Bridge separately for every s >= 2
- 3 warm-ups and 30 measured repetitions per cell
- Fresh public-only reconstruction check after each ring size

The run writes raw per-cell JSON, request/proof fixtures, public verifier logs, and a hash manifest to the local `claris-results-fullmatrix/` directory. Results will be uploaded only after each ring size and its independent verifier pass.

## Not yet complete / limits

- The current full-matrix run has not yet completed.
- The full evidence package is an analytical byte-accounting model; no deployed network transfer was measured.
- The ordinary-pair benchmark separates original-report validation from core proof verification. It does not claim one combined end-to-end service latency.
- External constructions (Park–Sealfon, Fiore et al., DualRing-PRF, SPRING, Chiang et al., and TalosLogic) have a source-grounded construction/security comparison in [SECURITY_PROPERTY_COMPARISON.md](docs/SECURITY_PROPERTY_COMPARISON.md), but matched executable benchmarks beyond the pinned Chiang et al. baseline are not complete.
- The joint QROM proof-system transfer obligations and real-AES tuple assumptions remain conditional. Functional tests do not establish those security proofs.
- The full matrix source revision is currently a local working copy; the complete source tree and raw per-sample files are not yet committed to this repository.
