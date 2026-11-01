"""Historical LF acceptance is narrower than ordinary source modification."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"sim"))
from source_normalization import verify_sources


class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-q')
        (self.root/'board').write_bytes(b'alpha\r\nbeta\r\n')
        self.git('add', 'board')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
        revision = self.git('rev-parse', 'HEAD').strip()
        self.old = hashlib.sha256((self.root/'board').read_bytes()).hexdigest()
        (self.root/'board').write_bytes(b'alpha\nbeta\n')
        new = hashlib.sha256((self.root/'board').read_bytes()).hexdigest()
        self.manifest = self.root/'manifest.json'
        self.data = dict(schema_version=1, transformation='CRLF-to-LF', git_revision=revision,
                         files={'board': dict(original_sha256=self.old, normalized_sha256=new)})
        self.save()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True, stderr=subprocess.PIPE)

    def save(self):
        self.manifest.write_text(json.dumps(self.data))

    def test_explicit_migration(self):
        result = verify_sources(self.root, {'board': self.old}, self.manifest)
        self.assertEqual(result['current_source_hashes']['board'], self.data['files']['board']['normalized_sha256'])
        with self.assertRaises(ValueError): verify_sources(self.root, {'board': self.old})

    def test_reject_content_change(self):
        (self.root/'board').write_bytes(b'alpha\ngamma\n')
        self.data['files']['board']['normalized_sha256'] = hashlib.sha256((self.root/'board').read_bytes()).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError, 'exact CRLF'): verify_sources(self.root, {'board': self.old}, self.manifest)

    def test_missing_history(self):
        self.data['git_revision'] = '0'*40; self.save()
        with self.assertRaisesRegex(ValueError, 'Historical Git object unavailable'): verify_sources(self.root, {'board': self.old}, self.manifest)

    def test_reject_path_escape(self):
        self.data['files']['../outside'] = self.data['files'].pop('board'); self.save()
        with self.assertRaisesRegex(ValueError, 'Invalid normalization path'): verify_sources(self.root, {}, self.manifest)

    def test_exact_fresh_source(self):
        verify_sources(self.root, {'board': self.data['files']['board']['normalized_sha256']})
