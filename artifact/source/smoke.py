#!/usr/bin/env python3
"""Fresh-key functional checks and separate public-verifier processes."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--ring-size', type=int, choices=[64,1024], default=64)
parser.add_argument('--result', type=Path)
args = parser.parse_args()
root = args.build.resolve()
cli = root/'ordinary/pair_cli'
exe = root/f'ring_n{args.ring_size}/joint_pair'
info = json.loads(subprocess.check_output([str(cli), 'info'], text=True))
assert info['blocks'] == 8 and info['proof_bytes'] == 49208 and not info['ring_or_used']
with tempfile.TemporaryDirectory(prefix='claris-smoke-') as temporary:
    work = Path(temporary)
    for mode in [None, 'verify', 'verify-link']:
        command = [str(exe), str(cli)] + ([mode] if mode else [])
        try:
            done = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=600)
            if done.returncode:
                raise RuntimeError(f'{mode or "generate"} failed ({done.returncode}):\n{done.stdout}\n{done.stderr}')
        finally:
            for key in work.glob('pair-key-*'):
                key.unlink()
        print(f'PASS: {mode or "generate and adversarial checks"}', flush=True)
    result = {'schema':'claris-smoke-v1', 'new_keys_generated':True,
              'joint':json.loads((work/'results.json').read_text()),
              'fresh_public_verifier':json.loads((work/'fresh.json').read_text()),
              'fresh_link_only_verifier':json.loads((work/'fresh_link.json').read_text()),
              'temporary_keys_removed':not list(work.glob('pair-key-*')),
              'transcript_profile':json.loads((root/'build_manifest.json').read_text())['transcript_profile'],
              'functional_test_only':True}
    # Replace the historical harness field by the two changes it now distinguishes.
    result['joint'].pop('ring_report_circuit_changed', None)
    result['joint']['ring_report_AES_constraint_algorithm_changed'] = False
    result['joint']['ring_report_OR_batching_changed'] = result['transcript_profile'] == 'CLARIS-Q-v2-G-v1'
if args.result:
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
