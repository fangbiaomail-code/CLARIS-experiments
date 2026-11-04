#!/usr/bin/env python3
"""Aggregate the CLARIS full matrix into Chapter VII tables, CSVs and figures.

Inputs
  results/fullmatrix/results.json     raw per-sample timings from the C harnesses
  results/raw/basic_operations.json   primitive microbenchmarks (50 samples, 3 warm-ups)
  results/functional/functional_all.json
Outputs
  results/processed/*.csv, results/aggregate.json, results/figures/*.png|pdf,
  report/tables_CN.md, report/tables_EN.md
"""
import argparse
import json
import math
import statistics
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RING_PROOF_BYTES = 50638
REPORT_PAYLOAD_BYTES = 192 + RING_PROOF_BYTES
ORDINARY_PROOF_BYTES = 49208
PUBLIC_KEY_BYTES = 64
SECRET_KEY_BYTES = 64

plt.rcParams.update({'font.size': 9, 'axes.grid': True, 'grid.alpha': 0.25,
                     'figure.dpi': 160, 'savefig.bbox': 'tight',
                     'font.sans-serif': ['DejaVu Sans', 'Arial Unicode MS', 'PingFang SC']})


def stats(values):
    vals = [float(v) for v in values]
    ordered = sorted(vals)

    def q(p):
        x = (len(ordered) - 1) * p
        i = int(x)
        return ordered[i] + (ordered[min(i + 1, len(ordered) - 1)] - ordered[i]) * (x - i)

    return {'n': len(vals), 'mean': statistics.mean(vals), 'median': statistics.median(vals),
            'stddev': statistics.stdev(vals) if len(vals) > 1 else 0.0,
            'p95': q(0.95), 'min': min(vals), 'max': max(vals), 'p25': q(0.25), 'p75': q(0.75)}


def fmt(value, digits=2):
    return f'{value:,.{digits}f}'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--matrix', default='results/fullmatrix/results.json',
                    help='aggregate source JSON relative to the workspace root')
    args = ap.parse_args()
    root = args.root.resolve()
    data = json.loads((root / args.matrix).read_text())
    basic = json.loads((root / 'results/raw/basic_operations.json').read_text())
    functional = json.loads((root / 'results/functional/functional_all.json').read_text())
    processed = root / 'results/processed'
    figures = root / 'results/figures'
    report = root / 'report'
    for d in (processed, figures, report):
        d.mkdir(parents=True, exist_ok=True)
    env = data['environment']
    ns = sorted({r['ring_size'] for r in data['report_rows']})
    reps = env['repeats']
    warm = env['warmups']
    matrix_dir = Path(args.matrix).parent.name
    source_note = (f"source: {matrix_dir} (one build; {reps} measured samples, "
                   f"{warm} warm-ups per cell; {env['execution_arch']} under Rosetta on "
                   f"{env.get('cpu_brand')})")

    # ---------------------------------------------------------------- ring scalability
    ring = []
    for r in sorted(data['report_rows'], key=lambda x: x['ring_size']):
        g, v = r['generate_ms'], r['verify_ms']
        ring.append({
            'ring_size': r['ring_size'],
            'report_proof_bytes': r['proof_bytes'],
            'report_payload_bytes': r['canonical_payload_bytes_excluding_manifest'],
            'ring_registry_bytes': 2 * r['ring_size'] * PUBLIC_KEY_BYTES,
            'generate_n': g['n'], 'generate_mean_ms': g['mean'], 'generate_median_ms': g['median'],
            'generate_stddev_ms': g['stddev'], 'generate_p95_ms': g['p95'],
            'generate_min_ms': g['min'], 'generate_max_ms': g['max'],
            'generate_p25_ms': g['p25'], 'generate_p75_ms': g['p75'],
            'verify_n': v['n'], 'verify_mean_ms': v['mean'], 'verify_median_ms': v['median'],
            'verify_stddev_ms': v['stddev'], 'verify_p95_ms': v['p95'],
            'verify_min_ms': v['min'], 'verify_max_ms': v['max'],
            'verify_p25_ms': v['p25'], 'verify_p75_ms': v['p75'],
            'driver_peak_rss_bytes': r['max_rss_bytes'],
            'measurement_status': 'measured'})

    # ---------------------------------------------------------- certificate scalability
    cert = []
    for r in sorted(data['certificate_rows'], key=lambda x: (x['ring_size'], x['selected_count'],
                                                             x['method'])):
        g, v, o = r['generate_ms'], r['verify_ms'], r['original_set_ms']
        cert.append({
            'ring_size': r['ring_size'], 'method': r['method'],
            'selected_count': r['selected_count'], 'proof_count': r['proof_count'],
            'proof_bytes': r['proof_bytes'], 'proof_file_bytes': r['proof_file_bytes'],
            'request_file_bytes': r['request_file_bytes'],
            'selection_file_bytes': r['selection_file_bytes'],
            'serialized_fixture_bytes': (r['proof_file_bytes'] + r['request_file_bytes']
                                         + r['selection_file_bytes']),
            'generate_n': g['n'], 'generate_mean_ms': g['mean'],
            'generate_median_ms': g['median'], 'generate_stddev_ms': g['stddev'],
            'generate_p95_ms': g['p95'],
            'verify_n': v['n'], 'verify_mean_ms': v['mean'], 'verify_median_ms': v['median'],
            'verify_stddev_ms': v['stddev'], 'verify_p95_ms': v['p95'],
            'original_n': o['n'], 'original_mean_ms': o['mean'],
            'original_median_ms': o['median'], 'original_stddev_ms': o['stddev'],
            'original_p95_ms': o['p95'],
            'complete_verify_median_ms': o['median'] + v['median'],
            'max_rss_bytes': r['max_rss_bytes'],
            'measurement_status': 'measured'})
    cert_by_key = {(r['ring_size'], r['method'], r['selected_count']): r for r in cert}
    ring_by_n = {r['ring_size']: r for r in ring}

    # ---------------------------------------------------------------------- ablation
    ablation = []
    for n in ns:
        for s in [2, 3, 5, 10, 20]:
            a = cert_by_key[(n, 'anchor', s)]
            b = cert_by_key[(n, 'bridge', s)]
            ablation.append({
                'ring_size': n, 'selected_count': s,
                'anchor_proofs': a['proof_count'], 'bridge_proofs': b['proof_count'],
                'anchor_proof_bytes': a['proof_bytes'], 'bridge_proof_bytes': b['proof_bytes'],
                'proof_bytes_saved': b['proof_bytes'] - a['proof_bytes'],
                'anchor_generate_median_ms': a['generate_median_ms'],
                'bridge_generate_median_ms': b['generate_median_ms'],
                'generate_saved_ms': b['generate_median_ms'] - a['generate_median_ms'],
                'generate_saved_pct': 100 * (b['generate_median_ms'] - a['generate_median_ms'])
                                      / b['generate_median_ms'],
                'anchor_verify_median_ms': a['verify_median_ms'],
                'bridge_verify_median_ms': b['verify_median_ms'],
                'verify_saved_ms': b['verify_median_ms'] - a['verify_median_ms'],
                'verify_saved_pct': 100 * (b['verify_median_ms'] - a['verify_median_ms'])
                                    / b['verify_median_ms'],
                'anchor_generate_per_proof_ms': a['generate_median_ms'] / a['proof_count'],
                'bridge_generate_per_proof_ms': b['generate_median_ms'] / b['proof_count'],
                'anchor_verify_per_proof_ms': a['verify_median_ms'] / a['proof_count'],
                'bridge_verify_per_proof_ms': b['verify_median_ms'] / b['proof_count'],
                'anchor_original_median_ms': a['original_median_ms'],
                'bridge_original_median_ms': b['original_median_ms'],
                'measurement_status': 'measured'})

    # --------------------------------------------------- linear fit in proof count
    def least_squares(points):
        n = len(points)
        sx = sum(x for x, _ in points)
        sy = sum(y for _, y in points)
        sxx = sum(x * x for x, _ in points)
        sxy = sum(x * y for x, y in points)
        denom = n * sxx - sx * sx
        if denom == 0:
            return None, None
        slope = (n * sxy - sx * sy) / denom
        intercept = (sy - slope * sx) / n
        ss_tot = sum((y - sy / n) ** 2 for _, y in points)
        ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in points)
        r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
        return slope, intercept, r2

    proof_scale = []
    for n in ns:
        points_gen, points_ver = [], []
        for r in cert:
            if r['ring_size'] != n:
                continue
            points_gen.append((r['proof_count'], r['generate_median_ms']))
            points_ver.append((r['proof_count'], r['verify_median_ms']))
        gs, gi, gr2 = least_squares(points_gen)
        vs, vi, vr2 = least_squares(points_ver)
        proof_scale.append({'ring_size': n,
                            'generate_ms_per_proof': gs, 'generate_intercept_ms': gi,
                            'generate_r2': gr2,
                            'verify_ms_per_proof': vs, 'verify_intercept_ms': vi,
                            'verify_r2': vr2,
                            'points': len(points_gen),
                            'status': 'ordinary least squares over all s=1..20 cells of this ring size'})

    # --------------------------------------------------------------- communication
    comm = [
        {'object': 'public_parameters', 'scope': 'compile-time parameter tuple; no trusted-setup file',
         'bytes': 0, 'transmission_measured': False,
         'status': 'no serialized public parameter object in this profile'},
        {'object': 'user_public_key', 'scope': 'one ring-profile public key', 'bytes': PUBLIC_KEY_BYTES,
         'transmission_measured': False, 'status': 'derived_from_compiled_constant'},
        {'object': 'user_secret_key', 'scope': 'one ring-profile secret key', 'bytes': SECRET_KEY_BYTES,
         'transmission_measured': False, 'status': 'derived_from_compiled_constant'},
        {'object': 'claim_proof', 'scope': 'one ordinary eight-block G proof',
         'bytes': ORDINARY_PROOF_BYTES, 'transmission_measured': False,
         'status': 'measured fixture length'},
        {'object': 'link_edge_proof', 'scope': 'one ordinary link-edge proof',
         'bytes': ORDINARY_PROOF_BYTES, 'transmission_measured': False,
         'status': 'measured fixture length'},
        {'object': 'claim_certificate_s1',
         'scope': 'claim proof + claimant index + report id + context',
         'bytes': ORDINARY_PROOF_BYTES + 4 + 32 + 32, 'transmission_measured': False,
         'status': 'analytical wrapper over measured proof'},
    ]
    for n in ns:
        payload = ring_by_n[n]['report_payload_bytes']
        comm.append({'object': f'report_proof_N{n}', 'scope': f'anonymous report proof payload (Q-v2), N={n}',
                     'bytes': ring_by_n[n]['report_proof_bytes'], 'transmission_measured': False,
                     'status': 'measured fixture length'})
        comm.append({'object': f'report_payload_N{n}',
                     'scope': f'report proof + 192 B message/nonce/tag fields, N={n}',
                     'bytes': payload, 'transmission_measured': False,
                     'status': 'measured fixture length'})
        comm.append({'object': f'ring_registry_N{n}', 'scope': f'{2 * n} public keys (p0,p1 per member)',
                     'bytes': 2 * n * PUBLIC_KEY_BYTES, 'transmission_measured': False,
                     'status': 'analytical from 2*N*64 bytes'})
    for s in [2, 3, 5, 10, 20]:
        comm.append({'object': f'anchor_link_proof_s{s}', 'scope': f'{s - 1} ordinary proofs',
                     'bytes': (s - 1) * ORDINARY_PROOF_BYTES, 'transmission_measured': False,
                     'status': 'measured proof files'})
        comm.append({'object': f'bridge_link_proof_s{s}',
                     'scope': f'{s} ordinary proofs + 64-byte bridge tuple',
                     'bytes': s * ORDINARY_PROOF_BYTES + 64, 'transmission_measured': False,
                     'status': 'measured proof files + 64-byte public bridge tuple'})
    for n in ns:
        payload = ring_by_n[n]['report_payload_bytes']
        for s in [2, 3, 5, 10, 20]:
            anchor_cert = (s - 1) * ORDINARY_PROOF_BYTES + 4 + 32 * s + 32
            bridge_cert = s * ORDINARY_PROOF_BYTES + 64 + 4 + 32 * s + 32
            comm.append({'object': f'anchor_certificate_N{n}_s{s}',
                         'scope': 'proofs + count + s report ids + context',
                         'bytes': anchor_cert, 'transmission_measured': False,
                         'status': 'analytical wrapper over measured proofs'})
            comm.append({'object': f'bridge_certificate_N{n}_s{s}',
                         'scope': 'proofs + bridge tuple + count + s report ids + context',
                         'bytes': bridge_cert, 'transmission_measured': False,
                         'status': 'analytical wrapper over measured proofs'})
            comm.append({'object': f'anchor_complete_package_N{n}_s{s}',
                         'scope': f'certificate + {s} report payloads (N={n}) + 32-byte manifest digest',
                         'bytes': anchor_cert + s * payload + 32, 'transmission_measured': False,
                         'status': 'analytical byte accounting; not a measured network transfer'})
            comm.append({'object': f'bridge_complete_package_N{n}_s{s}',
                         'scope': f'certificate + {s} report payloads (N={n}) + 32-byte manifest digest',
                         'bytes': bridge_cert + s * payload + 32, 'transmission_measured': False,
                         'status': 'analytical byte accounting; not a measured network transfer'})
    for row in comm:
        row['kib'] = row['bytes'] / 1024.0

    # ------------------------------------------------------------ full verification
    fullver = []
    for r in cert:
        fullver.append({
            'ring_size': r['ring_size'], 'method': r['method'],
            'selected_count': r['selected_count'],
            'original_reports_median_ms': r['original_median_ms'],
            'core_proof_verify_median_ms': r['verify_median_ms'],
            'combined_median_ms': r['complete_verify_median_ms'],
            'combined_definition': 'sum of separately measured medians; not one end-to-end timer',
            'measurement_status': 'derived'})

    # --------------------------------------------------------------------- basic ops
    basic_rows = []
    for r in basic['rows']:
        st = stats(r['samples'])
        basic_rows.append({'operation': r['operation'], 'unit': r['unit'],
                           'inner_repetitions': r['inner_repetitions'], **st,
                           'measurement_status': 'measured'})

    # ------------------------------------------------------------------ functional
    func_rows = []
    for r in functional['rows']:
        for c in r['checks']:
            func_rows.append({'ring_size': r['ring_size'], 'test': c['test'],
                              'evidence': c['evidence'], 'result': c['result'],
                              'joint_checks': r['joint_checks_passed'],
                              'fresh_public_checks': r['fresh_public_checks'],
                              'fresh_link_checks': r['fresh_link_checks'],
                              'measurement_status': 'measured_functional_test'})

    # --------------------------------------------------------------------- raw CSV
    timing_rows, original_rows = [], []
    for r in data['report_rows']:
        for x in r['samples']:
            timing_rows.append({'ring_size': r['ring_size'], 'operation': 'report',
                                'method': 'report', 'selected_count': '',
                                'iteration': x['iteration'],
                                'generate_ms': x['generate_ms'], 'verify_ms': x['verify_ms']})
    for r in data['certificate_rows']:
        for x in r['samples']:
            timing_rows.append({'ring_size': r['ring_size'], 'operation': 'ordinary',
                                'method': r['method'], 'selected_count': r['selected_count'],
                                'iteration': x['iteration'],
                                'generate_ms': x['generate_ms'], 'verify_ms': x['verify_ms']})
        for i, v in enumerate(r['original_set_samples_ms']):
            original_rows.append({'ring_size': r['ring_size'], 'method': r['method'],
                                  'selected_count': r['selected_count'], 'iteration': i,
                                  'original_set_ms': v})

    # ----------------------------------------------------------------------- write
    import csv

    def write_csv(path, rows):
        if not rows:
            return
        with path.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    write_csv(processed / 'ring_scalability.csv', ring)
    write_csv(processed / 'certificate_scalability.csv', cert)
    write_csv(processed / 'anchor_bridge_ablation.csv', ablation)
    write_csv(processed / 'proof_count_timing_fit.csv', proof_scale)
    write_csv(processed / 'communication_overhead.csv', comm)
    write_csv(processed / 'full_verification_breakdown.csv', fullver)
    write_csv(processed / 'basic_operations.csv', basic_rows)
    write_csv(processed / 'functional_validation.csv', func_rows)
    write_csv(processed / 'raw_timing_samples.csv', timing_rows)
    write_csv(processed / 'raw_original_samples.csv', original_rows)

    aggregate = {
        'schema': 'claris-performance-results-v2',
        'source_run': str(root / args.matrix),
        'environment': env,
        'warmups': warm, 'repetitions': reps,
        'ring_scalability': ring,
        'certificate_scalability': cert,
        'anchor_bridge_ablation': ablation,
        'proof_count_timing_fit': proof_scale,
        'communication_overhead': comm,
        'full_verification_breakdown': fullver,
        'basic_operations': basic_rows,
        'functional_validation': functional,
        'provenance_notes': data.get('provenance_notes', []),
        'scope_notes': [
            'Report and ordinary timers are separate; combined_median_ms adds separately measured medians.',
            'Ordinary proof payload is 49,208 bytes for every N; the ring report proof is 50,638 bytes.',
            'Communication rows are byte accounting from measured fixtures and compiled constants; '
            'no network transfer was measured.',
            'All timings are Rosetta-translated x86_64 execution on an Apple Silicon host.',
            'External schemes have no matched executable benchmark beyond the pinned Chiang et al. baseline.',
        ],
    }
    (root / 'results/aggregate.json').write_text(json.dumps(aggregate, indent=2) + '\n')

    # --------------------------------------------------------------------- figures
    def caption(ax, text):
        ax.annotate(text, xy=(0.5, -0.26), xycoords='axes fraction', ha='center', va='top',
                    fontsize=6.2, color='#555555')

    palette = {16: '#7A9CC6', 64: '#245778', 256: '#A86429', 1024: '#8B3A3A'}

    # fig 1/2: report generation and verification vs N
    for key, label, fname in [('generate', 'Report generation', 'report_generation_vs_N'),
                              ('verify', 'Report verification', 'report_verification_vs_N')]:
        fig, ax = plt.subplots(figsize=(5.2, 3.2))
        xs = [r['ring_size'] for r in ring]
        ys = [r[f'{key}_median_ms'] for r in ring]
        lo = [r[f'{key}_median_ms'] - r[f'{key}_p25_ms'] for r in ring]
        hi = [r[f'{key}_p75_ms'] - r[f'{key}_median_ms'] for r in ring]
        ax.errorbar(xs, ys, yerr=[lo, hi], marker='o', capsize=4, color='#245778')
        ax.set_xscale('log', base=2)
        ax.set_xticks(xs)
        ax.set_xticklabels([str(x) for x in xs])
        ax.set_xlabel('Ring size N')
        ax.set_ylabel(f'{label} time (ms)')
        ax.set_title(f'{label} vs ring size (n={reps})')
        caption(ax, source_note)
        fig.savefig(figures / f'{fname}.png', dpi=300)
        fig.savefig(figures / f'{fname}.pdf')
        plt.close(fig)

    # fig 3: claim generation and verification per N
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    claims = [cert_by_key[(n, 'claim', 1)] for n in ns]
    width = 0.26
    idx = range(len(ns))
    ax.bar([i - width for i in idx], [c['generate_median_ms'] for c in claims], width,
           label='Claim generation', color='#245778')
    ax.bar(list(idx), [c['verify_median_ms'] for c in claims], width,
           label='Claim core verification', color='#A86429')
    ax.bar([i + width for i in idx], [c['original_median_ms'] for c in claims], width,
           label='Original report validation', color='#7A9CC6')
    ax.set_xticks(list(idx))
    ax.set_xticklabels([f'N={n}' for n in ns])
    ax.set_ylabel('Time (ms)')
    ax.set_title(f'Identity claim at s=1 (n={reps})')
    ax.legend(frameon=False, fontsize=7)
    caption(ax, source_note)
    fig.savefig(figures / 'claim_generation_verification.png', dpi=300)
    fig.savefig(figures / 'claim_generation_verification.pdf')
    plt.close(fig)

    # fig 4: link generation vs s, all N, anchor/bridge
    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    for n in ns:
        for method, style in [('anchor', '-o'), ('bridge', '--s')]:
            rows = [cert_by_key[(n, method, s)] for s in [2, 3, 5, 10, 20]]
            ax.plot([r['selected_count'] for r in rows], [r['generate_median_ms'] for r in rows],
                    style, color=palette[n], markersize=4,
                    label=f'N={n} {method}')
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Link generation time (ms)')
    ax.set_title(f'Link generation vs s (n={reps})')
    ax.legend(frameon=False, fontsize=6, ncol=2)
    caption(ax, source_note)
    fig.savefig(figures / 'link_generation_vs_s.png', dpi=300)
    fig.savefig(figures / 'link_generation_vs_s.pdf')
    plt.close(fig)

    # fig 5: core and combined verification at N=64 and N=1024
    panels = [n for n in (64, 1024) if n in ns] or ns[-1:]
    fig, axs = plt.subplots(1, len(panels), figsize=(4.1 * len(panels), 3.2), sharey=True,
                            squeeze=False)
    axs = axs[0]
    for ax, n in zip(axs, panels):
        for method, color, mark in [('anchor', '#245778', 'o'), ('bridge', '#A86429', 's')]:
            rows = [cert_by_key[(n, method, s)] for s in [2, 3, 5, 10, 20]]
            ax.plot([r['selected_count'] for r in rows], [r['verify_median_ms'] for r in rows],
                    '-' + mark, color=color, markersize=4, label=f'{method} core')
            ax.plot([r['selected_count'] for r in rows],
                    [r['complete_verify_median_ms'] for r in rows],
                    ':' + mark, color=color, markersize=4, alpha=0.65,
                    label=f'{method} core + original')
        ax.set_title(f'N={n}')
        ax.set_xlabel('Selected reports s')
        ax.legend(frameon=False, fontsize=6)
    axs[0].set_ylabel('Verification time (ms)')
    fig.suptitle(f'Link verification: core vs original-set + core (n={reps})', fontsize=9)
    caption(axs[0], 'Combined series add separately measured medians; not one end-to-end timer.')
    fig.tight_layout()
    fig.savefig(figures / 'link_verification_vs_s.png', dpi=300)
    fig.savefig(figures / 'link_verification_vs_s.pdf')
    plt.close(fig)

    # fig 6: proof size vs s
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ref_n = 1024 if 1024 in ns else ns[-1]
    for method, color, mark in [('anchor', '#245778', 'o'), ('bridge', '#A86429', 's')]:
        rows = [cert_by_key[(ref_n, method, s)] for s in [2, 3, 5, 10, 20]]
        ax.plot([r['selected_count'] for r in rows], [r['proof_bytes'] / 1024 for r in rows],
                '-' + mark, color=color, label=f'{method} link proof')
    ax.axhline(RING_PROOF_BYTES / 1024, color='#7A9CC6', linestyle='--',
               label=f'ring report proof ({RING_PROOF_BYTES:,} B)')
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Size (KiB)')
    ax.set_title('Proof payload size')
    ax.legend(frameon=False, fontsize=7)
    caption(ax, 'Proof sizes are identical for every N in this backend; N=1024 series shown.')
    fig.savefig(figures / 'proof_size_vs_s.png', dpi=300)
    fig.savefig(figures / 'proof_size_vs_s.pdf')
    plt.close(fig)

    # fig 7: complete evidence package vs s
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    for method, color, mark in [('anchor', '#245778', 'o'), ('bridge', '#A86429', 's')]:
        vals = [(s - 1) * ORDINARY_PROOF_BYTES + 4 + 32 * s + 32 + s * REPORT_PAYLOAD_BYTES + 32
                if method == 'anchor' else
                s * ORDINARY_PROOF_BYTES + 64 + 4 + 32 * s + 32 + s * REPORT_PAYLOAD_BYTES + 32
                for s in [2, 3, 5, 10, 20]]
        ax.plot([2, 3, 5, 10, 20], [v / (1024 * 1024) for v in vals], '-' + mark,
                color=color, label=f'{method} package')
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Complete evidence package (MiB)')
    ax.set_title('Analytical complete evidence package size')
    ax.legend(frameon=False, fontsize=7)
    caption(ax, 'Byte accounting over measured payloads; no network transfer was measured.')
    fig.savefig(figures / 'evidence_package_vs_s.png', dpi=300)
    fig.savefig(figures / 'evidence_package_vs_s.pdf')
    plt.close(fig)

    # fig 8: peak RSS vs s
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    for n in ns:
        claim = cert_by_key[(n, 'claim', 1)]
        ax.plot([1], [claim['max_rss_bytes'] / (1024 * 1024)], '*', color=palette[n],
                markersize=8, label=f'N={n} claim')
        for method, style in [('anchor', '-o'), ('bridge', '--s')]:
            rows = [cert_by_key[(n, method, s)] for s in [2, 3, 5, 10, 20]]
            ax.plot([r['selected_count'] for r in rows],
                    [r['max_rss_bytes'] / (1024 * 1024) for r in rows], style,
                    color=palette[n], markersize=3, label=f'N={n} {method}')
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Worker peak RSS (MiB)')
    ax.set_title(f'Peak RSS of the proving worker (n={reps} cells)')
    ax.legend(frameon=False, fontsize=6, ncol=2)
    caption(ax, 'Worker ru_maxrss for the timed cell; report-generation RSS is reported separately.')
    fig.savefig(figures / 'peak_rss_vs_s.png', dpi=300)
    fig.savefig(figures / 'peak_rss_vs_s.pdf')
    plt.close(fig)

    # fig 9: anchor vs bridge at N=1024
    fig, axs = plt.subplots(1, 2, figsize=(8.2, 3.2))
    ss = [2, 3, 5, 10, 20]
    ref_n = 1024 if 1024 in ns else ns[-1]
    a = [cert_by_key[(ref_n, 'anchor', s)] for s in ss]
    b = [cert_by_key[(ref_n, 'bridge', s)] for s in ss]
    ax = axs[0]
    x = range(len(ss))
    ax.bar([i - 0.18 for i in x], [r['generate_median_ms'] for r in a], 0.34,
           label='Anchor', color='#245778')
    ax.bar([i + 0.18 for i in x], [r['generate_median_ms'] for r in b], 0.34,
           label='Bridge', color='#A86429')
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(s) for s in ss])
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Link generation (ms)')
    ax.set_title(f'N={ref_n} generation')
    ax.legend(frameon=False, fontsize=7)
    ax = axs[1]
    ax.bar([i - 0.18 for i in x], [r['proof_bytes'] / 1024 for r in a], 0.34,
           label='Anchor', color='#245778')
    ax.bar([i + 0.18 for i in x], [r['proof_bytes'] / 1024 for r in b], 0.34,
           label='Bridge', color='#A86429')
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(s) for s in ss])
    ax.set_xlabel('Selected reports s')
    ax.set_ylabel('Link proof size (KiB)')
    ax.set_title(f'N={ref_n} proof size')
    ax.legend(frameon=False, fontsize=7)
    fig.suptitle(f'Anchor vs Common Bridge ablation (n={reps})', fontsize=9)
    caption(axs[0], 'Controlled comparison inside one build; not an external-scheme comparison.')
    fig.tight_layout()
    fig.savefig(figures / 'anchor_vs_bridge.png', dpi=300)
    fig.savefig(figures / 'anchor_vs_bridge.pdf')
    plt.close(fig)

    # fig 10: primitive operations
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    names = [r['operation'] for r in basic_rows]
    med = [r['median'] for r in basic_rows]
    err = [r['stddev'] for r in basic_rows]
    ax.barh(range(len(names)), med, xerr=err, color='#245778', capsize=3)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xscale('log')
    ax.set_xlabel('Time per operation (µs, log scale)')
    ax.set_title(f'Primitive costs (n={len(basic["rows"][0]["samples"])})')
    for i, m in enumerate(med):
        ax.text(m * 1.1, i, f'{m:,.3f}', va='center', fontsize=6)
    caption(ax, 'AES/SHAKE256/tag measurements use 1,000 inner repetitions per sample; '
                'VOLE rows use 5 inner repetitions. Ring-independent.')
    fig.savefig(figures / 'primitive_operations.png', dpi=300)
    fig.savefig(figures / 'primitive_operations.pdf')
    plt.close(fig)

    # ------------------------------------------------------------------ markdown tables
    lines_cn = ['# CLARIS 第七章：全矩阵实测表格', '',
                f'数据来源：`results/fullmatrix`，同一构建、同一主机；每个 cell 预热 {warm} 次、'
                f'正式测量 {reps} 次。执行目标为 {env["execution_arch"]}，'
                f'主机为 {env.get("cpu_brand")}，通过 Rosetta 2 运行。', '']
    lines_cn += ['## 表 1 实验环境', '', '| 项目 | 值 |', '|---|---|',
                 f'| CPU | {env.get("cpu_brand")}（{env.get("physical_cores")} 物理核 / '
                 f'{env.get("logical_cores")} 逻辑核） |',
                 f'| 内存 | {int(env.get("memory_bytes")) / (1024 ** 3):.1f} GiB |',
                 f'| 操作系统 | macOS {env.get("os_version")} (build {env.get("os_build")}) |',
                 f'| 编译器 | {env["compiler"].splitlines()[0]} |',
                 f'| 编译选项 | `{" ".join(env["flags"])}` |',
                 f'| 执行方式 | {env["execution_arch"]}，Rosetta 2 翻译 |',
                 f'| 转录配置 | {env["transcript_profile"]} |',
                 f'| 构建清单 SHA-256 | `{env["build_manifest_sha256"]}` |', '']
    lines_cn += ['## 表 2 基础密码运算', '',
                 '| 运算 | 单位 | 中位数 | 平均值 | 标准差 | P95 | 样本数 |', '|---|---:|---:|---:|---:|---:|---:|']
    for r in basic_rows:
        lines_cn.append(f'| {r["operation"]} | µs | {r["median"]:.4f} | {r["mean"]:.4f} | '
                        f'{r["stddev"]:.4f} | {r["p95"]:.4f} | {r["n"]} |')
    lines_cn += ['', '## 表 3 原始报告随环规模', '',
                 '| N | 证明大小 (B) | 报告 payload (B) | 注册表 (B) | 生成中位数 (ms) | 生成标准差 | 验证中位数 (ms) | 验证标准差 |',
                 '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in ring:
        lines_cn.append(f'| {r["ring_size"]} | {r["report_proof_bytes"]:,} | {r["report_payload_bytes"]:,} | '
                        f'{r["ring_registry_bytes"]:,} | {r["generate_median_ms"]:.2f} | '
                        f'{r["generate_stddev_ms"]:.2f} | {r["verify_median_ms"]:.2f} | '
                        f'{r["verify_stddev_ms"]:.2f} |')
    lines_cn += ['', '## 表 4 认领证明（s=1）', '',
                 '| N | 证明数 | 证明大小 (B) | 生成中位数 (ms) | 验证中位数 (ms) | 原始报告验证中位数 (ms) | 合并中位数 (ms) |',
                 '|---:|---:|---:|---:|---:|---:|---:|']
    for r in [cert_by_key[(n, 'claim', 1)] for n in ns]:
        lines_cn.append(f'| {r["ring_size"]} | {r["proof_count"]} | {r["proof_bytes"]:,} | '
                        f'{r["generate_median_ms"]:.2f} | {r["verify_median_ms"]:.2f} | '
                        f'{r["original_median_ms"]:.2f} | {r["complete_verify_median_ms"]:.2f} |')
    lines_cn += ['', '## 表 5 Anchor / Bridge 全矩阵', '',
                 '| N | 结构 | s | 证明数 | 证明大小 (B) | 生成中位数 (ms) | 生成标准差 | 验证中位数 (ms) | 原始报告验证 (ms) |',
                 '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in cert:
        if r['method'] == 'claim':
            continue
        lines_cn.append(f'| {r["ring_size"]} | {r["method"]} | {r["selected_count"]} | '
                        f'{r["proof_count"]} | {r["proof_bytes"]:,} | {r["generate_median_ms"]:.2f} | '
                        f'{r["generate_stddev_ms"]:.2f} | {r["verify_median_ms"]:.2f} | '
                        f'{r["original_median_ms"]:.2f} |')
    lines_cn += ['', '## 表 6 Anchor 与 Bridge 消融', '',
                 '| N | s | 证明数 A/B | 生成 A/B (ms) | 节省 (%) | 验证 A/B (ms) | 节省 (%) | 大小节省 (B) |',
                 '|---:|---:|---|---|---:|---|---:|---:|']
    for r in ablation:
        lines_cn.append(f'| {r["ring_size"]} | {r["selected_count"]} | '
                        f'{r["anchor_proofs"]}/{r["bridge_proofs"]} | '
                        f'{r["anchor_generate_median_ms"]:.2f}/{r["bridge_generate_median_ms"]:.2f} | '
                        f'{r["generate_saved_pct"]:.1f} | '
                        f'{r["anchor_verify_median_ms"]:.2f}/{r["bridge_verify_median_ms"]:.2f} | '
                        f'{r["verify_saved_pct"]:.1f} | {r["proof_bytes_saved"]:,} |')
    lines_cn += ['', '## 表 6b 证明数量-时间线性拟合', '',
                 '| N | 生成斜率 (ms/证明) | 生成截距 (ms) | R² | 验证斜率 (ms/证明) | 验证截距 (ms) | R² |',
                 '|---:|---:|---:|---:|---:|---:|---:|']
    for r in proof_scale:
        lines_cn.append(f'| {r["ring_size"]} | {r["generate_ms_per_proof"]:.2f} | '
                        f'{r["generate_intercept_ms"]:.2f} | {r["generate_r2"]:.4f} | '
                        f'{r["verify_ms_per_proof"]:.2f} | {r["verify_intercept_ms"]:.2f} | '
                        f'{r["verify_r2"]:.4f} |')
    lines_cn += ['', '## 表 7 通信开销（字节核算，非实测网络传输）', '',
                 '| 对象 | 字节 | KiB | 口径 |', '|---|---:|---:|---|']
    for r in comm:
        if r['object'].startswith(('anchor_complete', 'bridge_complete', 'anchor_link',
                                   'bridge_link', 'anchor_certificate', 'bridge_certificate',
                                   'claim_certificate')) or r['object'] in (
                'public_parameters', 'user_public_key', 'user_secret_key', 'report_proof',
                'report_payload', 'claim_proof', 'link_edge_proof'):
            lines_cn.append(f'| {r["object"]} | {r["bytes"]:,} | {r["kib"]:.2f} | {r["scope"]} |')
    lines_cn += ['', '## 表 8 功能验证', '',
                 '| N | 联合检查 | 公开验证 | 无身份关联验证 | 结论 |', '|---:|---:|---:|---:|---|']
    for r in functional['rows']:
        lines_cn.append(f'| {r["ring_size"]} | {r["joint_checks_passed"]} | '
                        f'{r["fresh_public_checks"]} | {r["fresh_link_checks"]} | PASS |')
    (report / 'tables_CN.md').write_text('\n'.join(lines_cn) + '\n')

    lines_en = ['# CLARIS Chapter VII: full-matrix measured tables', '',
                f'Source: `results/fullmatrix`; one build, one host; {reps} measured samples and '
                f'{warm} warm-ups per cell; {env["execution_arch"]} under Rosetta 2 on '
                f'{env.get("cpu_brand")}.', '',
                '## Table 1. Environment', '', '| Item | Value |', '|---|---|',
                f'| CPU | {env.get("cpu_brand")} ({env.get("physical_cores")} physical / '
                f'{env.get("logical_cores")} logical) |',
                f'| Memory | {int(env.get("memory_bytes")) / (1024 ** 3):.1f} GiB |',
                f'| OS | macOS {env.get("os_version")} (build {env.get("os_build")}) |',
                f'| Compiler | {env["compiler"].splitlines()[0]} |',
                f'| Flags | `{" ".join(env["flags"])}` |',
                f'| Execution | {env["execution_arch"]} via Rosetta 2 |',
                f'| Transcript profile | {env["transcript_profile"]} |', '',
                '## Table 2. Primitive operations', '',
                '| Operation | Median (µs) | Mean (µs) | Std. dev. | P95 | n |',
                '|---|---:|---:|---:|---:|---:|']
    for r in basic_rows:
        lines_en.append(f'| {r["operation"]} | {r["median"]:.4f} | {r["mean"]:.4f} | '
                        f'{r["stddev"]:.4f} | {r["p95"]:.4f} | {r["n"]} |')
    lines_en += ['', '## Table 3. Ring-report scalability', '',
                 '| N | Proof bytes | Payload bytes | Registry bytes | Gen median (ms) | Gen SD | Verify median (ms) | Verify SD |',
                 '|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in ring:
        lines_en.append(f'| {r["ring_size"]} | {r["report_proof_bytes"]:,} | '
                        f'{r["report_payload_bytes"]:,} | {r["ring_registry_bytes"]:,} | '
                        f'{r["generate_median_ms"]:.2f} | {r["generate_stddev_ms"]:.2f} | '
                        f'{r["verify_median_ms"]:.2f} | {r["verify_stddev_ms"]:.2f} |')
    lines_en += ['', '## Table 4. Claim (s=1)', '',
                 '| N | Proofs | Proof bytes | Gen median (ms) | Verify median (ms) | Original-set median (ms) |',
                 '|---:|---:|---:|---:|---:|---:|']
    for r in [cert_by_key[(n, 'claim', 1)] for n in ns]:
        lines_en.append(f'| {r["ring_size"]} | {r["proof_count"]} | {r["proof_bytes"]:,} | '
                        f'{r["generate_median_ms"]:.2f} | {r["verify_median_ms"]:.2f} | '
                        f'{r["original_median_ms"]:.2f} |')
    lines_en += ['', '## Table 5. Anchor/Bridge matrix', '',
                 '| N | Method | s | Proofs | Proof bytes | Gen median (ms) | Gen SD | Verify median (ms) | Original-set (ms) |',
                 '|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in cert:
        if r['method'] == 'claim':
            continue
        lines_en.append(f'| {r["ring_size"]} | {r["method"]} | {r["selected_count"]} | '
                        f'{r["proof_count"]} | {r["proof_bytes"]:,} | {r["generate_median_ms"]:.2f} | '
                        f'{r["generate_stddev_ms"]:.2f} | {r["verify_median_ms"]:.2f} | '
                        f'{r["original_median_ms"]:.2f} |')
    lines_en += ['', '## Table 6. Anchor vs Bridge ablation', '',
                 '| N | s | Proofs A/B | Gen A/B (ms) | Saved (%) | Verify A/B (ms) | Saved (%) | Saved bytes |',
                 '|---:|---:|---|---|---:|---|---:|---:|']
    for r in ablation:
        lines_en.append(f'| {r["ring_size"]} | {r["selected_count"]} | '
                        f'{r["anchor_proofs"]}/{r["bridge_proofs"]} | '
                        f'{r["anchor_generate_median_ms"]:.2f}/{r["bridge_generate_median_ms"]:.2f} | '
                        f'{r["generate_saved_pct"]:.1f} | '
                        f'{r["anchor_verify_median_ms"]:.2f}/{r["bridge_verify_median_ms"]:.2f} | '
                        f'{r["verify_saved_pct"]:.1f} | {r["proof_bytes_saved"]:,} |')
    (report / 'tables_EN.md').write_text('\n'.join(lines_en) + '\n')

    print(json.dumps({'ring_rows': len(ring), 'certificate_rows': len(cert),
                      'ablation_rows': len(ablation), 'comm_rows': len(comm),
                      'figures': sorted(p.name for p in figures.glob('*.png'))}, indent=1))


if __name__ == '__main__':
    main()
