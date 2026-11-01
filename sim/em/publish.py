#!/usr/bin/env python3
"""Publish compact checked COMH/COML outputs; native FEM data remain ignored."""
# SPDX-License-Identifier: CERN-OHL-P-2.0
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_normalization import verify_sources

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
RESULTS = ROOT / 'sim/results/em'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def current_case_path(recorded):
    """Resolve a historical case label without changing its saved provenance."""
    path = Path(recorded).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('Unexpected case source location')
    if not path.exists() and path.suffix in ('.yaml', '.yml'):
        path = path.with_suffix('.json').resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Unexpected case source location')
    if not path.is_file():
        raise ValueError('Missing case source: '+str(path.relative_to(ROOT)))
    return path


def verify_case(out, model, normalization_manifest=None):
    p = json.loads((out/'provenance.json').read_text())
    if p['status'] != 'complete' or p['backend'] != 'cpu':
        raise ValueError('Incomplete/non-CPU case: '+out.name)
    original_root = (Path(p['case']).parent / p['configuration'].get('project_root','.')).resolve()
    sources = {str(Path(s).relative_to(original_root)):h for s,h in p['source'].items()}
    if sources != model['source_hashes']:
        raise ValueError('Mixed source inputs: '+out.name)
    verify_sources(ROOT, sources, normalization_manifest)
    for stage in ['extract','mesh','solve','postprocess']:
        manifest = json.loads((out/stage/'stage.json').read_text())
        for file, expected in manifest['artifacts'].items():
            if digest(out/stage/file) != expected:
                raise ValueError('Changed native artifact: '+out.name+'/'+stage+'/'+file)
    return p


def publish(normalization_manifest=None):
    model = json.loads((RESULTS/'board-path/report.json').read_text())
    if model['model_sha256'] != digest(HERE/'transformer-coupling/model.json') or model['script_sha256'] != digest(HERE/'transformer-coupling/model.py'):
        raise ValueError('Component model changed after the combined run')
    rows, snapshots = [], {}
    for channel in ['comh','coml']:
        for suffix in ['2d','filter-2d','connector-3d']:
            name = channel+'-'+suffix
            out = RESULTS/name
            p = verify_case(out, model, normalization_manifest)
            if digest(out/'provenance.json') != model['cases'][name]['provenance_sha256']:
                raise ValueError('Case changed after network composition: '+name)
            geometry = json.loads((out/'mesh/geometry.json').read_text())
            report = json.loads((out/'postprocess/report.json').read_text())
            config_path = current_case_path(p['case'])
            current = json.loads(config_path.read_text())
            physical = lambda c: {k:v for k,v in c.items() if k not in ['board','project_root','output','execution']}
            if physical(current) != physical(p['configuration']):
                raise ValueError('Case inputs changed after the run: '+name)
            snapshots[name] = {'case': str(config_path.relative_to(ROOT)),
                'recorded_case': str(Path(p['case']).relative_to(ROOT)),
                'case_sha256': digest(config_path), 'physical_configuration': {k:v for k,v in p['configuration'].items()
                if k not in ['board','project_root','output','execution']},
                'execution': p['effective_execution'], 'mesh_sha256':digest(out/'mesh/board.msh'),
                'mesh_nodes':geometry['mesh_nodes'], 'mesh_quality':geometry.get('mesh_quality'),
                'ports':geometry.get('ports'), 'diagnostic_only':name in model['configuration'].get('diagnostic_sections',[]), 'mode_classification':report.get('mode_classification'),
                'max_singular_value':report.get('max_singular_value'),
                'reciprocity_max_abs_error':report.get('reciprocity_max_abs_error'),
                'solver_image':p['solver_image'],'tools_image':p['tools_image'],
                'stages':model['cases'][name]['stages'],
                'latest_invocation_seconds':p['finished_unix']-p['started_unix']}
            if suffix in ('2d','filter-2d'):
                candidates = report['differential_candidates']
                diagnostic = name in model['configuration'].get('diagnostic_sections',[])
                if len(candidates) != 1 and not diagnostic:
                    raise ValueError('Ambiguous differential candidate: '+name)
                mode = candidates[0] if not diagnostic else {'m':0,'Z_PV[1] (Ohm)':None,'L_PV[1] (H/m)':None,'C_PV[1] (F/m)':None}
                rows.append({'channel':channel,'section':'IC-side' if suffix=='2d' else 'filtered-side','frequency_hz':p['configuration']['frequency_hz'],
                    'mode':int(mode['m']) if not diagnostic else 'diagnostic only','differential_impedance_ohms':mode['Z_PV[1] (Ohm)'],
                    'L_H_per_m':mode['L_PV[1] (H/m)'],'C_F_per_m':mode['C_PV[1] (F/m)']})
    destination = HERE/'report'
    temporary = HERE/'report-pending'
    if temporary.exists():shutil.rmtree(temporary)
    temporary.mkdir()
    for channel in ['comh','coml']:
        for suffix,label in [('2d','section'),('filter-2d','filter-section'),('connector-3d','connector')]:
            shutil.copy2(RESULTS/(channel+'-'+suffix)/'postprocess/fields.png',temporary/(channel+'-'+label+'.png'))
        # scikit-rf adds a trailing space to the Touchstone option line.
        # Normalize published text before calculating its provenance hash.
        source = RESULTS/'board-path'/(channel+'.s2p')
        target = temporary/(channel+'.s2p')
        target.write_text(''.join(line.rstrip()+'\n' for line in
                                  source.read_text(encoding='utf-8').splitlines()),
                          encoding='utf-8', newline='\n')
    for filename in ['board-path.png','board-path.csv','routing.png']:
        shutil.copy2(RESULTS/'board-path'/filename,temporary/filename)
    with (temporary/'summary.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    convergence = []
    for channel in ['comh','coml']:
        baseline = next(r['differential_impedance_ohms'] for r in rows if r['channel']==channel)
        variants = [('baseline',RESULTS/(channel+'-2d'))]
        for path in sorted((RESULTS/(channel+'-2d/sweeps/mesh-fine_mm')).glob('run-*')):
            variants.append(('mesh-refinement',path))
        for path in sorted((RESULTS/(channel+'-2d/sweeps/cross_section-air_margin_mm')).glob('run-*')):
            variants.append(('vertical-domain',path))
        for kind,path in variants:
            prov = verify_case(path,model,normalization_manifest)
            r = json.loads((path/'postprocess/report.json').read_text())
            if len(r['differential_candidates']) != 1:raise ValueError('Ambiguous refinement mode')
            z = r['differential_candidates'][0]['Z_PV[1] (Ohm)']
            convergence.append({'channel':channel,'check':kind,
                'fine_mm':prov['configuration']['mesh']['fine_mm'],
                'air_margin_mm':prov['configuration']['cross_section']['air_margin_mm'],
                'Zdiff_ohms':z,'change_from_baseline_percent':100*(z-baseline)/baseline,
                'mesh_sha256':digest(path/'mesh/board.msh')})
    with (temporary/'convergence.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(convergence[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(convergence)
    field_rows = []
    for label,suffix in [('Filtered-pair section','filter-section'),('Connector-side 3D PCB','connector')]:
        field_rows.append(f'| {label} | ![COMH {label}: first-port basis field]({"comh-"+suffix+".png"}) | ![COML {label}: first-port basis field]({"coml-"+suffix+".png"}) |')
    section_table = ['| Channel | Section | Baseline Zdiff at 4 MHz (Ω) |', '|---|---|---:|']
    section_table += [f"| {r['channel'].upper()} | {r['section']} | "+(f"{r['differential_impedance_ohms']:.3f}" if r['differential_impedance_ohms'] is not None else 'Not accepted: ambiguous modes')+' |' for r in rows]
    with (RESULTS/'board-path/board-path.csv').open() as f:
        combined_rows = list(csv.DictReader(f))
    network_table = ['| Channel | Frequency (MHz) | S21 (dB) | S11 (dB) |', '|---|---:|---:|---:|']
    network_table += [f"| {r['channel'].upper()} | {float(r['frequency_hz'])/1e6:g} | {float(r['s21_db']):.3f} | {float(r['s11_db']):.3f} |" for r in combined_rows]
    readable = '# COMH/COML board-only EM results\n\n'
    readable += 'Six native CPU cases completed (COML filtered section is diagnostic only): two local sections and one 3D connector region per channel. The primary-side routes use explicit section-derived line equivalents; dense primary 3D meshes failed quality checks and are excluded. The combined model runs from U201 pads to J501/J502 contact heads. Cables and mating connectors are excluded.\n\n'
    readable += '**Provisional hybrid EM/circuit results.** Completion records execution, not mesh/domain convergence, hardware correlation, EMC approval or isolation qualification. The two route-length line equivalents and the connector 3D network per channel are joined by the balanced component equivalent documented in [the model guide](../transformer-coupling/README.md).\n\n'
    readable += '![Saved top-layer communication routing](routing.png)\n\n'
    readable += '## Local sections\n\n'+'\n'.join(section_table)+'\n\n'
    readable += '**COML filtered-section warning:** its automatic parity-screened 4.5 Ω candidate is not accepted as the signal impedance. The combined COML model explicitly uses COMH filtered L/C as a proxy with the actual COML route length; layout differences remain unqualified.\n\nThe IC-side cuts use 0.45 mm traces with a 0.20 mm gap; the filtered-side cuts have different saved spacing. These local impedances are not full-path input impedances. Native modal fields are shown below; their normalization is not an operating voltage.\n\n'
    readable += '| COMH section | COML section |\n|---|---|\n| ![COMH differential candidate at 4 MHz](comh-section.png) | ![COML differential candidate at 4 MHz](coml-section.png) |\n\n'
    readable += 'The 0.05 / 0.035 / 0.025 mm section mesh checks and 6-to-9 mm vertical-air-domain check are in [convergence.csv](convergence.csv). They are limited sensitivity checks; the lateral section width, 3D fields, materials and populated component model are not qualified by them.\n\n'
    readable += '## Complete balanced board path\n\n'+'\n'.join(network_table)+'\n\n'
    readable += '![Hybrid board-path S parameters](board-path.png)\n\n'
    readable += 'The 100 Ω wave reference is a reporting convention, not a BQ79616 driver output-resistance model. Three frequency samples do not establish interpolation or fast-edge/transient accuracy. Shading varies only assumed transformer magnetizing/leakage inductance; it is not a full device tolerance bound.\n\n'
    readable += 'Native combined networks: [COMH](comh.s2p), [COML](coml.s2p). Scalars: [board-path.csv](board-path.csv), [summary.csv](summary.csv).\n\n'
    readable += '## PCB basis fields\n\n| Region | COMH | COML |\n|---|---|---|\n'+'\n'.join(field_rows)+'\n\n'
    readable += 'These are first-port basis excitations with other ports reference-terminated, not the populated-board operating field. Images use separate automatic color scales. The section pictures are normalized eigenfields; the COML filtered picture is a rejected diagnostic mode, not an accepted differential line mode. The secondary half-port picture does not drive both halves as the combined balanced circuit does. Field peaks are not dielectric-stress predictions.\n\n'
    readable += '## Assumptions and evidence\n\n'+'\n'.join('- '+a for a in model['assumptions'])+'\n\n'
    readable += 'The connector 3D field tolerance is 1e-8; the 2D section tolerance is 1e-9. The approximate flux-error estimator uses 1e-2; a same-mesh diagnostic kept saved port values unchanged. Very thin positive-quality tetrahedra remain, so local field peaks and 3D absolute values require caution. Mesh quality, physical inputs, source/image/stage/artifact hashes and component mappings are retained in [provenance.json](provenance.json).\n\n'
    readable += 'Native FEM meshes, field collections, solver inputs/logs and ParaView states remain locally under ignored `sim/results/em/`. Reproduce with the commands in the [EM guide](../README.md). No other EM simulation is scheduled in this repository. Measured hardware correlation remains separate.\n'
    (temporary/'README.md').write_text(readable)
    snapshot = {'schema':1,'scope':model['scope'],'source_hashes':model['source_hashes'],
                'cases':snapshots,'combined_network':model,
                'limitations':['Unconverged 3D finite domains; limited 2D refinement is reported separately.',
                               'Balanced component equivalent; no common-mode, cable, transient, EMC or hardware qualification.']}
    diagnostic = RESULTS/'session/estimator-comparison.json'
    if diagnostic.exists(): snapshot['estimator_diagnostic'] = json.loads(diagnostic.read_text())
    audit = RESULTS/'session/initial-audit.json'
    if audit.exists(): snapshot['initial_audit'] = json.loads(audit.read_text())
    budget = RESULTS/'session/budget.json'
    if budget.exists():
        import time
        b = json.loads(budget.read_text())
        snapshot['session_timing'] = {'budget_minutes':180, 'elapsed_seconds':time.time()-b['started_unix']}
    snapshot.update(verify_sources(ROOT, model['source_hashes'], normalization_manifest))
    previous = destination/'provenance.json'
    if previous.exists():
        old = json.loads(previous.read_text())
        if 'session_timing' in old: snapshot['session_timing'] = old['session_timing']
    snapshot['published_artifacts']={str(p.relative_to(temporary)):digest(p) for p in temporary.iterdir() if p.is_file()}
    (temporary/'provenance.json').write_text(json.dumps(snapshot,indent=2)+'\n')
    if destination.exists():shutil.rmtree(destination)
    temporary.rename(destination)
    print('Published',len(snapshots),'completed CPU cases to',destination)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-normalization", type=Path)
    publish(parser.parse_args().source_normalization)
