#!/usr/bin/env python3
"""Check shipped files against the source inventory. No network is used."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = root/'provenance/source_inventory.json'
if not manifest.exists():
    raise SystemExit('Missing source_inventory.json')
entries = json.loads(manifest.read_text())['files']
for item in entries:
    p = root/item['file']
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != item['sha256']:
        raise SystemExit('Integrity mismatch: '+item['file'])
print(f'Source integrity PASS: {len(entries)} files')
