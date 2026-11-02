#!/usr/bin/env python3
"""Aggregate CLARIS raw benchmark CSV files without modifying source data.

Usage:
  python3 scripts/aggregate_results.py results/raw results/processed/summary.csv

Expected columns include operation, variant, ring_size, selected_reports,
elapsed_ms, proof_bytes, certificate_bytes, peak_rss_bytes, success.
"""
from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * p
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    source_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    files = sorted(source_dir.glob("*.csv"))
    if not files:
        print(f"No raw CSV files found in {source_dir}", file=sys.stderr)
        return 1

    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for file in files:
        with file.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("warmup", "").lower() in {"1", "true", "yes"}:
                    continue
                key = (
                    row.get("operation", ""),
                    row.get("variant", ""),
                    row.get("ring_size", ""),
                    row.get("selected_reports", ""),
                )
                groups[key].append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "operation", "variant", "ring_size", "selected_reports", "samples",
        "success_count", "mean_ms", "median_ms", "stdev_ms", "p95_ms",
        "median_proof_bytes", "median_certificate_bytes", "median_peak_rss_bytes",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key, rows in sorted(groups.items()):
            times = [float(r["elapsed_ms"]) for r in rows if r.get("elapsed_ms")]
            proofs = [float(r["proof_bytes"]) for r in rows if r.get("proof_bytes")]
            certs = [float(r["certificate_bytes"]) for r in rows if r.get("certificate_bytes")]
            rss = [float(r["peak_rss_bytes"]) for r in rows if r.get("peak_rss_bytes")]
            successes = sum(r.get("success", "").lower() in {"1", "true", "yes"} for r in rows)
            writer.writerow({
                "operation": key[0],
                "variant": key[1],
                "ring_size": key[2],
                "selected_reports": key[3],
                "samples": len(times),
                "success_count": successes,
                "mean_ms": statistics.mean(times) if times else "",
                "median_ms": statistics.median(times) if times else "",
                "stdev_ms": statistics.stdev(times) if len(times) > 1 else "",
                "p95_ms": percentile(times, 0.95) if times else "",
                "median_proof_bytes": statistics.median(proofs) if proofs else "",
                "median_certificate_bytes": statistics.median(certs) if certs else "",
                "median_peak_rss_bytes": statistics.median(rss) if rss else "",
            })
    print(f"Wrote {output_path} from {len(files)} raw file(s), {len(groups)} group(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
