#!/usr/bin/env python3
"""Combine the COMH/COML PCB networks with a balanced component equivalent."""
# Copyright (C) 2021-2026 Gerhard Malberg
# SPDX-License-Identifier: CERN-OHL-P-2.0
import argparse
import csv
import hashlib
import heapq
import json
import math
from pathlib import Path

import numpy as np
import skrf as rf


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def series(z):
    z = np.atleast_1d(np.asarray(z, dtype=complex))
    a = np.tile(np.eye(2, dtype=complex), (len(z), 1, 1))
    a[:, 0, 1] = z
    return a


def shunt(y):
    a = series(np.zeros_like(y))
    a[:, 1, 0] = y
    return a


def reduce_ports(network, connections, reference=100):
    """Power-preserving signed series connections: v'=C.T v, i=C i'."""
    c = np.asarray(connections, dtype=float)
    if c.shape != (network.nports, 2) or np.linalg.matrix_rank(c) != 2:
        raise ValueError('Two independent reduced ports are required')
    z = np.einsum('pi,fpq,qj->fij', c, network.z, c)
    return rf.Network(f=network.f, z=z, z0=reference)


def section_line(base, frequency, length_m):
    report = json.loads((base/'postprocess/report.json').read_text())
    candidates = report.get('differential_candidates', [])
    if len(candidates) != 1:
        raise ValueError(f'A unique differential section mode is required: {base.name}')
    mode = candidates[0]
    l, c = mode['L_PV[1] (H/m)'], mode['C_PV[1] (F/m)']
    if l <= 0 or c <= 0 or length_m <= 0:
        raise ValueError('Line equivalent requires positive real L, C and length')
    z = math.sqrt(l/c)
    phase = 2j*np.pi*frequency*math.sqrt(l*c)*length_m
    a = np.empty((len(frequency),2,2),dtype=complex)
    a[:,0,0] = a[:,1,1] = np.cosh(phase)
    a[:,0,1] = z*np.sinh(phase)
    a[:,1,0] = np.sinh(phase)/z
    return rf.Network(f=frequency,a=a,z0=100), {'section':base.name,'length_m':length_m,
        'L_H_per_m':l,'C_F_per_m':c,'Z_ohms':z,'section_frequency_hz':4e6,
        'assumption':'Lossless uniform line; real 4 MHz section parameters held constant across 1/4/10 MHz'}


def component_abcd(frequency, config, magnetizing=None, leakage=None):
    omega = 2j * np.pi * frequency
    t = config['transformer']
    lm = t['magnetizing_inductance_H'] if magnetizing is None else magnetizing
    ll = t['leakage_inductance_H'] if leakage is None else leakage
    if lm <= 0 or ll < 0 or t['ratio'] != 1:
        raise ValueError('This model requires positive Lm, nonnegative leakage and a 1:1 transformer')
    load = shunt(1 / config['input_shunt_ohms'] + omega * config['bypass_capacitance_per_leg_F'] / 2)
    resistors = series(np.full(len(frequency), 2 * config['series_resistance_per_leg_ohms']))
    transformer = (series(np.full(len(frequency), t['primary_resistance_ohms']))
                   @ shunt(1 / (omega * lm))
                   @ series(t['secondary_resistance_ohms'] + omega * ll))
    return load, resistors, transformer


def route_length(board, components, start, end):
    """Saved centerline shortest path; pad interiors connect coincident endpoints."""
    from shapely.geometry import Polygon, Point
    a_ref, a_num = start.split(':')
    b_ref, b_num = end.split(':')
    pa = next(p for p in components[a_ref]['pads'] if p['number'] == a_num)
    pb = next(p for p in components[b_ref]['pads'] if p['number'] == b_num)
    if pa['net'] != pb['net']:
        raise ValueError(f'Route endpoints are on different nets: {start}, {end}')
    tracks = [t for t in board['copper'] if t['kind'] == 'track' and t['net'] == pa['net']]
    graph = {}
    def key(point): return tuple(round(float(x), 6) for x in point)
    def edge(a, b, length):
        graph.setdefault(a, []).append((b, length))
        graph.setdefault(b, []).append((a, length))
    for track in tracks:
        if 'start' not in track or 'end' not in track:
            raise ValueError('A routed arc needs an explicit arc-length implementation')
        a, b = key(track['start']), key(track['end'])
        edge(a, b, math.dist(a, b))
    pads = [pad for component in components.values() for pad in component['pads'] if pad['net'] == pa['net']]
    for pad in pads:
        center = key(pad['position'])
        # Pad shapes come from the saved extraction, including their rotations.
        polys = [Polygon(p['outer'], p['holes']) for item in board['copper']
                 if item['kind'] == 'pad' and item['net'] == pad['net']
                 for p in item['polygons'] if Polygon(p['outer'], p['holes']).covers(Point(center))]
        vertices = list(graph)
        graph.setdefault(center, [])
        for vertex in vertices:
            if vertex != center and any(poly.buffer(1e-6).covers(Point(vertex)) for poly in polys):
                edge(center, vertex, math.dist(center, vertex))
    source, target = key(pa['position']), key(pb['position'])
    queue, distance = [(0., source)], {source: 0.}
    while queue:
        d, node = heapq.heappop(queue)
        if node == target:
            return {'start': start, 'end': end, 'net': pa['net'], 'length_mm': d}
        if d > distance[node]: continue
        for neighbor, weight in graph.get(node, []):
            new = d + weight
            if new < distance.get(neighbor, float('inf')):
                distance[neighbor] = new
                heapq.heappush(queue, (new, neighbor))
    raise ValueError(f'No saved track/pad path between {start} and {end}')


def verify_components(components, pins, config):
    """Reject a changed part value, differential polarity or grounding topology."""
    def pad(ref, number):
        return next(p for p in components[ref]['pads'] if p['number'] == number)['net']
    def net(terminal): return pad(*terminal.split(':'))
    p, n = net(pins['ic_positive']), net(pins['ic_negative'])
    expected = {}
    for sign, ic_net in [('positive', p), ('negative', n)]:
        r = pins[sign+'_resistor']
        if not components[r]['value'].startswith('49R9') or pad(r, '1') != ic_net:
            raise ValueError(f'Changed resistor value/connectivity: {r}')
        if pad(r, '2') != pad(pins['transformer'], pins['primary_'+sign]):
            raise ValueError(f'Resistor no longer connects to transformer: {r}')
        expected[r] = components[r]['value']
    r = pins['shunt']
    if not components[r]['value'].startswith('1k ') or {pad(r,'1'), pad(r,'2')} != {p,n}:
        raise ValueError('Changed 1k differential shunt')
    for ref, expected_net in zip(pins['bypass'], [p,n]):
        if not components[ref]['value'].startswith('220pF ') or {pad(ref,'1'),pad(ref,'2')} != {expected_net,'GND'}:
            raise ValueError(f'Changed differential bypass: {ref}')
        expected[ref] = components[ref]['value']
    t = pins['transformer']
    if components[t]['value'] != config['transformer']['part'] or not pad(t,'5').startswith('unconnected-'):
        raise ValueError('Transformer part or floating secondary center tap changed')
    expected[t] = components[t]['value']
    return expected


def validate_sources(root, paths):
    sources = {}
    for out in paths:
        p = json.loads((out / 'provenance.json').read_text())
        if p['status'] != 'complete' or p['last_stage'] != 'postprocess':
            raise ValueError(f'Incomplete case: {out.name}')
        numerical = json.loads((out/'postprocess/report.json').read_text())
        if numerical.get('max_singular_value', 0) > 1 + 1e-5:
            raise ValueError(f'PCB network fails sampled passivity: {out.name}')
        if numerical.get('reciprocity_max_abs_error', 0) > 1e-4:
            raise ValueError(f'PCB network fails reciprocity: {out.name}')
        original_project = (Path(p['case']).parent / p['configuration'].get('project_root', '.')).resolve()
        for source, expected in p['source'].items():
            relative = str(Path(source).relative_to(original_project))
            if sha(root / relative) != expected:
                raise ValueError(f'Design input changed: {Path(source).name}')
            if relative in sources and sources[relative] != expected:
                raise ValueError('Cases use different design inputs')
            sources[relative] = expected
        for stage in ['extract', 'mesh', 'solve', 'postprocess']:
            manifest = json.loads((out / stage / 'stage.json').read_text())
            for file, expected in manifest['artifacts'].items():
                if sha(out / stage / file) != expected:
                    raise ValueError(f'Artifact changed: {out.name}/{stage}/{file}')
    return sources


def run(root, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root, output = Path(root).resolve(), Path(output).resolve()
    config_path = Path(__file__).with_name('model.json')
    config = json.loads(config_path.read_text())
    output.mkdir(parents=True, exist_ok=True)
    cases = [root / 'sim/results/em' / name for ch in config['channels']
             for name in [ch+'-2d', ch+'-filter-2d', ch+'-connector-3d']]
    sources = validate_sources(root, cases)
    records, networks = [], {}
    report = {'schema': 1, 'scope': 'Balanced COMH/COML IC-pad to board-connector hybrid EM/circuit model; no cable',
              'assumptions': config['assumptions'], 'configuration': config, 'channels': {},
              'source_hashes': sources, 'model_sha256': sha(config_path), 'script_sha256': sha(__file__)}
    for channel, pins in config['channels'].items():
        base = root / 'sim/results/em'
        board = json.loads((base / (channel+'-2d/extract/board.json')).read_text())
        components = {c['ref']: c for c in board['components']}
        checked_components = verify_components(components, pins, config)
        # Confirm the electrical meaning against saved PCB pads before cascading.
        path_records = []
        for sign in ['positive', 'negative']:
            resistor = pins[sign+'_resistor']
            paths = [(pins['ic_'+sign], resistor+':1'),
                     (resistor+':2', pins['transformer']+':'+pins['primary_'+sign]),
                     (pins['transformer']+':'+pins['secondary_'+sign], pins['connector_'+sign])]
            path_records.extend(route_length(board, components, a, b) for a, b in paths)
        secondary = rf.Network(base / (channel+'-connector-3d/postprocess/network.s3p'))
        secondary = reduce_ports(secondary, [[1,0], [1,0], [0,1]])
        ic, ic_line = section_line(base/(channel+'-2d'), secondary.f,
                                  .0005*(path_records[0]['length_mm']+path_records[3]['length_mm']))
        filtered_source = config.get('filtered_line_proxy',{}).get(channel,channel+'-filter-2d')
        if filtered_source in config.get('diagnostic_sections',[]):
            raise ValueError('A diagnostic-only section cannot supply line parameters')
        filtered, filtered_line = section_line(base/filtered_source, secondary.f,
                                               .0005*(path_records[1]['length_mm']+path_records[4]['length_mm']))
        load, resistors, transformer = component_abcd(ic.f, config)
        total = rf.Network(f=ic.f, a=ic.a @ load @ resistors @ filtered.a @ transformer @ secondary.a,
                           z0=config['reference_ohms'])
        total.comments = channel.upper()+': balanced IC-pad to board-connector network.\nNo cable; component assumptions in model.json and report.json.'
        total.write_touchstone(filename=channel, dir=str(output), r_ref=config['reference_ohms'])
        secondary.write_touchstone(filename=channel+'-secondary-reduced', dir=str(output), r_ref=100)
        filtered.write_touchstone(filename=channel+'-filter-reduced', dir=str(output), r_ref=100)
        maximum = float(np.max(np.linalg.svd(total.s, compute_uv=False)))
        if not np.isfinite(total.s).all() or maximum > 1 + 1e-4:
            raise ValueError(f'{channel} combined network is nonfinite or nonpassive: {maximum}')
        envelopes = []
        for lm in [150e-6, 300e-6, 450e-6]:
            for ll in [0, 250e-9, 500e-9]:
                l, r, t = component_abcd(ic.f, config, lm, ll)
                n = rf.Network(f=ic.f, a=ic.a @ l @ r @ filtered.a @ t @ secondary.a, z0=100)
                envelopes.append(20*np.log10(abs(n.s[:,1,0])))
        info = {'routes': path_records, 'ic_line':ic_line, 'filtered_line':filtered_line, 'checked_components': checked_components, 'max_singular_value': maximum,
                'reciprocity_max_abs_error': float(np.max(abs(total.s[:,0,1]-total.s[:,1,0]))),
                'transformer_sensitivity_scope': 'Illustrative Lm=150/300/450 uH, leakage=0/0.25/0.5 uH; not a full tolerance or frequency-validity bound'}
        if channel in config.get('filtered_line_proxy',{}):
            differences=[]
            for factor in [.5,2.]:
                a=filtered.a.copy();a[:,0,1]*=factor;a[:,1,0]/=factor
                variant=rf.Network(f=ic.f,a=ic.a@load@resistors@a@transformer@secondary.a,z0=100)
                differences.append(float(np.max(abs(variant.s_db[:,1,0]-total.s_db[:,1,0]))))
            info['filtered_proxy_sensitivity']={'impedance_factors':[.5,2.],
                'maximum_s21_change_db':max(differences),
                'scope':'Assumed impedance variation at fixed propagation velocity; not a bound on real geometry, asymmetry or mode conversion'}
        for i, frequency in enumerate(total.f):
            records.append({'channel': channel, 'frequency_hz': float(frequency),
                            's11_db': float(20*np.log10(abs(total.s[i,0,0]))),
                            's21_db': float(20*np.log10(abs(total.s[i,1,0]))),
                            's21_phase_deg': float(np.angle(total.s[i,1,0], deg=True))})
        report['channels'][channel] = info
        networks[channel] = (total, np.min(envelopes, axis=0), np.max(envelopes, axis=0))
    with (output / 'board-path.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader();writer.writerows(records)
    fig, axes = plt.subplots(2, 1, figsize=(8,7), sharex=True)
    for channel, (network, lower, upper) in networks.items():
        x = network.f/1e6
        axes[0].plot(x, network.s_db[:,1,0], 'o-' if channel=='comh' else 's--', label=channel.upper())
        axes[0].fill_between(x, lower, upper, alpha=.12)
        axes[1].plot(x, network.s_db[:,0,0], 'o-' if channel=='comh' else 's--', label=channel.upper())
    axes[0].set(ylabel='S21 (dB)', title='IC pads to board connector: hybrid EM / linear differential model')
    axes[1].set(xlabel='Frequency (MHz)', ylabel='S11 (dB)')
    for ax in axes: ax.grid(alpha=.25);ax.legend()
    fig.text(.5, .01, '100 Ω references; COML filtered line uses a declared proxy. Shaded: limited transformer sensitivity; no cable.', ha='center', fontsize=8)
    fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(output/'board-path.png',dpi=160);plt.close(fig)
    # Saved-copper plan view: show the modeled path without implying an operating field.
    fig, ax = plt.subplots(figsize=(11,8))
    colors = {'COMH':'#1565c0', 'COML':'#b33b1b'}
    for item in board['copper']:
        channel = next((name for name in colors if name in item['net']), None)
        if channel is None or item['layer'] != 'F.Cu': continue
        if item['kind'] == 'track':
            ax.plot([item['start'][0],item['end'][0]], [item['start'][1],item['end'][1]],
                    color=colors[channel], linewidth=max(.7,item['width_mm']*5), alpha=.8)
        elif item['kind'] == 'pad':
            for poly in item['polygons']:
                xy = np.asarray(poly['outer'])
                ax.fill(xy[:,0],xy[:,1],color=colors[channel],alpha=.45)
    for ref in ['U201','T501','T502','J501','J502','R501','R503','R504','R506']:
        comp = components[ref]
        x,y = comp['position']
        if ref == 'U201': x,y = 290.4,128.2
        offset = (-35,0) if ref == 'U201' else ((0,-20) if ref.startswith('T') else (15,0))
        ax.annotate(ref,(x,y),xytext=offset,textcoords='offset points',fontsize=9,
                    ha='right' if ref=='U201' else 'left',arrowprops={'arrowstyle':'-','color':'#555'})
    for label,color in colors.items(): ax.plot([],[],color=color,label=label)
    ax.set(xlim=(288.5,324.5),ylim=(141,114.5),xlabel='KiCad X (mm)',ylabel='KiCad Y (mm)',
           title='COMH / COML: saved PCB copper from U201 to board connectors')
    ax.set_aspect('equal');ax.legend(loc='lower left');ax.grid(alpha=.15)
    fig.text(.5,.01,'Saved top-layer routing: primary line equivalents plus 3D connector EM; no cable or mating connector.',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.035,1,1]);fig.savefig(output/'routing.png',dpi=160);plt.close(fig)
    report['saved_stackup'] = board['stackup']
    report['declared_thickness_mm'] = board['declared_thickness_mm']
    report['extraction_kicad_version'] = board['kicad_version']
    report['cases'] = {p.name: {'provenance_sha256': sha(p/'provenance.json'),
        'tools_image': json.loads((p/'provenance.json').read_text())['tools_image'],
        'solver_image': json.loads((p/'provenance.json').read_text())['solver_image'],
        'stages': {s: json.loads((p/s/'stage.json').read_text())['key'] for s in ['extract','mesh','solve','postprocess']}}
        for p in cases}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Verified and combined', len(cases), 'cases:', output)
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    run(a.project, a.output)
