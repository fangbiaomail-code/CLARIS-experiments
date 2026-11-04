#!/usr/bin/env python3
"""Patch a *copy* of the P01 backend with CLARIS proof-only hash namespaces.

CLI: python3 patch_transcript_domains.py SOURCE_DIR {Q,G}
Call after config/ordinary-header changes, before compiling any object.
Public wrapper hash_init/hash_init_x4 semantics remain unchanged.
This makes namespaces explicit; it does not establish base-proof extraction.
"""
from pathlib import Path
import hashlib
import json
import re
import sys


def apply_patch(source_dir, proof_kind, profile='v1'):
    root = Path(source_dir)
    if proof_kind not in ('Q', 'G'):
        raise ValueError('proof_kind must be Q (report) or G (ordinary pair)')
    if profile not in ('v1', 'v2') or (proof_kind == 'G' and profile != 'v1'):
        raise ValueError('v2 is available only for Q; G retains v1 unchanged')
    files = ('hash.h', 'faest.c', 'vector_com.c', 'vole_commit.c', 'vole_check.c')
    texts = {name: (root / name).read_text() for name in files}
    if any('CLARIS_PROOF_NAMESPACE_V' in s for s in texts.values()):
        raise ValueError('backend is already patched; use a fresh source copy')
    # Bind the parameter and circuit headers after all configuration changes.
    param_files = ('config.h', 'faest.h', 'faest_details.h', 'owf_proof.h',
                   'vole_params.h', 'quicksilver.h', 'aes.h')
    if profile == 'v2':
        param_files += ('quicksilver.c', 'owf_proof.c')
    params = hashlib.sha256(('CLARIS/P01/fa540fa152303a23b55a0a63efe20977076a6e15/'+profile+'\0').encode())
    for name in param_files:
        data = (root / name).read_bytes()
        params.update(name.encode() + b'\0' + len(data).to_bytes(8, 'big') + data)
    parameter_id = params.digest()
    namespace = ('CLARIS-PROOF-'+profile+'\0').encode() + proof_kind.encode() + parameter_id
    literals = ', '.join('0x%02x' % b for b in namespace)
    helpers = '''/* CLARIS_PROOF_NAMESPACE_V1: proof hashes only; wrapper hashes are unchanged. */
static inline void claris_proof_hash_init(hash_state* ctx, uint8_t stage)
{
    static const uint8_t ns[] = { NAMESPACE_BYTES };
    hash_init(ctx);
    hash_update(ctx, ns, sizeof(ns));
    hash_update_byte(ctx, stage);
}
static inline void claris_proof_hash_init_x4(hash_state_x4* ctx, uint8_t stage)
{
    static const uint8_t ns[] = { NAMESPACE_BYTES };
    hash_init_x4(ctx);
    hash_update_x4_1(ctx, ns, sizeof(ns));
    hash_update_x4_1_byte(ctx, stage);
}

'''.replace('NAMESPACE_BYTES', literals).replace('NAMESPACE_V1', 'NAMESPACE_'+profile.upper())
    h = texts['hash.h']
    needle = 'inline void shake_prg('
    assert h.count(needle) == 1
    head, tail = h.split(needle)
    # SHAKE leaf PRG: preserve equality of scalar and x4 evaluations.
    assert tail.count('hash_init_x4(&hasher);') == 1
    assert tail.count('hash_init(&hasher);') == 1
    tail = tail.replace('hash_init_x4(&hasher);', 'claris_proof_hash_init_x4(&hasher, 6);')
    tail = tail.replace('hash_init(&hasher);', 'claris_proof_hash_init(&hasher, 6);')
    texts['hash.h'] = head + helpers + needle + tail

    s = texts['faest.c']
    # The five upstream prover/verification families share the same stage order.
    names = ('faest', 'faest_tagged', 'faest_ring', 'faest_cbc_tagged_ring', 'faest_tagged_ring')
    count = 0
    for base in names:
        for suffix, stages in (('_sign_attempt', (1, 2, 3, 4, 5)), ('_verify', (1, 3, 4, 5))):
            name = base + suffix
            start = re.search(r'(?:static )?bool ' + re.escape(name) + r'\(', s)
            assert start, name
            end = re.search(r'\n(?:static )?bool ', s[start.end():])
            endpos = start.end() + end.start() if end else len(s)
            body = s[start.start():endpos]
            assert body.count('hash_init(&hasher);') == len(stages), name
            for stage in stages:
                body = body.replace('hash_init(&hasher);',
                                    f'claris_proof_hash_init(&hasher, {stage});', 1)
                count += 1
            s = s[:start.start()] + body + s[endpos:]
    assert 'hash_init(&hasher);' not in s
    s = s.replace('// TODO: Do we need to domain separate by the faest parameters?',
                  '// Proof kind, parameter digest, and stage are bound by claris_proof_hash_init.')
    texts['faest.c'] = s

    s = texts['vector_com.c']
    assert s.count('hash_init_x4(&hashx4);') == 1
    # Counter-based final-challenge grinding must match the verifier's stage 5.
    texts['vector_com.c'] = s.replace('hash_init_x4(&hashx4);',
                                    'claris_proof_hash_init_x4(&hashx4, 5);')
    s = texts['vole_commit.c']
    for old, new in (
        ('hash_init_x4(&leaves_hasher);', 'claris_proof_hash_init_x4(&leaves_hasher, 7);'),
        ('hash_init(&leaves_hasher);', 'claris_proof_hash_init(&leaves_hasher, 7);'),
        ('hash_init(&hasher);', 'claris_proof_hash_init(&hasher, 8);')):
        assert s.count(old) == 1
        s = s.replace(old, new)
    texts['vole_commit.c'] = s
    s = texts['vole_check.c']
    assert s.count('hash_init(&hasher);') == 1
    texts['vole_check.c'] = s.replace('hash_init(&hasher);',
                                    'claris_proof_hash_init(&hasher, 9);')
    before = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files}
    for name, data in texts.items():
        (root / name).write_text(data)
    manifest = {
        'profile': 'CLARIS-PROOF-'+profile, 'proof_kind': proof_kind,
        'parameter_id': parameter_id.hex(), 'namespace_hex': namespace.hex(),
        'stages': {'1':'statement prehash', '2':'prover seed and IV',
                   '3':'VOLE-check challenge', '4':'constraint-batching challenge',
                   '5':'opening challenge including grinding counter',
                   '6':'SHAKE leaf PRG', '7':'per-tree leaf digest',
                   '8':'VOLE commitment digest', '9':'VOLE-check digest'},
        'faest_init_sites': count, 'public_wrapper_hash_functions_changed': False,
        'source_before': before,
        'source_after': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files},
        'base_simulation_extractability_certified': False,
    }
    (root / 'transcript_namespace.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        raise SystemExit('usage: patch_transcript_domains.py SOURCE_DIR Q|G [v1|v2]')
    print(json.dumps(apply_patch(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)==4 else 'v1'), indent=2))
