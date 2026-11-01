#!/usr/bin/env python3
"""Run only the COMH/COML PCB cases, with a shared wall-clock deadline."""
# SPDX-License-Identifier: CERN-OHL-P-2.0
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / 'results/em'
CASES = ['isospi-2d/comh.yaml', 'isospi-2d/coml.yaml',
         'isospi-2d/comh-filter.yaml', 'isospi-2d/coml-filter.yaml',
         'isospi-3d/comh.yaml', 'isospi-3d/coml.yaml']


def container_ids(engine):
    p = subprocess.run([engine, 'ps', '-q'], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr.strip())
    return set(p.stdout.split())


def stop_owned(engine, before, output):
    # A timeout may leave a container behind its client. Only stop new
    # containers mounted on this exact job's output, preserving other work.
    for cid in container_ids(engine) - before:
        p = subprocess.run([engine, 'inspect', cid], capture_output=True, text=True)
        if not p.returncode and any(
                Path(m['Source']).resolve() == output.resolve()
                and m['Destination'] == '/work'
                for m in json.loads(p.stdout)[0].get('Mounts', [])):
            subprocess.run([engine, 'stop', '--time', '5', cid], check=True)


def run(args):
    cli = args.pcb_em or shutil.which('pcb-em')
    if not cli:
        raise SystemExit('Install pcb-em, or pass --pcb-em /path/to/pcb-em')
    cli = str(Path(cli).resolve())
    started = time.time()
    deadline = min(started + args.time_budget_minutes * 60,
                   args.deadline_unix or float('inf'))
    RESULTS.mkdir(parents=True, exist_ok=True)
    session = RESULTS / ('batch-' + time.strftime('%Y%m%d-%H%M%S'))
    session.mkdir()
    state = {'started_unix': started, 'deadline_unix': deadline,
             'backend': 'cpu', 'jobs': [], 'status': 'running'}

    def save():
        state['elapsed_seconds'] = time.time() - started
        (session / 'progress.json').write_text(json.dumps(state, indent=2) + '\n')

    engine = os.environ.get('PCB_EM_ENGINE', 'podman')
    try:
        for relative in CASES:
            remaining = deadline - time.time() - 120
            if remaining <= 0:
                state['status'] = 'budget-exhausted'
                break
            case = HERE / relative
            config = json.loads(case.read_text())
            output = (case.parent / config['output']).resolve()
            record = {'case': relative, 'started_unix': time.time(), 'status': 'running'}
            state['jobs'].append(record)
            save()
            print('Running', relative, flush=True)
            before = container_ids(engine)
            p = None
            try:
                with (session / (case.stem + '-' + case.parent.name + '.log')).open('w') as log:
                    job_deadline = time.monotonic() + min(remaining, args.per_case_minutes * 60)
                    for stage in ['mesh', 'all']:
                        if stage == 'all':
                            geometry = json.loads((output/'mesh/geometry.json').read_text())
                            record['mesh_nodes'] = geometry['mesh_nodes']
                            if geometry['mesh_nodes'] > args.max_mesh_nodes:
                                record.update(status='mesh-too-large', node_limit=args.max_mesh_nodes)
                                break
                        p = subprocess.Popen([cli, 'run', str(case), '--backend', 'cpu',
                                              '--mpi-ranks', '2', '--threads-per-rank', '1', '--stage', stage],
                                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                        try:
                            code = p.wait(timeout=max(.01,job_deadline-time.monotonic()))
                        except (subprocess.TimeoutExpired, KeyboardInterrupt):
                            stop_owned(engine, before, output)
                            if p.poll() is None:
                                os.killpg(p.pid, signal.SIGINT)
                            try:
                                p.wait(timeout=10)
                            except subprocess.TimeoutExpired:
                                os.killpg(p.pid, signal.SIGKILL)
                                p.wait()
                            raise
                        if code != 0: break
                if record['status'] != 'mesh-too-large':
                    record.update(status='complete' if code == 0 else 'failed', returncode=code)
            except subprocess.TimeoutExpired:
                record['status'] = 'timeout'
            except KeyboardInterrupt:
                record['status'] = 'interrupted'
                raise
            finally:
                record['elapsed_seconds'] = time.time() - record['started_unix']
                save()
        else:
            state['status'] = 'complete' if all(j['status'] == 'complete' for j in state['jobs']) else 'incomplete'
    except KeyboardInterrupt:
        state['status'] = 'interrupted'
        raise
    finally:
        save()
        print('Progress:', session / 'progress.json', flush=True)
    return 0 if state['status'] == 'complete' else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb-em', help='Installed pcb-em launcher; no sibling checkout required')
    parser.add_argument('--time-budget-minutes', type=float, default=180)
    parser.add_argument('--per-case-minutes', type=float, default=20)
    parser.add_argument('--max-mesh-nodes', type=int, default=70000, help='Refuse oversized meshes before launching the solver')
    parser.add_argument('--deadline-unix', type=float, help='Optional earlier absolute deadline')
    args = parser.parse_args()
    if args.time_budget_minutes <= 0 or args.per_case_minutes <= 0 or args.max_mesh_nodes <= 0:
        parser.error('Time budgets must be positive')
    raise SystemExit(run(args))
