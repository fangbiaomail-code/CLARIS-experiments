#!/usr/bin/env python3
"""Short thermal/context control: re-measure the N=16 report and claim cells only.

The first N=16 report cell of the full matrix started immediately after a 4m40s
functional test. This control re-runs the same 30-sample report/claim cells under the
current machine state and stops the driver once the claim cell is complete.

Usage: python3 benchmark/control_n16.py --build build --output results/control_n16
"""
import argparse
import json
import os
import signal
import statistics
import subprocess
import time
from pathlib import Path


def median(values):
    return statistics.median(values)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, default=Path('build'))
    ap.add_argument('--output', type=Path, default=Path('results/control_n16'))
    ap.add_argument('--repeats', type=int, default=30)
    ap.add_argument('--warmups', type=int, default=3)
    args = ap.parse_args()
    build = args.build.resolve()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit('use a new empty control directory')
    out.mkdir(parents=True, exist_ok=True)
    driver = build / 'ring_n16/ordinary_benchmark'
    worker = build / 'ordinary/ordinary_worker'
    process = subprocess.Popen([str(driver), str(worker), str(args.repeats), str(args.warmups)],
                               cwd=out, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    deadline = time.monotonic() + 900
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise SystemExit('driver exited before the claim cell completed')
            reports = out / 'reports.json'
            claim = out / 'claim_s1.json'
            if reports.is_file() and claim.is_file() and claim.stat().st_size > 100:
                break
            time.sleep(2)
        else:
            raise SystemExit('timeout waiting for the claim cell')
        time.sleep(1)
    finally:
        if process.poll() is None:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    reports = json.loads((out / 'reports.json').read_text())
    claim = json.loads((out / 'claim_s1.json').read_text())
    result = {
        'schema': 'claris-control-n16-v1',
        'purpose': 're-measure N=16 report/claim cells under the current machine state',
        'report_generate_median_ms': median([x['generate_ms'] for x in reports['samples']]),
        'report_verify_median_ms': median([x['verify_ms'] for x in reports['samples']]),
        'report_max_rss_bytes': reports.get('max_rss_bytes'),
        'claim_generate_median_ms': median([x['generate_ms'] for x in claim['samples']]),
        'claim_verify_median_ms': median([x['verify_ms'] for x in claim['samples']]),
        'repeats': args.repeats, 'warmups': args.warmups,
        'reports_samples': reports['samples'],
        'claim_samples': claim['samples'],
        'claim_proof_bytes': claim['proof_bytes'],
        'completed_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
    }
    (out / 'control.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if not k.endswith('samples')}, indent=1))


if __name__ == '__main__':
    main()
