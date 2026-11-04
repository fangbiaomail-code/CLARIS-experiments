# Experiment limitations and reproduction notes

1. The formal CLARIS performance data in the current Chapter VII draft come from the archived source package's `provenance/benchmark_summary_v2.json`, dated 2026-10-02, on macOS 15.3 / Apple Clang 16.0 / x86-64 AVX2 AES PCLMUL under Rosetta. These are not new measurements from the current hosted Linux runner.
2. The archived benchmark has 30 measured repetitions and 3 warm-ups per configuration. The analysis scripts reorganize recorded statistics and generate CSV/figures; they do not rerun the cryptographic benchmark.
3. The current formal CLARIS benchmark covers N={64,1024} and s={2,3,5}. It does not include measured N={16,256} or s={10,20}.
4. Current measured comparisons cover Anchor and Common Bridge inside the same CLARIS implementation. External published schemes do not yet have matched executable benchmarks.
5. No independent SHA3, AES-block, VOLE-suboperation microbenchmark is claimed in this Chapter VII dataset. Do not invent these timings.
6. Peak memory is process RSS, not the size of a proof object.
7. The proof-generation and core-verification timers exclude several wrapper, setup, I/O, and report-validation stages. Original report-set validation is reported separately. No single full end-to-end service latency was measured.
8. Functional tests and timing experiments do not prove the conditional QROM security theorem. The theorem's remaining assumptions/obligations must be stated separately.
