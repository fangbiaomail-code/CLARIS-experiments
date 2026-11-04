#!/usr/bin/env python3
"""Chapter VII full matrix: one build, one host, N in {16,64,256,1024}, s in {1,2,3,5,10,20}.

Every certificate cell is measured with the same generated report corpus and the same
ordinary backend. Each cell records the raw per-sample timings produced by the C
harnesses, the public reconstruction check, and process peak RSS.

Scope (from the harness): in-memory proof generation and verification; report timers
include message/nonce/context/tag derivation. Process launch, file I/O, IPC and public
request construction are excluded. Original-report validation is timed separately.
"""
import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CELLS = [('claim', 1), ('anchor', 2), ('bridge', 2), ('anchor', 3), ('bridge', 3),
         ('anchor', 5), ('bridge', 5), ('anchor', 10), ('bridge', 10),
         ('anchor', 20), ('bridge', 20)]


def stats(values):
    vals = [float(v) for v in values]
    if not vals:
        return None
    ordered = sorted(vals)

    def quantile(q):
        x = (len(ordered) - 1) * q
        i = int(x)
        return ordered[i] + (ordered[min(i + 1, len(ordered) - 1)] - ordered[i]) * (x - i)

    return {'n': len(vals), 'mean': statistics.mean(vals), 'median': statistics.median(vals),
            'stddev': statistics.stdev(vals) if len(vals) > 1 else 0.0,
            'p95': quantile(0.95), 'min': min(vals), 'max': max(vals),
            'p25': quantile(0.25), 'p75': quantile(0.75)}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sysctl(name):
    try:
        return subprocess.check_output(['sysctl', '-n', name], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--repeats', type=int, default=30)
    ap.add_argument('--warmups', type=int, default=3)
    ap.add_argument('--ring-sizes', nargs='+', type=int, choices=[16, 64, 256, 1024],
                    default=[16, 64, 256, 1024])
    ap.add_argument('--resume', action='store_true',
                    help='Reuse a ring size whose 30-sample cell files already exist.')
    args = ap.parse_args()
    build = args.build.resolve()
    out = args.output.resolve()
    if args.repeats < 30 or args.warmups < 1:
        ap.error('Chapter VII requires at least 30 measured repetitions and 1 warm-up')
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((build / 'build_manifest.json').read_text())
    worker = build / 'ordinary/ordinary_worker'
    started = datetime.now(timezone.utc).astimezone()

    environment = {
        'schema': 'claris-run-environment-v2',
        'started_at': started.isoformat(),
        'hostname': platform.node(),
        'platform': platform.platform(),
        'machine': platform.machine(),
        'cpu_brand': sysctl('machdep.cpu.brand_string'),
        'physical_cores': sysctl('hw.physicalcpu'),
        'logical_cores': sysctl('hw.logicalcpu'),
        'memory_bytes': sysctl('hw.memsize'),
        'os_version': sysctl('kern.osproductversion'),
        'os_build': sysctl('kern.osversion'),
        'execution_arch': 'x86_64 (AVX2/AES-NI/PCLMUL)',
        'execution_note': ('x86_64 binaries executed through Rosetta 2 translation on an '
                           'Apple Silicon host; timings include translation overhead and are '
                           'not native x86_64 hardware measurements.'),
        'compiler': manifest['compiler'],
        'flags': manifest['flags'],
        'transcript_profile': manifest['transcript_profile'],
        'build_manifest_sha256': sha256(build / 'build_manifest.json'),
        'source_inventory_sha256': sha256(build.parent / 'source/provenance/source_inventory.json'),
        'harness_revision_sha256': sha256(build.parent / 'source/provenance/benchmark_revision.json'),
        'repeats': args.repeats,
        'warmups': args.warmups,
        'benchmark_matrix': [[n, s] for n in args.ring_sizes for _, s in CELLS],
        'network_used': False,
    }
    for target in manifest['targets']:
        environment.setdefault('binaries', {})[target['target']] = target['benchmark_binary_sha256']

    result = {
        'schema': 'claris-full-matrix-v2',
        'started_at': started.isoformat(),
        'environment': environment,
        'scope': {
            'ordinary': ('in-memory witness expansion, fresh randomness, proving/retries and '
                         'verification; excludes public request construction, bridge setup, '
                         'file I/O, worker-buffer allocation and IPC'),
            'report': ('fresh message/nonce, context and tag derivation, witness expansion and '
                       'report proving; verification includes registry/public-report checks'),
            'original_set': 'separate in-memory validation of the selected original reports and registry',
            'full_verify': ('not measured as one combined timer; complete_verify_median_ms is the '
                            'sum of the original-set median and the ordinary-verification median'),
            'rss': ('worker ru_maxrss for proof cells; driver ru_maxrss after report generation; '
                    '/usr/bin/time -l peak for the independent public reconstruction'),
        },
        'report_rows': [],
        'certificate_rows': [],
        'fresh_public_verification': [],
    }

    for n in args.ring_sizes:
        work = out / f'n{n}'
        work.mkdir(exist_ok=True)
        driver = build / f'ring_n{n}/ordinary_benchmark'
        if not driver.is_file():
            raise SystemExit(f'missing driver for N={n}: {driver}')
        complete = ((work / 'reports.json').is_file()
                    and all((work / f'{m}_s{s}.json').is_file()
                            and (work / f'{m}_s{s}.originals.json').is_file()
                            for m, s in CELLS))
        verifier = work / 'fresh_verify.log'
        if args.resume and complete:
            elapsed = float('nan')
            print(f'=== N={n}: reusing completed 30-sample cell files ===', flush=True)
        else:
            print(f'=== N={n}: {args.repeats} measured samples, {args.warmups} warm-ups per cell ===',
                  flush=True)
            start = time.monotonic()
            command = [str(driver), str(worker), str(args.repeats), str(args.warmups)]
            with (work / 'run.log').open('w') as log:
                process = subprocess.Popen(command, cwd=work, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    print(line.rstrip(), flush=True)
                if process.wait():
                    raise SystemExit(f'benchmark failed for N={n}; see {work}/run.log')
            elapsed = time.monotonic() - start

        already_verified = (verifier.is_file()
                            and 'PUBLIC_RECONSTRUCTION_VERIFIED_NO_PRIVATE_KEY' in verifier.read_text())
        if not (args.resume and already_verified):
            with verifier.open('w') as log:
                subprocess.run(['/usr/bin/time', '-l', str(driver), str(worker), 'verify'],
                               cwd=work, stdout=log, stderr=subprocess.STDOUT, check=True)
        verifier_text = verifier.read_text()
        if 'PUBLIC_RECONSTRUCTION_VERIFIED_NO_PRIVATE_KEY' not in verifier_text:
            raise SystemExit(f'fresh public reconstruction failed for N={n}')
        peak = None
        for line in verifier_text.splitlines():
            if 'maximum resident set size' in line:
                peak = int(line.split()[0])
        result['fresh_public_verification'].append({
            'ring_size': n, 'all_reports_and_statements_reconstructed': True,
            'secret_keys_loaded': False, 'workload_seconds': elapsed,
            'verify_peak_rss_bytes': peak})

        reports = json.loads((work / 'reports.json').read_text())
        if not reports.get('all_verified') or len(reports['samples']) != args.repeats:
            raise SystemExit(f'invalid report row for N={n}')
        result['report_rows'].append({
            'ring_size': n,
            'proof_bytes': reports['report_proof_bytes'],
            'canonical_payload_bytes_excluding_manifest':
                reports['canonical_report_payload_bytes_excluding_manifest'],
            'generate_ms': stats(x['generate_ms'] for x in reports['samples']),
            'verify_ms': stats(x['verify_ms'] for x in reports['samples']),
            'max_rss_bytes': reports.get('max_rss_bytes'),
            'samples': reports['samples']})

        for method, s in CELLS:
            name = f'{method}_s{s}'
            cell = json.loads((work / (name + '.json')).read_text())
            originals = json.loads((work / (name + '.originals.json')).read_text())
            expected = 1 if method == 'claim' else (s - 1 if method == 'anchor' else s)
            if not cell.get('all_verified'):
                raise SystemExit(f'{name} N={n} did not verify')
            if len(cell['samples']) != args.repeats:
                raise SystemExit(f'{name} N={n} has {len(cell["samples"])} samples')
            if len(originals['samples']) != args.repeats:
                raise SystemExit(f'{name} N={n} has {len(originals["samples"])} original samples')
            if cell['proof_count'] != expected or cell['proof_bytes'] != 49208 * expected:
                raise SystemExit(f'{name} N={n} proof accounting mismatch')
            proof_file = work / (name + '.proofs')
            request_file = work / (name + '.requests')
            selection_file = work / (name + '.selection')
            result['certificate_rows'].append({
                'ring_size': n, 'method': method, 'selected_count': s,
                'proof_count': cell['proof_count'], 'proof_bytes': cell['proof_bytes'],
                'proof_file_bytes': proof_file.stat().st_size,
                'request_file_bytes': request_file.stat().st_size,
                'selection_file_bytes': selection_file.stat().st_size,
                'generate_ms': stats(x['generate_ms'] for x in cell['samples']),
                'verify_ms': stats(x['verify_ms'] for x in cell['samples']),
                'original_set_ms': stats(originals['samples']),
                'max_rss_bytes': cell.get('max_rss_bytes'),
                'sign_attempts': [x.get('sign_attempts') for x in cell['samples']],
                'samples': cell['samples'],
                'original_set_samples_ms': originals['samples']})
        (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        print(f'=== N={n} complete and independently verified in {elapsed:.1f}s ===', flush=True)

    result['completed_at'] = datetime.now(timezone.utc).astimezone().isoformat()
    (out / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    files = {str(p.relative_to(out)): sha256(p) for p in sorted(out.rglob('*'))
             if p.is_file() and p.name != 'file_hashes.json'}
    (out / 'file_hashes.json').write_text(json.dumps(files, indent=2) + '\n')
    print(out / 'results.json', flush=True)


if __name__ == '__main__':
    main()
