#!/usr/bin/env python3
"""Read-only population, connectivity and routed-geometry evidence from KiCad.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
CASE = Path(__file__).resolve().parent
BOARD = ROOT / 'design/battery_management_system_cell_monitoring_unit.kicad_pcb'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def extract():
    import pcbnew
    sys.path.insert(0, str(ROOT / 'tools'))
    from gen_doc_tables import parse
    scratch = ROOT / 'build/cell-voltage-input-filter'
    scratch.mkdir(parents=True, exist_ok=True)
    before = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / 'design').glob('*.kicad_sch'))}
    before[str(BOARD.relative_to(ROOT))] = digest(BOARD)
    netlist = scratch / 'design.net'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                    '-o', str(netlist), str(ROOT / 'design/battery_management_system_cell_monitoring_unit.kicad_sch')], check=True)
    pin_net, comps = parse(netlist.read_text())
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    pins = {}
    selected = set()

    def check(ref):
        f = footprints[ref]
        if f.IsDNP():
            raise ValueError(f'Required fitted part is DNP: {ref}')
        for pad in f.Pads():
            if (ref, pad.GetNumber()) in pin_net:
                actual = pad.GetNetname()
                if actual != pin_net[ref, pad.GetNumber()]:
                    raise ValueError(f'PCB/schematic mismatch: {ref}.{pad.GetNumber()}')
                pins[ref + '.' + pad.GetNumber()] = actual
        selected.add(ref)

    def unique(prefix, nets, value):
        found = [r for r, c in comps.items() if r.startswith(prefix) and value in c['value']
                 and r in footprints and not footprints[r].IsDNP()
                 and {n for (rr, _), n in pin_net.items() if rr == r} == set(nets)]
        if len(found) != 1:
            raise ValueError(f'Expected one {prefix} {value} on {nets}: {found}')
        check(found[0])
        return found[0]

    check('U201'); check('J401'); check('R202'); check('C208')
    taps = []
    for n in range(17):
        tap = 'GND' if n == 0 else '+BATT' if n == 16 else f'/balance/cell{n}'
        vc, cb = f'/balance/VC{n}', f'/balance/CB{n}'
        fuse = unique('F4', [tap, f'Net-(J401-Pin_{1 if n == 0 else (n+1)//2+10 if n%2 else n//2+1})'], '500mA')
        connector_net = next(v for (r, p), v in pin_net.items() if r == fuse and v != tap)
        jpin = next(p for (r, p), v in pin_net.items() if r == 'J401' and v == connector_net)
        taps.append(dict(tap=n, board_net=tap, connector_pin=jpin, fuse=fuse,
                         sense=unique('R3', [tap, vc], '100R'), balance=unique('R3', [tap, cb], '20R'),
                         vc_cap=unique('C3', [vc, f'/balance/VC{n-1}' if n else 'GND'], '470nF'),
                         cb_cap=unique('C3', [cb, f'/balance/CB{n-1}' if n else 'GND'], '470nF'),
                         vc_pin=str(35-2*n), cb_pin=str(34-2*n)))
        if pin_net['U201', str(35-2*n)] != vc or pin_net['U201', str(34-2*n)] != cb:
            raise ValueError(f'Unexpected U201 mapping at tap {n}')

    # Inventory actual routed copper. Branch-net totals are NOT point-to-point
    # series paths: retain them as geometry evidence, never sum them into series R.
    inventory = defaultdict(lambda: dict(length_mm=0., widths_mm=set(), layers=set(), vias=0))
    relevant = set(pins.values())
    for track in board.GetTracks():
        net = track.GetNetname()
        if net not in relevant:
            continue
        row = inventory[net]
        if isinstance(track, pcbnew.PCB_VIA):
            row['vias'] += 1
        else:
            row['length_mm'] += pcbnew.ToMM(track.GetLength())
            row['widths_mm'].add(round(pcbnew.ToMM(track.GetWidth()), 6))
            row['layers'].add(board.GetLayerName(track.GetLayer()))
    for row in inventory.values():
        row['widths_mm'] = sorted(row['widths_mm']); row['layers'] = sorted(row['layers'])
    dnp = sorted(r for r, f in footprints.items() if r.startswith('R3') and f.IsDNP())
    # Unique VC/CB resistor-to-IC nets permit a bounded route estimate. Include
    # the capacitor stubs in total routed length: deliberately conservative, not
    # a field extraction. Fused shared nets require a separate editable estimate.
    geometry = {}
    for n in range(17):
        geometry[str(n)] = {}
        for kind in ('VC', 'CB'):
            row = inventory[f'/balance/{kind}{n}']
            width = min(row['widths_mm']) if row['widths_mm'] else .25
            length = row['length_mm']
            geometry[str(n)][kind] = dict(length_mm=length, width_mm=width, vias=row['vias'],
                resistance_ohm=1.724e-8*(length*1e-3)/(width*1e-3*18e-6)+row['vias']*.002,
                note='Upper route estimate: includes stubs; all tracks treated as 18 um copper; 2 mOhm/via assumed. No zone-current extraction.')
    for rel, h in before.items():
        if digest(ROOT / rel) != h:
            raise RuntimeError('Design changed during read-only extraction: ' + rel)
    result = dict(schema_version=1, source_hashes=before, taps=taps, pins=pins,
                  components={r: comps[r] for r in sorted(selected)}, dnp_links=dnp,
                  dnp_nets={r: [pin_net[r, str(p)] for p in (1, 2)] for r in dnp},
                  geometry=geometry, routed_inventory=dict(sorted(inventory.items())),
                  licenses='Design-derived facts; no third-party model code imported',
                  limitations=['PCB route R is conservative, not a solved resistance network.',
                               'Shunt/mutual C and L remain assumptions; no FEM extraction claimed.'])
    write_json(CASE / 'topology.json', result)
    return result


if __name__ == '__main__':
    result = extract()
    print(f'Verified {len(result["taps"])} taps, {len(result["components"])} fitted parts; design bytes unchanged.')
