# Results

- Put raw, unmodified per-run CSV files in `raw/`.
- Put derived summaries in `processed/`.
- Include the source commit and environment metadata with every run.
- Do not overwrite raw data; create a new file for each run or revision.

Recommended raw CSV columns:

`timestamp_utc,git_commit,build_id,operation,variant,ring_size,selected_reports,run_index,warmup,elapsed_ms,proof_bytes,certificate_bytes,peak_rss_bytes,success,cpu,os,compiler,flags,notes`

Use one row per operation per repetition. For unsupported operations, record an explicit status in a separate metadata file rather than fabricating a numeric value.

The manuscript's previously reported values belong in a clearly labeled prior-results table, not in `raw/`, because the raw per-run samples are not available here.
