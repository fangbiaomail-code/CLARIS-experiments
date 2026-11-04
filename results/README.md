# Results

- Put raw, unmodified per-run data in `raw/`; preserve the security level and sample count in the filename or metadata.
- Put derived summaries in `processed/`.
- Include the source inventory/build hash and environment metadata with every run.
- Do not overwrite raw data; create a new file for each run or revision.
- A single-sample baseline is descriptive only; do not present it as a statistically robust comparison.
- Keep report verification, ordinary proof verification, and original-report validation separate unless a true combined end-to-end timer was recorded.

## Current files

- `raw/upstream_baseline_128.csv`: pinned upstream CCCS-11 baseline, 128-bit profile, one sample per N ∈ {16,64,256,1024}.
- `raw/primitive_benchmark.csv`: 50,000-run local AES-256 and SHAKE256 primitive measurements.
- `processed/claris_local_n64_summary.csv`: 30-run local CLARIS N=64 measurements for report, claim, Anchor, and Bridge at s = 2,3,5.
- `metadata/`: environment and provenance for the corresponding runs.

## Recommended raw CSV columns

`timestamp_utc,git_commit,build_id,operation,variant,ring_size,selected_reports,run_index,warmup,elapsed_ms,proof_bytes,certificate_bytes,peak_rss_bytes,success,cpu,os,compiler,flags,notes`

Use one row per operation per repetition. Unsupported operations should be marked explicitly rather than assigned an estimated numeric value.


## 2026-11-04 full matrix

- `raw/full_matrix_timings.csv`: 1,440 per-sample report and ordinary timings (4 report cells + 44 certificate cells x 30 samples).
- `raw/full_matrix_originals.csv`: 1,320 per-sample original-report validation timings.
- `raw/full_matrix_primitive_samples.csv`: 300 primitive samples (6 operations x 50).
- `processed/full_matrix_ring_scalability.csv`, `full_matrix_certificate_scalability.csv`, `full_matrix_anchor_bridge_ablation.csv`, `full_matrix_communication_overhead.csv`, `full_matrix_verification_breakdown.csv`, `full_matrix_basic_operations.csv`, `full_matrix_functional_validation.csv`, `full_matrix_operation_counts.csv`: derived summaries.
- `aggregate_full_matrix.json`: machine-readable aggregate with environment and provenance notes.
- `metadata/full_matrix_*`: environment, build summary, build manifest, harness revision and raw file hashes.
- The N=16 report cell was re-measured because the first run started right after a functional suite; both runs and the provenance note are retained.
