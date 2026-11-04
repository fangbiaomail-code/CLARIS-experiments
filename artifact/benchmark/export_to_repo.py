#!/usr/bin/env python3
"""Publish the completed full-matrix artifacts into the CLARIS-experiments repository.

Copies only derived/aggregated data, raw per-sample CSVs, figures, tables and
environment/build provenance. The multi-megabyte ABI fixtures (proofs/requests/
selection files) stay in the run directory; their SHA-256 manifest is published.
"""
import argparse
import csv
import json
import shutil
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--matrix', default='results/fullmatrix_final/results.json')
    args = ap.parse_args()
    root = args.root.resolve()
    repo = args.repo.resolve()
    data_path = root / args.matrix
    run = data_path.parent
    data = json.loads(data_path.read_text())
    aggregate = json.loads((root / 'results/aggregate.json').read_text())
    processed = repo / 'results/processed'
    raw = repo / 'results/raw'
    meta = repo / 'results/metadata'
    figs = repo / 'docs/figures/chapter_vii'
    for d in (processed, raw, meta, figs):
        d.mkdir(parents=True, exist_ok=True)

    copies = {
        'ring_scalability.csv': 'full_matrix_ring_scalability.csv',
        'certificate_scalability.csv': 'full_matrix_certificate_scalability.csv',
        'anchor_bridge_ablation.csv': 'full_matrix_anchor_bridge_ablation.csv',
        'communication_overhead.csv': 'full_matrix_communication_overhead.csv',
        'full_verification_breakdown.csv': 'full_matrix_verification_breakdown.csv',
        'basic_operations.csv': 'full_matrix_basic_operations.csv',
        'functional_validation.csv': 'full_matrix_functional_validation.csv',
    }
    for src, dst in copies.items():
        shutil.copy2(root / 'results/processed' / src, processed / dst)
    if (root / 'results/processed/operation_counts.csv').exists():
        shutil.copy2(root / 'results/processed/operation_counts.csv',
                     processed / 'full_matrix_operation_counts.csv')
    shutil.copy2(root / 'results/aggregate.json', repo / 'results/aggregate_full_matrix.json')

    for name, dst in [('raw_timing_samples.csv', 'full_matrix_timings.csv'),
                      ('raw_original_samples.csv', 'full_matrix_originals.csv')]:
        shutil.copy2(root / 'results/processed' / name, raw / dst)

    # Primitive per-sample rows come from the raw JSON.
    basic = json.loads((root / 'results/raw/basic_operations.json').read_text())
    with (raw / 'full_matrix_primitive_samples.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['operation', 'unit', 'iteration', 'value', 'inner_repetitions'])
        for row in basic['rows']:
            for i, v in enumerate(row['samples']):
                w.writerow([row['operation'], row['unit'], i, f'{v:.9f}',
                            row['inner_repetitions']])

    environment = dict(data['environment'])
    environment['run_directory'] = str(run)
    environment['completed_at'] = data.get('completed_at')
    (meta / 'full_matrix_environment.json').write_text(json.dumps(environment, indent=2) + '\n')

    manifest = json.loads((root / 'build/build_manifest.json').read_text())
    summary = {
        'schema': 'claris-full-matrix-build-summary-v1',
        'compiler': manifest['compiler'],
        'flags': manifest['flags'],
        'execution_target': manifest['execution_target'],
        'transcript_profile': manifest['transcript_profile'],
        'network_used': manifest['network_used'],
        'targets': [{'target': t['target'],
                     'binary_sha256': t['binary_sha256'],
                     'benchmark_binary_sha256': t['benchmark_binary_sha256']}
                    for t in manifest['targets']],
        'full_build_manifest_sha256': environment['build_manifest_sha256'],
        'source_inventory_sha256': environment['source_inventory_sha256'],
        'harness_revision_sha256': environment['harness_revision_sha256'],
    }
    (meta / 'full_matrix_build_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    shutil.copy2(root / 'build/build_manifest.json', meta / 'full_matrix_build_manifest.json')
    shutil.copy2(root / 'source/provenance/benchmark_revision.json',
                 meta / 'full_matrix_harness_revision.json')

    # Publish the hash manifest of the raw run directory (contents stay local).
    hashes = json.loads((run / 'file_hashes.json').read_text())
    published = {k: v for k, v in hashes.items() if not k.endswith('file_hashes.json')}
    (meta / 'full_matrix_raw_file_hashes.json').write_text(json.dumps(published, indent=2) + '\n')

    for p in sorted((root / 'results/figures').glob('*')):
        if p.suffix in ('.png', '.pdf'):
            shutil.copy2(p, figs / p.name)
    shutil.copy2(root / 'report/tables_CN.md', repo / 'docs/chapter_vii_tables_CN.md')
    shutil.copy2(root / 'report/tables_EN.md', repo / 'docs/chapter_vii_tables_EN.md')

    index = {
        'schema': 'claris-full-matrix-publication-v1',
        'ring_sizes': sorted({r['ring_size'] for r in aggregate['ring_scalability']}),
        'selected_counts': sorted({r['selected_count'] for r in aggregate['certificate_scalability']}),
        'cells': len(aggregate['certificate_scalability']),
        'samples_per_cell': aggregate['repetitions'],
        'warmups_per_cell': aggregate['warmups'],
        'figures': sorted(p.name for p in figs.glob('*.png')),
        'files': {
            'ring': 'results/processed/full_matrix_ring_scalability.csv',
            'certificate': 'results/processed/full_matrix_certificate_scalability.csv',
            'ablation': 'results/processed/full_matrix_anchor_bridge_ablation.csv',
            'communication': 'results/processed/full_matrix_communication_overhead.csv',
            'timing_samples': 'results/raw/full_matrix_timings.csv',
            'originals': 'results/raw/full_matrix_originals.csv',
            'environment': 'results/metadata/full_matrix_environment.json',
        },
    }
    (repo / 'results/processed/full_matrix_index.json').write_text(json.dumps(index, indent=2) + '\n')
    print(json.dumps(index, indent=1))


if __name__ == '__main__':
    main()
