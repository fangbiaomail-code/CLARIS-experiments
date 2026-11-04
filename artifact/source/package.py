#!/usr/bin/env python3
"""Create a deterministic source-only zip outside this source directory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
output = args.output.resolve()
if output == root or root in output.parents:
    parser.error('Archive must be outside the source package.')
if output.exists():
    parser.error('Choose a new archive path; existing files are not overwritten.')
subprocess.run([sys.executable,str(root/'verify_sources.py')],check=True)
inventory = json.loads((root/'provenance/source_inventory.json').read_text())
files = [item['file'] for item in inventory['files']]
files += ['provenance/source_inventory.json']
if (root/'provenance/local_validation.json').exists():
    files += ['provenance/local_validation.json']
output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in sorted(files):
        info = zipfile.ZipInfo('CLARIS-source/'+name,date_time=(2026,10,2,0,0,0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o100644 << 16)
        z.writestr(info,(root/name).read_bytes())
print(json.dumps({'archive':str(output),'files':len(files),'bytes':output.stat().st_size,
                  'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2))
