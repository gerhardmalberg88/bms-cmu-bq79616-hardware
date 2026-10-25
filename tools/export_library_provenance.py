#!/usr/bin/env python3
"""Export the imported-asset provenance subset after comparing local copies.

Requires the shared kicad-libraries checkout; no Git commit is assumed.
Copyright (C) 2021-2026 Gerhard Malberg
SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def generate(upstream):
    spec = importlib.util.spec_from_file_location(
        'shared_symbol_builder', upstream / 'tools/build_symbol_library.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with (upstream / 'ASSET_PROVENANCE.csv').open(encoding='utf-8-sig') as h:
        reader = csv.DictReader(h)
        columns = reader.fieldnames
        provenance = {r['asset_path']: r for r in reader}
    library = ROOT / 'design/kicad-libraries'
    manifest = (library / 'README.md').read_text(encoding='utf-8')
    matches = re.findall(r'^\| `([^`]+)` \| `([^`]+)` \| `([a-f0-9]+)` \|$', manifest, re.M)
    assert matches, 'No manifest rows found'
    buffer = io.StringIO(newline='')
    headers = ['project_asset', 'symbol', 'project_sha256', 'upstream_sha256',
               'comparison', 'manifest_blob_matches'] + columns
    writer = csv.DictWriter(buffer, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    for local_name, upstream_name, blob in matches:
        match = re.fullmatch(r'(.+) \(([^)]+)\)', local_name)
        local_path, symbol = match.groups() if match else (local_name, '')
        local_bytes = (library / local_path).read_bytes()
        upstream_bytes = (upstream / upstream_name).read_bytes()
        if symbol:
            local_block = module.blocks_in(local_bytes.decode('utf-8'))[symbol]
            source_block = module.blocks_in(upstream_bytes.decode('utf-8'))[symbol]
            assert local_block == source_block, local_name
            comparison = 'matching symbol block'
        else:
            assert local_bytes == upstream_bytes, local_name
            comparison = 'byte-identical file'
        git_blob = hashlib.sha1(b'blob ' + str(len(upstream_bytes)).encode() + b'\0' + upstream_bytes).hexdigest()
        assert git_blob.startswith(blob), 'Manifest content ID mismatch: ' + upstream_name
        row = provenance[upstream_name]
        assert row['redistribution_status'] == 'cleared_original', upstream_name
        assert row['upstream_license'] == 'CERN-OHL-P-2.0', upstream_name
        writer.writerow(dict(project_asset='design/kicad-libraries/' + local_path,
                             symbol=symbol, project_sha256=hashlib.sha256(local_bytes).hexdigest(),
                             upstream_sha256=hashlib.sha256(upstream_bytes).hexdigest(),
                             comparison=comparison, manifest_blob_matches='yes', **row))
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = generate(args.upstream.resolve())
    output = ROOT / 'docs/generated/library-provenance.csv'
    if args.check:
        assert output.read_text(encoding='utf-8') == result, 'Provenance export is stale'
        print('Imported library provenance and content hashes match.')
    else:
        output.write_text(result, encoding='utf-8', newline='')
        print('Wrote', output)


if __name__ == '__main__':
    main()
