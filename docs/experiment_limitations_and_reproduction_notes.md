# Experiment limitations and reproduction notes

1. The full matrix was measured on 2026-11-04 on one build and one host: Apple M1 (8 cores,
   8 GiB), macOS 15.3, Apple Clang 16.0, x86_64 target with AVX2/AES-NI/PCLMUL executed through
   Rosetta 2. Absolute times include translation overhead and are not native x86_64 values.
2. Every cell used 3 warm-ups and 30 measured samples; raw per-sample timings are in
   `results/raw/full_matrix_timings.csv` and original-report validation samples are in
   `results/raw/full_matrix_originals.csv`.
3. The matrix covers N ∈ {16, 64, 256, 1024} and s ∈ {2, 3, 5, 10, 20}, plus the s = 1 claim
   baseline. Unlike the earlier draft, no matrix cell is missing.
4. The first N=16 run was measured immediately after a ~5-minute functional suite; its report
   cell was about 10% slow (324.0 ms vs 291.9 ms in a control run). N=16 was re-measured on the
   same build and the re-measured cells are used; both runs are preserved (see
   `results/fullmatrix/n16` and `results/fullmatrix_n16_rerun`, and the provenance notes in
   `results/aggregate_full_matrix.json`).
5. Anchor and Bridge are compared inside the same implementation. External published schemes
   (Park–Sealfon, Fiore et al., DualRing-PRF, SPRING, TalosLogic) still have no matched
   executable benchmark here; the pinned Chiang et al. baseline is a different security profile
   and only one sample per N, so it is descriptive reference data, not a speed ranking.
6. Primitive microbenchmarks cover AES-256 key schedule, AES-256 CTR block, SHAKE256,
   rand_bytes and the vendor small-VOLE sender/receiver. The VOLE row is one protocol call at
   VOLE_MAX_K=12 and VOLE_COL_BLOCKS=36, not a whole proof transcript.
7. Peak memory is process RSS: the proving worker's `ru_maxrss` for certificate cells, the
   driver's `ru_maxrss` after report generation, and `/usr/bin/time -l` for the independent
   public reconstruction. It is not the size of a proof object.
8. Report timers include message/nonce/context/tag derivation, witness expansion and report
   proving. Ordinary proof timers exclude process launch, file I/O, public request construction,
   bridge setup and IPC. `complete_verify_median_ms` is the sum of two separately measured
   medians, not one end-to-end timer.
9. The host is a fanless Apple M1; sustained load produces roughly 10% cell-to-cell timing
   variation. Ablation conclusions therefore rest on proof counts/sizes (deterministic) and on
   the proof-count linear fit, not on a single cell's raw difference.
10. Functional and timing experiments do not prove the conditional QROM security theorem. The
    theorem's remaining assumptions/obligations must be stated separately.
11. Communication numbers are byte accounting over measured fixtures and compiled constants;
    no deployed network transfer was measured.
12. Operation call counts come from a separate counter-instrumented diagnostic build. That build
    adds work to hot loops and its timings are not used; only call counts are reported.
