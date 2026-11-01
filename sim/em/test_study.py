"""Deadline and container ownership checks without launching numerical jobs."""
# SPDX-License-Identifier: CERN-OHL-P-2.0
import argparse
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('study', Path(__file__).with_name('run-study.py'))
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_expired_deadline_preserves_existing_results(tmp_path, monkeypatch):
    marker = tmp_path/'existing.txt';marker.write_text('preserve')
    monkeypatch.setattr(study, 'RESULTS', tmp_path)
    args = argparse.Namespace(pcb_em='/unused/pcb-em', time_budget_minutes=180,
                              per_case_minutes=20, deadline_unix=1)
    assert study.run(args) == 1
    progress = json.loads(next(tmp_path.glob('batch-*/progress.json')).read_text())
    assert progress['status'] == 'budget-exhausted' and not progress['jobs']
    assert marker.read_text() == 'preserve'


def test_cleanup_stops_only_new_container_on_exact_output(tmp_path, monkeypatch):
    monkeypatch.setattr(study, 'container_ids', lambda engine: {'old','owned','unrelated'})
    calls = []
    def command(args, **kwargs):
        calls.append(args)
        if args[1] == 'inspect':
            mount = str(tmp_path) if args[2] == 'owned' else str(tmp_path/'other')
            return SimpleNamespace(returncode=0, stdout=json.dumps([{'Mounts':[{'Source':mount,'Destination':'/work'}]}]))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(study.subprocess, 'run', command)
    study.stop_owned('podman', {'old'}, tmp_path)
    assert [c for c in calls if c[1] == 'stop'] == [['podman','stop','--time','5','owned']]


def test_only_comh_coml_cases_are_scheduled():
    assert len(study.CASES) == 6
    assert all(Path(p).stem.startswith(('comh','coml')) for p in study.CASES)


def test_oversized_mesh_never_launches_solver(tmp_path, monkeypatch):
    monkeypatch.setattr(study,'HERE',tmp_path)
    monkeypatch.setattr(study,'RESULTS',tmp_path/'results')
    monkeypatch.setattr(study,'CASES',['case.json'])
    monkeypatch.setattr(study,'container_ids',lambda engine:set())
    (tmp_path/'case.json').write_text(json.dumps({'output':'results/oversized'}))
    geometry=tmp_path/'results/oversized/mesh/geometry.json'
    geometry.parent.mkdir(parents=True)
    geometry.write_text(json.dumps({'mesh_nodes':70001}))
    stages=[]
    def start(command,**kwargs):
        stages.append(command[-1])
        return SimpleNamespace(wait=lambda timeout:0)
    monkeypatch.setattr(study.subprocess,'Popen',start)
    args=argparse.Namespace(pcb_em='/unused/pcb-em',time_budget_minutes=180,
                            per_case_minutes=20,deadline_unix=None,max_mesh_nodes=70000)
    assert study.run(args)==1
    assert stages==['mesh']
    p=json.loads(next((tmp_path/'results').glob('batch-*/progress.json')).read_text())
    assert p['jobs'][0]['status']=='mesh-too-large'
