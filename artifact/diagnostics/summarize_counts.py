#!/usr/bin/env python3
"""Summarize counter-instrumented diagnostic runs into the Chapter VII operation-count table."""
import csv
import json
import sys
from pathlib import Path

NAMES = ['aes_key_schedule', 'aes_256_blocks', 'shake_init', 'shake_update', 'shake_final',
         'shake_init_x4', 'shake_update_x4', 'shake_final_x4', 'vole_sender', 'vole_receiver']


def row(operation, ring, count, scope, values):
    return {'operation': operation, 'ring_size': ring, 'selected_count': count,
            'count_scope': scope, **dict(zip(NAMES, values))}


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'diagnostics')
    data = json.loads((root / 'runs/operation_counts.json').read_text())
    rows = []
    for ring in data['rings']:
        n = ring['ring_size']
        for scope in ('sign', 'verify'):
            c = ring['report'].get(scope)
            if c:
                rows.append(row(f'report_{"generation" if scope == "sign" else "verification"}',
                                n, 1, 'one report operation', c))
        for cell in ring['cells']:
            method = 'claim' if cell['method'] == 'claim' else cell['method']
            proofs = cell['proof_count']
            gen = cell['counters_gen']
            ver = cell['counters_ver']
            rows.append(row(f'{method}_generation', n, proofs,
                            f'total for {proofs} proofs', gen))
            rows.append(row(f'{method}_verification', n, proofs,
                            f'total for {proofs} proofs', ver))
            rows.append(row(f'{method}_gen_per_proof', n, 1,
                            'one ordinary proof (total/proof_count)', [c // proofs for c in gen]))
            rows.append(row(f'{method}_ver_per_proof', n, 1,
                            'one ordinary proof (total/proof_count)', [c // proofs for c in ver]))
    out = root / 'operation_counts.csv'
    with out.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(out)
    per = [r for r in rows if r['count_scope'].startswith('one ordinary')]
    signatures = {tuple(r[k] for k in NAMES) for r in per}
    print(f'per-proof signatures: {len(signatures)} distinct across {len(per)} cells')


if __name__ == '__main__':
    main()
