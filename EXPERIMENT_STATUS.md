# CLARIS experiment execution status

Last updated: 2026-11-03 (UTC)

This status is separate from the Chapter VII target list in [CHAPTER_VII_EXPERIMENTS.md](CHAPTER_VII_EXPERIMENTS.md). A check is marked complete only when a corresponding run record exists.

## Completed

### 1. Upstream VOLEitH baseline — 128-bit profile

GitHub Actions run [#41467761462](https://github.com/fangbiaomail-code/CLARIS-experiments/actions/runs/41467761462) succeeded against pinned upstream commit `fa540fa152303a23b55a0a63efe20977076a6e15`.

| Ring size N | Signature bytes | Sign ms | Verify ms | Samples |
|---:|---:|---:|---:|---:|
| 16 | 4,594 | 4.709336 | 9.408377 | 1 |
| 64 | 4,594 | 4.713549 | 9.284365 | 1 |
| 256 | 4,594 | 5.205090 | 9.510123 | 1 |
| 1024 | 4,594 | 5.048226 | 9.223782 | 1 |

These are one-shot baseline observations, not a statistical performance comparison. The 128-bit baseline must not be ranked directly against the 256-bit CLARIS prototype.

### 2. Local CLARIS source build and checks

The archived CLARIS source artifact was extended in a separate working copy to support the complete ring/selection matrix. The extension changes only the experiment harness and supported ring-size list; it does not change the cryptographic relation or vendor implementation.

- Source inventory integrity: 114 files passed.
- Clean GCC build: ordinary proof target plus ring targets N = 16, 64, 256, 1024.
- Compiler: GCC 14.2.0; flags: `-O2 -march=x86-64 -mavx2 -maes -mpclmul -DNDEBUG`.
- Host: Intel Xeon Platinum 8573C, x86_64 Linux.
- Source inventory SHA-256: `f52e6c1fe5a562ca23137afa7dbcd1d2f53aa5e4a3ca1e26c857b9c7188de6be`.

Functional/algebraic checks passed:

- AES byte pseudoinverse relation: 65,536 byte pairs checked; 256 satisfying pairs.
- Transcript namespace checks: 180 scalar/vector/stage/lane checks.
- Batching/selector algebra checks passed.
- Opening-bound exact-counting check passed.
- Selector transcript diagnostics passed for N = 16, 64, 256, 1024. These are low-level functional diagnostics, not end-to-end forgery tests.
- Existing N=64 smoke suite: 27/27 joint checks, 10/10 fresh public joint-verifier checks, 9/9 fresh identity-free link-verifier checks.

### 3. Primitive microbenchmarks

50,000 repetitions per operation on the local host:

| Operation | Mean per call |
|---|---:|
| AES-256 key schedule | 0.133996 μs |
| One-block AES-256 CTR encryption | 0.004248 μs |
| SHAKE256, 64-byte input to 32-byte output | 0.480534 μs |

The source's hash interface invokes SHAKE256; these results are labelled SHAKE256, not fixed-output SHA3.

### 4. CLARIS N=64 ordinary-proof measurements

A separate 30-sample run with 3 warm-ups completed for report, claim, and Anchor/Bridge cells at s = 2, 3, 5. The processed table is [claris_local_n64_summary.csv](results/processed/claris_local_n64_summary.csv).

Selected values:

- Report proof: 50,660 bytes; generation mean 104.243 ms; verification mean 127.201 ms.
- Ordinary Claim proof: 49,208 bytes; generation mean 64.137 ms; core verification mean 89.922 ms.
- Three-report link: Anchor 98,416 proof bytes (2 proofs); Bridge 147,624 proof bytes (3 proofs).

### 5. CLARIS N=16 full-matrix measurements

N=16 has completed all 11 cells (Claim plus Anchor/Bridge at s = 2, 3, 5, 10, 20), with 30 samples and 3 warm-ups per cell. The fresh public verifier reconstructed all reports/statements without loading private keys.

Processed table: [claris_local_n16_summary.csv](results/processed/claris_local_n16_summary.csv).

Selected values:

- Report proof: 50,638 bytes; generation mean 72.015 ms; verification mean 96.447 ms.
- Claim proof: 49,208 bytes.
- At s=20, Anchor uses 19 proofs (934,952 bytes); Bridge uses 20 proofs (984,160 bytes).
- Peak worker RSS recorded for the s=20 Anchor cell: 20,455,424 bytes.

The s=10 Bridge timings have high dispersion; the sample statistics are retained rather than hiding the outliers.

## In progress

### 6. Full CLARIS matrix

The extended local benchmark is running with:

- N ∈ {16, 64, 256, 1024}
- s ∈ {2, 3, 5, 10, 20}
- Anchor and Bridge measured separately
- 30 measured repetitions and 3 warm-ups per cell

N=16 is complete. N=64 is currently running. The matrix will be marked complete only after all four ring sizes finish and each independent public-verifier reconstruction succeeds.

### 7. Matched 256-bit upstream baseline

GitHub Actions run [#41581088450](https://github.com/fangbiaomail-code/CLARIS-experiments/actions/runs/41581088450) is building the upstream 256-bit CCCS profile at the same four ring sizes. It is still running. This is the required security-level-matched baseline; the earlier 128-bit run is retained as a separate reference.

## Not yet complete / limits

- The full N × s CLARIS matrix has not yet completed.
- The full evidence package is still an analytical byte-accounting model; no deployed network transfer was measured.
- The ordinary-pair benchmark does not produce one combined end-to-end verifier latency. Report validation, proof verification, and wrapper checks remain separate.
- External constructions (Park–Sealfon, Fiore et al., DualRing-PRF, SPRING, Chiang et al., and TalosLogic) have a source-grounded construction/security comparison in [SECURITY_PROPERTY_COMPARISON.md](docs/SECURITY_PROPERTY_COMPARISON.md), but matched executable benchmarks beyond the Chiang et al. upstream baseline are not complete.
- The joint QROM proof-system transfer obligations and real-AES tuple assumptions remain conditional. Functional tests do not establish those security proofs.
- The matrix-extension source copy and raw per-sample files are currently in the working experiment environment; they have not yet been committed as a complete source tree to this repository.
