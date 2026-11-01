import argparse
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linux_tools import executable, add_tool_arguments, freecad_command

class ToolTests(unittest.TestCase):
    def test_path_and_override(self):
        self.assertTrue(Path(executable(None, 'python3')).is_absolute())
        self.assertEqual(executable(sys.executable, 'missing-default'), str(Path(sys.executable).resolve()))
        with self.assertRaisesRegex(SystemExit, 'Required executable'): executable('/no/such/tool', 'python3')

    def test_exclusive_freecad_options(self):
        parser=argparse.ArgumentParser(); add_tool_arguments(parser)
        with self.assertRaises(SystemExit): parser.parse_args(['--freecad-python','python3','--freecad-appimage','file'])

    def test_csv_lf(self):
        from manufacturing_release import csv_write
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'out.csv'; csv_write(path,['name'],[['value']])
            self.assertNotIn(b'\r\n',path.read_bytes())

    def test_appimage_cache_uses_content_hash(self):
        import hashlib
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); app=root/'freecad.AppImage'
            app.write_text('#!/bin/sh\nmkdir -p squashfs-root\nprintf "#!/bin/sh\\nexit 0\\n" > squashfs-root/AppRun\nchmod +x squashfs-root/AppRun\n')
            app.chmod(0o755)
            args=argparse.Namespace(freecad_python=None,freecad_appimage=app)
            command,_=freecad_command(args,root/'cache')
            self.assertIn(hashlib.sha256(app.read_bytes()).hexdigest(),command[0])
            marker=Path(command[0]).parents[1]/'extracted'; stamp=marker.stat().st_mtime_ns
            self.assertEqual(freecad_command(args,root/'cache')[0],command)
            self.assertEqual(marker.stat().st_mtime_ns,stamp)
