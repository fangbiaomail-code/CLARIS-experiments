#!/usr/bin/env python3
"""Counter-instrumented diagnostic build: count primitive calls per CLARIS operation.

This is a *diagnostic* build only. The counters add work to hot loops, so its timings
are not used; only call counts are taken from it. The benchmarking build in `build/`
remains free of instrumentation.

Usage:
  python3 diagnostics/make_counters.py --build build --output diagnostics
Produces results/processed/operation_counts.csv and results/raw/operation_count_runs.json.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

FLAGS = ['-arch', 'x86_64', '-O2', '-march=x86-64', '-mavx2', '-maes', '-mpclmul',
         '-DNDEBUG', '-D_bswap64=__builtin_bswap64', '-std=c11',
         '-Wno-ignored-attributes', '-Wno-unused-value',
         '-Wno-incompatible-pointer-types-discards-qualifiers']

COUNTERS_H = """#ifndef CLARIS_COUNTERS_H
#define CLARIS_COUNTERS_H
enum {
  CTR_AES_KEYSCHED = 0,
  CTR_AES_BLOCKS,
  CTR_HASH_INIT,
  CTR_HASH_UPDATE,
  CTR_HASH_FINAL,
  CTR_HASH_INIT_X4,
  CTR_HASH_UPDATE_X4,
  CTR_HASH_FINAL_X4,
  CTR_VOLE_SENDER,
  CTR_VOLE_RECEIVER,
  CTR_COUNT
};
extern unsigned long long claris_ctr[CTR_COUNT];
#endif
"""
COUNTERS_C = '#include "counters.h"\nunsigned long long claris_ctr[CTR_COUNT];\n'


def patch(path, old, new, count=1):
    text = path.read_text()
    if text.count(old) != count:
        raise SystemExit(f'anchor not found ({text.count(old)} != {count}) in {path}: {old[:70]!r}')
    path.write_text(text.replace(old, new))


def instrument_tree(root):
    (root / 'counters.h').write_text(COUNTERS_H)
    (root / 'counters.c').write_text(COUNTERS_C)

    patch(root / 'aes.h', '#include "block.h"', '#include "block.h"\n#include "counters.h"')
    patch(root / 'aes_impl.h', '#include "util.h"', '#include "util.h"\n#include "counters.h"')

    for signature in [
        ('inline void aes_fixed_key_ctr(\n\tconst aes_round_keys* restrict fixed_key, '
         'const block128* restrict keys,\n\tsize_t num_keys, uint32_t num_blocks, '
         'uint32_t counter, block128* restrict output)\n{\n'),
        ('inline void rijndael256_fixed_key_ctr(\n\tconst rijndael256_round_keys* restrict fixed_key, '
         'const block256* restrict keys,\n\tsize_t num_keys, uint32_t num_blocks, '
         'uint32_t counter, block256* restrict output)\n{\n'),
        ('inline void rijndael192_fixed_key_ctr(\n\tconst rijndael192_round_keys* restrict fixed_key, '
         'const block192* restrict keys,\n\tsize_t num_keys, uint32_t num_blocks, '
         'uint32_t counter, block192* restrict output)\n{\n')]:
        patch(root / 'aes_impl.h', signature,
              signature + '\tclaris_ctr[CTR_AES_BLOCKS] += (unsigned long long)num_keys * num_blocks;\n')

    patch(root / 'aes_impl.c', 'void rijndael256_keygen(rijndael256_round_keys* round_keys, block256 key)\n{\n',
          'void rijndael256_keygen(rijndael256_round_keys* round_keys, block256 key)\n{\n'
          '\tclaris_ctr[CTR_AES_KEYSCHED]++;\n')
    patch(root / 'aes_impl.c', 'void aes_keygen(aes_round_keys* round_keys, block_secpar key)\n{\n',
          'void aes_keygen(aes_round_keys* round_keys, block_secpar key)\n{\n'
          '\tclaris_ctr[CTR_AES_KEYSCHED]++;\n')
    # PRG key-schedule + counter-block setup used by the VOLE commit phase.
    patch(root / 'aes_impl.h',
          'ALWAYS_INLINE void aes_keygen_ctr(\n'
          '\taes_round_keys* restrict aeses, const block_secpar* restrict keys, '
          'const block128* restrict ivs,\n'
          '\tsize_t num_keys, uint32_t num_blocks, uint32_t counter, block128* restrict output)\n{\n',
          'ALWAYS_INLINE void aes_keygen_ctr(\n'
          '\taes_round_keys* restrict aeses, const block_secpar* restrict keys, '
          'const block128* restrict ivs,\n'
          '\tsize_t num_keys, uint32_t num_blocks, uint32_t counter, block128* restrict output)\n{\n'
          '\tclaris_ctr[CTR_AES_KEYSCHED] += (unsigned long long)num_keys;\n')
    # The AES OWF uses the multi-key CTR interface for block encryption.
    patch(root / 'aes_impl.h',
          'inline void aes_ctr(\n\tconst aes_round_keys* restrict aeses,\n'
          '\tsize_t num_keys, uint32_t num_blocks, uint32_t counter, block128* restrict output)\n{\n',
          'inline void aes_ctr(\n\tconst aes_round_keys* restrict aeses,\n'
          '\tsize_t num_keys, uint32_t num_blocks, uint32_t counter, block128* restrict output)\n{\n'
          '\tclaris_ctr[CTR_AES_BLOCKS] += (unsigned long long)num_keys * num_blocks;\n')

    patch(root / 'hash.h', '#include "KeccakHashtimes4.h"',
          '#include "KeccakHashtimes4.h"\n#include "counters.h"')
    for anchor, counter in [
        ('inline int hash_init(hash_state* ctx)\n{\n', 'CTR_HASH_INIT'),
        ('inline int hash_update(hash_state* ctx, const void* input, size_t bytes)\n{\n', 'CTR_HASH_UPDATE'),
        ('inline int hash_final(hash_state* ctx, void* digest, size_t bytes)\n{\n', 'CTR_HASH_FINAL'),
        ('inline void hash_init_x4(hash_state_x4* ctx)\n{\n', 'CTR_HASH_INIT_X4'),
        ('inline void hash_update_x4(hash_state_x4* ctx, const void** data, size_t size)\n{\n',
         'CTR_HASH_UPDATE_X4'),
        ('inline void hash_final_x4(hash_state_x4* ctx, void** buffer, size_t buflen)\n{\n',
         'CTR_HASH_FINAL_X4')]:
        patch(root / 'hash.h', anchor, anchor + f'\tclaris_ctr[{counter}]++;\n')

    patch(root / 'small_vole.c', '#include "small_vole.h"', '#include "small_vole.h"\n#include "counters.h"')
    sender = ('void vole_sender(\n\tunsigned int k, const block_secpar* restrict keys,\n'
              '\tblock128 iv, const prg_vole_fixed_key* restrict fixed_key,\n'
              '\tconst vole_block* restrict u, vole_block* restrict v, vole_block* restrict c, '
              'size_t col_len)\n{\n')
    patch(root / 'small_vole.c', sender, sender + '\tclaris_ctr[CTR_VOLE_SENDER]++;\n')
    receiver = ('void vole_receiver(\n\tunsigned int k, const block_secpar* restrict keys,\n'
                '\tblock128 iv, const prg_vole_fixed_key* restrict fixed_key,\n'
                '\tconst vole_block* restrict c, vole_block* restrict q,\n'
                '\tconst uint8_t* restrict delta, size_t col_len)\n{\n')
    patch(root / 'small_vole.c', receiver, receiver + '\tclaris_ctr[CTR_VOLE_RECEIVER]++;\n')


def patch_worker(path):
    patch(path, '#include "faest.c"', '#include "faest.c"\n#include "counters.h"')
    patch(path,
          'uint8_t key[32];readn(stdin,key,32);if(fgetc(stdin)!=EOF)return 53;',
          'unsigned long long gen_ctr[CTR_COUNT]={0},ver_ctr[CTR_COUNT]={0};\n'
          ' uint8_t key[32];readn(stdin,key,32);if(fgetc(stdin)!=EOF)return 53;')
    old_loop = ('for(int j=-warm;j<reps;++j){uint64_t attempts=0;double t=millis();'
                'prove_batch(requests,proofs,n,key,sk,&attempts);double gen=millis()-t;'
                't=millis();int ok=verify_batch(requests,proofs,n);double ver=millis()-t;'
                'if(!ok)return 55;')
    new_loop = ('for(int j=-warm;j<reps;++j){uint64_t attempts=0;unsigned long long c0[CTR_COUNT],c1[CTR_COUNT];'
                'for(int q=0;q<CTR_COUNT;q++)c0[q]=claris_ctr[q];'
                'double t=millis();prove_batch(requests,proofs,n,key,sk,&attempts);double gen=millis()-t;'
                'for(int q=0;q<CTR_COUNT;q++)gen_ctr[q]+=claris_ctr[q]-c0[q];'
                'for(int q=0;q<CTR_COUNT;q++)c1[q]=claris_ctr[q];'
                't=millis();int ok=verify_batch(requests,proofs,n);double ver=millis()-t;'
                'for(int q=0;q<CTR_COUNT;q++)ver_ctr[q]+=claris_ctr[q]-c1[q];'
                'if(!ok)return 55;')
    patch(path, old_loop, new_loop)
    patch(path,
          'fprintf(f,"],\\"max_rss_bytes\\":%zu,\\"all_verified\\":true}\\n",rss);',
          'fprintf(f,"],\\"max_rss_bytes\\":%zu,\\"counters_gen\\":[",rss);\n'
          ' for(int q=0;q<CTR_COUNT;q++)fprintf(f,"%s%llu",q?",":"",gen_ctr[q]);\n'
          ' fprintf(f,"],\\"counters_ver\\":[");\n'
          ' for(int q=0;q<CTR_COUNT;q++)fprintf(f,"%s%llu",q?",":"",ver_ctr[q]);\n'
          ' fprintf(f,"],\\"all_verified\\":true}\\n");')
    patch(path,
          'int ok=verify_batch(requests,proofs,n);free(requests);free(proofs);',
          'unsigned long long vbase[CTR_COUNT];for(int q=0;q<CTR_COUNT;q++)vbase[q]=claris_ctr[q];\n'
          ' int ok=verify_batch(requests,proofs,n);printf("COUNTERS verify ");\n'
          ' for(int q=0;q<CTR_COUNT;q++)printf("%s%llu",q?",":"",claris_ctr[q]-vbase[q]);\n'
          ' printf("\\n");free(requests);free(proofs);')


def patch_driver(path):
    patch(path, '#include "validate_star.c"', '#include "validate_star.c"\n#include "counters.h"')
    old = ('for(int i=-warm;i<reps;++i){int idx=i<0?0:i%5;double t=now();report_sign(p,idx,sk,key,owner,ins);'
           'double sign=now()-t;t=now();int ok=strict_ring(p)&&rv(p,&p->reports[idx]);double ver=now()-t;')
    new = ('for(int i=-warm;i<reps;++i){int idx=i<0?0:i%5;unsigned long long rb[CTR_COUNT],rvb[CTR_COUNT];'
           'for(int q=0;q<CTR_COUNT;q++){rb[q]=claris_ctr[q];}\n'
           'double t=now();report_sign(p,idx,sk,key,owner,ins);double sign=now()-t;\n'
           'if(i==0){printf("COUNTERS report N=%d sign ",FAEST_RING_SIZE);'
           'for(int q=0;q<CTR_COUNT;q++)printf("%s%llu",q?",":"",claris_ctr[q]-rb[q]);printf("\\n");}\n'
           'for(int q=0;q<CTR_COUNT;q++){rvb[q]=claris_ctr[q];}t=now();'
           'int ok=strict_ring(p)&&rv(p,&p->reports[idx]);double ver=now()-t;\n'
           'if(i==0){printf("COUNTERS report N=%d verify ",FAEST_RING_SIZE);'
           'for(int q=0;q<CTR_COUNT;q++)printf("%s%llu",q?",":"",claris_ctr[q]-rvb[q]);printf("\\n");}\n')
    patch(path, old, new)


def compile_all(root, build, source):
    cc = shutil.which('clang')
    if not cc:
        raise SystemExit('clang not found')
    darwin = sys.platform == 'darwin'
    targets = ['ordinary'] + [f'ring_n{n}' for n in (16, 64, 256, 1024)]
    for target in targets:
        src = build / target
        dst = root / target
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        instrument_tree(dst)
        # The counter headers are inline: every object must be rebuilt so the
        # increments are actually compiled into the hot paths.
        for source_file in sorted(dst.glob('*.c')) + sorted(dst.glob('*.s')):
            if source_file.name == 'counters.c':
                continue
            if target == 'ordinary' and source_file.name == 'faest.c':
                continue
            obj = source_file.with_suffix('.o')
            command = [cc, *FLAGS, '-I', str(dst), '-c', str(source_file), '-o', str(obj)]
            if source_file.suffix == '.s' and darwin:
                command += ['-Wa,-defsym,no_type=1', '-Wa,-defsym,no_size=1',
                            '-Wa,-defsym,no_plt=1']
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
        subprocess.run([cc, *FLAGS, '-I', str(dst), '-c', str(dst / 'counters.c'),
                        '-o', str(dst / 'counters.o')], check=True)
        objects = [p for p in sorted(dst.glob('*.o')) if p.name != 'faest.o' or target != 'ordinary']
        if target == 'ordinary':
            harness = root / 'ordinary_worker_counter.c'
            compile_cmd = [cc, *FLAGS, '-I', str(dst), str(harness),
                           *map(str, objects), '-o', str(dst / 'ordinary_worker')]
        else:
            harness = root / 'ordinary_benchmark_counter.c'
            compile_cmd = [cc, *FLAGS, '-I', str(dst), '-I', str(source / 'experiments/security'),
                           str(harness), *map(str, objects), '-o', str(dst / 'ordinary_benchmark')]
        subprocess.run(compile_cmd, check=True, stdout=subprocess.DEVNULL)
        print(f'built counter target {target}', flush=True)


def run(root, ns, reps=1, warm=0):
    out = root / 'runs'
    out.mkdir(exist_ok=True)
    worker = root / 'ordinary/ordinary_worker'
    results = {'schema': 'claris-operation-counts-v1', 'reps': reps, 'warmups': warm,
               'note': 'counter-instrumented diagnostic build; not used for timing',
               'rings': [], 'ordinary': []}
    for n in ns:
        work = out / f'n{n}'
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        driver = root / f'ring_n{n}/ordinary_benchmark'
        proc = subprocess.run([str(driver), str(worker), str(reps), str(warm)], cwd=work,
                              capture_output=True, text=True)
        if proc.returncode:
            raise SystemExit(f'diagnostic run failed N={n}: {proc.stdout[-2000:]}')
        ring = {'ring_size': n, 'report': {}, 'cells': []}
        for line in proc.stdout.splitlines():
            m = re.match(r'COUNTERS report N=(\d+) (sign|verify) ([\d,]+)', line)
            if m:
                ring['report'][m.group(2)] = [int(x) for x in m.group(3).split(',')]
        for p in sorted(work.glob('*.json')):
            if p.name in ('reports.json',) or '.originals.' in p.name:
                continue
            d = json.loads(p.read_text())
            if 'counters_gen' not in d:
                continue
            method, s = p.stem.split('_s')
            ring['cells'].append({'method': method, 'selected_count': int(s),
                                  'proof_count': d['proof_count'],
                                  'counters_gen': d['counters_gen'],
                                  'counters_ver': d['counters_ver'],
                                  'sources': p.name})
        results['rings'].append(ring)
        print(f'counted N={n}', flush=True)
        del n, ring
    (root / 'runs' / 'operation_counts.json').write_text(json.dumps(results, indent=2) + '\n')
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, default=Path('build'))
    ap.add_argument('--source', type=Path, default=Path('source'))
    ap.add_argument('--output', type=Path, default=Path('diagnostics'))
    args = ap.parse_args()
    root = args.output.resolve()
    root.mkdir(exist_ok=True)
    (root / 'ordinary_worker_counter.c').write_text(
        (args.source / 'experiments/benchmark/ordinary_worker.c').read_text())
    (root / 'ordinary_benchmark_counter.c').write_text(
        (args.source / 'experiments/benchmark/ordinary_benchmark.c').read_text())
    patch_worker(root / 'ordinary_worker_counter.c')
    patch_driver(root / 'ordinary_benchmark_counter.c')
    compile_all(root, args.build.resolve(), args.source.resolve())
    run(root, [16, 64, 256, 1024])
    print('done')


if __name__ == '__main__':
    main()
