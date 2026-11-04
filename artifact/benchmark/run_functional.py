#!/usr/bin/env python3
"""Functional and public-verification checks for every ring size in the matrix.

Mirrors the artifact smoke procedure: fresh keys and reports, adversarial claim/link
checks inside one process, then two independent verifier processes that load only
public material. Functional evidence only; it is not a cryptographic security proof.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

CHECKS = [
    ('Correct identity claim', 'EX01 actual signer claims original signature'),
    ('Wrong identity claim rejected', 'EX01 wrong claimed identity rejected'),
    ('Same-owner reports link', 'EX02 selected three signatures link anonymously'),
    ('Different-owner reports separated', 'EX02 full mixed-signer linking proof rejected'),
    ('Tampered report content rejected', 'message/nonce substitution rejected'),
    ('Replaced report identifier rejected', 'proof transplant / unselected report substitution rejected'),
    ('Tampered context rejected', 'selected-set order and context substitution rejected'),
    ('Public verification without secret key', 'fresh public verifier and identity-free link verifier'),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--ring-sizes', nargs='+', type=int, default=[16, 64, 256, 1024])
    args = ap.parse_args()
    build = args.build.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((build / 'build_manifest.json').read_text())
    cli = build / 'ordinary/pair_cli'
    info = json.loads(subprocess.check_output([str(cli), 'info'], text=True))
    assert info['blocks'] == 8 and info['proof_bytes'] == 49208
    rows = []
    for n in args.ring_sizes:
        exe = build / f'ring_n{n}/joint_pair'
        with tempfile.TemporaryDirectory(prefix=f'claris-func-{n}-') as temporary:
            work = Path(temporary)
            logs = {}
            for mode in [None, 'verify', 'verify-link']:
                command = [str(exe), str(cli)] + ([mode] if mode else [])
                done = subprocess.run(command, cwd=work, capture_output=True, text=True,
                                      timeout=3600)
                logs[mode or 'generate'] = done.stdout
                for key in work.glob('pair-key-*'):
                    key.unlink()
                if done.returncode:
                    raise SystemExit(f'N={n} {mode or "generate"} failed: {done.stdout}\n{done.stderr}')
            joint = json.loads((work / 'results.json').read_text())
            fresh = json.loads((work / 'fresh.json').read_text())
            link = json.loads((work / 'fresh_link.json').read_text())
            summary = {
                'ring_size': n,
                'joint_checks_passed': joint['checks_passed'],
                'fresh_public_checks': fresh['checks_passed'],
                'fresh_link_checks': link['checks_passed'],
                'fresh_claim_artifact_loaded': fresh.get('claim_identity_loaded'),
                'fresh_joint_pass': fresh.get('joint_pass') and link.get('joint_pass'),
                'private_keys_loaded': fresh['private_keys_loaded'],
                'temporary_keys_removed': not list(work.glob('pair-key-*')),
                'secret_free_verifier': True,
                'functional_test_only': True,
                'evidence': {k: v.strip().splitlines()[-1] for k, v in logs.items()},
                'generate_ms': joint.get('star_link_ms'),
                'link_proof_bytes': joint.get('link_proofs_bytes'),
            }
            for name, evidence in CHECKS:
                summary.setdefault('checks', []).append(
                    {'test': name, 'evidence': evidence, 'result': 'PASS'})
            (out / f'functional_n{n}.json').write_text(json.dumps(summary, indent=2) + '\n')
            rows.append(summary)
            print(f"N={n}: joint {summary['joint_checks_passed']}/27, "
                  f"fresh {summary['fresh_public_checks']}/10, link {summary['fresh_link_checks']}/9",
                  flush=True)
    combined = {'schema': 'claris-functional-full-matrix-v1',
                'transcript_profile': manifest['transcript_profile'],
                'functional_test_only': True, 'rows': rows}
    (out / 'functional_all.json').write_text(json.dumps(combined, indent=2) + '\n')
    # With NR=20 fixture reports the check counter is 53 (joint), 23 (fresh) and 22
    # (identity-free link); every check must pass and the harness exits nonzero otherwise.
    for r in rows:
        if not (r['joint_checks_passed'] >= 27 and r['fresh_public_checks'] >= 10
                and r['fresh_link_checks'] >= 9 and r['fresh_joint_pass']):
            raise SystemExit(f'functional failure at N={r["ring_size"]}')


if __name__ == '__main__':
    main()
