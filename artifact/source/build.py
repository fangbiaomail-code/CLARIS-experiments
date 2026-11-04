#!/usr/bin/env python3
"""Offline clean build of the CLARIS research artifact (Python standard library)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise RuntimeError(f"Unexpected source version: {path.name}")
    path.write_text(text.replace(old, new, 1))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ring-sizes', nargs='+', type=int, choices=[64, 1024], default=[64, 1024])
    parser.add_argument('--cc', default=os.environ.get('CC', 'clang'))
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument('--legacy-transcripts', action='store_true',
                        help='Reproduce the archived pre-namespace prototype explicitly.')
    profile.add_argument('--pre-or-batch-fix', action='store_true',
                        help='Reproduce the archived Q-v1/G-v1 profile before the OR batch revision.')
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('Keep generated files outside the source package.')
    if out.exists() and any(out.iterdir()):
        parser.error('Use a new empty output directory; no old objects are reused.')
    cc = shutil.which(args.cc)
    if not cc:
        parser.error(f'C compiler not found: {args.cc}')
    system, machine = platform.system(), platform.machine().lower()
    if system not in ('Darwin', 'Linux'):
        parser.error('This AVX2 source package supports macOS and Linux builds.')
    if system == 'Linux' and machine not in ('x86_64', 'amd64'):
        parser.error('Linux build requires x86_64 AVX2/AES/PCLMUL hardware.')
    subprocess.run([sys.executable, str(ROOT/'verify_sources.py')], check=True)
    out.mkdir(parents=True, exist_ok=True)
    flags = ['-O2', '-march=x86-64', '-mavx2', '-maes', '-mpclmul', '-DNDEBUG',
             '-D_bswap64=__builtin_bswap64', '-std=c11',
             '-Wno-ignored-attributes', '-Wno-unused-value']
    compiler_version = subprocess.check_output([cc, '--version'], text=True)
    if 'clang' in compiler_version.lower():
        flags += ['-Wno-incompatible-pointer-types-discards-qualifiers']
    if system == 'Darwin':
        flags = ['-arch', 'x86_64', *flags]
    else:
        flags += ['-D_POSIX_C_SOURCE=200809L', '-D_DEFAULT_SOURCE']
    records = []
    for kind, n in [('ordinary', 64), *[('ring', n) for n in args.ring_sizes]]:
        folder = out/('ordinary' if kind == 'ordinary' else f'ring_n{n}')
        shutil.copytree(ROOT/'vendor/p01', folder)
        replace_once(folder/'faest.c',
                     '(uint8_t *)aligned_alloc(alignof(uint8_t), FAEST_PUBLIC_KEY_BYTES * FAEST_RING_SIZE)',
                     '(uint8_t *)malloc(FAEST_PUBLIC_KEY_BYTES * FAEST_RING_SIZE)')
        if n != 64:
            replace_once(folder/'config.h', '#define FAEST_RING_2_POW (6)',
                         f'#define FAEST_RING_2_POW ({n.bit_length()-1})')
        if kind == 'ordinary':
            replace_once(folder/'owf_proof.h', '#define OWF_BLOCKS ((SECURITY_PARAM + 127) / 128)',
                         '#define OWF_BLOCKS 8')
            replace_once(folder/'faest.h', '#define FAEST_PUBLIC_KEY_BYTES FAEST_SECRET_KEY_BYTES',
                         '#define FAEST_PUBLIC_KEY_BYTES (2 * FAEST_IV_BYTES)')
        if not args.legacy_transcripts:
            if kind == 'ring' and not args.pre_or_batch_fix:
                subprocess.run([sys.executable, str(ROOT/'patches/patch_ring_batching_v2.py'),
                                str(folder)], check=True)
            patcher = ROOT/'patches/patch_transcript_domains.py'
            if not patcher.exists():
                raise RuntimeError('Missing required transcript-domain patch.')
            namespace_version = 'v2' if kind == 'ring' and not args.pre_or_batch_fix else 'v1'
            subprocess.run([sys.executable, str(patcher), str(folder),
                            'G' if kind == 'ordinary' else 'Q', namespace_version], check=True)
        objects = []
        commands = []
        logpath = folder/'build.log'
        with logpath.open('w') as log:
            sources = sorted(folder.glob('*.c')) + sorted(folder.glob('*.s'))
            for source in sources:
                if kind == 'ordinary' and source.name == 'faest.c':
                    continue  # pair_cli includes the implementation for adversarial tests.
                obj = source.with_suffix('.o')
                command = [cc, *flags, '-I', str(folder), '-c', str(source), '-o', str(obj)]
                if source.suffix == '.s' and system == 'Darwin':
                    command += ['-Wa,-defsym,no_type=1', '-Wa,-defsym,no_size=1', '-Wa,-defsym,no_plt=1']
                commands.append(command)
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
                objects.append(str(obj))
            harness = ROOT/'experiments/security/ordinary'/('pair_cli.c' if kind == 'ordinary' else 'joint_pair.c')
            exe = folder/('pair_cli' if kind == 'ordinary' else 'joint_pair')
            command = [cc, *flags, '-I', str(folder), str(harness), *objects, '-o', str(exe)]
            commands.append(command)
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
            benchmark = ROOT/'experiments/benchmark'/('ordinary_worker.c' if kind == 'ordinary' else 'ordinary_benchmark.c')
            benchmark_exe = folder/benchmark.stem
            command = [cc, *flags, '-I', str(folder), '-I', str(ROOT/'experiments/security'),
                       str(benchmark), *objects, '-o', str(benchmark_exe)]
            commands.append(command)
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        record = {'target':folder.name, 'all_objects_built_from_source':True,
                  'commands':commands, 'sources_sha256':{p.name:sha(p) for p in sources},
                  'binary_sha256':sha(exe), 'benchmark_binary_sha256':sha(benchmark_exe)}
        if kind == 'ordinary':
            record['parameters'] = json.loads(subprocess.check_output([str(exe), 'info'], text=True))
            if record['parameters']['proof_bytes'] != 49208:
                raise RuntimeError('Unexpected ordinary proof length.')
        records.append(record)
        print(f'Built {folder.name}', flush=True)
    result = {'schema':'claris-build-v1', 'compiler':compiler_version, 'flags':flags,
              'host':platform.platform(), 'execution_target':'x86_64 AVX2 AES PCLMUL',
              'transcript_profile':('legacy' if args.legacy_transcripts else
                                    'CLARIS-v1-namespaced' if args.pre_or_batch_fix else
                                    'CLARIS-Q-v2-G-v1'),
              'network_used':False, 'targets':records}
    (out/'build_manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print(out/'build_manifest.json')


if __name__ == '__main__':
    main()
