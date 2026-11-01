"""Strict historical source verification for an explicitly authorized LF migration.

Copyright (C) 2026 Gerhard Malberg; SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify_sources(root, sources, manifest=None):
    root = Path(root).resolve()
    evidence = None
    if manifest is not None:
        raw = Path(manifest).read_bytes()
        data = json.loads(raw)
        if data.get('schema_version') != 1 or data.get('transformation') != 'CRLF-to-LF':
            raise ValueError('Unsupported source-normalization manifest')
        revision = data.get('git_revision', '')
        if not re.fullmatch('[0-9a-f]{40,64}', revision):
            raise ValueError('Normalization requires an exact historical Git revision')
        verified = {}
        for name, entry in data['files'].items():
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or str(path) != name:
                raise ValueError(f'Invalid normalization path: {name}')
            current_path = (root / name).resolve()
            if not current_path.is_relative_to(root):
                raise ValueError(f'Normalization path escapes repository: {name}')
            try:
                original = subprocess.check_output(['git', 'show', f'{revision}:{name}'], cwd=root, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError as exc:
                raise ValueError(f'Historical Git object unavailable for normalization: {revision}:{name}') from exc
            normalized = original.replace(b'\r\n', b'\n')
            if (sha(original) != entry['original_sha256'] or sha(normalized) != entry['normalized_sha256']
                    or current_path.read_bytes() != normalized or original == normalized):
                raise ValueError(f'Not an exact CRLF-to-LF source migration: {name}')
            verified[name] = entry
        evidence = {'manifest_sha256': sha(raw), 'git_revision': revision,
                    'transformation': 'CRLF-to-LF', 'verified_files': verified}
    current = {}
    for name, expected in sources.items():
        actual = sha((root / name).read_bytes())
        if actual != expected:
            entry = evidence['verified_files'].get(name) if evidence else None
            if not entry or entry['original_sha256'] != expected or entry['normalized_sha256'] != actual:
                raise ValueError(f'Design input changed: {name}; exact source hash or verified normalization required')
        current[name] = actual
    return {'current_source_hashes': current, 'source_normalization': evidence}
