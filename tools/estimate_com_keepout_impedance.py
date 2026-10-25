#!/usr/bin/env python3
# SPDX-License-Identifier: CERN-OHL-P-2.0
"""Estimate a plane-free, soldermask-coated coplanar strip pair.

Independent 2-D electrostatic finite-volume estimate, not a qualified fab solver.
Requires numpy and scipy. Reads the saved KiCad stackup; never changes the design.
See docs/CMU-007-si-pi-analysis.md for assumptions, convergence and applicability.
"""

import argparse
import json
import math
from pathlib import Path
import re

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from scipy.special import ellipk


ETA0 = 376.730313668


def stackup_inputs():
    root = Path(__file__).resolve().parents[1]
    stem = root / 'design' / 'battery_management_system_cell_monitoring_unit'
    board = stem.with_suffix('.kicad_pcb').read_text(encoding='utf-8')
    stack = board.split('(stackup', 1)[1].split('(copper_finish', 1)[0]
    sections = re.split(r'\(layer "', stack)[1:]
    layers = {s.split('"', 1)[0]: s for s in sections}
    thickness = lambda s: sum(float(v) for v in re.findall(r'\(thickness\s+([\d.]+)', s))
    dielectric = [s for name, s in layers.items() if name.startswith('dielectric ')]
    ers = {float(v) for s in dielectric for v in re.findall(r'\(epsilon_r\s+([\d.]+)', s)}
    if len(ers) != 1:
        raise ValueError('This model requires a uniform substrate Dk; review changed stackup.')
    # In etched inner-layer regions, the nominal copper-layer thickness is resin-filled.
    h = sum(thickness(s) for s in dielectric)
    h += sum(thickness(s) for name, s in layers.items() if re.fullmatch(r'In\d+\.Cu', name))
    return dict(substrate_mm=h, copper_mm=thickness(layers['F.Cu']),
                substrate_er=ers.pop(), mask_mm=thickness(layers['F.Mask']),
                bottom_mask_mm=thickness(layers['B.Mask']))


def mesh_axis(low, high, fine_low, fine_high, step, landmarks):
    """Uniform near the conductor; geometric expansion into remote space."""
    n = int(math.ceil((fine_high-fine_low)/step))
    points = list(np.linspace(fine_low, fine_high, n+1))
    for direction, start, stop in [(-1, fine_low, low), (1, fine_high, high)]:
        v, delta = start, step
        while direction*(stop-v) > 1e-12:
            delta *= 1.12
            v += direction*min(delta, abs(stop-v))
            points.append(v)
    # Exact conductor and dielectric boundaries; remove nearly duplicate mesh points.
    points.extend(v for v in landmarks if low <= v <= high)
    return np.array(sorted(set(round(float(v), 12) for v in points)))


def solve(width, gap, cfg, step, extent, coat, mask_er, air=False, copper=None):
    """Return odd-mode charge/eps0 per volt, using V+=1, V-= -1."""
    h, t = cfg['substrate_mm'], cfg['copper_mm'] if copper is None else copper
    m, mb, er = cfg['mask_mm'], cfg['bottom_mask_mm'], cfg['substrate_er']
    a, b = gap/2, gap/2+width
    if extent <= max(b+0.15, h+mb):
        raise ValueError('Domain must contain conductor, substrate and remote air.')
    # Ensure fine cells land on all conductor boundaries without tiny sliver cells.
    xfine = math.ceil((b+m+0.10)/step)*step
    ylow = -math.ceil(0.10/step)*step
    yhigh = math.ceil((t+m+0.10)/step)*step
    x = mesh_axis(0, extent, 0, xfine, step, [0, a, b, b+m])
    y = mesh_axis(-extent, extent, ylow, yhigh, step, [-h-mb, -h, 0, t, m, t+m])
    nx, ny = len(x), len(y)
    X, Y = np.meshgrid(x, y)
    metal = ((X >= a-1e-10) & (X <= b+1e-10) &
             (Y >= -1e-10) & (Y <= t+1e-10))
    fixed = metal.copy()
    fixed[[0, -1], :] = True
    fixed[:, [0, -1]] = True
    value = metal.astype(float).ravel()
    free = ~fixed.ravel()
    index = np.full(nx*ny, -1, dtype=int)
    index[free] = np.arange(free.sum())

    def eps(xp, yp):
        xp, yp = np.broadcast_arrays(xp, yp)
        e = np.ones(xp.shape)
        if air:
            return e
        e[(yp < 0) & (yp > -h)] = er
        if coat != 'bare':
            e[(yp <= -h) & (yp > -h-mb)] = mask_er
            if coat == 'flat':
                e[(yp >= 0) & (yp < t+m)] = mask_er
            elif coat == 'conformal':
                dx = np.maximum(np.maximum(a-xp, xp-b), 0)
                dy = np.maximum(yp-t, 0)
                coating = (yp >= 0) & ((yp < m) | (dx*dx+dy*dy < m*m))
                e[coating] = mask_er
        return e

    # Node-centred finite volumes. Face conductance = integral(eps dl)/distance.
    # Four-point Gaussian quadrature on each half-face respects interfaces at nodes.
    q, qw = np.polynomial.legendre.leggauss(4)
    def integrated_face(mid, lo, center, hi, horizontal):
        total = 0
        for v0, v1 in [(lo, center), (center, hi)]:
            for node, weight in zip(q, qw):
                v = (v0+v1)/2 + node*(v1-v0)/2
                total = total + weight*(v1-v0)/2*(eps(mid, v) if horizontal else eps(v, mid))
        return total

    yl = np.r_[y[0], (y[:-1]+y[1:])/2][:, None]
    yu = np.r_[(y[:-1]+y[1:])/2, y[-1]][:, None]
    xl = np.r_[x[0], (x[:-1]+x[1:])/2][None, :]
    xu = np.r_[(x[:-1]+x[1:])/2, x[-1]][None, :]
    gx = integrated_face((x[:-1]+x[1:])[None, :]/2, yl, y[:, None], yu, True)/np.diff(x)[None, :]
    gy = integrated_face((y[:-1]+y[1:])[:, None]/2, xl, x[None, :], xu, False)/np.diff(y)[:, None]
    nodes = np.arange(nx*ny).reshape(ny, nx)
    u = np.r_[nodes[:, :-1].ravel(), nodes[:-1, :].ravel()]
    v = np.r_[nodes[:, 1:].ravel(), nodes[1:, :].ravel()]
    g = np.r_[gx.ravel(), gy.ravel()]
    rows, cols, data = [], [], []
    rhs = np.zeros(free.sum())
    for first, second in [(u, v), (v, u)]:
        use = free[first]
        rows.append(index[first[use]]); cols.append(index[first[use]]); data.append(g[use])
        both = use & free[second]
        rows.append(index[first[both]]); cols.append(index[second[both]]); data.append(-g[both])
        boundary = use & ~free[second]
        np.add.at(rhs, index[first[boundary]], g[boundary]*value[second[boundary]])
    matrix = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                        shape=(len(rhs), len(rhs))).tocsc()
    potential = value.copy()
    potential[free] = spsolve(matrix, rhs)
    residual = np.max(np.abs(matrix@potential[free]-rhs))
    if not np.all(np.isfinite(potential)) or residual > 1e-8:
        raise RuntimeError(f'Electrostatic solution failed: residual={residual}')
    is_metal = metal.ravel()
    outward = is_metal[u] & ~is_metal[v]
    inward = is_metal[v] & ~is_metal[u]
    charge = np.sum(g[outward]*(potential[u[outward]]-potential[v[outward]]))
    charge += np.sum(g[inward]*(potential[v[inward]]-potential[u[inward]]))
    return dict(c_over_eps0=float(charge), residual=float(residual), unknowns=int(free.sum()))


def thin_strip_analytic(width, gap, er):
    """Infinite-substrate, zero-metal-thickness CPS cross-check (no soldermask)."""
    k = gap/(gap+2*width)
    return ETA0/math.sqrt((er+1)/2)*ellipk(k*k)/ellipk(1-k*k)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--width', type=float, required=True, help='Each trace width, mm')
    parser.add_argument('--gap', type=float, default=0.20, help='Edge-to-edge pair gap, mm')
    parser.add_argument('--step', type=float, default=0.005, help='Near-conductor cell size, mm')
    parser.add_argument('--extent', type=float, default=16.0, help='Remote half-domain extent, mm')
    parser.add_argument('--mask-er', type=float, default=3.3, help='Unconfirmed soldermask Dk')
    parser.add_argument('--substrate-er', type=float, help='Optional sensitivity override')
    parser.add_argument('--coat', choices=['all', 'bare', 'flat', 'conformal'], default='all')
    parser.add_argument('--thin-check', action='store_true', help='Zero-thickness, thick-substrate analytic validation')
    args = parser.parse_args()
    if min(args.width, args.gap, args.step, args.extent, args.mask_er) <= 0:
        parser.error('Dimensions and permittivities must be positive')
    cfg = stackup_inputs()
    if args.substrate_er is not None:
        cfg['substrate_er'] = args.substrate_er
    if args.thin_check:
        cfg['substrate_mm'] = args.extent*0.95
    copper = 0.0 if args.thin_check else None
    air = solve(args.width, args.gap, cfg, args.step, args.extent, 'bare', args.mask_er, air=True, copper=copper)
    result = dict(model='Plane-free coplanar strip pair, quasi-TEM finite volume',
                  inputs=cfg, mask_er_assumed=args.mask_er, width_mm=args.width,
                  edge_gap_mm=args.gap, step_mm=args.step, extent_mm=args.extent, air=air,
                  thin_strip_infinite_substrate_ohm=thin_strip_analytic(args.width,args.gap,cfg['substrate_er']),
                  results={})
    coats = ['bare'] if args.thin_check else (['bare','flat','conformal'] if args.coat == 'all' else [args.coat])
    for coat in coats:
        solution = solve(args.width,args.gap,cfg,args.step,args.extent,coat,args.mask_er,copper=copper)
        solution['zdiff_ohm'] = 2*ETA0/math.sqrt(air['c_over_eps0']*solution['c_over_eps0'])
        result['results'][coat] = solution
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
