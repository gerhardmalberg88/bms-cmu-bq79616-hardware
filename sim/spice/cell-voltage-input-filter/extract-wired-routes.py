#!/usr/bin/env python3
"""Read-only track-graph evidence for the wired review; does not simulate.

SPDX-License-Identifier: CERN-OHL-P-2.0
"""
import argparse
import hashlib
import heapq
import json
import math
from collections import defaultdict
from pathlib import Path
import pcbnew

CASE = Path(__file__).resolve().parent
ROOT = CASE.parents[2]

def route(n, board, footprints, topology):
 net=f'/balance/CB{n}';row=topology['taps'][n];graph=defaultdict(list);pts=set();tracks=[];vias=[]
 def key(p,layer):return (p.x,p.y,layer)
 for x in board.GetTracks():
  if x.GetNetname()!=net:continue
  if isinstance(x,pcbnew.PCB_VIA):vias.append(x);continue
  if isinstance(x,pcbnew.PCB_ARC):raise ValueError('Arc not implemented')
  a=key(x.GetStart(),x.GetLayer());z=key(x.GetEnd(),x.GetLayer());pts.update([a,z]);tracks.append((a,z,pcbnew.ToMM(x.GetWidth())))
 pads=[]
 for ref in [row['cb_cap'],'U201']:
  pad=next(p for p in footprints[ref].Pads() if p.GetNetname()==net)
  k=key(pad.GetPosition(),pad.GetLayer());pads.append(k);pts.add(k)
 for via in vias:
  for layer in {a[2] for a in pts}:
   if via.IsOnLayer(layer):pts.add(key(via.GetPosition(),layer))
 def edge(a,z,length,width,via=False):
  r=.002 if via else 1.724e-8*length*1e-3/(width*1e-3*18e-6)
  info={'length_mm':length,'resistance_ohm':r,'via':via}
  graph[a].append((z,info));graph[z].append((a,info))
 for a,z,width in tracks:
  dx=z[0]-a[0];dy=z[1]-a[1]
  candidates=[p for p in pts if p[2]==a[2] and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)<=1 and min(a[0],z[0])<=p[0]<=max(a[0],z[0]) and min(a[1],z[1])<=p[1]<=max(a[1],z[1])]
  candidates.sort(key=lambda p:(p[0]-a[0])**2+(p[1]-a[1])**2)
  for u,v in zip(candidates,candidates[1:]):edge(u,v,math.hypot(v[0]-u[0],v[1]-u[1])/1e6,width)
 for via in vias:
  nodes=[p for p in pts if p[:2]==(via.GetPosition().x,via.GetPosition().y) and via.IsOnLayer(p[2])]
  for u,v in zip(sorted(nodes),sorted(nodes)[1:]):edge(u,v,0,0,True)
 start,end=pads;dist={start:0};previous={};q=[(0,start)]
 while q:
  cost,u=heapq.heappop(q)
  if cost!=dist[u]:continue
  if u==end:break
  for v,info in graph[u]:
   new=cost+info['length_mm']+(1e-9 if info['via'] else 0)
   if new<dist.get(v,math.inf):dist[v]=new;previous[v]=(u,info);heapq.heappush(q,(new,v))
 if end not in dist:raise ValueError(f'No route for {n} between {start} and {end}')
 path=[];v=end
 while v!=start:
  u,info=previous[v];path.append(dict(start=u,end=v,**info));v=u
 return {'tap':n,'cap_ref':row['cb_cap'],'cb_pin':row['cb_pin'],'length_mm':sum(x['length_mm'] for x in path),'resistance_ohm':sum(x['resistance_ohm'] for x in path),'vias':sum(x['via'] for x in path),'path':list(reversed(path))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        parser.error('Output exists; use a new path or explicitly pass --force.')
    topology = json.loads((CASE/'topology.json').read_text())
    def hashes():
        return {rel: hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
                for rel in topology['source_hashes']}
    before = hashes()
    if before != topology['source_hashes']:
        raise ValueError('Design no longer matches saved topology; no extraction performed.')
    board = pcbnew.LoadBoard(str(ROOT/'design/battery_management_system_cell_monitoring_unit.kicad_pcb'))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    rows = [route(n, board, footprints, topology) for n in range(17)]
    if hashes() != before:
        raise RuntimeError('Design changed during read-only routing extraction.')
    result = {
        'schema_version': 1, 'source_hashes': before,
        'method': 'Read-only KiCad track endpoint graph; shortest routed distance from the tap-n capacitor pad to U201 CBn pad. Vias join layers with zero planar length, separately counted.',
        'assumptions': [
            '18 um copper; R=rho*l/(width*thickness), rho=1.724e-8 ohm m; 2 mOhm per via.',
            'L remains an assumed nH/mm coefficient plus assumed via inductance, not a field solution.',
            'Neighboring capacitor landing stubs collapse to one capacitor-bank node per CB net. Remaining total route impedance stays upstream; this is a lumped approximation, not the exact distributed copper network.'
        ], 'routes': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('Extracted 17 CB paths; source hashes unchanged; no simulation.')


if __name__ == '__main__':
    main()
