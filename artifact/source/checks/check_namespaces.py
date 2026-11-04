#!/usr/bin/env python3
"""Compile/run hash equality probes and test family/parameter separation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--result', type=Path)
args = parser.parse_args()
build = args.build.resolve()
manifest = json.loads((build/'build_manifest.json').read_text())
if manifest['transcript_profile'] == 'legacy':
    raise SystemExit('This check requires the default namespaced build.')
outputs = {}
for target in manifest['targets']:
    folder = build/target['target']
    command = target['commands'][-1]
    cc = command[0]
    exe = folder/'namespace_probe'
    objects = sorted(str(p) for p in folder.glob('*.o'))
    subprocess.run([cc,*manifest['flags'],'-I',str(folder),
                    str(Path(__file__).with_name('namespace_probe.c')), *objects,
                    '-o',str(exe)], check=True)
    text = subprocess.check_output([str(exe)], text=True)
    assert text.endswith('SCALAR_X4_PASS\n')
    outputs[folder.name] = dict(line.split() for line in text.splitlines()[:-1])
expected = hashlib.shake_256(b'public-wrapper-probe').hexdigest(32)
assert all(row['wrapper'] == expected for row in outputs.values())
for stage in range(1,10):
    values = [row[f'stage_{stage}'] for row in outputs.values()]
    assert len(set(values)) == len(values)
result = {'functional_check_only':True,'all_passed':True,
          'scalar_vector_stage_lane_checks':len(outputs)*9*4,
          'proof_kind_and_parameter_outputs_distinct':True,
          'public_wrapper_matches_python_shake256':True,'digests':outputs}
if args.result:
    args.result.parent.mkdir(parents=True,exist_ok=True)
    args.result.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
