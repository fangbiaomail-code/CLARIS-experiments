#!/usr/bin/env python3
"""Repair a fresh COPY of the Q backend before the namespace patch.

Only the two-selector Q configuration is supported. Never apply to G builds.
Separates branch/outer batching challenges and batches selector equations
individually. Proof/witness layouts and degree are unchanged.
"""
from pathlib import Path
import hashlib
import json
import sys


def apply_patch(source_dir):
    root = Path(source_dir)
    paths = {name: root / name for name in ('quicksilver.h', 'quicksilver.c')}
    s = paths['quicksilver.c'].read_text()
    h = paths['quicksilver.h'].read_text()
    if 'CLARIS_RING_BATCHING_V2' in s + h:
        raise ValueError('already patched; start with a fresh source copy')
    if '#define OWF_BLOCKS 8' in (root / 'owf_proof.h').read_text():
        raise ValueError('Q-only patch must not be applied to an ordinary G build')
    before = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()}
    old = '#define QUICKSILVER_CHALLENGE_BYTES ((3 * SECURITY_PARAM + 64) / 8)'
    assert h.count(old) == 1
    h = h.replace(old, '''/* CLARIS_RING_BATCHING_V2: independent outer and inner key tuples. */
#if FAEST_RING_HOTVECTOR_DIM != 2
#error "CLARIS v2 Q backend requires the audited two-selector configuration"
#endif
#define CLARIS_QS_BATCH_KEY_BYTES ((3 * SECURITY_PARAM + 64) / 8)
#define QUICKSILVER_CHALLENGE_BYTES (2 * CLARIS_QS_BATCH_KEY_BYTES)''')
    old = '\tpoly_secpar_vec hash_combination[2];'
    assert h.count(old) == 1
    h = h.replace(old, old + '''
    poly_secpar_vec branch_hash_combination[2];
    hasher_gfsecpar_key branch_key_secpar;
    hasher_gfsecpar_64_key branch_key_64;''')
    for old, new, expected in (
        ('&state->key_secpar, &state->state_or_', '&state->branch_key_secpar, &state->state_or_', 4),
        ('&state->key_64, &state->state_or_', '&state->branch_key_64, &state->state_or_', 4)):
        assert h.count(old) == expected, (old, h.count(old))
        h = h.replace(old, new)
    # Independent slices of the same fresh stage-4 XOF output. These slices
    # are uniform and independent in the ROM; no extra proof bytes are sent.
    helper = '''/* CLARIS_RING_BATCHING_V2 */
static void claris_init_branch_hash_keys(quicksilver_state* state, const uint8_t* challenge)
{
    challenge += CLARIS_QS_BATCH_KEY_BYTES;
    for (size_t i = 0; i < 2; ++i, challenge += SECURITY_PARAM / 8)
        state->branch_hash_combination[i] = poly_secpar_load_dup(challenge);
    hasher_gfsecpar_init_key(&state->branch_key_secpar, poly_secpar_load_dup(challenge));
    hasher_gfsecpar_64_init_key(&state->branch_key_64,
                              poly64_load_dup(challenge + SECURITY_PARAM / 8));
}

'''
    pos = s.index('void quicksilver_init_or_prover(')
    s = s[:pos] + helper + s[pos:]
    # Exactly the two OR initializers get the second key tuple.
    for name in ('quicksilver_init_or_prover', 'quicksilver_init_or_verifier'):
        start = s.index('void ' + name + '(')
        end = s.index('\n}', start)
        body = s[start:end]
        old = 'quicksilver_init_hash_keys(state, challenge);'
        assert body.count(old) == 1
        body = body.replace(old, old + '\n    claris_init_branch_hash_keys(state, challenge);')
        s = s[:start] + body + s[end:]
    s = s.replace('// initialize hash keys, which are reused by prover for both branch and final (ZK)hashes.',
                  '// Initialize independent keys for branch and final batching.')
    start = s.index('static poly_secpar_vec quicksilver_lincombine_hasher_state(')
    end = s.index('\n}', start)
    body = s[start:end]
    assert body.count('state->hash_combination[i]') == 1
    body = body.replace('state->hash_combination[i]', 'state->branch_hash_combination[i]')
    s = s[:start] + body + s[end:]
    # Field labels must be distinct. from_1 is a bit-vector conversion and
    # is not the specified index-to-field map.
    assert s.count('poly_secpar_from_1(idx + 1)') == 16
    s = s.replace('poly_secpar_from_1(idx + 1)', 'poly_secpar_set_low32(idx + 1)')
    old = '+ FAEST_RING_SIZE + FAEST_RING_HOTVECTOR_DIM;'
    assert s.count(old) == 4
    s = s.replace(old, '+ FAEST_RING_SIZE + FAEST_RING_HOTVECTOR_DIM * (FAEST_RING_HOTVECTOR_BITS + 1);')

    start = s.index('\t// Well-formedness of hotvec (single active bit).')
    end = s.index('\t// Final ZKHash.', start)
    prover = '''    /* Each selector equation is a separate outer-batch coefficient. */
    for (uint32_t idx = 0; idx < FAEST_RING_HOTVECTOR_BITS + 1; ++idx) {
        qs_prover_poly_deg1 labels[2] = {
            qs_prover_poly_const_add_deg1(state, poly_secpar_set_low32(idx + 1), hotvec0_mul_idx_sum),
            qs_prover_poly_const_add_deg1(state, poly_secpar_set_low32(idx + 1), hotvec1_mul_idx_sum)
        };
        qs_prover_poly_deg1 bits[2] = {hotvec0[idx], hotvec1[idx]};
        for (size_t dim = 0; dim < 2; ++dim) {
            qs_prover_poly_deg2 c = qs_prover_poly_deg1_mul_deg1(state, labels[dim], bits[dim]);
            /* Multiply by X^2 to align the omitted residual with degree four. */
            hasher_gfsecpar_update(&state->key_secpar, &state->state_secpar_const, poly_secpar_from_byte(0));
            hasher_gfsecpar_update(&state->key_secpar, &state->state_secpar_linear, poly_secpar_from_byte(0));
            hasher_gfsecpar_update(&state->key_secpar, &state->state_secpar_quad, c.c0);
            hasher_gfsecpar_update(&state->key_secpar, &state->state_secpar_cubic, c.c1);
            hasher_gfsecpar_64_update(&state->key_64, &state->state_64_const, poly_secpar_from_byte(0));
            hasher_gfsecpar_64_update(&state->key_64, &state->state_64_linear, poly_secpar_from_byte(0));
            hasher_gfsecpar_64_update(&state->key_64, &state->state_64_quad, c.c0);
            hasher_gfsecpar_64_update(&state->key_64, &state->state_64_cubic, c.c1);
        }
    }
    free(hotvec0);
    free(hotvec1);

'''
    s = s[:start] + prover + s[end:]
    start = s.index('\t// Well-formedness of hotvec (single active bit).')
    end = s.index('\tpoly_secpar_vec linear_term =', start)
    verifier = '''    /* Same per-index/per-dimension order as the prover. */
    for (uint32_t idx = 0; idx < FAEST_RING_HOTVECTOR_BITS + 1; ++idx) {
        qs_verifier_key labels[2] = {
            quicksilver_verifier_const_add_key(state, poly_secpar_set_low32(idx + 1), hotvec0_mul_idx_sum),
            quicksilver_verifier_const_add_key(state, poly_secpar_set_low32(idx + 1), hotvec1_mul_idx_sum)
        };
        qs_verifier_key bits[2] = {hotvec0[idx], hotvec1[idx]};
        for (size_t dim = 0; dim < 2; ++dim) {
            qs_verifier_key c = quicksilver_verifier_key_mul_key(state, labels[dim], bits[dim]);
            quicksilver_verifier_increase_key_deg(state, &c, 2);
            hasher_gfsecpar_update(&state->key_secpar, &state->state_secpar_const, c.key);
            hasher_gfsecpar_64_update(&state->key_64, &state->state_64_const, c.key);
        }
    }
    free(hotvec0);
    free(hotvec1);

'''
    s = s[:start] + verifier + s[end:]
    paths['quicksilver.c'].write_text(s)
    paths['quicksilver.h'].write_text(h)
    manifest = {'profile':'CLARIS Q batching v2', 'scope':'Q only; G unchanged',
                'dimension':2, 'challenge_bytes_before':104, 'challenge_bytes_after':208,
                'selector_checks':'2*(FAEST_RING_HOTVECTOR_BITS+1)',
                'proof_layout_changed':False, 'witness_layout_changed':False,
                'max_check_degree':4, 'source_before':before,
                'source_after':{n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in paths.items()}}
    (root / 'ring_batching_v2.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: patch_ring_batching_v2.py SOURCE_DIR')
    print(json.dumps(apply_patch(sys.argv[1]),indent=2))
