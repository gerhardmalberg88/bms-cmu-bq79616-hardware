#!/usr/bin/env python3
"""Generate the review-only, physically wired Qucs-S sheet. Never runs a solver.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import hashlib
import json
from pathlib import Path

CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def engineering(value, kind):
    unit = {'R': 'Ohm', 'C': 'F', 'L': 'H', 'Vdc': 'V', 'Idc': 'A'}[kind]
    for prefix, scale in [('G', 1e9), ('M', 1e6), ('k', 1e3), ('', 1),
                          ('m', 1e-3), ('u', 1e-6), ('n', 1e-9), ('p', 1e-12)]:
        if abs(value) >= scale:
            return f'{value/scale:.6g} {prefix}{unit}'
    return f'{value:.6g} {unit}'


def generate(output, audit_dir, force=False):
    if output.exists() and not force:
        raise ValueError(f'Refusing to overwrite {output}; choose another --output or use --force after reviewing your edits.')
    topology = json.loads((CASE/'topology.json').read_text())
    review = json.loads((CASE/'circuit/wired-review.json').read_text())
    geometry = json.loads((CASE/'circuit/wired-review-geometry.json').read_text())
    for rel, expected in geometry['source_hashes'].items():
        if digest(ROOT/rel) != expected:
            raise ValueError('Design changed since route extraction: '+rel)
    if topology['source_hashes'] != geometry['source_hashes']:
        raise ValueError('Topology and review routing use different designs')
    p = {k: v['value'] for k, v in review['parameters'].items()}
    routes = {r['tap']: r for r in geometry['routes']}
    components, wires, paintings, parts, anchors = [], [], [], {}, {}
    TOP, DY = 800, 480
    CELL, TAP, VC, VLEAK, AVSS = 220, 1270, 1890, 2090, 2450
    CB, BLEAK, DIE, SWITCH, CDS = 3170, 3370, 3970, 4390, 4710

    def y(n):
        return TOP+(16-n)*DY

    def scaled(point):
        return (round(point[0]*2), round(point[1]*1.6))

    def physical_wire(a, b):
        if a == b:
            return
        assert a[0] == b[0] or a[1] == b[1], (a, b)
        wires.append(tuple(sorted((a, b))))

    def wire(a, b):
        physical_wire(scaled(a), scaled(b))

    def path(*points):
        for a, b in zip(points, points[1:]):
            wire(a, b)

    def txt(x, yy, text, size=16):
        xx, yyy = scaled((x, yy))
        paintings.append(f'<Text {xx} {yyy} {size} #233e5b 0 "{text}">')

    def component(kind, name, x, yy, value, vertical=False):
        # Native Qucs current-source node ordering is opposite to SPICE's.
        rot = (3 if vertical else 0) if kind == 'Idc' else (1 if vertical else 0)
        center = scaled((x, yy))
        value_text = engineering(value, kind)
        properties = {
            'R': f'"{value_text}" 1 "25" 0 "0" 0 "0" 0 "25" 0 "european" 0',
            'C': f'"{value_text}" 1 "" 0 "neutral" 0',
            'L': f'"{value_text}" 1 "" 0',
            'Vdc': f'"{value_text}" 1', 'Idc': f'"{value_text}" 1',
        }[kind]
        dx, dy = (18, -25) if vertical else (-26, 18)
        components.append(f'<{kind} {name} 1 {center[0]} {center[1]} {dx} {dy} 0 {rot} {properties}>')
        offsets = [(0, -30), (0, 30)] if vertical else [(-30, 0), (30, 0)]
        terminals = []
        for ox, oy in offsets:
            native = (center[0]+ox, center[1]+oy)
            terminals.append(native)
            physical_wire(native, scaled((x+ox, yy+oy)))
        parts[name] = dict(kind=kind, terminals=terminals, value=value,
                           displayed_value=value_text, vertical=vertical)

    def controlled_switch(n, yy):
        # Qucs Relais is an electrical voltage-controlled switch. It contains
        # no coil model, timed events, or physical TI gate-drive assumptions.
        x = SWITCH
        center = scaled((x, yy))
        properties = f'"0.5 V" 0 "0 V" 0 "{engineering(p["switch_ron"], "R")}" 1 "{engineering(p["switch_roff"], "R")}" 1 "25" 0 "SPST" 0'
        name = f'S_cell{n}'
        components.append(f'<Relais {name} 1 {center[0]} {center[1]} 75 -25 0 0 {properties}>')
        offsets = [(-30, -30), (30, -30), (30, 30), (-30, 30)]
        terminals = []
        for ox, oy in offsets:
            a = (center[0]+ox, center[1]+oy)
            b = scaled((x+ox, yy+oy))
            terminals.append(a)
            physical_wire(a, (b[0], a[1])); physical_wire((b[0], a[1]), b)
        parts[name] = dict(kind='Relais', terminals=terminals, value=p['switch_ron'])
        component('Vdc', f'V_enable{n}', x-180, yy, 0, True)
        # Controller return follows the lower CB die node using real wires.
        path((x-180, yy-30), (x-30, yy-30))
        path((x-30, yy+30), (x-30, yy+120), (x-180, yy+120))
        path((x-180, yy+30), (x-180, yy+DY-250))

    def cap_branch(ref, xx, yy, lower, leakx):
        component('R', 'R_'+ref+'_ESR', xx, yy+180, p['cap_esr'], True)
        component('L', 'L_'+ref+'_ESL', xx, yy+280, p['cap_esl'], True)
        component('C', ref, xx, yy+390, p['cap_c'], True)
        path((xx, yy), (xx, yy+150)); path((xx, yy+210), (xx, yy+250))
        path((xx, yy+310), (xx, yy+360)); path((xx, yy+420), (xx, lower))
        component('R', 'R_'+ref+'_leak', leakx, yy+300, p['cap_leak'], True)
        path((xx, yy+110), (leakx, yy+110), (leakx, yy+270))
        path((leakx, yy+330), (leakx, yy+450), (xx, yy+450))

    txt(60, 25, '16S NMC / BQ79616 VC-CB CIRCUIT - STATIC INSPECTION SHEET', 25)
    txt(60, 65, 'Cell: LG INR21700-M50, 3.63 V nominal, 18.2 Wh; 16S1P assumed. R_cell + R_relax = 30 mOhm; split and relaxation time are unfitted assumptions.')
    txt(60, 100, 'Visible values; all electrical connections use wires. Junction dots connect; crossings without dots do not. Double-click to inspect a component.')
    txt(60, 135, 'CB loop: capacitor bank -> measured routed path -> assumed package L -> internal switch and assumed Cds -> adjacent pin -> capacitor bank.')
    txt(60, 170, 'All enable sources are static 0 V (OFF). Switch symbol is an electrical surrogate, not a fitted relay. 0/1 V control is abstract logic, not gate voltage.')
    txt(60, 205, 'ASSUMED: cell RC/L, package L, Cds, input returns and L/C per mm. TDK C/ESR/ESL/leakage and TI Ron limits have manufacturer references in wired-review.json.')
    txt(60, 240, 'Cap-bank landing stubs are collapsed. Main ADC internals and detailed harness mutual coupling are outside this sheet. No hardware wait is guaranteed.')
    txt(60, 275, 'One scripted study: repeated odd / OFF / even / OFF balancing. See circuit/README.md and report/README.md for assumptions and results.')
    txt(110, 660, 'NMC CELL STACK', 18)
    txt(420, 660, 'WIRE / CONTACT / FUSE / PCB', 18)
    txt(1400, 660, 'VC SENSING', 18); txt(2120, 660, 'IC INPUT LOAD', 18)
    txt(2530, 660, 'CB FEED / CAPACITOR BANK', 18)
    txt(3470, 660, 'CAP-BANK TO U201 / PACKAGE', 18)
    txt(4140, 660, 'INTERNAL SWITCH / Cds', 18)
    txt(1300, 350, 'BAT branch / equivalent board load')
    component('R', 'R202', 1450, 430, 30)
    path((TAP, y(16)), (TAP, 430), (1420, 430))
    path((1480, 430), (1650, 430), (1810, 430))
    component('C', 'C208', 1650, 520, 10e-9, True)
    component('Idc', 'I_BAT', 1810, 520, p['bat_current'], True)
    path((1650, 430), (1650, 490)); path((1810, 430), (1810, 490))
    path((1650, 550), (1650, 610), (AVSS, 610)); path((1810, 550), (1810, 610))
    component('Idc', 'I_board', 2170, 520, p['board_current'], True)
    path((TAP, 430), (TAP, 390), (2170, 390), (2170, 490))
    path((2170, 550), (2170, 610))
    bottom = y(0)+860
    wire((AVSS, 610), (AVSS, bottom))
    for row in reversed(topology['taps']):
        n = row['tap']; yy = y(n); by = yy+100
        for key, point in [('cell', (CELL, yy)), ('tap', (TAP, yy)), ('vc', (VC, yy)), ('cb', (CB, by)), ('die', (DIE, by))]:
            anchors[f'{key}{n}'] = scaled(point)
        txt(40, yy-20, f'Tap {n}', 15)
        if n:
            component('Vdc', f'V_cell{n}', CELL, yy+80, p['cell_voltage'], True)
            component('R', f'R_cell{n}', CELL, yy+170, p['cell_r'], True)
            component('L', f'L_cell{n}', CELL, yy+250, p['cell_l'], True)
            component('R', f'R_relax{n}', CELL, yy+380, p['cell_relax_r'], True)
            component('C', f'C_relax{n}', 60, yy+380, p['cell_relax_c'], True)
            path((CELL, yy), (CELL, yy+50)); wire((CELL, yy+110), (CELL, yy+140))
            wire((CELL, yy+200), (CELL, yy+220)); wire((CELL, yy+280), (CELL, yy+350))
            wire((CELL, yy+410), (CELL, yy+DY))
            path((CELL, yy+320), (60, yy+320), (60, yy+350))
            path((60, yy+410), (60, yy+440), (CELL, yy+440))
        seq = [('R', f'R_wire{n}', 430, p['wire_r']), ('L', f'L_wire{n}', 550, p['wire_l']),
               ('R', f'R_contact{n}', 670, p['contact_r']), ('R', 'R_'+row['fuse'], 790, p['fuse_r']),
               ('L', 'L_'+row['fuse'], 910, p['fuse_l']), ('R', f'R_PCB{n}', 1030, p['shared_pcb_r']),
               ('L', f'L_PCB{n}', 1150, p['shared_pcb_l'])]
        previous = (CELL, yy)
        for kind, name, xx, value in seq:
            component(kind, name, xx, yy, value); wire(previous, (xx-30, yy)); previous = (xx+30, yy)
        wire(previous, (TAP, yy))
        geo = topology['geometry'][str(n)]['VC']
        seq = [('R', row['sense'], 1410, p['sense_r']), ('L', 'L_'+row['sense'], 1530, p['resistor_l']),
               ('R', f'R_VCtrace{n}', 1650, geo['resistance_ohm']), ('L', f'L_VCtrace{n}', 1770, geo['length_mm']*p['trace_l_per_mm'])]
        previous = (TAP, yy)
        for kind, name, xx, value in seq:
            component(kind, name, xx, yy, value); wire(previous, (xx-30, yy)); previous = (xx+30, yy)
        wire(previous, (VC, yy))
        component('Idc', f'I_input{n}', 2250, yy, p['vc_input_current'])
        wire((VC, yy), (2220, yy)); wire((2280, yy), (AVSS, yy))
        component('C', f'C_input{n}', 2250, yy+60, p['input_pin_c']+geo['length_mm']*p['trace_c_per_mm'])
        path((VC, yy), (VC, yy+60), (2220, yy+60)); wire((2280, yy+60), (AVSS, yy+60))
        cap_branch(row['vc_cap'], VC, yy, yy+DY, VLEAK)
        if n == 0:
            wire((VC, yy+DY), (AVSS, yy+DY))
        path((TAP, yy), (TAP, by), (2660, by))
        geo = topology['geometry'][str(n)]['CB']; route = routes[n]
        remain_r = geo['resistance_ohm']-route['resistance_ohm']
        remain_l = (geo['length_mm']-route['length_mm'])*p['trace_l_per_mm']
        if remain_r <= 0 or remain_l <= 0:
            raise ValueError(f'Invalid route partition at CB{n}')
        seq = [('R', row['balance'], 2690, p['balance_r']), ('L', 'L_'+row['balance'], 2810, p['resistor_l']),
               ('R', f'R_CBfeed{n}', 2930, remain_r), ('L', f'L_CBfeed{n}', 3050, remain_l)]
        previous = (2660, by)
        for kind, name, xx, value in seq:
            component(kind, name, xx, by, value); wire(previous, (xx-30, by)); previous = (xx+30, by)
        wire(previous, (CB, by))
        cap_branch(row['cb_cap'], CB, by, by+DY, BLEAK)
        component('C', f'C_CBtrace{n}', 2820, by+60, geo['length_mm']*p['trace_c_per_mm'])
        path((CB, by), (CB, by+60), (2850, by+60)); wire((2790, by+60), (AVSS, by+60))
        # Existing total route impedance is partitioned, not duplicated.
        seq = [('R', f'R_CBloop{n}', 3490, route['resistance_ohm']),
               ('L', f'L_CBloop{n}', 3650, route['length_mm']*p['trace_l_per_mm']+route['vias']*p['via_l']),
               ('L', f'L_CBpin{n}', 3810, p['cb_package_l'])]
        previous = (CB, by)
        for kind, name, xx, value in seq:
            component(kind, name, xx, by, value); wire(previous, (xx-30, by)); previous = (xx+30, by)
        wire(previous, (DIE, by))
        txt(3900, by-40, f'U201 CB{n} pin {row["cb_pin"]}', 13)
        # A bounded coupling capacitor provides an explicit CB-to-VC path.
        component('C', f'C_VC_CB{n}', 2670, yy-80, p['vc_cb_c'])
        path((VC, yy), (VC+80, yy), (VC+80, yy-80), (2640, yy-80))
        path((2700, yy-80), (CB+80, yy-80), (CB+80, by), (CB, by))
        if n:
            controlled_switch(n, by+250)
            component('C', f'C_ds{n}', CDS, by+250, p['switch_cds'], True)
            path((DIE, by), (SWITCH+30, by), (CDS, by), (CDS, by+220))
            path((SWITCH+30, by), (SWITCH+30, by+220))
            path((SWITCH+30, by+280), (SWITCH+30, by+DY), (DIE, by+DY))
            path((CDS, by+280), (CDS, by+DY), (SWITCH+30, by+DY))
        else:
            wire((AVSS, by+DY), (CB, by+DY))
    path((TAP, y(0)), (TAP, bottom), (AVSS, bottom))
    path((CELL, y(0)), (CELL, y(0)+120))
    ground = scaled((CELL, y(0)+120))
    components.append(f'<GND * 1 {ground[0]} {ground[1]} 0 0 0 0>')
    parts['ground'] = dict(kind='GND', terminals=[ground])
    txt(1400, bottom-50, 'LOCAL AVSS RETURN - physically wired to tap 0 after the wire/contact/fuse/PCB impedances')
    txt(60, y(0)+180, 'Stack negative / reference', 14)
    wires = list(dict.fromkeys(wires))
    junctions = {p for seg in wires for p in seg}
    junctions |= {p for part in parts.values() for p in part['terminals']}
    segments = []
    for a, b in wires:
        hits = [a, b]+[q for q in junctions if (a[0] == b[0] == q[0] and a[1] < q[1] < b[1]) or
                                           (a[1] == b[1] == q[1] and a[0] < q[0] < b[0])]
        hits = sorted(set(hits)); segments.extend(zip(hits, hits[1:]))
    segments = list(dict.fromkeys(segments))
    wire_lines = [f'<{a[0]} {a[1]} {b[0]} {b[1]} "" 0 0 0 "">' for a, b in segments]
    sections = {'Properties': ['<View=-100,-40,9900,3400,0.3,0,0>', '<Grid=10,10,1>',
                               f'<DataSet={output.stem}.dat>', f'<DataDisplay={output.stem}.dpl>',
                               '<OpenDisplay=0>', '<RunScript=0>', '<showFrame=0>'],
                'Symbol': [], 'Components': components, 'Wires': wire_lines, 'Diagrams': [], 'Paintings': paintings}
    text = '<Qucs Schematic 26.1.1>\n'+''.join(f'<{name}>\n'+'\n'.join(rows)+f'\n</{name}>\n' for name, rows in sections.items())
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(text)
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit = dict(parts=parts, wires=segments, anchors=anchors, simulation_executed=False,
                 input_hashes={f: digest(CASE/f) for f in ['topology.json', 'circuit/wired-review.json', 'circuit/wired-review-geometry.json', 'prepare-wired-review.py']},
                 schematic_sha256=digest(output))
    (audit_dir/'layout.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(f'Wrote {output}: {len(parts)} components; {len(segments)} unlabeled wire segments. No solver invoked.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=CASE/'circuit/cell-filter-16-cells-with-wires.sch')
    parser.add_argument('--audit-dir', type=Path, default=ROOT/'build/cell-voltage-input-filter/balancing-review')
    parser.add_argument('--force', action='store_true', help='Overwrite the requested output; never used implicitly.')
    args = parser.parse_args()
    generate(args.output.resolve(), args.audit_dir.resolve(), args.force)
