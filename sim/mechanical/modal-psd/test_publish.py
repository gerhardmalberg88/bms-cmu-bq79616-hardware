"""Regression checks for publication refusal and retained numerical status."""
import csv
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mechanical_publish', HERE / 'publish.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublicationTests(unittest.TestCase):
    def test_changed_board_refuses_publication_without_touching_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            board = root / 'changed.kicad_pcb'
            board.write_text('a different saved board')
            output = root / 'report'
            output.mkdir()
            sentinel = output / 'keep.txt'
            sentinel.write_text('existing report')
            with self.assertRaisesRegex(publisher.VerificationError, 'Saved board differs'):
                publisher.publish(root / 'native', HERE / 'case.json', output, board=board)
            self.assertEqual(sentinel.read_text(), 'existing report')

    def test_corrupted_native_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = publisher.read(HERE / 'case.json')
            native = root / 'native'
            run_root = native / 'cpu/coarse'
            (run_root / 'input').mkdir(parents=True)
            (run_root / 'extract').mkdir()
            shutil.copyfile((HERE / case['board']).resolve(), run_root / 'input/board.kicad_pcb')
            run = {'case': case, 'source_sha256': case['publication']['source_sha256'],
                   'backend': 'cpu', 'status': 'complete',
                   'stages': {s: {'status': 'completed'} for s in publisher.STAGES}}
            publisher.write(run_root / 'run.json', run)
            publisher.write(run_root / 'case.json', case)
            publisher.write(native / 'cpu/study.json', {
                'source_sha256': run['source_sha256'], 'status': 'unconverged',
                'variants': {'coarse': run}})
            artifact = run_root / 'extract/board.json'
            artifact.write_bytes(b'recorded extraction')
            publisher.write(run_root / 'cache.json', {'extract': {'artifacts': {'board.json': publisher.sha(artifact)}}})
            artifact.write_bytes(b'corrupted extraction')
            output = root / 'report'
            output.mkdir()
            sentinel = output / 'keep.txt'
            sentinel.write_text('existing report')
            with self.assertRaisesRegex(publisher.VerificationError, 'Artifact hash mismatch'):
                publisher.publish(native, HERE / 'case.json', output)
            self.assertEqual(sentinel.read_text(), 'existing report')

    def test_artifact_cannot_escape_manifest_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'stage').mkdir()
            outside = root / 'outside'
            outside.write_text('not a stage artifact')
            with self.assertRaisesRegex(publisher.VerificationError, 'escapes'):
                publisher.checked_file(root / 'stage', '../outside', publisher.sha(outside))

    def test_compact_report_verifies_and_retains_failure(self):
        case = publisher.read(HERE / 'case.json')
        board = (HERE / case['board']).resolve()
        provenance = publisher.verify_report(HERE / 'report', board, HERE / 'case.json')
        checks = publisher.read(HERE / 'report/checks.json')
        self.assertEqual(provenance['status'], 'provisional')
        self.assertFalse(checks['mesh_convergence_pass'])
        for result in checks['mesh_comparisons'].values():
            self.assertFalse(result['accepted'])
            self.assertLess(result['maximum_frequency_change'], .02)
            self.assertGreater(result['maximum_rms_change'], .05)
        with (HERE / 'report/rms-response.csv').open() as stream:
            for row in csv.DictReader(stream):
                key = f"{row['backend']}/{row['mesh']}"
                field = row['field'] + '_' + str('XYZ'.index(row['base_axis']))
                self.assertEqual(float(row['maximum_component_rms']), checks['runs'][key]['psd']['maxima'][field])
        with (HERE / 'report/modal-frequencies.csv').open() as stream:
            for row in csv.DictReader(stream):
                key = f"{row['backend']}/{row['mesh']}"
                mode = int(float(row['mode'])) - 1
                self.assertEqual(float(row['frequency_hz']), checks['runs'][key]['modal']['frequencies_hz'][mode])

    def test_modified_published_csv_is_rejected(self):
        case = publisher.read(HERE / 'case.json')
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'report'
            shutil.copytree(HERE / 'report', report)
            (report / 'rms-response.csv').write_text('modified\n')
            with self.assertRaisesRegex(publisher.VerificationError, 'Artifact hash mismatch'):
                publisher.verify_report(report, (HERE / case['board']).resolve(), HERE / 'case.json')


if __name__ == '__main__':
    unittest.main()
