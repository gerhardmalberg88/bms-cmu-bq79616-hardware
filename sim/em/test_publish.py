"""Resolve renamed inputs while retaining original simulation evidence."""
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('publish', Path(__file__).with_name('publish.py'))
publish = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish)


def test_renamed_case_resolves_to_json_without_rewriting_record(tmp_path, monkeypatch):
    monkeypatch.setattr(publish, 'ROOT', tmp_path)
    current = tmp_path/'case.json'
    current.write_text('{"name":"saved physical inputs"}')
    historical = tmp_path/'case.yaml'
    assert publish.current_case_path(historical) == current
    assert not historical.exists()
    assert json.loads(current.read_text())['name'] == 'saved physical inputs'


def test_missing_cases_and_outside_paths_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(publish, 'ROOT', tmp_path)
    (tmp_path/'case.json').write_text('{}')
    for missing in ['missing.yaml', 'missing.json', 'case.txt']:
        with pytest.raises(ValueError, match='Missing case'):
            publish.current_case_path(tmp_path/missing)
    with pytest.raises(ValueError, match='Unexpected case'):
        publish.current_case_path(tmp_path.parent/'outside.json')


def test_existing_recorded_file_is_preferred(tmp_path, monkeypatch):
    monkeypatch.setattr(publish, 'ROOT', tmp_path)
    recorded = tmp_path/'case.yaml'
    recorded.write_text('{}')
    (tmp_path/'case.json').write_text('{"changed":true}')
    assert publish.current_case_path(recorded) == recorded


def test_renamed_case_cannot_follow_symlink_outside_project(tmp_path, monkeypatch):
    project = tmp_path/'project'
    project.mkdir()
    monkeypatch.setattr(publish, 'ROOT', project)
    outside = tmp_path/'outside.json'
    outside.write_text('{}')
    (project/'case.json').symlink_to(outside)
    with pytest.raises(ValueError, match='Unexpected case'):
        publish.current_case_path(project/'case.yaml')
