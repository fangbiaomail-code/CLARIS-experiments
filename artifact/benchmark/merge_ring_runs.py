#!/usr/bin/env python3
"""Merge a re-measured ring size into the full-matrix dataset with explicit provenance."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--main', type=Path, required=True)
    ap.add_argument('--rerun', type=Path, required=True)
    ap.add_argument('--ring', type=int, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--reason', required=True)
    args = ap.parse_args()
    main = json.loads((args.main / 'results.json').read_text())
    rerun = json.loads((args.rerun / 'results.json').read_text())
    ring = args.ring
    old_report = [r for r in main['report_rows'] if r['ring_size'] == ring]
    old_cert = [r for r in main['certificate_rows'] if r['ring_size'] == ring]
    new_report = [r for r in rerun['report_rows'] if r['ring_size'] == ring]
    new_cert = [r for r in rerun['certificate_rows'] if r['ring_size'] == ring]
    assert len(new_report) == 1 and len(new_cert) == 11
    main['report_rows'] = [r for r in main['report_rows'] if r['ring_size'] != ring] + new_report
    main['certificate_rows'] = ([r for r in main['certificate_rows'] if r['ring_size'] != ring]
                                + new_cert)
    main['report_rows'].sort(key=lambda r: r['ring_size'])
    main['certificate_rows'].sort(key=lambda r: (r['ring_size'], r['selected_count'], r['method']))
    main['fresh_public_verification'] = ([r for r in main['fresh_public_verification']
                                          if r['ring_size'] != ring]
                                         + [r for r in rerun['fresh_public_verification']
                                            if r['ring_size'] == ring])
    main['fresh_public_verification'].sort(key=lambda r: r['ring_size'])
    main.setdefault('provenance_notes', []).append({
        'ring_size': ring,
        'action': 're-measured and substituted',
        'reason': args.reason,
        'discarded_run_report_median_ms': (
            old_report[0]['generate_ms']['median'] if old_report else None),
        'discarded_run_verify_median_ms': (
            old_report[0]['verify_ms']['median'] if old_report else None),
        'substituted_report_median_ms': new_report[0]['generate_ms']['median'],
        'substituted_verify_median_ms': new_report[0]['verify_ms']['median'],
        'rerun_started_at': rerun.get('started_at'),
        'discarded_cells_preserved_at': str(args.main / f'n{ring}'),
    })
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'results.json').write_text(json.dumps(main, indent=2) + '\n')
    files = {str(p.relative_to(args.output)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(args.output.rglob('*')) if p.is_file() and p.name != 'file_hashes.json'}
    (args.output / 'file_hashes.json').write_text(json.dumps(files, indent=2) + '\n')
    print(json.dumps(main['provenance_notes'], indent=1))


if __name__ == '__main__':
    main()
