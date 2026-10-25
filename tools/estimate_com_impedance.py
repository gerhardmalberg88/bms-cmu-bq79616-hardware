#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Read the CMU project and reproduce its preliminary UNCOATED microstrip estimate.

Equations: NI Ultiboard User Manual, Differential Impedance Calculator,
https://download.ni.com/support/manuals/374488c.pdf
Scope and limitations: docs/CMU-007-si-pi-analysis.md, section 2.1.
Uses Python's standard library only. Does not modify design files.
"""

import json
import math
from pathlib import Path
import re


def estimate(width_mm, gap_mm, height_mm, copper_mm, er):
    """Return isolated-line Z0, differential Z, and odd-mode Z in ohms."""
    z0 = 87 / math.sqrt(er + 1.41) * math.log(
        5.98 * height_mm / (0.8 * width_mm + copper_mm)
    )
    zdiff = 2 * z0 * (1 - 0.48 * math.exp(-0.96 * gap_mm / height_mm))
    return z0, zdiff, zdiff / 2


def main():
    root = Path(__file__).resolve().parents[1]
    stem = root / 'design' / 'battery_management_system_cell_monitoring_unit'
    board = stem.with_suffix('.kicad_pcb').read_text(encoding='utf-8')
    project = json.loads(stem.with_suffix('.kicad_pro').read_text(encoding='utf-8'))
    netclass = next(c for c in project['net_settings']['classes'] if c['name'] == 'CMU_COM_TOP')

    # Restrict extraction to the stackup, excluding the board layer-name list.
    stackup = board.split('(stackup', 1)[1]
    copper_section = stackup.split('(layer "F.Cu"', 1)[1].split('(layer ', 1)[0]
    dielectric_section = stackup.split('(layer "dielectric 1"', 1)[1].split('(layer ', 1)[0]
    thickness = float(re.search(r'\(thickness\s+([0-9.]+)', copper_section)[1])
    height = sum(float(v) for v in re.findall(r'\(thickness\s+([0-9.]+)', dielectric_section))
    permittivities = {float(v) for v in re.findall(r'\(epsilon_r\s+([0-9.]+)', dielectric_section)}
    if len(permittivities) != 1:
        raise ValueError('This simple model requires equal Dk in all first-dielectric plies.')
    er = permittivities.pop()
    width, gap = netclass['diff_pair_width'], netclass['diff_pair_gap']
    z0, zdiff, zodd = estimate(width, gap, height, thickness, er)
    target = 100.0  # Project intent, not a BQ79616 numerical requirement.
    coupling = 1 - 0.48 * math.exp(-0.96 * gap / height)
    target_z0 = target / (2 * coupling)
    synthesized_width = (
        5.98 * height / math.exp(target_z0 * math.sqrt(er + 1.41) / 87) - thickness
    ) / 0.8

    print(json.dumps({
        'model': 'Preliminary uncoated differential microstrip approximation',
        'netclass': netclass['name'],
        'scope': 'F.Cu over continuous In1.Cu reference only; excludes isolation keepouts',
        'height_mm': height,
        'finished_copper_mm': thickness,
        'er_placeholder': er,
        'width_mm': width,
        'edge_gap_mm': gap,
        'project_target_ohm': target,
        'uncoated_synthesized_width_mm': round(synthesized_width, 6),
        'isolated_trace_z0_ohm': round(z0, 3),
        'differential_ohm': round(zdiff, 3),
        'odd_mode_ohm': round(zodd, 3),
        'excludes': ['soldermask', 'etch shape', 'nearby copper', 'dispersion', 'losses',
                     'pads and vias', 'filters and transformers', 'cable'],
        'status': 'Uncoated cross-check only; the selected width uses the coated estimate in CMU-007. Requires confirmed pressed stackup, Dk and mask construction.'
    }, indent=2))


if __name__ == '__main__':
    main()
