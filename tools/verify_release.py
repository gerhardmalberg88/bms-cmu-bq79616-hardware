#!/usr/bin/env python3
"""Verify package checksums, ZIP members and required independent readback evidence.

Copyright (C) 2021-2026 Gerhard Malberg; SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(path):
    path = Path(path).resolve()
    checks = {}
    for line in (path/'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        target = (path/name).resolve()
        if not target.is_relative_to(path) or not target.is_file():
            raise ValueError(f'Invalid/missing package file: {name}')
        if sha(target.read_bytes()) != expected:
            raise ValueError(f'Checksum mismatch: {name}')
        checks[name] = expected
    actual = {p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file()}
    if actual != set(checks) | {'SHA256SUMS', 'complete-package.zip', 'complete-package.zip.sha256'}:
        raise ValueError('Package contains missing or unlisted files')
    expected, name = (path/'complete-package.zip.sha256').read_text().strip().split('  ', 1)
    if name != 'complete-package.zip' or sha((path/name).read_bytes()) != expected:
        raise ValueError('Complete-package ZIP checksum mismatch')
    with zipfile.ZipFile(path/name) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(checks) | {'SHA256SUMS'}:
            raise ValueError('Complete-package ZIP member mismatch')
        for member in archive.namelist():
            if archive.read(member) != (path/member).read_bytes():
                raise ValueError(f'Complete-package ZIP bytes differ: {member}')
    with zipfile.ZipFile(path/'fabrication.zip') as archive:
        expected_members = {p.relative_to(path/'fabrication').as_posix() for p in (path/'fabrication').rglob('*') if p.is_file()}
        if set(archive.namelist()) != expected_members or archive.testzip() is not None:
            raise ValueError('Fabrication ZIP member mismatch')
        for member in archive.namelist():
            if archive.read(member) != (path/'fabrication'/member).read_bytes():
                raise ValueError(f'Fabrication ZIP bytes differ: {member}')
    with zipfile.ZipFile(path/'verification/source-snapshot.zip') as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupt source snapshot')
        hashes = json.loads((path/'verification/source-sha256.json').read_text())
        for name, expected in hashes.items():
            if sha(archive.read(name)) != expected:
                raise ValueError(f'Source snapshot mismatch: {name}')
    readback = json.loads((path/'verification/export-readback.json').read_text())
    for key in ('drills_match_source', 'step_population_matches_fitted_BOM', 'step_stl_bounds_match',
                'ipc_pin_net_partition_matches', 'source_unchanged'):
        if readback.get(key) is not True:
            raise ValueError(f'Failed independent readback: {key}')
    geometry = json.loads((path/'verification/step-geometry.json').read_text())
    if len(geometry) != 2 or not all(g['valid'] and g['solids'] > 0 for g in geometry.values()):
        raise ValueError('Invalid STEP readback')
    print(f'Verified {len(checks)} file checksums, both delivery ZIPs, source snapshot and readback evidence: {path.name}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    verify(parser.parse_args().release)
