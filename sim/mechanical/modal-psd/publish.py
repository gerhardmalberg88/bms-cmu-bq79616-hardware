#!/usr/bin/env python3
"""Verify and publish existing modal/PSD evidence; never launch a solver.

Copyright (C) 2026 Gerhard Malberg. SPDX-License-Identifier: CERN-OHL-P-2.0
Python standard library only. Native files remain read-only.
"""
import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ('extract', 'mesh', 'convert', 'modal', 'psd', 'postprocess')
PHYSICS = ('material', 'components', 'mounts', 'modal', 'psd')
KIND = 'cmu-modal-psd-publication-v1'


class VerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def checked_file(root, relative, expected):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), f'Artifact escapes its root: {relative}')
    require(path.is_file() and sha(path) == expected, f'Artifact hash mismatch: {relative}')
    return path


def check_board(board, case):
    require(sha(board) == case['publication']['source_sha256'],
            'Saved board differs from the recorded study input; do not republish stale results')


def verify_native(root, board, case):
    check_board(board, case)
    source = case['publication']['source_sha256']
    records, runs, studies = {}, {}, {}

    def record(relative):
        path = root / relative
        records[relative] = sha(path)
        return read(path)

    for backend in ('cpu', 'cuda'):
        study = record(f'{backend}/study.json')
        require(study['source_sha256'] == source, 'Study input hash differs')
        require(study['status'] == 'unconverged', 'This publication expects the recorded provisional study')
        studies[backend] = study
        for mesh in ('coarse', 'fine'):
            key = f'{backend}/{mesh}'
            run = record(f'{key}/run.json')
            require(run['source_sha256'] == source and run['backend'] == backend, f'Run identity differs: {key}')
            require(run['status'] == 'complete', f'Incomplete numerical run: {key}')
            require(all(run['stages'][s]['status'] == 'completed' for s in STAGES), f'Run is not uncached: {key}')
            require(study['variants'][mesh] == run, f'Study/run record disagreement: {key}')
            expected_mesh = dict(case['mesh'], size_mm=case['mesh']['size_mm'] * (1 if mesh == 'coarse' else 2 / 3))
            require(run['case']['mesh'] == expected_mesh, f'Mesh settings differ: {key}')
            require(all(run['case'][k] == case[k] for k in PHYSICS), f'Physical case differs: {key}')
            require(run['case'] == read(root / key / 'case.json'), f'Saved case differs: {key}')
            records[f'{key}/case.json'] = sha(root / key / 'case.json')
            checked_file(root, f'{key}/input/board.kicad_pcb', source)
            records[f'{key}/input/board.kicad_pcb'] = source
            cache = record(f'{key}/cache.json')
            for stage in STAGES:
                require(bool(cache[stage]['artifacts']), f'Empty stage manifest: {key}/{stage}')
                for name, expected in cache[stage]['artifacts'].items():
                    relative = f'{key}/{stage}/{name}'
                    checked_file(root / key / stage, name, expected)
                    records[relative] = expected
            extracted = read(root / key / 'extract/board.json')
            require(extracted['source_sha256'] == source, f'Extraction source differs: {key}')
            require(abs(extracted['thickness_mm'] - case['publication']['saved_thickness_mm']) < 1e-9,
                    'Saved board thickness differs')
            runs[key] = run
        comparison = record(f'{backend}/comparison.json')
        require(comparison == study['comparison'] and not comparison['accepted'], 'Mesh verdict differs')
    backends = {}
    for mesh in ('coarse', 'fine'):
        comparison = record(f'backend-comparison-{mesh}.json')
        for backend in ('cpu', 'cuda'):
            require(comparison['mesh_sha256'] == records[f'{backend}/{mesh}/mesh/board.msh'],
                    'Backend comparison uses a different mesh')
        require(comparison['accepted'], 'Recorded backend agreement failed')
        backends[mesh] = comparison
    return records, runs, studies, backends


def verify_report(output, board, case_path):
    case = read(case_path)
    check_board(board, case)
    provenance = read(output / 'provenance.json')
    require(provenance['kind'] == KIND, 'Unrecognized report directory')
    require(provenance['case_sha256'] == sha(case_path), 'Published case changed')
    require(provenance['source_sha256'] == sha(board), 'Published source changed')
    for name, expected in provenance['published_artifacts_sha256'].items():
        checked_file(output, name, expected)
    return provenance


def generate(root, out, case_path, records, runs, studies, backends):
    case = read(case_path)
    checks = {'status': 'provisional', 'mesh_convergence_pass': False,
              'runs': {}, 'mesh_comparisons': {}, 'backend_comparisons': backends}
    with (out / 'modal-frequencies.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        header = None
        for key in runs:
            with (root / key / 'modal/frequencies.csv').open(newline='') as source:
                reader = csv.reader(source)
                columns = next(reader)
                if header is None:
                    header = columns
                    writer.writerow(['backend', 'mesh'] + columns)
                require(columns == header, 'Modal CSV schemas differ')
                writer.writerows([key.split('/') + row for row in reader])
    units = {'displacement': 'm', 'acceleration': 'm/s^2', 'stress': 'Pa', 'strain': '1'}
    with (out / 'rms-response.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['backend', 'mesh', 'base_axis', 'field', 'maximum_component_rms', 'unit'])
        for key, run in runs.items():
            modal = read(root / key / 'modal/modal-summary.json')
            psd = read(root / key / 'psd/psd-summary.json')
            mesh = read(root / key / 'mesh/mesh-summary.json')
            require(psd['status'] == 'complete', f'PSD incomplete: {key}')
            checks['runs'][key] = {'modal': modal, 'psd': psd, 'mesh': mesh,
                                  'status': run['status'], 'wall_seconds': run['wall_seconds']}
            for field, value in psd['maxima'].items():
                quantity, axis = field.rsplit('_', 1)
                writer.writerow(key.split('/') + ['XYZ'[int(axis)], quantity, value, units[quantity]])
    for backend, study in studies.items():
        checks['mesh_comparisons'][backend] = {k: v for k, v in study['comparison'].items() if k != 'probe_rms'}
        checks['mesh_comparisons'][backend].update(wall_seconds=study['wall_seconds'],
                                                 status=study['status'], under_one_hour=study['under_one_hour'])
    write(out / 'checks.json', checks)
    for name in ('mass-audit.csv', 'board-response.png', 'response-psd.png'):
        shutil.copyfile(root / 'cpu/fine/postprocess' / name, out / name)
    fine = checks['runs']['cpu/fine']
    maxima = fine['psd']['maxima']
    lines = [
        '# BMS CMU modal and PSD results', '',
        '**Completed CPU/GPU runs; provisional results. The componentwise RMS mesh-convergence check failed.**', '',
        'These are the existing 2026-11-02 simulations, republished after input and artifact hash verification; no FEM rerun was performed.', '',
        '| Backend | Uncached total, both meshes | Execution | Mesh acceptance |',
        '|---|---:|---|---|',
    ]
    for backend, study in studies.items():
        lines.append(f"| {backend.upper()} | {study['wall_seconds']/60:.2f} min | All stages completed | Failed RMS check |")
    lines += ['', 'Installation and image builds are excluded. Timings include extraction, both meshes, modal analysis, PSD, reporting and mesh comparison.', '',
              '## Modal results', '', '| Mode | CPU 3 mm mesh (Hz) | CPU 2 mm mesh (Hz) |', '|---|---:|---:|']
    coarse = checks['runs']['cpu/coarse']['modal']['frequencies_hz']
    for i, (a, b) in enumerate(zip(coarse[:10], fine['modal']['frequencies_hz'][:10]), 1):
        lines.append(f'| {i} | {a:.2f} | {b:.2f} |')
    mesh_change = studies['cpu']['comparison']['maximum_frequency_change'] * 100
    rms_change = studies['cpu']['comparison']['maximum_rms_change'] * 100
    lines += ['', f'First-ten-frequency mesh change: **{mesh_change:.3f}%**, below 2%. Each run retains 16 modes through at least 6608 Hz; eigenpair residuals are below 1e-6 and mass-orthogonality errors below 1e-6.', '',
              '## PSD response', '',
              'Fine CPU mesh, 2% damping. Values are spatial maxima of individual response-component RMS, not time-domain peaks; different columns may attain their maxima at different locations.', '',
              '| Independent base axis | Relative displacement (µm) | Absolute acceleration (g RMS) | Stress component (MPa RMS) | Strain component (µstrain RMS) |',
              '|---|---:|---:|---:|---:|']
    for i, axis in enumerate('XYZ'):
        lines.append(f"| {axis} | {maxima[f'displacement_{i}']*1e6:.5g} | {maxima[f'acceleration_{i}']/9.80665:.5g} | {maxima[f'stress_{i}']/1e6:.5g} | {maxima[f'strain_{i}']*1e6:.5g} |")
    lines += ['', f'**RMS mesh convergence failed:** the maximum gated probe change is {rms_change:.2f}% (limit 5%). This includes very small cross-axis displacement components; weak recovered surface shear is also mesh-sensitive. The comparison uses a floor of 1% of the peak reference component within each sampled field. Small magnitude does not waive the gate.', '',
              'CPU/GPU agreement passed on both identical meshes (frequency tolerance 0.1%, RMS tolerance 1%). PSD integration and modal-truncation checks passed separately; neither backend agreement nor accurate eigenpairs establishes mesh or physical-model convergence. [Numerical checks](checks.json) include effective modal masses, damping sensitivities and per-field errors.', '',
              '![Fine CPU board response](board-response.png)', '',
              'The board plot shows the root-sum-square of acceleration-component RMS for Z-base excitation, in g.', '',
              '![Fine CPU response PSD](response-psd.png)', '',
              'The PSD plot is the maximum across sampled probe DOFs at each frequency; it is an envelope, not the spectrum of one fixed response location.', '',
              '## Model and limits', '',
              'The saved 1.708 mm PCB is homogenized with E=24.37 GPa, ν=0.165 and density=1944 kg/m³. These are generic effective properties, not measured board properties. Top/bottom 7 mm outer-diameter annular contacts at H1–H4 are assumed rigid. Quadratic solids use two thickness layers and 3/2 mm in-plane meshes (79,815/133,305 displacement unknowns).', '',
              '157 fitted component masses are distributed over attachment regions without package stiffness or mass offsets; DNP parts are excluded. Four connector masses use manufacturer data; 153 use dimensional/material estimates with ±50% screening uncertainty. The assembled board-plus-component mass is approximately 28.484 g. See the [mass audit](mass-audit.csv).', '',
              'Excitation is synthetic, one-sided flat 1/1980 g²/Hz over 20–2000 Hz: 1 g RMS separately in X, Y and Z. Damping is 2%, with 1% and 5% sensitivity calculations. Modal cross terms, support-node mass coupling, residual flexibility and the direct base-motion term in absolute acceleration are included. Low retained in-plane effective mass is reported explicitly; the static residual contribution is not a substitute for dynamic in-plane modes.', '',
              'Cables, enclosure flexibility, package stiffness, nonlinear contacts and solder joints are omitted. Stress is component RMS, not RMS von Mises. No fatigue-life, component-qualification or hardware-acceptance claim follows from these provisional fields.', '',
              '## Files and reproduction', '',
              '- [Case and commands](../README.md) · [explicit case](../case.json)',
              '- [Modal frequencies, participation and residuals](modal-frequencies.csv) · [RMS response, SI units](rms-response.csv)',
              '- [Numerical checks](checks.json) · [source, tool and artifact provenance](provenance.json)', '',
              'Reading this report needs no native archive or lab checkout. Raw meshes, matrices, mode fields and logs remain outside tracked content. Hardware inputs and this publication retain CERN-OHL-P-2.0; upstream tools retain their own licenses.', '']
    (out / 'README.md').write_text('\n'.join(lines))
    provenance = {'kind': KIND, 'status': 'provisional', 'published_date': '2026-11-03',
                  'simulation_date': '2026-11-02', 'source_board': case['board'],
                  'source_board_path_base': 'case.json directory',
                  'source_sha256': case['publication']['source_sha256'], 'case_sha256': sha(case_path),
                  'publisher_sha256': sha(Path(__file__)), 'workflow_identity': case['publication'],
                  'native_artifacts_sha256': records,
                  'runs': {key: {'images': run['images'], 'started_utc': datetime.fromtimestamp(run['started_unix'], timezone.utc).isoformat(),
                                 'wall_seconds': run['wall_seconds'], 'stages': run['stages']} for key, run in runs.items()},
                  'native_path_policy': 'Manifest paths are relative to the explicitly supplied native-results root; no host-specific paths are required.',
                  'published_artifacts_sha256': {p.name: sha(p) for p in sorted(out.iterdir())}}
    write(out / 'provenance.json', provenance)


def publish(native_root, case_path, output, board=None):
    case = read(case_path)
    board = Path(board) if board else (case_path.parent / case['board']).resolve()
    require(not output.resolve().is_relative_to(native_root.resolve()), 'Report must be outside native inputs')
    records, runs, studies, backends = verify_native(native_root, board, case)
    if output.exists():
        old = verify_report(output, board, case_path)
        require({p.name for p in output.iterdir()} == set(old['published_artifacts_sha256']) | {'provenance.json'},
                'Report contains unowned files; choose another output directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.publish-', dir=output.parent) as temporary:
        staging = Path(temporary) / 'report'
        staging.mkdir()
        generate(native_root, staging, case_path, records, runs, studies, backends)
        require(sum(p.stat().st_size for p in staging.iterdir()) < 5 * 1024**2, 'Compact report exceeds 5 MiB')
        check_board(board, case)
        # Recheck after copying: a changed native artifact must never be published.
        for name, expected in records.items():
            checked_file(native_root, name, expected)
        backup = Path(temporary) / 'previous'
        if output.exists():
            output.rename(backup)
        try:
            staging.rename(output)
        except BaseException:
            if backup.exists():
                backup.rename(output)
            raise
    verify_report(output, board, case_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-root', type=Path, help='Existing root containing cpu/, cuda/ and backend comparisons')
    parser.add_argument('--case', type=Path, default=HERE / 'case.json')
    parser.add_argument('--output', type=Path, default=HERE / 'report')
    parser.add_argument('--verify-report', action='store_true', help='Verify compact report and current input without native data')
    args = parser.parse_args()
    try:
        if args.verify_report:
            verify_report(args.output, (args.case.parent / read(args.case)['board']).resolve(), args.case)
        else:
            require(args.native_root is not None, 'Supply --native-root to publish existing evidence')
            publish(args.native_root, args.case, args.output)
        print(f'Verified provisional report: {args.output}')
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f'Publication refused: {error}\n')


if __name__ == '__main__':
    main()
