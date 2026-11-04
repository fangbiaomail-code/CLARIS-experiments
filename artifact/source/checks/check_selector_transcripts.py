#!/usr/bin/env python3
"""Actual low-level Q proofs isolating selector checks on duplicated rings."""
import argparse
import json
from pathlib import Path
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build',type=Path,required=True)
parser.add_argument('--legacy-build',type=Path)
parser.add_argument('--result',type=Path)
args=parser.parse_args()
result={'scope':'low-level duplicated-ring selector diagnostics, not an end-to-end forgery',
        'new_profile':[],'legacy_diagnostic':[]}
for legacy,build in [(False,args.build),(True,args.legacy_build)]:
    if build is None:continue
    build=build.resolve();manifest=json.loads((build/'build_manifest.json').read_text())
    expected='CLARIS-v1-namespaced' if legacy else 'CLARIS-Q-v2-G-v1'
    if manifest['transcript_profile']!=expected:raise SystemExit('Unexpected build profile')
    for target in manifest['targets']:
        if not target['target'].startswith('ring_n'):continue
        if legacy and target['target']!='ring_n64':continue
        folder=build/target['target'];exe=folder/'check_selector_transcripts'
        source=Path(__file__).with_suffix('.c')
        command=[target['commands'][0][0],*manifest['flags'],'-I',str(folder),str(source),
                 *sorted(str(p) for p in folder.glob('*.o')),'-o',str(exe)]
        subprocess.run(command,check=True)
        output=subprocess.check_output([str(exe)]+(['legacy'] if legacy else []),text=True,timeout=300)
        row=json.loads(output);assert row['checks_passed']==4
        result['legacy_diagnostic' if legacy else 'new_profile'].append(row)
        print(f'PASS {target["target"]} {expected}',flush=True)
if args.result:
    args.result.parent.mkdir(parents=True,exist_ok=True)
    args.result.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
