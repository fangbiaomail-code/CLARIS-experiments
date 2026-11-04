# CLARIS experiment execution status

Last updated: 2026-11-04 (UTC)

This status is separate from the target list in [CHAPTER_VII_EXPERIMENTS.md](CHAPTER_VII_EXPERIMENTS.md). A check is marked complete only when a corresponding run record exists.

## Completed

### 1. Full CLARIS matrix on one build and one host (2026-11-04)

The full Chapter VII matrix has been measured:

- N ∈ {16, 64, 256, 1024}; s ∈ {2, 3, 5, 10, 20}; claim baseline at s = 1.
- Anchor and Common Bridge measured separately for every s ≥ 2.
- 3 warm-ups and 30 measured samples in every cell (44 certificate cells and 4 report cells; 1,440 timed samples, all raw samples retained).
- Original-report validation timed separately for every cell, including s = 10 and s = 20.
- Fresh public-only reconstruction (`PUBLIC_RECONSTRUCTION_VERIFIED_NO_PRIVATE_KEY`) after each ring size; no signing keys loaded.
- One build for all ring sizes, transcript profile CLARIS-Q-v2-G-v1.

Environment: Apple M1, 8 GiB, macOS 15.3 (24D60), Apple Clang 16.0.0; x86_64 target with AVX2/AES-NI/PCLMUL executed through Rosetta 2. Build manifest SHA-256 `534301c2171bfbbea5fe3f62da6a95e5661b6064522894427cebc1a32193119e`; build provenance in `results/metadata/full_matrix_build_summary.json`.

| N | report proof B | report gen ms | report ver ms | claim gen ms | claim ver ms | original-set (s=20) ms |
|---:|---:|---:|---:|---:|---:|---:|
| 16 | 50,638 | 293.80 | 358.02 | 283.51 | 356.98 | 7,132 |
| 64 | 50,660 | 319.87 | 380.40 | 278.57 | 351.58 | 8,023 |
| 256 | 50,704 | 450.91 | 486.79 | 292.40 | 366.91 | 9,748 |
| 1024 | 50,792 | 896.12 | 834.28 | 286.72 | 363.63 | 16,066 |

All values are medians of 30 measured samples. Claim/link proofs are 49,208 B each. Link generation is linear in the number of ordinary proofs: 271.6–291.6 ms per proof generation and 343.2–366.2 ms per proof verification, with R² > 0.9996 over all s = 1…20 cells of each ring size.

The first N=16 run started immediately after a ~5-minute functional suite and its report cell was ~10% slow (324.0 ms vs 291.9 ms in a control re-measurement). N=16 was re-measured on the same build and host; the re-measured cells are used and the first run is preserved in `results/fullmatrix/n16`. Provenance is recorded in `results/aggregate_full_matrix.json`.

### 2. Primitive microbenchmarks

Six operations actually used by the code, 50 samples each with 3 warm-ups and inner repetitions: AES-256 key schedule, AES-256 CTR block, SHAKE256, rand_bytes, vendor small-VOLE sender and receiver. See `results/processed/full_matrix_basic_operations.csv` and `results/raw/full_matrix_primitive_samples.csv`.

### 3. Primitive call counts from a counter build

A separate counter-instrumented build counts AES key schedules, AES-256 blocks, SHAKE256 init/update/final and VOLE sender/receiver calls per operation. Counts are in `results/processed/full_matrix_operation_counts.csv`; the diagnostic build is not used for timing.

### 4. Functional checks at all four ring sizes

All four ring sizes pass the joint, fresh-public and identity-free link checks (53 / 23 / 22 checks under the 20-report fixture), with temporary signing keys removed. These are functional checks, not a security proof.

### 5. Anchor/Bridge ablation, peak RSS and communication accounting

- Ablation: Anchor uses s−1 ordinary proofs and Bridge s; the proof-size saving is exactly 49,208 B (1/s of the certificate). See `results/processed/full_matrix_anchor_bridge_ablation.csv`.
- Peak RSS: proving worker 71.7–95.7 MiB; report-generation driver 71.8–87.5 MiB; independent public verification 50.7–58.0 MiB.
- Communication: byte accounting only, distinguishing proof-only, certificate + references, and complete evidence package (`results/processed/full_matrix_communication_overhead.csv`).

### 6. Published artifact

`artifact/` contains the exact source package, the harness extension and the scripts used for the run (build, matrix driver, functional checks, primitive benchmark, analysis, counter diagnostics). The harness changes are recorded with previous/current SHA-256 in `artifact/source/provenance/benchmark_revision.json`.

### 7. Upstream VOLEitH baseline (archived)

Pinned upstream commit `fa540fa152303a23b55a0a63efe20977076a6e15`; 128-bit and matched 256-bit one-shot observations for N = 16, 64, 256, 1024 remain in `results/raw/upstream_baseline_*.csv`. They are descriptive only and are not a matched-security comparison with CLARIS.

## Not complete / limits

- External schemes (Park–Sealfon, Fiore et al., DualRing-PRF, SPRING, TalosLogic) still have no matched executable benchmark. The published Chiang et al. implementation is the only runnable external baseline; its security profile differs from the AES-256 CLARIS prototype and each N has one sample, so no speed ranking is computed.
- All timings are Rosetta-translated x86_64 execution on an Apple Silicon host, not native x86_64 or ARM.
- `complete_verify_median_ms` is the sum of two separately measured medians (original-set validation and ordinary proof verification), not one end-to-end timer.
- Communication sizes are byte accounting over measured fixtures and compiled constants; no deployed network transfer was measured.
- The 2026-10-02 archived CLARIS measurements and the earlier 2026-11-01 runs are retained for provenance but are not mixed into the 2026-11-04 matrix.
- The joint QROM proof-system transfer obligations and real-AES tuple assumptions remain conditional; functional tests do not establish those proofs.
